from typing import Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # Initialize private variables
            cls._instance._debug_mode = False
            cls._instance._log_level = 'INFO'
            cls._instance._game_rounds = 5
            cls._instance._fileverse_api_url = 'https://api.singha.today'
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Load environment variables
            self._debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
            self._log_level = os.getenv('LOG_LEVEL', 'INFO')
            self._game_rounds = int(os.getenv('GAME_ROUNDS', '5'))
            self._fileverse_api_url = os.getenv('FILEVERSE_API_URL', 'https://api.singha.today')
            
            # Then load config
            self._load_config()
            self._initialized = True
            
            if self.debug_mode:
                logger.info("🐛 Running in DEBUG mode")
    
    @property
    def debug_mode(self) -> bool:
        return self._debug_mode
    
    @property
    def log_level(self) -> str:
        return self._log_level
    
    @property
    def game_rounds(self) -> int:
        return self._game_rounds
    
    @property
    def fileverse_api_url(self) -> str:
        return self._fileverse_api_url
    
    def _load_config(self):
        """Load configuration from .env and config.yaml"""
        # Load environment variables from .env
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)
        
        # Load YAML config
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Set required environment variables
        self.required_env = {
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        }
        
        # Validate required environment variables
        self._validate_env()
        
        # Setup proxy if configured
        if self.network_config.get('proxy'):
            os.environ['HTTPS_PROXY'] = self.network_config['proxy']
            os.environ['HTTP_PROXY'] = self.network_config['proxy']
    
    def _validate_env(self):
        """Validate required environment variables"""
        missing = [k for k, v in self.required_env.items() if not v]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please create a .env file with these variables."
            )
    
    def get_api_key(self, provider: str) -> str:
        """Get API key from environment variables"""
        key = os.getenv(f'{provider.upper()}_API_KEY')
        if not key:
            raise ValueError(f"No API key found for {provider}")
        return key
    
    def get_space_config(self, space_name: str) -> Dict[str, Any]:
        """Get configuration for a specific game space"""
        if space_name == 'merchants_1o1':
            return {
                'players': ['Marco Polo', 'Trader Joe'],
                'initial_coins': 10,
                'rounds': self._game_rounds if not self._debug_mode else 2
            }
        raise ValueError(f"Unknown space: {space_name}")
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        return self._config.get('llm', {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        return self._config.get('logging', {})
    
    @property
    def game_config(self) -> Dict[str, Any]:
        return self._config.get('game', {})
    
    @property
    def network_config(self) -> Dict[str, Any]:
        return self._config.get('network', {})
    
    @property
    def spaces_config(self) -> Dict[str, Any]:
        return self._config.get('spaces', {})

    def _load_llm_config(self) -> Dict[str, Any]:
        return {
            "default_provider": "gemini",
            "models": {
                "player1": {
                    "default": "gemini-2.0-flash",
                    "backup": "gemini-2.0-flash-lite-preview-02-05",
                    "max_tokens": 1024,
                    "temperature": 0.7
                },
                "player2": {
                    "default": "gemini-2.0-flash",
                    "backup": "gemini-2.0-flash-lite-preview-02-05",
                    "max_tokens": 1024,
                    "temperature": 0.7
                }
            }
        }

    @property
    def game_rounds(self) -> int:
        """Get number of game rounds based on mode"""
        return 2 if self.debug_mode else 5 