from typing import Dict, List, Type
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
        existing = cls._adapters.get(identifier)
        if existing is not None and existing.__qualname__ != adapter_class.__qualname__:
            raise ValueError(f"Adapter with identifier '{identifier}' already registered. Avoid duplicate tools.")
        cls._adapters[identifier] = adapter_class
        return adapter_class

    @classmethod
    def identifiers(cls) -> List[str]:
        return sorted(cls._adapters)

    @classmethod
    def get_adapter(cls, identifier: str) -> BaseAdapter:
        """Instantiate and return an adapter by identifier."""
        adapter_class = cls._adapters.get(identifier)
        if not adapter_class:
            raise ValueError(
                f"INVALID_INPUT: Adapter '{identifier}' not found in registry. Known: {', '.join(cls.identifiers())}"
            )
        return adapter_class()


registry = AdapterRegistry()
