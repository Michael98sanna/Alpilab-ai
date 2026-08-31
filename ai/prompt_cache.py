"""In-memory prompt cache with TTL."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta


class PromptCache:
    """Simple in-memory prompt cache with TTL."""

    def __init__(self, ttl_sec: int = 3600) -> None:
        self.cache: dict[str, dict[str, datetime | str]] = {}
        self.ttl = timedelta(seconds=ttl_sec)

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()

    def get(self, prompt: str) -> str | None:
        """Return a cached response when still valid."""
        key = self._hash_prompt(prompt)
        entry = self.cache.get(key)
        if entry is None:
            return None

        timestamp = entry["timestamp"]
        assert isinstance(timestamp, datetime)
        if datetime.now(UTC) - timestamp < self.ttl:
            response = entry["response"]
            assert isinstance(response, str)
            return response

        del self.cache[key]
        return None

    def set(self, prompt: str, response: str) -> None:
        """Store a response in the cache."""
        key = self._hash_prompt(prompt)
        self.cache[key] = {
            "response": response,
            "timestamp": datetime.now(UTC),
        }

    def clear(self) -> None:
        """Remove all cached entries."""
        self.cache.clear()
