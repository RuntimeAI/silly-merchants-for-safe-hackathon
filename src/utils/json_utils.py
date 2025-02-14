import json
from datetime import datetime

class GameJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def game_json_dumps(obj):
    """Helper function to dump JSON with custom encoder"""
    return json.dumps(obj, cls=GameJSONEncoder) 