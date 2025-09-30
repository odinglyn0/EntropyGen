# main.py
import asyncio
import logging
import signal
import sys
import hashlib
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from websocket_manager import WebSocketManager
from entropy_processor import EntropyProcessor
from deduplication_buffer import DeduplicationBuffer
from kafka_producer import KafkaEntropyProducer
from memory_monitor import MemoryMonitor
import config

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        'entropy_system.log',
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

class EntropySystem:
    def __init__(self):
        self.entropy_processor = EntropyProcessor()
        self.dedup_buffer = DeduplicationBuffer(config.DEDUPLICATION_BUFFER_MAX_SIZE_GB)
        self.kafka_producer = KafkaEntropyProducer()
        self.websocket_manager = WebSocketManager(self._handle_message)
        self.memory_monitor = MemoryMonitor()
        self.shutdown_event = asyncio.Event()
        self.message_count = 0
        self.processing_semaphore = asyncio.Semaphore(config.MESSAGE_PROCESSING_BATCH)
        self.memory_check_task = None

    async def _handle_message(self, endpoint: str, message: str):
        async with self.processing_semaphore:
            try:
                if len(message) == 0:
                    return
                
                message_hash = hashlib.sha256(message.encode('utf-8', errors='ignore')).hexdigest()
                
                if not self.dedup_buffer.add(message_hash):
                    logger.debug("Dupe, excl", extra={"endpoint": endpoint, "hash": message_hash})
                    return
                
                self.message_count += 1
                
                entropy_hash = self.entropy_processor.add_message(message)
                
                if entropy_hash:
                    success = self.kafka_producer.send(entropy_hash)
                    if success:
                        logger.info("Generated and sent entropy hash", extra={"hash_prefix": f"{entropy_hash[:16]}..."})
                    else:
                        logger.error("Failed to send entropy hash to Kafka", extra={"hash": entropy_hash})
                
                if self.message_count % config.STATS_LOG_INTERVAL_MESSAGES == 0:
                    await self._log_stats()
                    
            except Exception as e:
                logger.error("Err handling message", extra={"endpoint": endpoint, "error": str(e)}, exc_info=True)

    async def _log_stats(self):
        try:
            dedup_stats = self.dedup_buffer.get_stats()
            kafka_stats = self.kafka_producer.get_stats()
            status = self.websocket_manager.get_connection_status()
            queue_sizes = self.websocket_manager.get_queue_sizes()
            memory_stats = self.memory_monitor.check_memory()
            
            active_connections = sum(1 for v in status.values() if v)
            total_queue_size = sum(queue_sizes.values())
            buffer_size = self.entropy_processor.get_buffer_size()
            
            logger.info("STATS", extra={
                "messages": self.message_count,
                "connections_active": active_connections,
                "connections_total": len(status),
                "dedup_entries": dedup_stats['entries'],
                "dedup_mb": f"{dedup_stats['estimated_mb']:.2f}",
                "dedup_fill_percent": f"{dedup_stats['fill_percent']:.1f}",
                "kafka_sent": kafka_stats['sent'],
                "kafka_success_rate": f"{kafka_stats['success_rate']:.1f}",
                "queue_size": total_queue_size,
                "buffer_size": buffer_size,
                "memory_rss_mb": f"{memory_stats['rss_mb']:.2f}",
                "memory_percent": f"{memory_stats['percent']:.2f}",
            })
            
            if memory_stats['status'] == 'critical':
                logger.critical("CRITICAL MEM USAGE - Forcing cleanup", extra=memory_stats)
                self.memory_monitor.force_gc()
                self.entropy_processor.clear_buffer()
                
        except Exception as e:
            logger.error("Err logging stats", extra={"error": str(e)}, exc_info=True)

    async def _memory_check_loop(self):
        while not self.shutdown_event.is_set():
            try:
                memory_stats = self.memory_monitor.check_memory()
                
                if memory_stats['status'] == 'critical':
                    self.memory_monitor.force_gc()
                    self.entropy_processor.clear_buffer()
                
                await asyncio.sleep(config.MEMORY_CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Err in mem check loop", extra={"error": str(e)}, exc_info=True)

    async def start(self):
        logger.info("Starting EntropyGen")
        logger.info("Monitoring sockets", extra={"count": len(config.WEBSOCKET_ENDPOINTS)})
        
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        
        self.memory_check_task = asyncio.create_task(self._memory_check_loop())
        
        await self.websocket_manager.start()
        
        await self.shutdown_event.wait()

    async def stop(self):
        logger.info("Shutting down EntropyGen")
        self.shutdown_event.set()
        
        if self.memory_check_task and not self.memory_check_task.done():
            self.memory_check_task.cancel()
            try:
                await self.memory_check_task
            except asyncio.CancelledError:
                pass
        
        await self.websocket_manager.stop()
        
        self.kafka_producer.flush(timeout=5.0)
        self.kafka_producer.close()
        
        await self._log_stats()
        
        logger.info("EntropyGen shutdown")

async def main():
    system = EntropySystem()
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Received SIGINT, condluding")
    except Exception as e:
        logger.critical("Fatal err", extra={"error": str(e)}, exc_info=True)
    finally:
        await system.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
