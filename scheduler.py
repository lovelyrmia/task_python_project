from __future__ import annotations

from log import logging
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock
from task import Task, TaskExecutor, TaskStatus


logger = logging.getLogger("[SCHEDULER]")

class Scheduler:
    def __init__(
        self,
        executor: TaskExecutor,
        max_workers: int = 5,
    ):
        self.executor = executor
        self.max_workers = max_workers
        self.tasks: list[Task] = []
        self._lock = Lock()

    def add_task(self, task: Task) -> None:
        with self._lock:
            self.tasks.append(task)

        logger.info(
            "Task scheduled task_id=%s user=%s time=%s "
            "action=%s target=%s",
            task.id,
            task.user,
            task.time,
            task.action,
            task.target,
        )

    def run_due_tasks(
        self,
        now: datetime | None = None,
    ) -> None:
        """Run all pending tasks due at the current minute."""
        now = now or datetime.now()

        with self._lock:
            due_tasks = [
                task
                for task in self.tasks
                if task.status == TaskStatus.PENDING
                and task.is_due(now)
            ]

        if not due_tasks:
            logger.debug("No tasks due at %s", now.strftime("%H:%M"))
            return

        logger.info(
            "Dispatching %d task(s) at %s",
            len(due_tasks),
            now.strftime("%H:%M"),
        )

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as pool:
            futures = [
                pool.submit(self.executor.execute, task)
                for task in due_tasks
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    logger.exception("Unexpected executor error")

    def start(self, interval: float = 1.0) -> None:
        """Continuously check for due tasks until interrupted."""
        logger.info("Scheduler started")

        try:
            while True:
                self.run_due_tasks()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped")

