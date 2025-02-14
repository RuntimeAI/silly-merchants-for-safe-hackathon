from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
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

# Setup router logger
logger = logging.getLogger("merchants_1o1_router")
logger.setLevel(logging.INFO)

# Create a thread pool executor for running the game
executor = ThreadPoolExecutor(max_workers=4)

router = APIRouter(prefix="/merchants_1o1", tags=["merchants_1o1"])

# Store active games
active_games: Dict[str, NegotiationRuntime] = {}

class GameInitRequest(BaseModel):
    strategy_advisory: str

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
        if game_id := next((id for id, g in active_games.items() if g == game), None):
            del active_games[game_id]

@router.post("/initiate")
async def initiate_game(request: GameInitRequest):
    try:
        game_id = str(uuid.uuid4())
        game_logger = GameLogger(game_id)
        game = NegotiationRuntime(logger=game_logger)
        
        # Store game
        active_games[game_id] = game
        
        async def event_stream():
            try:
                # Game start event
                yield {
                    "event": "game_start",
                    "data": {
                        "game_id": game_id,
                        "players": {
                            "Marco Polo": {"coins": 10},
                            "Trader Joe": {"coins": 10}
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                }

                # Process each round
                for round_num in range(1, 6):
                    # Round start
                    yield {
                        "event": "round_start",
                        "data": {
                            "round": round_num,
                            "standings": game.get_player_statuses(),
                            "timestamp": datetime.now().isoformat()
                        }
                    }

                    # Player 1's turn
                    # Deep thinking (private)
                    thinking = game.player1.generate_thinking()
                    yield {
                        "event": "player_thinking",
                        "data": {
                            "round": round_num,
                            "player": "Marco Polo",
                            "thinking": thinking,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    # Action
                    action = game.player1.generate_action()
                    yield {
                        "event": "player_action",
                        "data": {
                            "round": round_num,
                            "player": "Marco Polo",
                            "message": action["message"],
                            "transfers": action["transfers"],
                            "timestamp": datetime.now().isoformat()
                        }
                    }

                    # Process transfers
                    game.process_transfers(game.player1, action["transfers"])
                    
                    # Player 2's turn (similar structure)
                    thinking = game.player2.generate_thinking()
                    yield {
                        "event": "player_thinking",
                        "data": {
                            "round": round_num,
                            "player": "Trader Joe",
                            "thinking": thinking,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    action = game.player2.generate_action()
                    yield {
                        "event": "player_action",
                        "data": {
                            "round": round_num,
                            "player": "Trader Joe",
                            "message": action["message"],
                            "transfers": action["transfers"],
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    game.process_transfers(game.player2, action["transfers"])

                    # Round summary
                    yield {
                        "event": "round_summary",
                        "data": {
                            "round": round_num,
                            "standings": game.get_player_statuses(),
                            "transfers": game.memory.transfers[-2:],  # Last 2 transfers
                            "messages": game.memory.messages[-2:],    # Last 2 messages
                            "timestamp": datetime.now().isoformat()
                        }
                    }

                    await asyncio.sleep(1)  # Pause between rounds

                # Game end
                final_status = game.get_player_statuses()
                winner = max(final_status.items(), key=lambda x: x[1])[0]
                
                yield {
                    "event": "game_end",
                    "data": {
                        "winner": winner,
                        "final_standings": final_status,
                        "history": {
                            "transfers": game.memory.transfers,
                            "messages": game.memory.messages
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                }

            except Exception as e:
                yield {
                    "event": "error",
                    "data": {
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                }

        async def format_events():
            async for event in event_stream():
                yield f"data: {game_json_dumps(event)}\n\n"  # Use custom encoder

        return StreamingResponse(
            format_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(500, f"Error initiating game: {str(e)}")

@router.get("/{game_id}/status")
async def get_game_status(game_id: str):
    logger.info(f"Getting status for game: {game_id}")
    
    if game_id not in active_games:
        logger.warning(f"Game not found: {game_id}")
        raise HTTPException(404, "Game not found")
    
    try:
        game = active_games[game_id]
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
        game = active_games[game_id]
        result = game.run()
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