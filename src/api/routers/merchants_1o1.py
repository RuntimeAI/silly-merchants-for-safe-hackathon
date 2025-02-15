from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
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
from src.utils.json_utils import game_json_dumps
from ..events.manager import GameEventManager
import os
from src.utils.fileverse_client import FileverseClient
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merchants_1o1_router")

# Create a thread pool executor for running the game
executor = ThreadPoolExecutor(max_workers=4)

router = APIRouter(prefix="/merchants_1o1", tags=["merchants_1o1"])

# Update log file path constants
LOGS_BASE_DIR = 'logs'
GAME_LOGS_DIR = os.path.join(LOGS_BASE_DIR, 'merchants_1o1')

# Create logs directory structure
os.makedirs(GAME_LOGS_DIR, exist_ok=True)

# Store active games
active_games: Dict[str, tuple[NegotiationRuntime, GameEventManager]] = {}
game_loggers = {}

# Initialize fileverse client
fileverse = FileverseClient()

def get_log_filename(game_id: str) -> str:
    """Generate log filename with game type and timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'game_1o1_{timestamp}_{game_id}.log'

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

def log_event(event_type: str, event_name: str, data: Dict[str, Any]):
    """Format and log game events"""
    timestamp = data.get('timestamp', '')
    
    if event_type == 'system':
        if event_name == 'game_created':
            logger.info(f"""
{Fore.GREEN}🎮 Game Created: {data.get('game_id')}
Debug Mode: {data.get('debug_mode')}
Max Rounds: {data.get('max_rounds')}
Players:{Style.RESET_ALL}""")
            for name, info in data.get('players', {}).items():
                logger.info(f"{Fore.CYAN}  • {name}: {info.get('coins')} coins{Style.RESET_ALL}")
                
        elif event_name == 'game_started':
            logger.info(f"""
{Fore.GREEN}🎯 Game Started: {data.get('game_id')}
Strategy Advisory:{Style.RESET_ALL}
{data.get('strategy', 'No strategy provided')}""")
            
    elif event_type == 'round':
        if event_name == 'round_started':
            logger.info(f"""
{Fore.YELLOW}📍 Round {data.get('round')} Started
Current Standings:{Style.RESET_ALL}""")
            for player, coins in data.get('standings', {}).items():
                logger.info(f"{Fore.CYAN}  • {player}: {coins} coins{Style.RESET_ALL}")
                
        elif event_name == 'round_ended':
            logger.info(f"""
{Fore.YELLOW}📊 Round {data.get('round')} Ended
Trades:{Style.RESET_ALL}""")
            for trade in data.get('trades', []):
                logger.info(f"{Fore.GREEN}  • {trade.get('from')} → {trade.get('to')}: {trade.get('amount')} coins{Style.RESET_ALL}")
            logger.info(f"{Fore.CYAN}Final Standings:{Style.RESET_ALL}")
            for player, coins in data.get('standings', {}).items():
                logger.info(f"{Fore.CYAN}  • {player}: {coins} coins{Style.RESET_ALL}")
                
    elif event_type == 'player':
        if event_name == 'player_thinking':
            logger.info(f"""
{Fore.MAGENTA}🤔 {data.get('player')}'s Thoughts:
{data.get('thinking', '')}{Style.RESET_ALL}""")
            
        elif event_name == 'player_action':
            action = data.get('action', {})
            logger.info(f"""
{Fore.GREEN}⚡ {data.get('player')}'s Action:
Message: {action.get('message', '')}
Transfers:{Style.RESET_ALL}""")
            for transfer in action.get('transfers', []):
                logger.info(f"{Fore.GREEN}  • To {transfer.get('recipient')}: {transfer.get('amount')} coins{Style.RESET_ALL}")

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
        logger.info(f"{Fore.GREEN}🐛 Creating game in DEBUG mode{Style.RESET_ALL}")
    else:
        os.environ['DEBUG_MODE'] = 'false'
    
    game_id = str(uuid.uuid4())
    event_manager = GameEventManager(game_id)
    game_logger = GameLogger(game_id, log_dir=GAME_LOGS_DIR)
    
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
async def start_game(
    game_id: str, 
    request: GameStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a game with the given ID"""
    try:
        logger = GameLogger(game_id, log_dir=GAME_LOGS_DIR)
        game_loggers[game_id] = logger
        logger.info(f"Starting game: {game_id}")
        
        if game_id not in active_games:
            raise HTTPException(404, "Game not found")
            
        game, event_manager = active_games[game_id]
        if game.state != "created":
            raise HTTPException(400, "Game already started")
            
        if request.strategy_advisory:
            game.set_strategy(request.strategy_advisory)
        
        # Run game in background
        background_tasks.add_task(game.run_game)
        
        return {"status": "Game started successfully"}
        
    except Exception as e:
        logger.error(f"Error starting game: {str(e)}")
        raise HTTPException(500, f"Error starting game: {str(e)}")

def get_event_manager(game_id: str) -> GameEventManager:
    """Get or create event manager for a game"""
    if game_id not in active_games:
        raise HTTPException(404, "Game not found")
        
    game, event_manager = active_games[game_id]
    return event_manager

@router.get("/games/{game_id}/events")
async def stream_game_events(
    game_id: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> EventSourceResponse:
    """Stream game events using Server-Sent Events (SSE)"""
    try:
        # Get or create event manager for this game
        event_manager = get_event_manager(game_id)
        
        # Setup file logging independently
        background_tasks.add_task(setup_game_file_logging, game_id)
        
        # Return SSE response
        return EventSourceResponse(
            event_manager.subscribe(request),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming events: {str(e)}")
        raise HTTPException(500, f"Error streaming events: {str(e)}")

async def setup_game_file_logging(game_id: str):
    """Setup file logging for a game without blocking the main flow"""
    try:
        # Create game-specific log file with timestamp
        log_filename = get_log_filename(game_id)
        log_file = os.path.join(GAME_LOGS_DIR, log_filename)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Get game logger
        game_logger = logging.getLogger(f"game_{game_id}")
        
        # Remove any existing handlers to avoid duplicates
        for handler in game_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                game_logger.removeHandler(handler)
                
        # Add new handler and set level
        game_logger.addHandler(file_handler)
        game_logger.setLevel(logging.DEBUG)
        
        game_logger.info(f"Game file logging initialized for game {game_id}")
        
    except Exception as e:
        logger.error(f"Error setting up game file logging: {str(e)}")

async def run_game(game_id: str):
    """Run game and emit events"""
    game, event_manager = active_games[game_id]
    logger.info(f"Running game {game_id}")
    
    try:
        # Initialize round
        round_num = 1
        game.round = round_num  # Set initial round
        
        # Game loop
        while round_num <= game.max_rounds:
            logger.info(f"Starting round {round_num}")
            
            # Round start
            await event_manager.emit_system("round_started", {
                "round": round_num,
                "standings": game.get_player_statuses()
            })
            
            # Player 1's turn
            logger.info("Processing Player 1's turn")
            for event in game.process_player1_turn():
                await event_manager.emit(event["type"], event["name"], event["data"])
                await asyncio.sleep(0.5)  # Add delay between events
            
            # Player 2's turn
            logger.info("Processing Player 2's turn")
            for event in game.process_player2_turn():
                await event_manager.emit(event["type"], event["name"], event["data"])
                await asyncio.sleep(0.5)  # Add delay between events
            
            # Round end
            await event_manager.emit_system("round_ended", {
                "round": round_num,
                "standings": game.get_player_statuses(),
                "summary": game.get_round_summary()
            })
            
            round_num += 1
            game.round = round_num  # Update round number
            await asyncio.sleep(1)  # Pause between rounds
        
        # Game end
        logger.info("Game completed")
        final_state = {
            "winner": game.get_winner(),
            "standings": game.get_player_statuses()
        }
        await event_manager.emit_system("game_ended", final_state)
        
        # Upload game summary
        try:
            logger.info("Uploading game summary...")
            upload_result = await upload_game_summary(game_id, game.get_event_history())
            
            if upload_result:
                # Append URLs to log file
                log_filename = get_log_filename(game_id)
                log_file_path = os.path.join(GAME_LOGS_DIR, log_filename)
                with open(log_file_path, 'a') as f:
                    f.write(f"\n\n=== Game Summary ===")
                    f.write(f"\nGame ID: {game_id}")
                    f.write(f"\nTimestamp: {datetime.now().isoformat()}")
                    f.write(f"\nIPFS Hash: {upload_result['ipfs_hash']}")
                    f.write(f"\nIPFS URL: {upload_result['ipfs_url']}")
                    f.write(f"\nLocal Log: {upload_result['log_file']}")
                    f.write("\n==================\n")
                
                # Emit upload complete event
                await event_manager.emit_system("upload_complete", upload_result)
                
            # Always emit session end event
            await event_manager.emit_system("session_ended", {
                "game_id": game_id,
                "message": "Game session completed",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            # Emit error and session end
            await event_manager.emit_system("upload_complete", {
                "error": str(e),
                "message": "Failed to upload game summary"
            })
            await event_manager.emit_system("session_ended", {
                "game_id": game_id,
                "message": "Game session completed with errors",
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error in game {game_id}: {str(e)}")
        await event_manager.emit_error(str(e))
        
    finally:
        # Clean up game resources
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
        game_logger = GameLogger(game_id, log_dir=GAME_LOGS_DIR)
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

async def upload_game_summary(game_id: str, events: list) -> dict:
    """Upload game summary to Fileverse"""
    try:
        client = FileverseClient()
        
        # Get log file content
        log_filename = get_log_filename(game_id)
        log_file_path = os.path.join(GAME_LOGS_DIR, log_filename)
        
        if not os.path.exists(log_file_path):
            raise Exception(f"Log file not found: {log_file_path}")
            
        # Read the complete log file
        with open(log_file_path, 'r') as f:
            log_content = f.read()
        
        # Prepare upload data with full log content
        game_data = {
            "timestamp": datetime.now().isoformat(),
            "game_id": game_id,
            "log_content": log_content,
            "metadata": {
                "game_type": "merchants_1o1",
                "log_file": log_filename,
                "timestamp": datetime.now().isoformat(),
                "total_events": len(events),
                "final_state": next((
                    event["data"] for event in reversed(events)
                    if event["type"] == "system" and event["name"] == "game_ended"
                ), None)
            }
        }
        
        # Upload to Fileverse
        logger.info(f"Uploading game log to Fileverse...")
        file_id = await client.save_game_log(game_id, game_data)
        
        if not file_id:
            raise Exception("No file ID returned from Fileverse")
            
        # Get file details
        file_details = client.get_file(file_id)
        logger.info(f"Game log uploaded successfully. ID: {file_id}")
        
        return {
            "ipfs_hash": file_id,
            "ipfs_url": file_details.get("url") or f"https://ipfs.io/ipfs/{file_id}",
            "log_file": log_filename
        }
        
    except Exception as e:
        logger.error(f"Failed to upload game summary: {str(e)}")
        raise 