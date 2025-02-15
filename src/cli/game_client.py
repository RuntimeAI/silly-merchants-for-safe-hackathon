import asyncio
import aiohttp
import json
from typing import AsyncGenerator, Optional
from colorama import init, Fore, Style
import sys
import time
import uuid
from datetime import datetime
import os

# Initialize colorama for colored output
init()

class SillyMerchantsClient:
    def __init__(self, base_url: str = "http://localhost:8000", debug: bool = False):
        self.base_url = base_url
        self.debug = debug
        if debug:
            print(f"{Fore.YELLOW}🐛 Client initialized in DEBUG mode{Style.RESET_ALL}")

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
                if self.debug:
                    print(f"{Fore.BLUE}DEBUG: Create game response: {json.dumps(data, indent=2)}{Style.RESET_ALL}")
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
        """Subscribe to game events with reconnection logic"""
        retry_count = 0
        max_retries = 3
        retry_delay = 1.0

        while retry_count < max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/merchants_1o1/games/{game_id}/events",
                        headers={
                            'Accept': 'text/event-stream',
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive'
                        },
                        timeout=aiohttp.ClientTimeout(total=30)  # Increase timeout
                    ) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to subscribe: {await response.text()}")
                        
                        print(f"\n{Fore.CYAN}=== Starting SSE Stream ==={Style.RESET_ALL}")
                        
                        try:
                            async for line in response.content:
                                try:
                                    decoded_line = line.decode('utf-8').strip()
                                    if self.debug:
                                        print(f"{Fore.YELLOW}SSE: {decoded_line}{Style.RESET_ALL}")
                                    
                                    # Skip empty lines and keepalive
                                    if not decoded_line or decoded_line.startswith(':'):
                                        continue
                                        
                                    # Handle double-wrapped data: events
                                    if decoded_line.startswith('data: data: '):
                                        try:
                                            # Remove both data: prefixes
                                            event_data = decoded_line[12:]
                                            if self.debug:
                                                print(f"{Fore.BLUE}EVENT DATA: {event_data}{Style.RESET_ALL}")
                                            event = json.loads(event_data)
                                            if event.get('type') != 'ping':
                                                yield event
                                                retry_count = 0
                                        except json.JSONDecodeError as e:
                                            if self.debug:
                                                print(f"{Fore.RED}JSON Parse Error: {e}")
                                                print(f"Problem line: {event_data}{Style.RESET_ALL}")
                                            continue
                                    # Handle single data: events
                                    elif decoded_line.startswith('data: '):
                                        try:
                                            event_data = decoded_line[6:]
                                            if self.debug:
                                                print(f"{Fore.BLUE}EVENT DATA: {event_data}{Style.RESET_ALL}")
                                            event = json.loads(event_data)
                                            if event.get('type') != 'ping':
                                                yield event
                                                retry_count = 0
                                        except json.JSONDecodeError as e:
                                            if self.debug:
                                                print(f"{Fore.RED}JSON Parse Error: {e}")
                                                print(f"Problem line: {event_data}{Style.RESET_ALL}")
                                            continue
                                    
                                except UnicodeDecodeError as e:
                                    print(f"{Fore.RED}Decode Error: {e}{Style.RESET_ALL}")
                                    continue
                                except asyncio.CancelledError:
                                    print(f"{Fore.YELLOW}Event stream cancelled{Style.RESET_ALL}")
                                    return
                                except asyncio.TimeoutError:
                                    print(f"{Fore.YELLOW}Event stream timeout, reconnecting...{Style.RESET_ALL}")
                                    break
                                
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            print(f"{Fore.YELLOW}Stream interrupted, attempting to reconnect...{Style.RESET_ALL}")
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                            else:
                                raise Exception("Max retries exceeded")

            except Exception as e:
                if isinstance(e, (asyncio.CancelledError, asyncio.TimeoutError)):
                    print(f"{Fore.YELLOW}Connection timeout, retrying...{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Connection error: {str(e)}{Style.RESET_ALL}")
                
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception(f"Connection failed after {max_retries} retries")
                
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

def print_banner():
    banner = f"""
{Fore.YELLOW}
╔═══════════════════════════════════════════════╗
║             🎮 SILLY MERCHANTS 🎮             ║
║         The AI Trading Game Arena!            ║
╚═══════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_strategy_guide():
    guide = f"""
{Fore.CYAN}📝 Strategy Guide:
1. You'll be playing as Marco Polo against Trader Joe
2. Your strategy will guide Marco Polo's decisions
3. Consider including:
   - Early game approach
   - Risk tolerance
   - Cooperation vs Competition
   - Response to betrayal
   - End game strategy{Style.RESET_ALL}
"""
    print(guide)

def get_strategy_input() -> str:
    """Get strategy input from user"""
    print(f"\n{Fore.GREEN}Enter your strategy below (press Enter twice when done):{Style.RESET_ALL}\n")
    strategy_lines = []
    empty_lines = 0
    
    while empty_lines < 2:  # Exit after two empty lines
        try:
            line = input()
            if not line.strip():
                empty_lines += 1
            else:
                empty_lines = 0
                strategy_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    strategy = "\n".join(strategy_lines)
    if not strategy.strip():
        print(f"{Fore.RED}Strategy cannot be empty! Using default strategy.{Style.RESET_ALL}")
        return """
        Strategy for Marco Polo:
        - Build trust in early rounds
        - Be cautious with large transfers
        - Look for opportunities to cooperate
        - Consider betrayal only if heavily betrayed
        """
    return strategy

def format_game_event(event: dict) -> Optional[str]:
    """Format game events in an entertaining way"""
    try:
        event_type = event.get('type')
        event_name = event.get('name')
        data = event.get('data', {})
        
        # Create common elements
        separator = "=" * 50
        style_reset = Style.RESET_ALL
        box_top = "+" + "-" * 48 + "+"
        box_bottom = "+" + "-" * 48 + "+"
        
        # Add debug logging
        print(f"{Fore.BLUE}DEBUG: Received event - Type: {event_type}, Name: {event_name}{style_reset}")
        
        if event_type == 'player':
            if event_name == 'player_thinking':
                player = data.get('player', 'Unknown')
                thinking = data.get('thinking', '')
                
                # Format the thinking text
                formatted_thinking = ""
                for line in thinking.split('\n'):
                    # Handle markdown-style headers
                    if line.startswith('**') and line.endswith('**'):
                        formatted_thinking += f"{Fore.YELLOW}{line.strip('*')}{Style.RESET_ALL}\n"
                    elif line.startswith('*   '):  # List items
                        formatted_thinking += f"{Fore.CYAN}  • {line[4:]}{Style.RESET_ALL}\n"
                    elif line.startswith('    *   '):  # Nested list items
                        formatted_thinking += f"{Fore.CYAN}    ◦ {line[8:]}{Style.RESET_ALL}\n"
                    else:
                        formatted_thinking += f"{line}\n"
                
                # Create separator and style reset once
                separator = "=" * 50
                style_reset = Style.RESET_ALL
                
                return f"""
{Fore.MAGENTA}🤔 {player}'s STRATEGIC ANALYSIS
{separator}
{formatted_thinking}
{separator}""" + style_reset
            
            elif event_name == 'player_action':
                player = data.get('player', 'Unknown')
                action = data.get('action', {})
                message = action.get('message', '')
                transfers = action.get('transfers', [])
                
                # Format transfers with more detail
                transfer_info = []
                for t in transfers:
                    amount = t.get('amount', 0)
                    recipient = t.get('recipient', 'Unknown')
                    if amount > 0:
                        transfer_info.append(f"  💰 Transferring {amount} coins to {recipient}")
                    else:
                        transfer_info.append(f"  🤝 Choosing not to transfer coins to {recipient} this round")
                
                transfer_text = "\n".join(transfer_info) if transfer_info else "  📝 No transfers planned this round"
                
                # Create separator and style reset once
                separator = "=" * 50
                style_reset = Style.RESET_ALL
                
                return f"""
{Fore.GREEN}⚡ {player}'s DECISION & ACTION
{separator}
💬 ANNOUNCEMENT:
  "{message}"

🎲 PLANNED ACTIONS:
{transfer_text}
{separator}""" + style_reset

        # Handle error events
        if event_type == 'error':
            return f"""
{Fore.RED}❌ Error Occurred:
  Type: {event_name}
  Details: {data.get('error', 'Unknown error')}{Style.RESET_ALL}"""
            
        if event_type == 'system':
            if event_name == 'game_created':
                players = data.get('players', {})
                player_info = "\n".join([
                    f"  👤 {name}: {coins.get('coins', 0) if isinstance(coins, dict) else coins} coins" 
                    for name, coins in players.items()
                ])
                # Create separator and style reset once
                separator = "=" * 50
                style_reset = Style.RESET_ALL
                
                return f"""
{Fore.GREEN}🎮 Game Created!
{separator}
📋 Game Details:
  🎲 Game ID: {data.get('game_id')}
  🔄 Rounds: {data.get('max_rounds', 5)}
  �� Debug Mode: {data.get('debug_mode', False)}

👥 Initial Player Setup:
{player_info}
{separator}""" + style_reset
            
            elif event_name == 'game_started':
                initial_state = data.get('initial_state', {})
                player_info = "\n".join([
                    f"  > {name}: {coins} coins" 
                    for name, coins in initial_state.items()
                ])
                return f"""
{Fore.GREEN}>> Game Started!
{separator}
Game Configuration:
  * Players: {', '.join(data.get('players', []))}
  * Rounds: {data.get('max_rounds', 5)}

Current State:
{player_info}
{separator}""" + style_reset
            
            elif event_name == 'round_started':
                round_num = data.get('round', '?')
                standings = data.get('standings', {})
                status = "\n".join([
                    f"| {player}: {coins} coins" 
                    for player, coins in standings.items()
                ])
                return f"""
{Fore.GREEN}>> Round {round_num} Begins!
{separator}
Current Standings:
{box_top}
{status}
{box_bottom}
{separator}""" + style_reset
            
            elif event_name == 'round_summary':
                round_num = data.get('round', '?')
                standings = data.get('standings', {})
                transfers = data.get('transfers', [])
                
                # Format standings with simple indicators
                standings_info = "\n".join([
                    f"| {'+' if coins > 10 else '-' if coins < 10 else '='} {player}: {coins} coins" 
                    for player, coins in standings.items()
                ])
                
                # Format transfers
                transfer_section = ""
                if transfers:
                    transfer_list = "\n".join([
                        f"  * {t.get('from')} -> {t.get('to')}: {t.get('amount')} coins" 
                        for t in transfers
                    ])
                    transfer_section = f"Transfers this round:\n{transfer_list}"
                
                return f"""
{Fore.YELLOW}>> Round {round_num} Summary
{separator}
{transfer_section if transfers else "No transfers this round"}

Current Standings:
{box_top}
{standings_info}
{box_bottom}

{separator}""" + style_reset
            
            elif event_name == 'round_ended':
                round_num = data.get('round', '?')
                standings = data.get('standings', {})
                trades = data.get('trades', [])
                
                trade_info = "\n".join([
                    f"  💰 {trade.get('from')} → {trade.get('to')}: {trade.get('amount')} coins" 
                    for trade in trades
                ])
                status = "\n".join([
                    f"  🎭 {player}: {coins if isinstance(coins, int) else coins.get('coins', 0)} coins" 
                    for player, coins in standings.items()
                ])
                
                return f"""
{Fore.CYAN}📊 Round {round_num} Results:
{trade_info if trades else 'No trades this round'}
Current Standings:
{status}{Style.RESET_ALL}"""

            elif event_name == 'game_ended':
                winner = data.get('winner', 'Unknown')
                standings = data.get('final_standings', {})
                
                # Handle tie case
                is_tie = winner == "Tie"
                winner_display = "TIE GAME!" if is_tie else f"Winner: {winner}"
                
                standings_info = "\n".join([
                    # Don't show winner star in case of tie
                    f"| {('*' if player == winner and not is_tie else ' ')} {player}: {coins} coins" 
                    for player, coins in standings.items()
                ])
                
                return f"""
{Fore.GREEN}>> Game Over!
{separator}
{winner_display}

Final Standings:
{box_top}
{standings_info}
{box_bottom}

{('Everyone wins!' if is_tie else 'Close game!') if abs(max(standings.values()) - min(standings.values())) <= 2 else 'Decisive battle!'}
{separator}""" + style_reset

            elif event_name == 'upload_complete':
                # Handle upload complete event
                if 'error' in data:
                    return f"""
{Fore.RED}📤 Game Summary Upload Failed
{separator}
❌ Error: {data.get('error')}
Message: {data.get('message', 'Unknown error')}
{separator}{Style.RESET_ALL}"""
                else:
                    return f"""
{Fore.GREEN}📤 Game Summary Upload Complete!
{separator}
✅ Successfully uploaded game summary
🔗 IPFS URL: {data.get('ipfs_url')}
🔑 IPFS Hash: {data.get('ipfs_hash')}

💾 Local log file: {data.get('log_file', 'logs/merchants_1o1/game_1o1_<timestamp>_<game_id>.log')}
{separator}{Style.RESET_ALL}"""

    except Exception as e:
        return f"{Fore.RED}Error formatting event: {str(e)}{Style.RESET_ALL}"

def format_game_summary(events: list) -> str:
    """Format complete game summary"""
    messages = []
    transfers = []
    final_standings = {}
    
    for event in events:
        if event['type'] == 'player' and event['name'] == 'player_action':
            round_num = len(messages) // 2 + 1
            player = event['data']['player']
            action = event['data']['action']
            
            # Record message
            messages.append({
                'round': round_num,
                'player': player,
                'message': action['message']
            })
            
            # Record transfers
            for t in action.get('transfers', []):
                if t.get('amount', 0) > 0:
                    transfers.append({
                        'round': round_num,
                        'from': player,
                        'to': t['recipient'],
                        'amount': t['amount']
                    })
        
        elif event['type'] == 'system' and event['name'] == 'game_ended':
            final_standings = event['data']['final_standings']
    
    # Format conversation history
    conversation = "\n".join([
        f"Round {m['round']} - {m['player']}: \"{m['message']}\"" 
        for m in messages
    ])
    
    # Format transfer history with indicators
    transfer_history = "\n".join([
        f"Round {t['round']} - {t['from']} {'🔻' if t['amount'] > 0 else '🔺'} {t['amount']} coins {'🔺' if t['amount'] > 0 else '🔻'} {t['to']}"
        for t in transfers
    ])
    
    winner = max(final_standings.items(), key=lambda x: x[1])[0]
    
    # Create separator and style reset once
    separator = "=" * 50
    style_reset = Style.RESET_ALL
    
    return f"""
{Fore.CYAN}📜 GAME SUMMARY
{separator}

💬 Conversation History:
{conversation}

💰 Transfer History:
{transfer_history}

🏆 Final Result:
┌{('─' * 48)}┐
│ Winner: {winner}{' ' * (40-len(winner))}│
{' '.join(f"│ {player}: {coins} coins{' ' * (40-len(f'{player}: {coins} coins'))}│" for player, coins in final_standings.items())}
└{('─' * 48)}┘
{separator}""" + style_reset

async def upload_game_summary(events: list) -> dict:
    """Upload game summary to Fileverse"""
    try:
        from src.utils.fileverse_client import FileverseClient
        from src.utils.logger import GameLogger
        
        client = FileverseClient()
        logger = GameLogger(str(uuid.uuid4()))
        
        # First collect all messages and transfers
        messages = []
        transfers = []
        message_count = 0
        
        for event in events:
            if event['type'] == 'player' and event['name'] == 'player_action':
                message_count += 1
                round_num = (message_count + 1) // 2
                player = event['data']['player']
                action = event['data']['action']
                
                messages.append({
                    "round": round_num,
                    "player": player,
                    "message": action['message']
                })
                
                for t in action.get('transfers', []):
                    if t.get('amount', 0) > 0:
                        transfers.append({
                            "round": round_num,
                            "from": player,
                            "to": t['recipient'],
                            "amount": t['amount']
                        })
        
        # Get log file content
        log_content = ""
        log_file_path = os.path.join('logs', f'{logger.log_id}.log')
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                log_content = f.read()
        
        # Prepare game data with full content
        game_data = {
            "timestamp": datetime.now().isoformat(),
            "game_id": str(uuid.uuid4()),
            "events": events,
            "summary": {
                "messages": messages,
                "transfers": transfers
            },
            "logs": {
                "content": log_content,
                "events": [
                    {
                        "timestamp": event.get('timestamp'),
                        "type": event.get('type'),
                        "name": event.get('name'),
                        "data": event.get('data')
                    }
                    for event in events
                ]
            }
        }
        
        # Upload to Fileverse and get response
        response = await client.save_game_log(game_data["game_id"], game_data)
        
        if isinstance(response, dict):
            ipfs_hash = response.get('ipfs_hash')
            ipfs_url = response.get('ipfs_url')
            return {
                'ipfs_hash': ipfs_hash,
                'ipfs_url': ipfs_url or f"https://ipfs.io/ipfs/{ipfs_hash}"
            }
        return {
            'ipfs_hash': response,
            'ipfs_url': f"https://ipfs.io/ipfs/{response}"
        }
        
    except Exception as e:
        print(f"{Fore.RED}Failed to upload game summary: {str(e)}{Style.RESET_ALL}")
        return None

async def main():
    print_banner()
    print_strategy_guide()
    
    strategy = get_strategy_input()
    
    if not strategy.strip():
        print(f"{Fore.RED}Strategy cannot be empty! Exiting...{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}🎲 Creating new game...{Style.RESET_ALL}")
    client = SillyMerchantsClient()
    
    try:
        # Create and start game
        game_id = await client.create_game()
        print(f"{Fore.GREEN}✅ Game created successfully! (ID: {game_id}){Style.RESET_ALL}")
        
        await client.start_game(game_id, strategy)
        print(f"{Fore.GREEN}✅ Game started! Watching the action...{Style.RESET_ALL}")
        
        # Store all events for summary
        all_events = []
        upload_complete = False
        
        # Subscribe to events with error handling
        event_count = 0
        try:
            async for event in client.subscribe_events(game_id):
                all_events.append(event)
                event_count += 1
                print(f"\n{Fore.BLUE}DEBUG: Event #{event_count}{Style.RESET_ALL}")
                formatted_event = format_game_event(event)
                if formatted_event:
                    print(formatted_event)
                    await asyncio.sleep(0.5)
                
                # Check for game end events
                if event.get('type') == 'system':
                    if event.get('name') == 'game_ended':
                        print(format_game_summary(all_events))
                    elif event.get('name') == 'upload_complete':
                        if 'error' in event['data']:
                            print(f"\n{Fore.RED}❌ Upload failed: {event['data']['error']}{Style.RESET_ALL}")
                        else:
                            print(f"\n{Fore.GREEN}✅ Game summary uploaded!")
                            print(f"📄 Log file: {event['data']['log_file']}")
                            print(f"🔗 IPFS URL: {event['data']['ipfs_url']}{Style.RESET_ALL}")
                    elif event.get('name') == 'session_ended':
                        print(f"\n{Fore.GREEN}👋 Game session completed!{Style.RESET_ALL}")
                        break
                    
        except asyncio.CancelledError:
            print(f"\n{Fore.YELLOW}Game interrupted by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error in event stream: {str(e)}{Style.RESET_ALL}")
            raise
                
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.RED}Stack trace:{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Game interrupted by user{Style.RESET_ALL}")

def run_game():
    """Entry point for the game client"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye!{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    run_game() 