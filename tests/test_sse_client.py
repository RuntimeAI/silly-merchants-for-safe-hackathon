import asyncio
import aiohttp
import json
from typing import AsyncGenerator
from colorama import init, Fore, Style
from datetime import datetime
import argparse
import logging

# Initialize colorama for colored output
init()

logger = logging.getLogger(__name__)

class GameClient:
    def __init__(self, base_url: str = "http://localhost:8000", debug: bool = False):
        self.base_url = base_url
        self.debug = debug
    
    async def create_game(self) -> str:
        """Create a new game"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/merchants_1o1/games",
                params={"debug": "true" if self.debug else "false"}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to create game: {await response.text()}")
                data = await response.json()
                return data["game_id"]
    
    async def start_game(self, game_id: str, strategy: str):
        """Start a game"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/merchants_1o1/games/{game_id}/start",
                json={"strategy_advisory": strategy}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to start game: {await response.text()}")
                return await response.json()
    
    async def subscribe_events(self, game_id: str) -> AsyncGenerator[dict, None]:
        """Subscribe to game events with detailed logging"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/merchants_1o1/games/{game_id}/events",
                    headers={'Accept': 'text/event-stream'}
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to subscribe: {await response.text()}")
                    
                    # Process events
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        logger.debug(f"Raw SSE line: {line}")  # Log raw SSE data
                        
                        # Skip empty lines and comments
                        if not line or line.startswith(':'):
                            continue
                        
                        # Parse SSE data
                        if line.startswith('data: '):
                            try:
                                event = json.loads(line[6:])
                                logger.debug(f"Parsed event: {json.dumps(event, indent=2)}")  # Log parsed event
                                yield event
                            except json.JSONDecodeError as e:
                                logger.error(f"Error parsing event: {str(e)}")
                                logger.error(f"Problem line: {line[6:]}")
                                continue
                            
            except Exception as e:
                logger.error(f"Error in event subscription: {str(e)}")
                raise

def format_event(event: dict) -> str:
    """Format event for display with timestamps and raw data"""
    timestamp = datetime.fromisoformat(event['timestamp']).strftime("%H:%M:%S.%f")[:-3]
    
    # Add debug indicator
    debug_indicator = "🐛 " if event.get('data', {}).get('debug_info') else ""
    
    # Basic event info
    output = [
        f"\n{Fore.CYAN}Event at {timestamp}{Style.RESET_ALL}",
        f"Type: {event['type']}",
        f"Name: {event['name']}",
        f"Raw Data: {json.dumps(event['data'], indent=2)}"
    ]
    
    return "\n".join(output)

async def main(debug: bool):
    # Create client with debug mode
    client = GameClient(debug=debug)
    
    try:
        print(f"{Fore.GREEN}Creating new game in DEBUG mode...{Style.RESET_ALL}")
        # Create game
        game_id = await client.create_game()
        print(f"{Fore.GREEN}Created game: {game_id}{Style.RESET_ALL}")
        
        # Start game
        print(f"{Fore.GREEN}Starting game...{Style.RESET_ALL}")
        strategy = """
        Strategy for Marco Polo:
        - Build trust in early rounds
        - Be cautious with large transfers
        - Look for opportunities to cooperate
        - Consider betrayal only if heavily betrayed
        """
        await client.start_game(game_id, strategy)
        print(f"{Fore.GREEN}Game started successfully{Style.RESET_ALL}")
        
        # Subscribe to events
        print(f"{Fore.GREEN}Subscribing to game events...{Style.RESET_ALL}")
        try:
            async for event in client.subscribe_events(game_id):
                print(format_event(event))
                
                # Exit if game is over
                if event['type'] == 'system' and event['name'] == 'game_end':
                    print(f"\n{Fore.GREEN}Game completed successfully!{Style.RESET_ALL}")
                    break
                    
        except asyncio.CancelledError:
            print(f"\n{Fore.YELLOW}Event subscription cancelled{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
    
    finally:
        print(f"\n{Fore.GREEN}Test complete{Style.RESET_ALL}")

async def test_debug_mode():
    client = GameClient(debug=True)
    
    try:
        # Create game
        print(f"{Fore.GREEN}Creating new game in DEBUG mode...{Style.RESET_ALL}")
        response = await client.create_game()
        game_id = response["game_id"]
        max_rounds = response["max_rounds"]
        
        print(f"{Fore.GREEN}Created game: {game_id} with {max_rounds} rounds{Style.RESET_ALL}")
        assert max_rounds == 2, f"Expected 2 rounds in debug mode, got {max_rounds}"
        
        # Rest of the test...
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--test", action="store_true", help="Run tests")
    args = parser.parse_args()
    
    try:
        if args.test:
            asyncio.run(test_debug_mode())
        else:
            asyncio.run(main(args.debug))
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}") 