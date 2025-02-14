from typing import Dict, List
from ..agents.players import Player1, Player2, Player3
import json
import logging
from datetime import datetime
import os
from ..agents.coordinator import CoordinatorAgent
import re
from ....utils.config import Config

class ConversationMemory:
    def __init__(self):
        self.messages = []
        self.transfers = []
    
    def add_message(self, speaker: str, message: str):
        self.messages.append({
            'round': len(self.messages) // 3 + 1,  # 3 players per round
            'speaker': speaker,
            'message': message,
            'timestamp': datetime.now()
        })
    
    def add_transfer(self, sender: str, recipient: str, amount: int):
        self.transfers.append({
            'round': len(self.messages) // 3 + 1,
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

class NegotiationScene:
    def __init__(self, max_rounds: int = 5):
        config = Config()
        self.max_rounds = max_rounds
        # Get space-specific config
        space_config = config.get_space_config('merchants_multi')
        # Define players in order from config
        self.player_order = space_config['players']
        self.players = {
            self.player_order[0]: Player1(self.player_order[0]),
            self.player_order[1]: Player2(self.player_order[1]),
            self.player_order[2]: Player3(self.player_order[2])
        }
        self.coordinator = CoordinatorAgent('Coordinator')
        self.memory = ConversationMemory()
        self.logger = self._setup_logger()
        self.system_prompt = self._get_system_prompt()
        
    def _setup_logger(self):
        logger = logging.getLogger('multi_negotiation')  # Changed logger name
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(f'logs/multi_negotiation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatters
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(message)s')
        fh.setFormatter(file_formatter)
        ch.setFormatter(console_formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _get_system_prompt(self) -> str:
        """Get the shared system prompt for all agents"""
        return """You are participating in a 5-round negotiation game with three players:
        - Alex (Player 1): Speaks first each round
        - Blake (Player 2): Speaks second each round
        - Charlie (Player 3): Speaks last each round
        
        Game Rules:
        1. Each player starts with 10 coins
        2. Players can transfer coins to form alliances
        3. The player with most coins at the end wins
        4. Players take turns in fixed order: Alex → Blake → Charlie
        
        IMPORTANT: You must respond with ONLY a valid JSON object in this exact format:
        {
            "message": "your strategic message as a single string",
            "transfers": [
                {"recipient": "player_name", "amount": number}
            ]
        }
        
        Response Requirements:
        - Must be valid JSON
        - Message must be a single string
        - Transfers must be an array (can be empty: [])
        - Recipient must be one of: Alex, Blake, Charlie
        - Amount must be a positive integer
        - Cannot transfer more coins than you have
        """
    
    def _log_thinking(self, agent_name: str, prompt: str):
        """Log agent's thinking process"""
        self.logger.info(f"\n🤔 {agent_name} is thinking...")
        
        # Extract and show key points
        points = []
        
        # Game state
        if "Current round:" in prompt:
            round_info = re.search(r"Current round: (\d+) of \d+", prompt)
            if round_info:
                points.append(f"Round {round_info.group(1)}")
        
        # Coins
        if "Your coins:" in prompt:
            coins_info = re.search(r"Your coins: (\d+)", prompt)
            if coins_info:
                points.append(f"Has {coins_info.group(1)} coins")
        
        # Strategy points
        if "Recent conversation:" in prompt:
            points.append("Analyzing recent conversations...")
        if "Recent transfers:" in prompt:
            points.append("Reviewing recent transfers...")
        if "Consider forming alliances" in prompt:
            points.append("Evaluating potential alliances...")
        if "transfers" in prompt.lower():
            points.append("Calculating possible transfers...")
        
        for point in points:
            self.logger.info(f"   �� {point}")

    def get_player_statuses(self) -> Dict[str, int]:
        return {name: player.coins for name, player in self.players.items()}
    
    def process_player_turn(self, player_name: str, round: int, context: str, statuses: Dict[str, int]):
        """Process a single player's turn"""
        player = self.players[player_name]
        
        try:
            # Log thinking process
            self._log_thinking(player_name, context)
            
            # Get raw response from player with system prompt
            raw_response = player.process(
                action='negotiate',
                round=round,
                conversation_history=context,
                player_statuses=statuses,
                system_prompt=self.system_prompt
            )
            
            # Format response through coordinator
            action = self.coordinator.process(
                action='format_response',
                raw_response=raw_response,
                player_name=player_name,
                available_coins=player.coins
            )
            
            # Log thinking and response
            if 'thinking' in action:
                self.logger.info("\n💭 Thinking process:")
                self.logger.info(f"   {action['thinking']}\n")
            
            # Log the final decision
            self.logger.info(f"🗣️ {player_name} speaks: {action['message']}")
            
            # Record and process
            self.memory.add_message(player_name, action['message'])
            if 'transfers' in action:
                for transfer in action['transfers']:
                    valid, reason = self.coordinator.validate_transfer(
                        player_name,
                        transfer['recipient'],
                        transfer['amount'],
                        statuses
                    )
                    if valid:
                        self.process_transfers([transfer], player_name)
                    else:
                        self.logger.warning(f"⚠️ Invalid transfer: {reason}")
            
            return action
            
        except Exception as e:
            self.logger.error(f"❌ Error processing {player_name}'s action: {str(e)}")
            return {
                "reasoning": ["Error occurred during processing"],
                "message": f"Error: {str(e)}",
                "transfers": []
            }

    def process_transfers(self, transfers: List[Dict[str, any]], acting_player: str):
        for transfer in transfers:
            sender = self.players[acting_player]
            recipient = self.players[transfer['recipient']]
            amount = transfer['amount']
            if sender.transfer_coins(amount, recipient):
                self.memory.add_transfer(acting_player, transfer['recipient'], amount)
                self.logger.info(f"💰 {acting_player} transferred {amount} coins to {transfer['recipient']}")
    
    def run_scene(self) -> Dict[str, any]:
        self.logger.info("\n🎮 Starting Negotiation Game (5 Rounds)")
        self.logger.info("\nPlayers and their models:")
        for name, player in self.players.items():
            self.logger.info(f"  {name}: {player.model} (backup: {player.backup_model})")
        self.logger.info(f"  Coordinator: {self.coordinator.model} (backup: {self.coordinator.backup_model})\n")
        
        for round in range(1, self.max_rounds + 1):
            self.logger.info(f"\n📍 Round {round}/{self.max_rounds}")
            self.logger.info("Current standings:")
            for name in self.player_order:  # Use ordered player list
                self.logger.info(f"  {name}: {self.players[name].coins} coins")
            self.logger.info("")
            
            round_actions = []
            
            # Process players in strict order
            for player_name in self.player_order:
                self.logger.info(f"\n👤 {player_name}'s turn:")
                
                # Get current game state
                context = self.memory.get_recent_context()
                statuses = self.get_player_statuses()
                
                # Process player's turn and wait for completion
                action = self.process_player_turn(player_name, round, context, statuses)
                round_actions.append(action)
                
                # Ensure a visual break between players
                self.logger.info("------------------------")
            
            # Round summary
            summary = self.coordinator.process(
                action='summarize',
                round_num=round,
                actions=round_actions,
                player_balances=self.get_player_statuses()
            )
            self.logger.info(f"\n📊 Round {round} Summary:\n{summary}\n")
            self.logger.info("================================")
        
        # Game end
        final_statuses = self.get_player_statuses()
        winner = max(final_statuses.items(), key=lambda x: x[1])
        
        self.logger.info("\n🏁 Game Over!")
        self.logger.info(f"🏆 Winner: {winner[0]} with {winner[1]} coins!")
        self.logger.info("\nFinal Standings:")
        for name in self.player_order:  # Use ordered player list
            self.logger.info(f"  {name}: {self.players[name].coins} coins")
        
        return {
            'winner': winner[0],
            'final_statuses': final_statuses,
            'conversation_memory': self.memory
        } 