import requests
import json
from typing import Dict, Any
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FileverseClient:
    def __init__(self, base_url: str = None):
        # Use environment variable with fallback
        self.base_url = base_url or os.getenv('FILEVERSE_API_URL', 'https://api.singha.today')
        logger.info(f"Initialized FileverseClient with base URL: {self.base_url}")
        
    def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file content by ID"""
        try:
            response = requests.get(f'{self.base_url}/api/files/{file_id}')
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Retrieved file: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving file: {str(e)}")
            raise
    
    async def save_game_log(self, game_id: str, game_data: Dict[str, Any]) -> str:
        """Save game log as markdown file"""
        try:
            # Format game data as markdown
            content = self._format_game_markdown(game_id, game_data)
            
            # Create file
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                f'{self.base_url}/api/files',
                headers=headers,
                json={'content': content}
            )
            response.raise_for_status()
            
            result = response.json()
            file_id = result.get('fileId')
            file_hash = result.get('hash')
            
            if not file_id:
                raise ValueError(f"No fileId in response: {result}")
                
            logger.info(f"Game log saved with file ID: {file_id} (hash: {file_hash})")
            return file_id
            
        except Exception as e:
            logger.error(f"Error saving game log: {str(e)}")
            raise
    
    def _format_game_markdown(self, game_id: str, data: Dict[str, Any]) -> str:
        """Format game data as markdown"""
        timestamp = data.get('timestamp', '')
        winner = data.get('winner', 'No winner')
        final_standings = data.get('final_standings', {})
        history = data.get('history', {})
        messages = history.get('messages', [])
        transfers = history.get('transfers', [])
        
        md = [
            f"# Game Report: {game_id}",
            f"*Generated at: {timestamp}*",
            "",
            "## Final Results",
            f"**Winner:** {winner}",
            "",
            "### Final Standings",
        ]
        
        # Add standings
        for player, coins in final_standings.items():
            md.append(f"- {player}: {coins} coins")
        
        # Add conversation history
        md.extend([
            "",
            "## Game History",
            "",
            "### Conversation Log",
            "| Round | Speaker | Message |",
            "|-------|---------|---------|",
        ])
        
        for msg in messages:
            md.append(f"| {msg['round']} | {msg['speaker']} | {msg['message']} |")
        
        # Add transfer history
        md.extend([
            "",
            "### Transfer Log",
            "| Round | From | To | Amount |",
            "|-------|------|-----|--------|",
        ])
        
        for transfer in transfers:
            md.append(
                f"| {transfer['round']} | {transfer['sender']} | "
                f"{transfer['recipient']} | {transfer['amount']} |"
            )
        
        return "\n".join(md) 