import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from .spaces.merchants_1o1.runtime.negotiation import NegotiationRuntime as OneOnOneTrading
from .spaces.merchants_multi.runtime.negotiation import NegotiationScene as MultiplayerTrading
from .core.config import GameConfig

def run_1o1():
    """Run 1v1 trading game"""
    load_dotenv()
    config = GameConfig()
    
    print("🎮 Starting 1v1 Trading Game")
    print(f"Max Rounds: {config.max_rounds}")
    print(f"Initial Balance: {config.initial_balance}")
    
    # Create and run game - players are initialized in constructor
    game = OneOnOneTrading(max_rounds=config.max_rounds)
    result = game.run()
    
    # Print final results
    print("\nFinal Results:")
    for player, coins in result['final_statuses'].items():
        print(f"{player}: {coins} coins")
    print(f"\nWinner: {result['winner']} 🎉")

def run_multiplayer():
    """Run multiplayer trading game"""
    load_dotenv()
    config = GameConfig()
    
    print("🎮 Starting Multiplayer Trading Game")
    print(f"Max Rounds: {config.max_rounds}")
    print(f"Initial Balance: {config.initial_balance}")
    
    # Create and run game - players are initialized in constructor
    game = MultiplayerTrading(max_rounds=config.max_rounds)
    result = game.run_scene()
    
    # Print final results
    print("\nFinal Results:")
    for player, coins in result['final_statuses'].items():
        print(f"{player}: {coins} coins")
    print(f"\nWinner: {result['winner']} 🎉")

def format_code():
    """Format code using black and isort"""
    subprocess.run(["black", "src", "tests"])
    subprocess.run(["isort", "src", "tests"])

def lint_code():
    """Run linting tools"""
    subprocess.run(["flake8", "src", "tests"])
    subprocess.run(["mypy", "src", "tests"]) 