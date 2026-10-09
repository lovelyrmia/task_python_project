from __future__ import annotations

from log import logging
import uuid

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Callable
from user import UserManager

logger = logging.getLogger("[TASK-EXECUTOR]")

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class Task:
    user: str
    time: str
    action: str
    target: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING

    def is_due(self, now: datetime | None = None) -> bool:
        """Check whether this task is scheduled for the current minute."""
        now = now or datetime.now()
        return self.time == now.strftime("%H:%M")


class TaskExecutor:
    def __init__(
        self,
        user_manager: UserManager,
        actions: dict[str, Callable[[str], None]] | None = None,
    ):
        self.user_manager = user_manager
        self.actions = actions or {}
        self._task_lock = Lock()

    def execute(self, task: Task) -> None:
        with self._task_lock:
            if task.status != TaskStatus.PENDING:
                logger.warning(
                    "Task skipped id=%s status=%s",
                    task.id,
                    task.status.value,
                )
                return
            task.status = TaskStatus.RUNNING

        logger.info(
            "Execution requested task_id=%s user=%s "
            "action=%s target=%s",
            task.id,
            task.user,
            task.action,
            task.target,
        )

        if not self.user_manager.reserve_quota(task.user):
            task.status = TaskStatus.REJECTED
            logger.warning(
                "Task rejected task_id=%s user=%s",
                task.id,
                task.user,
            )
            return

        try:
            action_handler = self.actions.get(task.action)

            if action_handler is None:
                raise ValueError(
                    f"Unsupported action: {task.action}"
                )

            # Run the registered action.
            action_handler(task.target)

            self.user_manager.complete_quota(task.user)
            task.status = TaskStatus.SUCCESS

            logger.info(
                "Task completed task_id=%s user=%s "
                "action=%s target=%s",
                task.id,
                task.user,
                task.action,
                task.target,
            )

        except Exception:
            # Count a started attempt against quota, even if it fails.
            self.user_manager.complete_quota(task.user)
            task.status = TaskStatus.FAILED

            logger.exception(
                "Task failed task_id=%s user=%s "
                "action=%s target=%s",
                task.id,
                task.user,
                task.action,
                task.target,
            )

