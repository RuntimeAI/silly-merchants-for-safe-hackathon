import os
import logging
from typing import Dict, List, Any
from datetime import datetime
from src.utils.config import Config
from src.utils.logger import GameLogger
from ..agents.players import Player1, Player2
from ..agents.coordinator import CoordinatorAgent
import json
import re
import uuid
import asyncio
from src.api.events.types import GameEventType
from src.utils.fileverse_client import FileverseClient

class ConversationMemory:
    def __init__(self):
        self.messages = []
        self.transfers = []
    
    def add_message(self, speaker: str, message: str):
        self.messages.append({
            'round': len(self.messages) // 2 + 1,  # 2 players per round
            'speaker': speaker,
            'message': message,
            'timestamp': datetime.now()
        })
    
    def add_transfer(self, sender: str, recipient: str, amount: int):
        self.transfers.append({
            'round': len(self.messages) // 2 + 1,
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': datetime.now()
        })
    
    def get_recent_context(self, n_messages: int = 5) -> str:
        """Get recent conversation context"""
        recent = self.messages[-n_messages:] if self.messages else []
        context = "\nRecent conversation:\n"
        for msg in recent:
            context += f"Round {msg['round']} - {msg['speaker']}: {msg['message']}\n"
        
        if self.transfers:
            context += "\nRecent transfers:\n"
            for transfer in self.transfers[-n_messages:]:
                context += f"Round {transfer['round']} - {transfer['sender']} → {transfer['recipient']}: {transfer['amount']} coins\n"
        
        return context

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for serialization"""
        return {
            'messages': [
                {
                    'round': msg['round'],
                    'speaker': msg['speaker'],
                    'message': msg['message'],
                    'timestamp': msg['timestamp'].isoformat()  # Convert datetime to string
                }
                for msg in self.messages
            ],
            'transfers': [
                {
                    'round': transfer['round'],
                    'sender': transfer['sender'],
                    'recipient': transfer['recipient'],
                    'amount': transfer['amount'],
                    'timestamp': transfer['timestamp'].isoformat()  # Convert datetime to string
                }
                for transfer in self.transfers
            ]
        }

class NegotiationRuntime:
    def __init__(self, logger=None, event_manager=None):
        self.state = "created"  # States: created -> running -> complete/error
        self.logger = logger or GameLogger(str(uuid.uuid4()))
        self.event_manager = event_manager
        self.log_messages = []  # Add this to store logs
        self.player1 = Player1("Marco Polo")
        self.player2 = Player2("Trader Joe")
        self.round = 1
        
        # Get config and set debug mode
        config = Config()
        self.debug_mode = config.debug_mode
        self.max_rounds = config.game_rounds  # This will now be 2 in debug mode
        
        # Log configuration
        self.logger.info(f"Game initialized with {self.max_rounds} rounds (Debug mode: {self.debug_mode})")
        
        # Reduce delays in debug mode
        self.turn_delay = 0.2 if self.debug_mode else 0.5
        self.round_delay = 0.5 if self.debug_mode else 1.0
        
        space_config = config.get_space_config('merchants_1o1')
        self.player_order = space_config['players']
        self.players = {
            self.player_order[0]: self.player1,
            self.player_order[1]: self.player2
        }
        self.coordinator = CoordinatorAgent('Coordinator')
        self.memory = ConversationMemory()
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the shared system prompt for all agents"""
        return """You are participating in a 5-round negotiation game with two players:
        - Alpha (Player 1): Speaks first each round
        - Beta (Player 2): Speaks second each round
        
        Game Rules:
        1. Each player starts with 10 coins
        2. Players can transfer coins to form alliances
        3. The player with most coins at the end wins
        4. Players take turns in fixed order: Alpha → Beta
        
        IMPORTANT: You must respond with ONLY a valid JSON object in this exact format:
        {
            "message": "your strategic message as a single string",
            "transfers": [
                {"recipient": "player_name", "amount": number}
            ]
        }
        """
    
    def get_player_statuses(self) -> Dict[str, int]:
        return {name: player.coins for name, player in self.players.items()}
    
    async def run_game(self) -> Dict[str, Any]:
        """Run the complete game"""
        try:
            # Game start
            self.state = "running"
            await self._emit_event(GameEventType.GAME_STARTED, {
                "max_rounds": self.max_rounds,
                "players": self.get_player_statuses()
            })

            # Run rounds
            for round_num in range(1, self.max_rounds + 1):
                await self._run_round(round_num)
            
            # Game end
            final_results = self._calculate_final_results()
            
            # Save logs locally
            await self._emit_event(GameEventType.SYSTEM_STATUS, {
                "action": "saving_logs",
                "status": "in_progress"
            })
            self._save_local_logs()
            await self._emit_event(GameEventType.SYSTEM_STATUS, {
                "action": "saving_logs",
                "status": "completed"
            })
            
            # Upload logs
            await self._emit_event(GameEventType.SYSTEM_STATUS, {
                "action": "uploading_logs",
                "status": "in_progress"
            })
            file_id = await self._upload_logs(final_results)
            await self._emit_event(GameEventType.SYSTEM_STATUS, {
                "action": "uploading_logs",
                "status": "completed",
                "file_id": file_id
            })
            
            # Mark game as complete
            self.state = "complete"
            await self._emit_event(GameEventType.GAME_ENDED, {
                "winner": final_results["winner"],
                "final_standings": final_results["final_statuses"],
                "history": final_results["conversation_memory"],
                "log_file_id": file_id
            })
            
            # Allow time for final cleanup
            await asyncio.sleep(10)
            
            return final_results
            
        except Exception as e:
            self.state = "error"
            await self._emit_event(GameEventType.ERROR, {"error": str(e)})
            raise

    async def _run_round(self, round_num: int):
        """Run a single round"""
        # Round start
        await self._emit_event(GameEventType.ROUND_STARTED, {
            "round": round_num,
            "standings": self.get_player_statuses()
        })
        
        # Player 1's turn
        await self._run_player_turn(self.player1, round_num)
        
        # Player 2's turn
        await self._run_player_turn(self.player2, round_num)
        
        # Round end
        await self._emit_event(GameEventType.ROUND_ENDED, {
            "round": round_num,
            "standings": self.get_player_statuses(),
            "summary": self._get_round_summary(round_num)
        })

    async def _run_player_turn(self, player, round_num: int):
        """Run a player's turn"""
        # Thinking phase
        thinking = player.generate_thinking()
        await self._emit_event(GameEventType.PLAYER_THINKING, {
            "player": player.name,
            "round": round_num,
            "thinking": thinking
        })
        
        # Action phase
        action = player.generate_action()
        await self._emit_event(GameEventType.PLAYER_ACTION, {
            "player": player.name,
            "round": round_num,
            "action": action
        })
        
        # Process transfers
        self._process_transfers(player, action["transfers"])

    async def _emit_event(self, event_type: GameEventType, data: Dict[str, Any]):
        """Emit an event with proper delay"""
        if self.event_manager:
            try:
                # Add debug info if in debug mode
                if self.debug_mode:
                    data['debug_info'] = {
                        'mode': 'debug',
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Emit the event
                await self.event_manager.emit(
                    "system" if event_type.value.startswith("system_") else "game",
                    event_type.value,
                    data
                )
                
                # Small delay to ensure event processing
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error emitting event {event_type}: {str(e)}")
                raise

    def _process_transfers(self, player, transfers):
        for transfer in transfers:
            recipient = transfer['recipient']
            amount = transfer['amount']
            if recipient in self.players:
                if player.transfer_coins(amount, self.players[recipient]):
                    self.logger.info(f"💰 {player.name} transferred {amount} coins to {recipient}")
                    self.memory.add_transfer(player.name, recipient, amount) 

    def get_logs(self) -> List[str]:
        """Get all game logs"""
        return self.log_messages

    def _log_message(self, message: str):
        """Log a message and store it"""
        self.logger.info(message)
        self.log_messages.append(message) 

    def _calculate_final_results(self) -> Dict[str, Any]:
        """Calculate final game results"""
        final_statuses = self.get_player_statuses()
        
        # Determine winner
        max_coins = max(final_statuses.values())
        winners = [p for p, c in final_statuses.items() if c == max_coins]
        winner = winners[0] if len(winners) == 1 else "Tie"
        
        return {
            "winner": winner,
            "final_statuses": final_statuses,
            "conversation_memory": self.memory.to_dict()
        }

    def _get_round_summary(self, round_num: int) -> Dict[str, Any]:
        """Get summary for a specific round"""
        return {
            "round": round_num,
            "standings": self.get_player_statuses(),
            "messages": [
                {
                    'round': m['round'],
                    'speaker': m['speaker'],
                    'message': m['message'],
                    'timestamp': m['timestamp'].isoformat()  # Convert datetime to string
                }
                for m in self.memory.messages if m['round'] == round_num
            ],
            "transfers": [
                {
                    'round': t['round'],
                    'sender': t['sender'],
                    'recipient': t['recipient'],
                    'amount': t['amount'],
                    'timestamp': t['timestamp'].isoformat()  # Convert datetime to string
                }
                for t in self.memory.transfers if t['round'] == round_num
            ]
        }

    def _save_local_logs(self):
        """Save logs locally"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = f"logs/game_{timestamp}.log"
        os.makedirs("logs", exist_ok=True)
        
        with open(log_path, "w") as f:
            for msg in self.log_messages:
                f.write(f"{msg}\n")
        
        self.logger.info(f"Logs saved to {log_path}")

    async def _upload_logs(self, final_results: Dict[str, Any]) -> str:
        """Upload logs to Fileverse"""
        client = FileverseClient()
        game_data = {
            "timestamp": datetime.now().isoformat(),
            "winner": final_results["winner"],
            "final_standings": final_results["final_statuses"],
            "history": final_results["conversation_memory"]
        }
        
        return await client.save_game_log(str(uuid.uuid4()), game_data) 