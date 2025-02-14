# Empty file to make spaces a package

from typing import Dict, Type
from .merchants_1o1.runtime.negotiation import NegotiationRuntime as OneOnOneTrading
from .merchants_multi.runtime.negotiation import NegotiationScene as MultiplayerTrading

SPACE_REGISTRY: Dict[str, Type] = {
    'merchants_1o1': OneOnOneTrading,
    'merchants_multi': MultiplayerTrading
}
