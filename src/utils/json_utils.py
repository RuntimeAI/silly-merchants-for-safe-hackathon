from json import JSONEncoder
import json
from datetime import datetime
from typing import Any

class GameJSONEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def game_json_dumps(obj: Any) -> str:
    """Dump object to JSON string with custom encoder"""
    return json.dumps(obj, cls=GameJSONEncoder) 