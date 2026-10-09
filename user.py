from __future__ import annotations
from log import logging
from dataclasses import dataclass
from threading import Lock
from typing import Callable


logger = logging.getLogger("[USER]")

@dataclass
class User:
    username: str
    quota: int
    executed: int = 0
    reserved: int = 0


class UserManager:
    def __init__(self):
        self._users: dict[str, User] = {}
        self._lock = Lock()

    def add_user(self, username: str, quota: int) -> None:
        if quota < 0:
            raise ValueError("Quota cannot be negative.")

        with self._lock:
            if username in self._users:
                raise ValueError(f"User already exists: {username}")

            self._users[username] = User(username, quota)

        logger.info("Registered user=%s quota=%d", username, quota)

    def get_user(self, username: str) -> User:
        with self._lock:
            if username not in self._users:
                raise KeyError(f"Unknown user: {username}")
            return self._users[username]

    def reserve_quota(self, username: str) -> bool:
        """
        Atomically reserve quota before execution.
        Concurrent tasks cannot exceed the user's quota.
        """
        with self._lock:
            user = self._users.get(username)

            if user is None:
                logger.warning("Unknown user rejected: %s", username)
                return False

            if user.executed + user.reserved >= user.quota:
                logger.warning(
                    "Quota exceeded user=%s executed=%d "
                    "reserved=%d quota=%d",
                    username,
                    user.executed,
                    user.reserved,
                    user.quota,
                )
                return False

            user.reserved += 1
            return True

    def complete_quota(self, username: str) -> None:
        """Commit a reserved quota after an execution attempt."""
        with self._lock:
            user = self._users[username]
            user.reserved -= 1
            user.executed += 1

    def release_quota(self, username: str) -> None:
        """Release a reservation if execution could not start."""
        with self._lock:
            self._users[username].reserved -= 1

