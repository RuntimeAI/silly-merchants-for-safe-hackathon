from enum import Enum

class GameEventType(Enum):
    # Game lifecycle events
    GAME_CREATED = "game_created"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    
    # Round events
    ROUND_STARTED = "round_started"
    ROUND_ENDED = "round_ended"
    
    # Player events
    PLAYER_THINKING = "player_thinking"
    PLAYER_ACTION = "player_action"
    
    # System events
    SYSTEM_STATUS = "system_status"
    LOGS_SAVED = "logs_saved"
    ERROR = "error" 