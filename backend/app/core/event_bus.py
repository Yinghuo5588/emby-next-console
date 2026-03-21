"""
事件总线 - 解耦 Webhook 接收与下游处理
"""
import logging
import threading
from collections import defaultdict

logger = logging.getLogger("app.event_bus")


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler):
        """订阅事件"""
        with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, *args, **kwargs):
        """发布事件 - 异步分发，不阻塞发布者"""
        with self._lock:
            handlers = self._subscribers[event_type][:]

        for handler in handlers:
            try:
                threading.Thread(target=handler, args=args, kwargs=kwargs, daemon=True).start()
            except Exception as e:
                logger.error(f"Event dispatch error [{event_type}]: {e}")


# 全局单例
bus = EventBus()
