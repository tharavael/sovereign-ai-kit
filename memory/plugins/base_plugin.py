#!/usr/bin/env python3
"""
Base class for Long-Term Memory (LTM) plugins.
Implement this interface to integrate a semantic search backend.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class LTMPlugin(ABC):
    """Abstract base class for LTM integrations."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for semantically relevant content.

        Args:
            query: Natural language search query
            limit: Maximum results to return

        Returns:
            List of dicts with at minimum: {"content": str, "score": float}
        """
        pass

    @abstractmethod
    def store(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store content for future semantic retrieval.

        Args:
            content: Text content to store
            metadata: Optional metadata (type, context, timestamp, etc.)

        Returns:
            True if stored successfully
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check if the LTM backend is operational.

        Returns:
            Dict with at minimum: {"healthy": bool, "message": str}
        """
        pass
