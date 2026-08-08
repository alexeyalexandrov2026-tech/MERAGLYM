from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

class BaseAdapter(ABC):
    """
    Abstract base class for all OSINT adapters in MERAGLYM.
    Ensures consistent interface for collecting and returning intelligence data.
    """
    
    # Each adapter must declare its unique identifier and region.
    identifier: str
    region: str = "GLOBAL"
    version: str = "1.0.0"

    @abstractmethod
    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the adapter logic given an input payload (e.g. {"type": "Email", "value": "test@example.com"}).
        Returns a list of standardized Observation payloads to be ingested into the Intelligence Graph.
        """
        pass

    async def _handle_rate_limit(self):
        """
        Utility for adapters to implement standard backoff or rate-limiting.
        """
        pass
