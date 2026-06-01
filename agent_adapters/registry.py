from typing import Dict, Type
from .base import BaseAdapter

class Registry:
    """Agent adapter registry"""

    _adapters: Dict[str, Type[BaseAdapter]] = {}

    @classmethod
    def register(cls, adapter_id: str, adapter_class: Type[BaseAdapter]):
        """Register an adapter"""
        cls._adapters[adapter_id] = adapter_class

    @classmethod
    def get(cls, adapter_id: str) -> BaseAdapter:
        """Get adapter instance by ID"""
        if adapter_id not in cls._adapters:
            raise ValueError(f"Unknown adapter: {adapter_id}")
        return cls._adapters[adapter_id]()

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered adapter IDs"""
        return list(cls._adapters.keys())

    @classmethod
    def detect_available(cls) -> list[str]:
        """Detect which agents are installed"""
        available = []
        for adapter_id in cls._adapters:
            try:
                if cls.get(adapter_id).detect_installation():
                    available.append(adapter_id)
            except Exception:
                pass
        return available
