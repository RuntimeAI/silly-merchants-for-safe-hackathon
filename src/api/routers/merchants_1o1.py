from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError
from typing import Dict, Optional, List, Any, AsyncGenerator
import uuid
import logging
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from src.spaces.merchants_1o1.runtime.negotiation import NegotiationRuntime
from datetime import datetime
from src.utils.logger import GameLogger
from src.utils.json_utils import game_json_dumps  # Add this import
from ..events.manager import GameEventManager
import os
from src.utils.fileverse_client import FileverseClient

# Setup router logger
logger = logging.getLogger("merchants_1o1_router")
logger.setLevel(logging.INFO)

# Create a thread pool executor for running the game
executor = ThreadPoolExecutor(max_workers=4)

router = APIRouter(prefix="/merchants_1o1", tags=["merchants_1o1"])

# Store active games
active_games: Dict[str, tuple[NegotiationRuntime, GameEventManager]] = {}

# Initialize fileverse client
fileverse = FileverseClient()

class GameInitRequest(BaseModel):
    strategy_advisory: str
    debug_mode: Optional[bool] = False

class GameMessage(BaseModel):
    round: int
    speaker: str
    message: str
    timestamp: datetime

class GameTransfer(BaseModel):
    round: int
    sender: str
    recipient: str
    amount: int
    timestamp: datetime

class GameResponse(BaseModel):
    game_id: str
    status: str
    current_round: Optional[int] = None
    standings: Optional[Dict[str, int]] = None
    winner: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    transfer_history: Optional[List[Dict[str, Any]]] = None
    log_messages: List[str] = []

class GameStartRequest(BaseModel):
    strategy_advisory: str

async def process_game_in_thread(game: NegotiationRuntime):
    """Run game in a thread and return result"""
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, game.run)
    except Exception as e:
        logger.error(f"Error running game: {str(e)}")
        return {'error': str(e)}

async def game_stream(game: NegotiationRuntime) -> AsyncGenerator[str, None]:
    """Stream game events"""
    queue = asyncio.Queue()
    current_round_logs = []
    
    try:
        # Send initial game state
        initial_state = {
            'type': 'init',
            'standings': game.get_player_statuses()
        }
        yield f"data: {json.dumps(initial_state)}\n\n"
        await asyncio.sleep(0.1)
        
        # Setup logging handler
        class AsyncQueueHandler(logging.Handler):
            def emit(self, record):
                try:
                    message = self.format(record)
                    current_round_logs.append(message)
                    
                    # Check if this is the end of a player's turn
                    if "------------------------" in message:
                        event_data = {
                            'type': 'turn_complete',
                            'messages': current_round_logs.copy(),
                            'standings': game.get_player_statuses(),
                            'timestamp': datetime.now().isoformat()
                        }
                        current_round_logs.clear()
                        
                        # Schedule event sending
                        loop = asyncio.get_running_loop()
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(queue.put(event_data))
                        )
                except Exception as e:
                    logger.error(f"Error in AsyncQueueHandler: {str(e)}")

        # Add queue handler to game logger
        queue_handler = AsyncQueueHandler()
        queue_handler.setFormatter(logging.Formatter('%(message)s'))
        game.logger.addHandler(queue_handler)

        try:
            # Start game processing
            game_task = asyncio.create_task(process_game_in_thread(game))
            
            # Stream events while game is running
            while not game_task.done():
                try:
                    # Get next log message with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing event: {str(e)}")
                    continue

            # Process game result
            result = await game_task
            if 'error' in result:
                yield f"data: {json.dumps({'type': 'error', 'message': result['error']})}\n\n"
            else:
                # Send any remaining logs
                if current_round_logs:
                    final_logs = {
                        'type': 'turn_complete',
                        'messages': current_round_logs,
                        'standings': game.get_player_statuses(),
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(final_logs)}\n\n"
                
                # Send game completion event
                completion_event = {
                    'type': 'game_over',
                    'winner': result['winner'],
                    'final_standings': result['final_statuses'],
                    'conversation_history': result['conversation_memory'].messages,
                    'transfer_history': result['conversation_memory'].transfers
                }
                yield f"data: {json.dumps(completion_event)}\n\n"

        except asyncio.CancelledError:
            logger.info("Stream cancelled by client")
            raise
        
    except Exception as e:
        logger.error(f"Error in game stream: {str(e)}")
        error_data = {
            'type': 'error',
            'message': str(e)
        }
        yield f"data: {json.dumps(error_data)}\n\n"
    
    finally:
        # Cleanup
        game.logger.removeHandler(queue_handler)
        if game_id := next((id for id, g in active_games.items() if g[0] == game), None):
            del active_games[game_id]

@router.post("/games")
async def create_game(
    background_tasks: BackgroundTasks,
    debug: Optional[bool] = False
):
    """Create a new game"""
    # Set debug mode in environment BEFORE creating anything
    if debug:
        os.environ['DEBUG_MODE'] = 'true'
        logger.info("🐛 Creating game in DEBUG mode")
    else:
        os.environ['DEBUG_MODE'] = 'false'
    
    game_id = str(uuid.uuid4())
    event_manager = GameEventManager(game_id)
    game_logger = GameLogger(game_id)
    
    # Initialize game with event manager
    game = NegotiationRuntime(logger=game_logger, event_manager=event_manager)
    active_games[game_id] = (game, event_manager)
    
    # Log the actual number of rounds
    logger.info(f"Game created with {game.max_rounds} rounds (Debug mode: {debug})")
    
    # Emit initial game state
    await event_manager.emit_system("game_created", {
        "game_id": game_id,
        "status": "created",
        "debug_mode": debug,
        "max_rounds": game.max_rounds,
        "players": {
            "Marco Polo": {"coins": 10},
            "Trader Joe": {"coins": 10}
        }
    })
    
    return {
        "game_id": game_id, 
        "debug_mode": debug,
        "max_rounds": game.max_rounds
    }

@router.post("/games/{game_id}/start")
async def start_game(game_id: str, request: GameStartRequest):
    """Start a game with the given ID"""
    logger.info(f"Starting game: {game_id} with request: {request}")  # Add request logging
    
    if game_id not in active_games:
        logger.warning(f"Game not found: {game_id}")
        raise HTTPException(404, "Game not found")
    
    try:
        game, event_manager = active_games[game_id]
        
        # Emit game start event
        await event_manager.emit_system("game_started", {
            "game_id": game_id,
            "strategy": request.strategy_advisory
        })
        
        # Run game in background
        background_tasks = BackgroundTasks()
        background_tasks.add_task(run_game, game_id)
        
        return {
            "game_id": game_id,
            "status": "started",
            "message": "Game started successfully"
        }
        
    except ValidationError as e:  # Add specific error handling
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(422, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting game: {str(e)}")
        raise HTTPException(500, f"Error starting game: {str(e)}")

@router.get("/games/{game_id}/events")
async def stream_events(game_id: str):
    """Stream game events"""
    if game_id not in active_games:
        raise HTTPException(404, "Game not found")
    
    game, event_manager = active_games[game_id]
    
    async def event_generator():
        try:
            # Send initial keepalive
            yield ":\n\n"
            
            # Stream events
            async for event in event_manager.subscribe():
                yield event
                
        except Exception as e:
            logger.error(f"Error streaming events: {str(e)}")
            # Send error event
            error_event = {
                "type": "error",
                "name": "stream_error",
                "data": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {game_json_dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream',
            'X-Accel-Buffering': 'no'  # Disable proxy buffering
        }
    )

async def run_game(game_id: str):
    """Run game and emit events"""
    game, event_manager = active_games[game_id]
    
    try:
        # Run the complete game
        await game.run_game()
        
    except Exception as e:
        logger.error(f"Error in game {game_id}: {str(e)}")
        await event_manager.emit_error(str(e))
    
    finally:
        # Cleanup after sufficient delay
        await asyncio.sleep(10)
        if game_id in active_games:
            logger.info(f"Cleaning up game {game_id}")
            del active_games[game_id]

@router.get("/{game_id}/status")
async def get_game_status(game_id: str):
    logger.info(f"Getting status for game: {game_id}")
    
    if game_id not in active_games:
        logger.warning(f"Game not found: {game_id}")
        raise HTTPException(404, "Game not found")
    
    try:
        game, _ = active_games[game_id]
        standings = game.get_player_statuses()
        logs = game.get_logs()
        
        response = GameResponse(
            game_id=game_id,
            status="in_progress",
            standings=standings,
            log_messages=logs
        )
        logger.info(f"Returning status: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting game status: {str(e)}")
        raise HTTPException(500, f"Error getting game status: {str(e)}")

@router.post("/{game_id}/run")
async def run_game(game_id: str):
    logger.info(f"Running game: {game_id}")
    
    if game_id not in active_games:
        logger.warning(f"Game not found: {game_id}")
        raise HTTPException(404, "Game not found")
    
    try:
        game, _ = active_games[game_id]
        result = await game.run_game()
        logger.info(f"Game completed. Result: {result}")
        
        # Clean up finished game
        del active_games[game_id]
        logger.info(f"Game {game_id} removed from active games")
        
        return {
            "game_id": game_id,
            "status": "completed",
            "winner": result["winner"],
            "final_standings": result["final_statuses"],
            "log_messages": game.get_logs()
        }
        
    except Exception as e:
        logger.error(f"Error running game: {str(e)}")
        raise HTTPException(500, f"Error running game: {str(e)}")

@router.get("/stream/{game_id}")
async def stream_game(game_id: str, request: Request):
    async def event_generator():
        game_logger = GameLogger(game_id)
        runtime = NegotiationRuntime(logger=game_logger)  # Pass only the logger
        
        try:
            # Start game
            event = game_logger.log_game_start({
                "Marco Polo": {"coins": 10},
                "Trader Joe": {"coins": 10}
            })
            yield f"data: {json.dumps(event)}\n\n"
            
            # Run game
            for round_num in range(1, 6):
                # Round start
                event = game_logger.log_round_start(round_num, runtime.get_player_status())
                yield f"data: {json.dumps(event)}\n\n"
                
                # Player 1's turn
                events = runtime.process_player1_turn()
                for event in events:
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.1)  # Small delay for readability
                
                # Player 2's turn
                events = runtime.process_player2_turn()
                for event in events:
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.1)
                
                # Round summary
                event = game_logger.log_round_summary(round_num, runtime.get_round_summary())
                yield f"data: {json.dumps(event)}\n\n"
                
                if round_num < 5:
                    await asyncio.sleep(1)  # Pause between rounds
            
            # Game end
            event = game_logger.log_game_end()
            yield f"data: {json.dumps(event)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    ) 