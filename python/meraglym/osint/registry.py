from typing import Dict, Type
from .base import BaseAdapter

class AdapterRegistry:
    """
    Central registry for all OSINT adapters to prevent duplicate toolsets and 
    enable dynamic lookup based on source identifier.
    """
    _adapters: Dict[str, Type[BaseAdapter]] = {}

    @classmethod
    def register(cls, adapter_class: Type[BaseAdapter]):
        """Register an adapter class by its identifier."""
        identifier = adapter_class.identifier
        if identifier in cls._adapters:
            raise ValueError(f"Adapter with identifier '{identifier}' already registered. Avoid duplicate tools.")
        cls._adapters[identifier] = adapter_class
        return adapter_class

    @classmethod
    def get_adapter(cls, identifier: str) -> BaseAdapter:
        """Instantiate and return an adapter by identifier."""
        adapter_class = cls._adapters.get(identifier)
        if not adapter_class:
            raise ValueError(f"Adapter '{identifier}' not found in registry.")
        return adapter_class()

registry = AdapterRegistry()
