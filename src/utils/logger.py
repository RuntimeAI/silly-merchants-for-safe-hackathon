import logging
import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

# Create default logger instance
logger = logging.getLogger("default")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class GameLogger:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup file logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        self.log_file = log_dir / f"game_{game_id}_{self.timestamp}.log"
        
        # Setup logger
        self._logger = logging.getLogger(f"game_{game_id}")
        self._logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self._logger.addHandler(fh)
        self._logger.addHandler(ch)
        
        self.game_summary = {
            "game_id": game_id,
            "rounds": [],
            "transfers": [],
            "messages": []
        }

    def addHandler(self, handler):
        """Add a handler to the logger"""
        self._logger.addHandler(handler)
    
    def removeHandler(self, handler):
        """Remove a handler from the logger"""
        self._logger.removeHandler(handler)
    
    def info(self, message):
        """Log an info message"""
        self._logger.info(message)
    
    def error(self, message):
        """Log an error message"""
        self._logger.error(message)
    
    def warning(self, message):
        """Log a warning message"""
        self._logger.warning(message)

    def log_game_start(self, players: Dict[str, Any]):
        message = (
            f"\n{'='*50}\n"
            f"🎮 Game {self.game_id} Started\n"
            f"⏰ Time: {self.timestamp}\n"
            f"👥 Players:\n"
        )
        for name, data in players.items():
            message += f"  - {name}: {data['coins']} coins\n"
        message += f"{'='*50}\n"
        
        self._logger.info(message)
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
        
        self._logger.info(message)
        return {"type": "round_start", "content": message}

    def log_player_thinking(self, player: str, thinking: str):
        message = (
            f"\n{'='*50}\n"
            f"🤔 {player}'s Deep Analysis\n"
            f"{'='*50}\n"
            f"{thinking}\n"
            f"{'='*50}\n"
        )
        
        self._logger.info(message)
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
        
        self._logger.info(message)
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
        
        self._logger.info(message)
        self.game_summary["rounds"].append(summary)
        return {"type": "round_summary", "content": message}

    def log_game_end(self) -> Dict[str, Any]:
        message = (
            f"\n{'='*50}\n"
            f"🏁 Game {self.game_id} Ended\n"
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
        
        self._logger.info(message)
        return {
            "type": "game_end",
            "content": message,
            "summary": self.game_summary
        } 