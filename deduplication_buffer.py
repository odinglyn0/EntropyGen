# deduplication_buffer.py
import logging
from collections import OrderedDict
import config

logger = logging.getLogger(__name__)

class DeduplicationBuffer:
    def __init__(self, max_size_gb: int = 10):
        self.max_entries = config.DEDUPLICATION_MAX_ENTRIES
        self.buffer: OrderedDict[str, None] = OrderedDict()
        self.eviction_count = 0
        self.duplicate_count = 0

    def add(self, message_hash: str) -> bool:
        if message_hash in self.buffer:
            self.duplicate_count += 1
            self.buffer.move_to_end(message_hash)
            return False
        
        if len(self.buffer) >= self.max_entries:
            evicted_count = max(1, self.max_entries // 10)
            for _ in range(evicted_count):
                if self.buffer:
                    self.buffer.popitem(last=False)
                    self.eviction_count += 1
        
        self.buffer[message_hash] = None
        return True

    def contains(self, message_hash: str) -> bool:
        return message_hash in self.buffer

    def get_stats(self) -> dict:
        entry_count = len(self.buffer)
        estimated_bytes = entry_count * 100
        
        return {
            "entries": entry_count,
            "max_entries": self.max_entries,
            "fill_percent": (entry_count / self.max_entries * 100) if self.max_entries > 0 else 0,
            "evictions": self.eviction_count,
            "duplicates": self.duplicate_count,
            "estimated_mb": estimated_bytes / (1024 * 1024),
        }

    def clear(self):
        self.buffer.clear()
        logger.info("Deduplication buffer cleared", extra={})
