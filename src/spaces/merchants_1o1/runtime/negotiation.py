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
from colorama import Fore, Style
from src.utils.json_utils import game_json_dumps

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
        self.strategy_advisory = """
        Strategy for Marco Polo:
        - Be smart, and earn more coins
        - Build trust in early rounds
        - Be cautious with large transfers
        - Look for opportunities to cooperate
        - Consider betrayal only if heavily betrayed
        """
    
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
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime for JSON serialization"""
        return dt.isoformat() if isinstance(dt, datetime) else str(dt)

    def get_player_statuses(self) -> Dict[str, int]:
        """Get player statuses (simplified)"""
        return {name: player.coins for name, player in self.players.items()}
    
    async def run_game(self) -> None:
        """Run the game loop"""
        try:
            self.state = "running"
            self.logger.info(f"{Fore.GREEN}Starting game with {self.max_rounds} rounds{Style.RESET_ALL}")
            
            # Emit game start event
            if self.event_manager:
                await self.event_manager.emit_system("game_started", {
                    "players": self.player_order,
                    "initial_state": self.get_player_statuses(),
                    "max_rounds": self.max_rounds,
                    "debug_mode": self.debug_mode
                })

            # Main game loop
            for round_num in range(1, self.max_rounds + 1):
                try:
                    self.round = round_num
                    self.logger.info(f"\n{Fore.CYAN}=== Round {round_num} ==={Style.RESET_ALL}")
                    
                    # Emit round start event
                    if self.event_manager:
                        await self.event_manager.emit_system("round_started", {
                            "round": round_num,
                            "standings": self.get_player_statuses()
                        })
                    
                    # Process Player 1's turn
                    events = self.process_player1_turn()
                    for event in events:
                        if self.event_manager:
                            await self.event_manager.emit(
                                event["type"],
                                event["name"],
                                event["data"]
                            )
                        await asyncio.sleep(self.turn_delay)
                    
                    # Process Player 2's turn
                    events = self.process_player2_turn()
                    for event in events:
                        if self.event_manager:
                            await self.event_manager.emit(
                                event["type"],
                                event["name"],
                                event["data"]
                            )
                        await asyncio.sleep(self.turn_delay)
                    
                    # Round summary
                    if self.event_manager:
                        await self.event_manager.emit_system("round_summary", 
                            self.get_round_summary()
                        )
                    await asyncio.sleep(self.round_delay)
                    
                except Exception as e:
                    self.logger.error(f"{Fore.RED}Error in round {round_num}: {str(e)}{Style.RESET_ALL}")
                    if self.event_manager:
                        await self.event_manager.emit_error(f"Round {round_num} error: {str(e)}")
                    raise
            
            # Game end
            self.state = "complete"
            if self.event_manager:
                await self.event_manager.emit_system("game_ended", {
                    "winner": self.get_winner(),
                    "final_standings": self.get_player_statuses()
                })
                
        except Exception as e:
            self.state = "error"
            self.logger.error(f"{Fore.RED}Game error: {str(e)}{Style.RESET_ALL}")
            if self.event_manager:
                await self.event_manager.emit_error(str(e))
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

    def set_strategy(self, strategy: str):
        """Set the strategy for the game"""
        if not strategy.strip():
            self.logger.warning("Empty strategy provided, using default strategy")
            return
            
        self.strategy_advisory = strategy
        self.player1.set_strategy(strategy)
        self.logger.info(f"Strategy set: {strategy[:100]}...")

    def process_player1_turn(self) -> List[Dict[str, Any]]:
        """Process Player 1's turn"""
        self.logger.info(f"{Fore.CYAN}Starting Player 1 (Marco Polo) turn{Style.RESET_ALL}")
        events = []
        try:
            # Create context with current game state
            context = {
                "round": self.round,
                "max_rounds": self.max_rounds,
                "player_statuses": self.get_player_statuses(),
                "conversation_history": self.memory.get_recent_context(),
                "strategy": self.strategy_advisory
            }
            
            # Thinking phase
            thinking = self.player1.generate_thinking(context)
            events.append({
                "type": "player",
                "name": "player_thinking",
                "data": {
                    "player": "Marco Polo",
                    "thinking": thinking,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Action phase with same context
            action = self.player1.generate_action(context)
            events.append({
                "type": "player",
                "name": "player_action",
                "data": {
                    "player": "Marco Polo",
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Process transfers
            self._process_transfers(self.player1, action.get("transfers", []))
            
            return events
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}Error in Player 1's turn: {str(e)}{Style.RESET_ALL}")
            raise

    def process_player2_turn(self) -> List[Dict[str, Any]]:
        """Process Player 2's turn"""
        self.logger.info(f"{Fore.CYAN}Starting Player 2 (Trader Joe) turn{Style.RESET_ALL}")
        events = []
        try:
            # Thinking phase
            thinking = self.player2.generate_thinking()
            events.append({
                "type": "player",
                "name": "player_thinking",
                "data": {
                    "player": "Trader Joe",
                    "thinking": thinking,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Action phase
            action = self.player2.generate_action()
            events.append({
                "type": "player",
                "name": "player_action",
                "data": {
                    "player": "Trader Joe",
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Process transfers
            self._process_transfers(self.player2, action["transfers"])
            
            return events
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}Error in Player 2's turn: {str(e)}{Style.RESET_ALL}")
            raise

    def get_winner(self) -> str:
        """Get the winner of the game"""
        statuses = self.get_player_statuses()
        max_coins = max(statuses.values())
        winners = [p for p, c in statuses.items() if c == max_coins]
        return winners[0] if len(winners) == 1 else "Tie"

    def get_round_summary(self) -> Dict[str, Any]:
        """Get summary of the current round"""
        return {
            "round": self.round,
            "standings": self.get_player_statuses(),
            "transfers": [
                {
                    "from": t["sender"],
                    "to": t["recipient"],
                    "amount": t["amount"]
                }
                for t in self.memory.transfers 
                if t["round"] == self.round
            ]
        } 