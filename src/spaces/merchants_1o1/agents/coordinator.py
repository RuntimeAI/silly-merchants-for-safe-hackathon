from typing import Dict, Optional, List, Any
from .base import NegotiationAgent
import json
import re
from ....utils.config import Config
from ....utils.llm_providers.openrouter import OpenRouterProvider
from ....utils.logger import logger

class CoordinatorAgent(NegotiationAgent):
    def __init__(self, name: str):
        super().__init__(name)
        
        # Override model config with coordinator-specific config
        config = Config()
        model_config = config.llm_config['models']['coordinator']
        self.model = model_config['default']
        self.backup_model = model_config['backup']
        
        self.logger.info(f"Coordinator {name} initialized")

    def _get_role_prompt(self) -> str:
        return """You are the coordinator for a trading game.
        Your role is to facilitate negotiations and ensure fair play.
        Be objective and impartial in your assessments."""

    def evaluate_round(self, round_num: int, player_statuses: Dict[str, Any]) -> str:
        """Evaluate the current round state"""
        prompt = (
            f"Round {round_num} Status:\n"
            f"Player standings: {player_statuses}\n\n"
            "Provide a brief, impartial analysis of the current game state."
        )
        return self.generate_response(prompt, temperature=0.7)

    def process(self, *args, **kwargs):
        """Process different coordinator actions"""
        action = kwargs.get('action')
        if action == 'format_response':
            return self.format_response(
                kwargs.get('raw_response'),
                kwargs.get('player_name'),
                kwargs.get('available_coins')
            )
        elif action == 'summarize':
            return self.summarize_round(
                kwargs.get('round_num'),
                kwargs.get('actions'),
                kwargs.get('player_balances')
            )
        raise ValueError(f"Unknown action: {action}")

    def format_response(self, raw_response: str, player_name: str, available_coins: int) -> Dict:
        """Format player response with bilingual commentary"""
        try:
            # First try to parse as JSON
            parsed = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            if self._is_valid_format(parsed):
                return self._validate_transfers(parsed, available_coins)
        except:
            pass
        
        prompt = f"""
        As a bilingual host, format this player's response and add entertaining commentary in both languages.

        Player: {player_name}
        Available Coins: {available_coins}
        Raw Response: ```{raw_response}```
        
        Format as JSON:
        {{
            "thinking": "🎙️ [English Commentary] Strategic analysis here\\n🎭 [中文点评] 你的精彩评论",
            "message": "player's message in English",
            "transfers": [
                {{"recipient": "player_name", "amount": number}}
            ]
        }}

        Requirements:
        - Keep player's message in English for accuracy
        - Provide commentary in both English and Chinese
        - Validate transfers (max: {available_coins} coins)
        - Use emojis and entertaining tone
        - Create dramatic moments
        """
        
        try:
            formatted = self.llm.generate(prompt)
            result = json.loads(formatted)
            return self._validate_transfers(result, available_coins)
        except json.JSONDecodeError:
            return {
                "thinking": """🤔 [English] Seems our player is having trouble expressing their thoughts...
                             [中文] 哎呀！这位选手说话有点难懂呢~ 让我们看看能不能理解一下~""",
                "message": f"I'm having trouble expressing my thoughts clearly.",
                "transfers": []
            }
        except Exception as e:
            return {
                "thinking": f"""😅 [English] Oops! We've hit a small technical bump: {str(e)}
                              [中文] 哎呦喂！遇到了点小问题：{str(e)}""",
                "message": "I need a moment to collect my thoughts.",
                "transfers": []
            }

    def summarize_round(self, round_num: int, actions: List[Dict], player_balances: Dict[str, int]) -> str:
        """Create an entertaining bilingual round summary"""
        # Format actions for better readability
        formatted_actions = []
        for action in actions:
            if isinstance(action, dict):
                formatted_action = {
                    "player": action.get("player_name", "Unknown"),
                    "message": action.get("message", "No message"),
                    "transfers": action.get("transfers", [])
                }
                formatted_actions.append(formatted_action)

        prompt = f"""
        Create an exciting bilingual summary for round {round_num}!

        Round Actions:
        {json.dumps(formatted_actions, indent=2, ensure_ascii=False)}

        Current Balances:
        {json.dumps(player_balances, indent=2, ensure_ascii=False)}

        Respond in this JSON format:
        {{
            "round_summary": {{
                "highlights": {{
                    "en": "Most exciting moves and strategies",
                    "zh": "本回合最激动人心的操作和策略"
                }},
                "alliances": {{
                    "en": "Analysis of alliances and betrayals",
                    "zh": "联盟与背叛的情况分析"
                }},
                "impact": {{
                    "en": "How coin distribution affects the game",
                    "zh": "金币分布的变化对游戏的影响"
                }},
                "next_round": {{
                    "en": "Expectations for next round",
                    "zh": "对下一回合的期待和预测"
                }}
            }}
        }}
        """
        
        try:
            summary = self.llm.generate(prompt)
            parsed_summary = json.loads(summary)
            return json.dumps(parsed_summary, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({
                "round_summary": {
                    "status": f"""
                    🎭 Round {round_num} Review | 第{round_num}回合精彩回顾：
                    
                    [English] What an exciting round, despite our technical hiccup! 
                    [中文] 哎呀呀！本回合可真是跌宕起伏啊！
                    
                    Current Standing | 目前战况：
                    {' '.join([f'🎮 {name}: {coins} coins | {coins}枚金币' for name, coins in player_balances.items()])}
                    
                    [English] Stay tuned for the next round!
                    [中文] 让我们期待下回合的精彩表现！✨
                    """
                }
            }, ensure_ascii=False, indent=2)

    def _is_valid_format(self, data: Dict) -> bool:
        """Check if the response follows the required format"""
        return (
            isinstance(data, dict) and
            "thinking" in data and
            isinstance(data["thinking"], str) and
            "message" in data and
            isinstance(data["message"], str) and
            "transfers" in data and
            isinstance(data["transfers"], list) and
            all(
                isinstance(t, dict) and
                "recipient" in t and
                "amount" in t and
                isinstance(t["amount"], (int, float))
                for t in data["transfers"]
            )
        )
    
    def _validate_transfers(self, response: Dict, available_coins: int) -> Dict:
        """Validate and adjust transfers if needed"""
        if not response.get("transfers"):
            response["transfers"] = []
            return response
        
        total_transfer = sum(t["amount"] for t in response["transfers"])
        if total_transfer > available_coins:
            # Scale down transfers proportionally
            scale = available_coins / total_transfer
            for transfer in response["transfers"]:
                transfer["amount"] = int(transfer["amount"] * scale)
            response["message"] = f"{response['message']} (Note: Transfers adjusted to match available coins)"
        
        return response

    def validate_transfer(self, sender: str, recipient: str, amount: int, 
                         player_balances: Dict[str, int]) -> tuple[bool, str]:
        """Validate a proposed coin transfer"""
        if amount <= 0:
            return False, "Transfer amount must be positive"
        
        if sender not in player_balances:
            return False, f"Invalid sender: {sender}"
            
        if recipient not in player_balances:
            return False, f"Invalid recipient: {recipient}"
            
        if amount > player_balances[sender]:
            return False, f"{sender} doesn't have enough coins for this transfer"
            
        return True, "Transfer valid"

class GameCoordinator:
    def __init__(self):
        self.round = 1
        self.max_rounds = 5
        self.player1 = Player1("Marco Polo")
        self.player2 = Player2("Trader Joe")
        
    def _format_player_status(self) -> Dict[str, int]:
        """Format player status as simple dict"""
        status = {
            self.player1.name: self.player1.coins,
            self.player2.name: self.player2.coins
        }
        
        # Print current standings in a clean format
        print(f"\n{'='*50}")
        print(f"📊 Current Standings")
        print(f"{'='*50}")
        for name, coins in status.items():
            print(f"👤 {name}: {coins} coins")
        print(f"{'='*50}\n")
        
        return status

    def _validate_action(self, action: Dict[str, Any], player_name: str) -> Dict[str, Any]:
        """Validate and normalize player action"""
        try:
            if not isinstance(action, dict):
                raise ValueError("Invalid action format")
            
            # Validate and log only important game events
            if action.get("transfers"):
                transfers = action["transfers"]
                total = sum(t["amount"] for t in transfers)
                if total > 0:
                    logger.info(
                        f"💸 {player_name} transfers: "
                        f"Total {total} coins in {len(transfers)} transaction(s)"
                    )
            
            return action
        except Exception as e:
            logger.error(f"❌ Invalid action from {player_name}: {str(e)}")
            return {
                "message": f"Error: {str(e)}",
                "transfers": []
            } 