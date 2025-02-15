import logging
from typing import Dict, Any, AsyncGenerator
import asyncio
import json
from datetime import datetime
from src.utils.json_utils import game_json_dumps

logger = logging.getLogger(__name__)

class GameEventManager:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.event_queue = asyncio.Queue()
        self._lock = asyncio.Lock()
    
    def _format_sse_event(self, event: Dict[str, Any]) -> str:
        """Format event as SSE data"""
        event_json = game_json_dumps(event)
        return f"data: {event_json}\n\n"
    
    async def emit(self, event_type: str, event_name: str, data: Dict[str, Any]):
        """Emit an event with proper error handling"""
        try:
            async with self._lock:
                event = {
                    "id": f"evt_{datetime.now().timestamp()}",
                    "type": event_type,
                    "name": event_name,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Format and queue the event
                event_str = self._format_sse_event(event)
                logger.debug(f"Emitting event: {game_json_dumps(event)}")  # Use game_json_dumps instead of json.dumps
                await self.event_queue.put(event_str)
                
                # Log the event for debugging
                logger.debug(f"Queued event: {event_name}")
                
        except Exception as e:
            logger.error(f"Error emitting event: {str(e)}")
            raise
    
    async def emit_message(self, name: str, data: Dict[str, Any]):
        """Emit a message event"""
        await self.emit("message", name, data)
    
    async def emit_system(self, name: str, data: Dict[str, Any]):
        """Emit a system event"""
        await self.emit("system", name, data)
    
    async def emit_error(self, error: str, details: Dict[str, Any] = None):
        """Emit an error event"""
        await self.emit("error", "error", {
            "error": error,
            "details": details or {}
        })
    
    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to events"""
        try:
            logger.info("New client subscribed to events")
            while True:
                # Get next event from queue
                event = await self.event_queue.get()
                
                # Yield the event
                yield event
                
                # Mark as done and add small delay
                self.event_queue.task_done()
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Event subscription cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in event subscription: {str(e)}")
            raise 