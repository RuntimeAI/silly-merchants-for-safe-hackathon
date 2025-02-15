import logging
import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import os

# Create default logger instance
logger = logging.getLogger("default")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class GameLogger:
    """Custom logger for game events"""
    def __init__(self, log_id: str, log_dir: str = 'logs'):
        self.log_id = log_id
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger(f"game_{log_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Create file handler
        log_file = os.path.join(log_dir, f"{log_id}.log")
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.logger.info(f"Game logger initialized with ID: {log_id}")
        
        self.game_summary = {
            "game_id": log_id,
            "rounds": [],
            "transfers": [],
            "messages": []
        }

    def addHandler(self, handler):
        """Add a handler to the logger"""
        self.logger.addHandler(handler)
    
    def removeHandler(self, handler):
        """Remove a handler from the logger"""
        self.logger.removeHandler(handler)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)

    def log_game_start(self, players: Dict[str, Any]):
        message = (
            f"\n{'='*50}\n"
            f"🎮 Game {self.log_id} Started\n"
            f"⏰ Time: {datetime.now().strftime('%Y%m%d_%H%M%S')}\n"
            f"👥 Players:\n"
        )
        for name, data in players.items():
            message += f"  - {name}: {data['coins']} coins\n"
        message += f"{'='*50}\n"
        
        self.logger.info(message)
        return {"type": "game_start", "content": message}

    def log_round_start(self, round_num: int, player_status: Dict[str, Any]):
        message = (
            f"\n{'='*50}\n"
            f"📍 Round {round_num} Started\n"
            f"{'='*50}\n"
            "Current Status:\n"
        )
        for name, coins in player_status.items():
            message += f"  - {name}: {coins} coins\n"
        message += f"{'='*50}\n"
        
        self.logger.info(message)
        return {"type": "round_start", "content": message}

    def log_player_thinking(self, player: str, thinking: str):
        message = (
            f"\n{'='*50}\n"
            f"🤔 {player}'s Deep Analysis\n"
            f"{'='*50}\n"
            f"{thinking}\n"
            f"{'='*50}\n"
        )
        
        self.logger.info(message)
        return {"type": "player_thinking", "content": message}

    def log_player_action(self, player: str, action: Dict[str, Any]):
        message = (
            f"\n{'='*50}\n"
            f"📢 {player}'s Action\n"
            f"{'='*50}\n"
            f"💬 Message: {action['message']}\n"
            "💰 Transfers:\n"
        )
        for transfer in action['transfers']:
            message += f"  - {transfer['amount']} coins to {transfer['recipient']}\n"
        message += f"{'='*50}\n"
        
        self.logger.info(message)
        self.game_summary["transfers"].append({
            "round": len(self.game_summary["rounds"]) + 1,
            "from": player,
            **action
        })
        return {"type": "player_action", "content": message}

    def log_round_summary(self, round_num: int, summary: Dict[str, Any]):
        message = (
            f"\n{'='*50}\n"
            f"📊 Round {round_num} Summary\n"
            f"{'='*50}\n"
            f"Final Status:\n"
        )
        for name, coins in summary['final_status'].items():
            message += f"  - {name}: {coins} coins\n"
        message += f"\nKey Events:\n"
        for event in summary['events']:
            message += f"  - {event}\n"
        message += f"{'='*50}\n"
        
        self.logger.info(message)
        self.game_summary["rounds"].append(summary)
        return {"type": "round_summary", "content": message}

    def log_game_end(self) -> Dict[str, Any]:
        message = (
            f"\n{'='*50}\n"
            f"🏁 Game {self.log_id} Ended\n"
            f"{'='*50}\n"
            f"\nFinal Results:\n"
        )
        
        # Calculate final standings
        final_round = self.game_summary["rounds"][-1]
        winner = max(final_round["final_status"].items(), key=lambda x: x[1])[0]
        
        message += f"🏆 Winner: {winner}\n\n"
        message += "Final Standings:\n"
        for name, coins in final_round["final_status"].items():
            message += f"  - {name}: {coins} coins\n"
        
        # Add transfer history
        message += "\n💰 Transfer History:\n"
        for transfer in self.game_summary["transfers"]:
            message += (
                f"Round {transfer['round']}: {transfer['from']} transferred "
                f"{sum(t['amount'] for t in transfer['transfers'])} coins\n"
            )
        
        message += f"\n{'='*50}\n"
        
        self.logger.info(message)
        return {
            "type": "game_end",
            "content": message,
            "summary": self.game_summary
        } 