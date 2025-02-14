import requests
import json
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_separator():
    print(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}")

def format_timestamp(timestamp):
    """Format timestamp from ISO format"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "unknown time"

def stream_game():
    print_separator()
    print(f"{Fore.GREEN}🎮 Starting New Game...{Style.RESET_ALL}")
    print_separator()
    
    response = requests.post(
        'http://localhost:8000/merchants_1o1/initiate',
        json={"strategy_advisory": "Be aggressive early, then betray in final round"},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            # Remove "data: " prefix and parse JSON
            event = json.loads(line.decode('utf-8').replace('data: ', ''))
            timestamp = format_timestamp(event['data']['timestamp'])
            
            # Pretty print based on event type
            if event['event'] == 'game_start':
                print(f"\n{Fore.GREEN}🎮 Game Started at {timestamp}!{Style.RESET_ALL}")
                print(f"Players:")
                for name, data in event['data']['players'].items():
                    print(f"  • {name}: {data['coins']} coins")
                print_separator()
                
            elif event['event'] == 'round_start':
                round_num = event['data']['round']
                print(f"\n{Fore.YELLOW}📍 Round {round_num} Started at {timestamp}{Style.RESET_ALL}")
                print("Current Standings:")
                for name, coins in event['data']['standings'].items():
                    print(f"  • {name}: {coins} coins")
                print_separator()
                
            elif event['event'] == 'player_thinking':
                player = event['data']['player']
                print(f"\n{Fore.CYAN}🤔 {player}'s Deep Analysis at {timestamp}:{Style.RESET_ALL}")
                print(f"{event['data']['thinking']}")
                print_separator()
                
            elif event['event'] == 'player_action':
                player = event['data']['player']
                print(f"\n{Fore.MAGENTA}📢 {player}'s Action at {timestamp}:{Style.RESET_ALL}")
                print(f"💬 Message: {event['data']['message']}")
                if event['data']['transfers']:
                    print("💰 Transfers:")
                    for transfer in event['data']['transfers']:
                        print(f"  • {transfer['amount']} coins to {transfer['recipient']}")
                else:
                    print("💰 No transfers")
                print_separator()
                
            elif event['event'] == 'round_summary':
                print(f"\n{Fore.YELLOW}📊 Round {event['data']['round']} Summary at {timestamp}:{Style.RESET_ALL}")
                print("Final Standings:")
                for name, coins in event['data']['standings'].items():
                    print(f"  • {name}: {coins} coins")
                if event['data']['transfers']:
                    print("\nRecent Transfers:")
                    for transfer in event['data']['transfers']:
                        print(f"  • Round {transfer['round']}: {transfer['sender']} → {transfer['recipient']}: {transfer['amount']} coins")
                print_separator()
                
            elif event['event'] == 'game_end':
                print(f"\n{Fore.GREEN}🏁 Game Over at {timestamp}!{Style.RESET_ALL}")
                print(f"🏆 Winner: {event['data']['winner']}")
                print("\nFinal Standings:")
                for name, coins in event['data']['final_standings'].items():
                    print(f"  • {name}: {coins} coins")
                
                print("\n💰 Transfer History:")
                for transfer in event['data']['history']['transfers']:
                    print(f"  • Round {transfer['round']}: {transfer['sender']} → {transfer['recipient']}: {transfer['amount']} coins")
                
                print("\n💬 Message History:")
                for msg in event['data']['history']['messages']:
                    print(f"  • Round {msg['round']} - {msg['speaker']}: {msg['message']}")
                print_separator()
            
            elif event['event'] == 'error':
                print(f"\n{Fore.RED}❌ Error at {timestamp}:{Style.RESET_ALL}")
                print(event['data']['message'])
                print_separator()

if __name__ == '__main__':
    try:
        stream_game()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Game monitoring stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}") 