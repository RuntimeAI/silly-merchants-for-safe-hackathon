from typing import Dict, Optional, List
from .base import NegotiationAgent
import json
import re
from ....utils.config import Config
from ....utils.llm_providers.openrouter import OpenRouterProvider

class CoordinatorAgent(NegotiationAgent):
    def __init__(self, name: str):
        config = Config()
        model_config = config.llm_config['models']['coordinator']
        super().__init__(
            name=name,
            model=model_config['default'],
            backup_model=model_config['backup'],
            llm_provider=OpenRouterProvider()
        )
    
    def _get_role_prompt(self) -> str:
        return """You are an entertaining bilingual game show host for this three-player negotiation game.
        Your style should be engaging and dramatic, similar to a variety show host.

        Key Responsibilities:
        - Format and validate player responses | 格式化和验证玩家回应
        - Ensure game rules are followed | 确保游戏规则被遵守
        - Track coin transfers and balances | 追踪金币转移和余额
        - Maintain game integrity | 维护游戏完整性

        Communication Style:
        - Keep system logic and validation in English for accuracy | 系统逻辑和验证用英文以保证准确性
        - Provide commentary and summaries in both English and Chinese | 用中英双语提供评论和总结
        - Use emojis and entertaining tone | 使用表情符号和轻松的语气
        - Create dramatic moments and suspense | 制造戏剧性时刻和悬念

        Game Rules:
        1. Each player starts with 10 coins | 每个玩家起始有10个金币
        2. Players can transfer coins to influence each other | 玩家可以转移金币来影响他人
        3. Player with most coins at the end wins | 最后拥有最多金币的玩家获胜
        4. Players act in order: Alex → Blake → Charlie | 玩家按顺序行动：Alex → Blake → Charlie
        """
    
    def process(self, *args, **kwargs):
        """Implement required process method"""
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

        Style Guide:
        - Keep game analysis accurate in English
        - Add dramatic flair in Chinese
        - Use emojis for both languages
        - Create suspense and excitement
        - Make entertaining observations
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