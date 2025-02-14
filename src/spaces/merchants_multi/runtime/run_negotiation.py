from .negotiation import NegotiationScene
import json
from datetime import datetime
import os

def run_negotiation(rounds: int = 5):
    """Run a multiplayer negotiation game"""
    game = NegotiationScene(max_rounds=rounds)
    result = game.run_scene()
    
    print("\nFull Conversation History:")
    # Access messages from the memory object
    for message in result['conversation_memory'].messages:
        print(f"Round {message['round']} - {message['speaker']}: {message['message']}")
    
    print("\nTransfer History:")
    # Access transfers from the memory object
    for transfer in result['conversation_memory'].transfers:
        print(f"Round {transfer['round']} - {transfer['sender']} → {transfer['recipient']}: {transfer['amount']} coins")
    
    print("\nFinal Results:")
    for player, coins in result['final_statuses'].items():
        print(f"{player}: {coins} coins")
    
    print(f"\nWinner: {result['winner']} 🎉")

    # Save results to merchants_multi specific directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "../transcripts")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"multi_negotiation_{timestamp}.md")
    
    with open(filename, 'w') as f:
        f.write("# Multiplayer Business Negotiation Game Results\n\n")
        f.write(f"## Winner: {result['winner']}\n\n")
        f.write("## Final Coin Status\n")
        for player, coins in result['final_statuses'].items():
            f.write(f"- {player}: {coins} coins\n")
        f.write("\n## Conversation History\n")
        for message in result['conversation_memory'].messages:
            f.write(f"- {message['message']}\n")
    
    print(f"Game results saved to {filename}")
    return result

if __name__ == "__main__":
    run_negotiation(5) 