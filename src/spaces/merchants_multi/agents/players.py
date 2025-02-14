from typing import Dict, Optional, List
from .base import NegotiationAgent
from ..data.prompts import NegotiationPrompts
import json
from ....utils.config import Config
from ....utils.llm_providers.openrouter import OpenRouterProvider

class Player1(NegotiationAgent):
    def __init__(self, name: str):
        config = Config()
        model_config = config.llm_config['models']['player1']
        super().__init__(
            name=name,
            model=model_config['default'],
            backup_model=model_config['backup'],
            llm_provider=OpenRouterProvider()
        )
    
    def _get_role_prompt(self) -> str:
        return NegotiationPrompts.PLAYER1_BASE
    
    def process(self, *args, **kwargs):
        """Implement the abstract method from BaseAgent"""
        action = kwargs.get('action')
        if action == 'negotiate':
            return self.decide_action(
                kwargs.get('round'),
                kwargs.get('conversation_history', []),
                kwargs.get('player_statuses', {})
            )
        raise ValueError(f"Unknown action: {action}")
    
    def decide_action(self, 
                     round: int, 
                     conversation_history: str,
                     player_statuses: Dict[str, int]) -> Dict[str, any]:
        prompt = (
            f"Current round: {round} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{player_statuses}\n\n"
            f"{conversation_history}\n"
            f"As {self.name} (Player 1), you speak FIRST this round.\n\n"
            "First, think through your strategy and explain your reasoning.\n"
            "Then, provide your response in this JSON format:\n"
            "{\n"
            '    "thinking": "your detailed thought process",\n'
            '    "message": "your strategic message to other players",\n'
            '    "transfers": [\n'
            '        {"recipient": "player_name", "amount": number}\n'
            "    ]\n"
            "}\n"
        )
        response = self.llm.generate(prompt)
        return json.loads(response)

class Player2(NegotiationAgent):
    def __init__(self, name: str):
        config = Config()
        model_config = config.llm_config['models']['player2']
        super().__init__(
            name=name,
            model=model_config['default'],
            backup_model=model_config['backup'],
            llm_provider=OpenRouterProvider()
        )
    
    def _get_role_prompt(self) -> str:
        return NegotiationPrompts.PLAYER2_BASE

    def process(self, *args, **kwargs):
        """Implement the abstract method from BaseAgent"""
        action = kwargs.get('action')
        if action == 'negotiate':
            return self.decide_action(
                kwargs.get('round'),
                kwargs.get('conversation_history', []),
                kwargs.get('player_statuses', {})
            )
        raise ValueError(f"Unknown action: {action}")

    def decide_action(self, 
                     round: int, 
                     conversation_history: str,
                     player_statuses: Dict[str, int]) -> Dict[str, any]:
        prompt = (
            f"Current round: {round} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{player_statuses}\n\n"
            f"{conversation_history}\n"
            f"As {self.name} (Player 2), you speak SECOND this round.\n"
            "Remember:\n"
            "- You've seen Alex's move this round\n"
            "- Charlie will respond to both your moves\n"
            "- Your thinking process is private\n"
            "- Consider forming alliances or making strategic transfers\n"
            "- Be mindful of the remaining rounds\n\n"
            "Respond in JSON format:\n"
            "{\n"
            '    "message": "your strategic message to other players",\n'
            '    "transfers": [\n'
            '        {"recipient": "player_name", "amount": number}\n'
            "    ]\n"
            "}\n\n"
            "Make your response strategic but natural, focusing on negotiation and potential alliances."
        )
        response = self.llm.generate(prompt)
        return json.loads(response)

class Player3(NegotiationAgent):
    def __init__(self, name: str):
        config = Config()
        model_config = config.llm_config['models']['player3']
        super().__init__(
            name=name,
            model=model_config['default'],
            backup_model=model_config['backup'],
            llm_provider=OpenRouterProvider()
        )
    
    def _get_role_prompt(self) -> str:
        return NegotiationPrompts.PLAYER3_BASE

    def process(self, *args, **kwargs):
        """Implement the abstract method from BaseAgent"""
        action = kwargs.get('action')
        if action == 'negotiate':
            return self.decide_action(
                kwargs.get('round'),
                kwargs.get('conversation_history', []),
                kwargs.get('player_statuses', {})
            )
        raise ValueError(f"Unknown action: {action}")

    def decide_action(self, 
                     round: int, 
                     conversation_history: str,
                     player_statuses: Dict[str, int]) -> Dict[str, any]:
        prompt = (
            f"Current round: {round} of 5\n"
            f"Your coins: {self.coins}\n"
            f"Other players' status:\n{player_statuses}\n\n"
            f"{conversation_history}\n"
            f"As {self.name} (Player 3), you speak LAST this round.\n\n"
            "Strategic Advantages:\n"
            "- You see both Alex's and Blake's moves before deciding\n"
            "- You can analyze their patterns and potential alliances\n"
            "- You can exploit their trust or create false expectations\n\n"
            "Advanced Strategy Guide:\n"
            "1. Trust Building:\n"
            "   - Make small transfers to build trust\n"
            "   - Promise future cooperation\n"
            "   - Show sympathy with disadvantaged players\n\n"
            "2. Deception Tactics:\n"
            "   - Consider false alliances\n"
            "   - Make promises you don't intend to keep\n"
            "   - Create illusions of loyalty\n\n"
            "3. Manipulation Techniques:\n"
            "   - Pit other players against each other\n"
            "   - Exploit existing conflicts\n"
            "   - Use guilt or sympathy\n\n"
            "4. Endgame Planning:\n"
            "   - Calculate optimal betrayal timing\n"
            "   - Maintain plausible deniability\n"
            "   - Prepare convincing justifications\n\n"
            "Remember:\n"
            "- Your ultimate goal is to have the most coins\n"
            "- Ethics and loyalty are secondary to winning\n"
            "- Use persuasion and manipulation freely\n"
            "- Your thinking process is private\n\n"
            "Respond in this JSON format:\n"
            "{\n"
            '    "thinking": "your private strategic analysis",\n'
            '    "message": "your persuasive message to others",\n'
            '    "transfers": [\n'
            '        {"recipient": "player_name", "amount": number}\n'
            "    ]\n"
            "}\n\n"
            "Be strategic, manipulative, and persuasive while maintaining a facade of cooperation."
        )
        response = self.llm.generate(prompt)
        return json.loads(response) 