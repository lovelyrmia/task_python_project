from __future__ import annotations
from log import logging
from user import UserManager
from task import Task, TaskExecutor
from scheduler import Scheduler


def mock_action(target: str) -> None:
    logger = logging.getLogger("[MOCK-ACTION]")
    """Replace this demonstration handler with real operations."""
    logger.info("Performing demonstration action on %s", target)


def main():
    users = UserManager()
    users.add_user("alice", quota=3)
    users.add_user("bob", quota=5)

    actions = {
        "sync": mock_action,
        "backup": mock_action,
        "delete": mock_action,
    }

    executor = TaskExecutor(users, actions)
    scheduler = Scheduler(executor, max_workers=5)

    scheduler.add_task(
        Task("alice", "14:08", "sync", "/data/x")
    )
    scheduler.add_task(
        Task("bob", "14:09", "backup", "/srv/y")
    )
    scheduler.add_task(
        Task("alice", "14:10", "delete", "/tmp/z")
    )

    scheduler.start(interval=1.0)

if __name__ == "__main__":
    main()
