import logging
from typing import Dict, Any, AsyncGenerator
import asyncio
import json
from datetime import datetime
from src.utils.json_utils import game_json_dumps
from fastapi import Request
import time

logger = logging.getLogger(__name__)

class GameEventManager:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.subscribers = []
        self.logger = logging.getLogger(f"event_manager_{game_id}")
    
    def _format_sse_event(self, event: Dict[str, Any]) -> str:
        """Format event as SSE data"""
        event_json = game_json_dumps(event)
        return f"data: {event_json}\n\n"
    
    async def emit(self, event_type: str, event_name: str, data: Dict[str, Any]):
        """Emit an event to all subscribers"""
        event = {
            "id": f"evt_{time.time()}",
            "type": event_type,
            "name": event_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all subscribers
        for queue in self.subscribers:
            await queue.put(event)
    
    async def emit_message(self, name: str, data: Dict[str, Any]):
        """Emit a message event"""
        await self.emit("message", name, data)
    
    async def emit_system(self, event_name: str, data: Dict[str, Any]):
        """Emit a system event"""
        await self.emit("system", event_name, data)
    
    async def emit_error(self, error_message: str):
        """Emit an error event"""
        await self.emit_system("error", {"error": error_message})
    
    async def subscribe(self, request: Request) -> AsyncGenerator[str, None]:
        """Subscribe to game events"""
        try:
            queue = asyncio.Queue()
            self.subscribers.append(queue)
            self.logger.info(f"New subscriber added. Total subscribers: {len(self.subscribers)}")
            
            try:
                # Send initial ping
                yield "data: {\"type\":\"ping\"}\n\n"
                
                while True:
                    if await request.is_disconnected():
                        break
                        
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        if event is None:  # Shutdown signal
                            break
                        
                        # Format and send event - remove double data: wrapping
                        event_data = json.dumps(event)
                        self.logger.debug(f"Sending event: {event_data}")
                        yield f"data: {event_data}\n\n"
                        
                        # Send keepalive
                        yield ":keepalive\n\n"
                        
                    except asyncio.TimeoutError:
                        yield ":keepalive\n\n"
                        continue
                
            except asyncio.CancelledError:
                self.logger.info("Subscription cancelled")
                raise
            finally:
                self.subscribers.remove(queue)
                self.logger.info(f"Subscriber removed. Remaining subscribers: {len(self.subscribers)}")
                
        except Exception as e:
            self.logger.error(f"Error in subscription: {str(e)}")
            raise

    def close(self):
        """Close all subscriptions"""
        for queue in self.subscribers:
            queue.put_nowait(None)  # Signal shutdown
        self.subscribers.clear() 