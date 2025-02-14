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

class NegotiationRuntime:
    def __init__(self, logger: GameLogger):
        self.player1 = Player1("Marco Polo")
        self.player2 = Player2("Trader Joe")
        self.logger = logger
        self.round = 1
        self.max_rounds = 5  # Set this directly in __init__
        
        config = Config()
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
    
    def run(self):
        """Run the negotiation game"""
        self.logger.info(f"\n🎮 Starting PvP Negotiation Game ({self.max_rounds} Rounds)")
        
        for round in range(1, self.max_rounds + 1):
            self.logger.info(f"\n📍 Round {round}/{self.max_rounds}")
            self.logger.info("Current standings:")
            for name, coins in self.get_player_statuses().items():
                self.logger.info(f"  {name}: {coins} coins")
            
            for player_name in self.player_order:
                self.logger.info(f"\n👤 {player_name}'s turn:")
                self._process_player_turn(player_name, round)
                self.logger.info("------------------------")
            
            self._log_round_summary(round)
            if round < self.max_rounds:
                self.logger.info("================================")
        
        # Game end
        final_statuses = self.get_player_statuses()
        winner = max(final_statuses.items(), key=lambda x: x[1])
        
        self.logger.info("\n🏁 Game Over!")
        self.logger.info(f"🏆 Winner: {winner[0]} with {winner[1]} coins!")
        self.logger.info("\nFinal Standings:")
        for name in self.player_order:
            self.logger.info(f"  {name}: {self.players[name].coins} coins")
        
        return {
            'winner': winner[0],
            'final_statuses': final_statuses,
            'conversation_memory': self.memory
        }
    
    def _process_player_turn(self, player_name: str, round: int):
        """Process a single player's turn"""
        player = self.players[player_name]
        try:
            # Get current game state
            context = {
                'round': round,
                'player_statuses': self.get_player_statuses()
            }
            
            # Process player's action
            action = player.process(
                action='negotiate',
                round=round,
                player_statuses=self.get_player_statuses()
            )
            
            # Log deep thinking to file (if present in response)
            if 'thinking' in action:
                self.logger.info(f"🤔 {player_name}'s private analysis (Round {round}):")
                self.logger.info(action['thinking'])
                self.logger.info("------------------------")
                # Remove thinking from action before processing further
                del action['thinking']
            
            # Process visible actions
            if 'message' in action:
                message = action['message']
                self.logger.info(f"🗣️ {player_name} speaks: {message}")
                self.memory.add_message(player_name, message)
            
            if 'transfers' in action:
                for transfer in action['transfers']:
                    recipient = transfer['recipient']
                    amount = transfer['amount']
                    if recipient in self.players:
                        if player.transfer_coins(amount, self.players[recipient]):
                            self.logger.info(f"💰 {player_name} transferred {amount} coins to {recipient}")
                            self.memory.add_transfer(player_name, recipient, amount)
        
        except Exception as e:
            self.logger.error(f"❌ Error processing {player_name}'s action: {str(e)}")
    
    def _log_round_summary(self, round: int):
        """Log summary of the round"""
        self.logger.info(f"\n📊 Round {round} Summary:")
        # Add round summary logic here 

    def process_player1_turn(self) -> List[Dict[str, Any]]:
        events = []
        
        # Generate thinking
        thinking = self.player1.generate_thinking()
        events.append(self.logger.log_player_thinking("Marco Polo", thinking))
        
        # Generate action
        action = self.player1.generate_action()
        events.append(self.logger.log_player_action("Marco Polo", action))
        
        # Process transfers
        self.process_transfers(self.player1, action['transfers'])
        
        return events

    def process_player2_turn(self) -> List[Dict[str, Any]]:
        events = []
        
        # Generate thinking
        thinking = self.player2.generate_thinking()
        events.append(self.logger.log_player_thinking("Trader Joe", thinking))
        
        # Generate action
        action = self.player2.generate_action()
        events.append(self.logger.log_player_action("Trader Joe", action))
        
        # Process transfers
        self.process_transfers(self.player2, action['transfers'])
        
        return events

    def process_transfers(self, player, transfers):
        for transfer in transfers:
            recipient = transfer['recipient']
            amount = transfer['amount']
            if recipient in self.players:
                if player.transfer_coins(amount, self.players[recipient]):
                    self.logger.info(f"💰 {player.name} transferred {amount} coins to {recipient}")
                    self.memory.add_transfer(player.name, recipient, amount) 