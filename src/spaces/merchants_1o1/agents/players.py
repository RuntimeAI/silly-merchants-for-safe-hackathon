from typing import Dict, Any
from .base import NegotiationAgent
from ..data.prompts import NegotiationPrompts
import json
from ....utils.config import Config
from ....utils.llm_providers.fallback import FallbackProvider
from ....utils import logger
import logging

logger = logging.getLogger(__name__)

class Player1(NegotiationAgent):
    def __init__(self, name: str):
        # Call parent constructor first
        super().__init__(name)
        
        # Initialize strategy
        self.strategy_advisory = """
        Strategy for Marco Polo:
        - Build trust in early rounds
        - Be cautious with large transfers
        - Look for opportunities to cooperate
        - Consider betrayal only if heavily betrayed
        """
        self.logger.info(f"Player1 {name} initialized with default strategy")

    def set_strategy(self, strategy: str):
        """Set the strategy for this player"""
        if not strategy or not strategy.strip():
            self.logger.warning("Empty strategy provided, keeping default strategy")
            return
            
        self.strategy_advisory = strategy
        self.logger.info(f"Strategy set for {self.name}: {strategy[:100]}...")

    def _get_role_prompt(self) -> str:
        return NegotiationPrompts.PLAYER1_BASE

    def _get_thinking_prompt(self, context: Dict[str, Any]) -> str:
        """Generate deep thinking prompt for strategic analysis"""
        return (
            f"Current round: {context['round']} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{context['player_statuses']}\n\n"
            "=== DEEP THINKING (Private Analysis) ===\n"
            "As Marco Polo, analyze the current situation. This is your private thought process that others cannot see.\n\n"
            f"Strategic Advisory:\n{context['strategy']}\n\n"
            "Consider and analyze deeply:\n"
            "1. Trust Assessment:\n"
            "   - Analyze Trader Joe's past behavior patterns\n"
            "   - Evaluate likelihood of cooperation vs betrayal\n"
            "2. Game Theory Analysis:\n"
            "   - Calculate optimal coin distribution\n"
            "   - Evaluate risk/reward ratios\n"
            "3. Strategic Planning:\n"
            "   - Plan next 2-3 moves ahead\n"
            "   - Consider bluffing or misdirection\n"
            "4. Psychological Warfare:\n"
            "   - Identify opponent's weaknesses\n"
            "   - Plan manipulation tactics\n\n"
            "Provide your complete private strategic analysis."
        )

    def _get_action_prompt(self, context: Dict[str, Any]) -> str:
        """Generate action prompt with clear sections"""
        return (
            f"Current round: {context['round']} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{context['player_statuses']}\n\n"
            "Based on your deep analysis, generate your next move with these sections:\n\n"
            "=== SPEAK (Public Communication) ===\n"
            "Create a diplomatic message to Trader Joe that aligns with your strategy.\n"
            "This will be visible to others.\n\n"
            "=== ACTION (Game Moves) ===\n"
            "Decide on coin transfers that support your strategy.\n\n"
            "Respond with this exact JSON structure:\n"
            "{\n"
            '    "message": "Your diplomatic message to Trader Joe",\n'
            '    "transfers": [{"recipient": "Trader Joe", "amount": number}]\n'
            "}\n\n"
            "Requirements:\n"
            "- Message should be strategic but not reveal your true intentions\n"
            "- Transfers must be numbers, not strings\n"
            "- No markdown or explanations in the response\n"
            "- Only the JSON object is allowed"
        )

    def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process the agent's action with separate thinking and action phases"""
        action = kwargs.get('action')
        if action == 'negotiate':
            try:
                context = {
                    'round': kwargs.get('round'),
                    'player_statuses': kwargs.get('player_statuses', {}),
                    'strategy': self.strategy_advisory
                }
                
                # Phase 1: Deep Strategic Thinking (Private)
                thinking_prompt = self._get_thinking_prompt(context)
                thinking = self.generate_response(thinking_prompt, temperature=0.9)
                
                # Print thinking in a clean, formatted way
                print(f"\n{'='*50}")
                print(f"🤔 {self.name}'s Private Analysis (Round {context['round']}/5)")
                print(f"{'='*50}")
                print(thinking.strip())
                print(f"{'='*50}\n")
                
                # Phase 2: Public Action Generation
                action_prompt = self._get_action_prompt(context)
                response = self.generate_response(
                    action_prompt,
                    temperature=0.7
                )
                
                try:
                    action_dict = json.loads(response)
                    # Store thinking but don't log it
                    action_dict['thinking'] = thinking
                    
                    # Log only the important game state changes
                    logger.info(
                        f"\n📢 {self.name}'s Action (Round {context['round']}/5):\n"
                        f"💬 Message: {action_dict['message']}\n"
                        f"💰 Transfers: {json.dumps(action_dict['transfers'], indent=2)}"
                    )
                    return action_dict
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid action from {self.name}")
                    return {
                        "thinking": thinking,
                        "message": "Error processing response",
                        "transfers": []
                    }
            except Exception as e:
                logger.error(f"❌ Error in {self.name}'s turn: {str(e)}")
                raise
            
        raise ValueError(f"Unknown action: {action}")

    def generate_thinking(self, strategy: str = None) -> str:
        """Generate deep strategic thinking"""
        strategy = strategy or self.strategy_advisory
        context = {
            'round': self.round,
            'player_statuses': self.get_player_statuses(),
            'strategy': strategy
        }
        thinking_prompt = self._get_thinking_prompt(context)
        thinking = self.generate_response(thinking_prompt, temperature=0.9)
        return thinking

    def generate_action(self, strategy: str = None) -> Dict[str, Any]:
        """Generate action based on strategy"""
        strategy = strategy or self.strategy_advisory
        context = {
            'round': self.round,
            'player_statuses': self.get_player_statuses(),
            'strategy': strategy
        }
        action_prompt = self._get_action_prompt(context)
        try:
            response = self.generate_response(action_prompt, temperature=0.7)
            action = json.loads(response)
            return {
                "message": action.get("message", "No message"),
                "transfers": action.get("transfers", [])
            }
        except Exception as e:
            self.logger.error(f"Error generating action: {str(e)}")
            return {
                "message": "Error occurred while deciding action",
                "transfers": []
            }

class Player2(NegotiationAgent):
    def __init__(self, name: str):
        # Call parent constructor first
        super().__init__(name)
        self.logger.info(f"Player2 {name} initialized")
        
        # Override model config with player2-specific config
        config = Config()
        model_config = config.llm_config['models']['player2']
        self.model = model_config['default']
        self.backup_model = model_config['backup']

    def _get_role_prompt(self) -> str:
        return NegotiationPrompts.PLAYER2_BASE

    def _get_thinking_prompt(self, context: Dict[str, Any]) -> str:
        """Generate thinking prompt for strategic analysis"""
        return (
            f"Current round: {context['round']} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{context['player_statuses']}\n\n"
            "As Trader Joe, analyze the current situation and plan your strategy.\n"
            "Consider:\n"
            "- Marco Polo's previous actions and patterns\n"
            "- Potential counter-strategies\n"
            "- Risk assessment of different approaches\n"
            "- Optimal timing for cooperation or competition\n\n"
            "Provide your private strategic analysis."
        )

    def _get_action_prompt(self, context: Dict[str, Any]) -> str:
        """Generate action prompt for Trader Joe"""
        return (
            f"Current round: {context['round']} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{context['player_statuses']}\n\n"
            "As Trader Joe, generate your next trading action.\n"
            "You must respond with a valid JSON object using this exact structure:\n"
            "{\n"
            '    "message": "your message to Marco Polo",\n'
            '    "transfers": [{"recipient": "Marco Polo", "amount": number}]\n'
            "}\n"
            "Important:\n"
            "- Respond with ONLY the JSON object\n"
            "- No markdown formatting\n"
            "- No explanations\n"
            "- amount must be a number\n"
            "- transfers can be empty list []"
        )

    def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process the agent's action"""
        action = kwargs.get('action')
        if action == 'negotiate':
            context = {
                'round': kwargs.get('round'),
                'player_statuses': kwargs.get('player_statuses', {})
            }
            
            # First, generate deep thinking
            thinking = self.generate_response(self._get_thinking_prompt(context))
            print(f"\n🤔 {self.name}'s private thoughts:\n{thinking}\n")
            
            # Then generate action with explicit JSON requirements
            action_prompt = (
                f"Current round: {context['round']} of 5\n"
                f"Your coins: {self.coins}\n"
                f"Other players' status:\n{context['player_statuses']}\n\n"
                "Based on your analysis, generate a trading action.\n"
                "Your response must be a valid JSON object with exactly this structure:\n"
                "{\n"
                '    "message": "your message to other player",\n'
                '    "transfers": [{"recipient": "string", "amount": number}]\n'
                "}\n"
                "Do not include any markdown or explanation, just the JSON object."
            )
            
            response = self.generate_response(
                action_prompt,
                temperature=0.7  # Lower temperature for more consistent JSON
            )
            
            try:
                action_dict = json.loads(response)
                action_dict['thinking'] = thinking
                return action_dict
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response}")
                return {
                    "thinking": thinking,
                    "message": "Error processing response",
                    "transfers": []
                }
        raise ValueError(f"Unknown action: {action}")

    def generate_thinking(self) -> str:
        """Generate deep strategic thinking"""
        context = {
            'round': self.round,
            'player_statuses': self.get_player_statuses()
        }
        thinking_prompt = self._get_thinking_prompt(context)
        thinking = self.generate_response(thinking_prompt, temperature=0.9)
        return thinking

    def generate_action(self) -> Dict[str, Any]:
        """Generate action based on thinking"""
        context = {
            'round': self.round,
            'player_statuses': self.get_player_statuses()
        }
        action_prompt = self._get_action_prompt(context)
        response = self.generate_response(action_prompt, temperature=0.7)
        
        try:
            action_dict = json.loads(response)
            return action_dict
        except json.JSONDecodeError:
            return {
                "message": "Error processing response",
                "transfers": []
            } 