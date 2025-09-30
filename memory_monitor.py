# memory_monitor.py
import psutil
import logging
import gc
import config

logger = logging.getLogger(__name__)

class MemoryMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.threshold_percent = config.MEMORY_THRESHOLD_PERCENT
        self.critical_percent = config.MEMORY_CRITICAL_PERCENT

    def check_memory(self) -> dict:
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        stats = {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "percent": memory_percent,
            "status": "normal"
        }
        
        if memory_percent >= self.critical_percent:
            stats["status"] = "critical"
            logger.critical("Mem use critical", extra={"percent": f"{memory_percent:.2f}"})
            gc.collect()
        elif memory_percent >= self.threshold_percent:
            stats["status"] = "warning"
            logger.warning("Mem use high", extra={"percent": f"{memory_percent:.2f}"})
            gc.collect()
        
        return stats

    def force_gc(self):
        collected = gc.collect()
        logger.info("Forced garbage collection", extra={"collected_objects": collected})
        return collected
