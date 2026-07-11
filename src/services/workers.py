"""Background worker pool for heavy operations."""
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from functools import wraps
from typing import Any, Callable, Coroutine

_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="sentinel-worker",
)


class BackgroundTask:
    def __init__(self, name: str) -> None:
        self.name = name
        self.start_time: float = 0.0
        self.future: Future | None = None

    def done(self) -> bool:
        return self.future is not None and self.future.done()

    def result(self) -> Any:
        return self.future.result() if self.future else None


def run_in_background(fn: Callable[..., Any]) -> Callable[..., BackgroundTask]:
    """Decorator: runs a sync function in a thread pool."""
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> BackgroundTask:
        task = BackgroundTask(fn.__name__)
        task.start_time = time.time()
        task.future = _executor.submit(fn, *args, **kwargs)
        return task
    return wrapper


_async_tasks: dict[str, asyncio.Task[Any]] = {}


def run_async_in_background(name: str, coro: Coroutine[Any, Any, Any]) -> None:
    """Run an async coroutine in the event loop's background."""
    loop = asyncio.get_event_loop()
    task = loop.create_task(coro)
    _async_tasks[name] = task
    task.add_done_callback(lambda _: _async_tasks.pop(name, None))


def get_task_status(name: str) -> str | None:
    if name in _async_tasks:
        t = _async_tasks[name]
        if t.done():
            return "completed" if not t.cancelled() else "cancelled"
        return "running"
    return None
