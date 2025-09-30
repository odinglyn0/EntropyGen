# websocket_manager.py
import asyncio
import logging
import base64
from typing import Dict, Optional, Callable
import websockets
from websockets.exceptions import WebSocketException
import config

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, message_callback: Callable):
        self.endpoints = config.WEBSOCKET_ENDPOINTS
        self.connections: Dict[str, Optional[websockets.WebSocketClientProtocol]] = {}
        self.tasks: Dict[str, Optional[asyncio.Task]] = {}
        self.message_callback = message_callback
        self.running = False
        self.message_queues: Dict[str, asyncio.Queue] = {}

    async def start(self):
        self.running = True
        for endpoint_config in self.endpoints:
            url, *_ = endpoint_config.split(';===;', 1)
            self.message_queues[url] = asyncio.Queue(maxsize=config.MESSAGE_QUEUE_MAX_SIZE)
            self.tasks[url] = asyncio.create_task(self._maintain_connection(endpoint_config))
        logger.info("Started socket connections", extra={"count": len(self.endpoints)})

    async def stop(self):
        self.running = False
        for endpoint, task in self.tasks.items():
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        for endpoint, conn in self.connections.items():
            if conn and not conn.closed:
                await conn.close()
        
        for queue in self.message_queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        logger.info("Stopped all socket connections")

    async def _maintain_connection(self, endpoint_config: str):
        attempt = 0
        
        url, *init_msg_parts = endpoint_config.split(';===;', 1)
        init_msg = None
        if init_msg_parts:
            try:
                init_msg = base64.b64decode(init_msg_parts[0]).decode('utf-8')
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                logger.error("Failed to decode init message", extra={"url": url, "error": str(e)})

        while self.running:
            try:
                attempt += 1
                logger.info("Connecting to endpoint", extra={"url": url, "attempt": attempt})
                
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,
                    max_queue=32
                ) as websocket:
                    self.connections[url] = websocket
                    attempt = 0
                    
                    if url in config.BLITZORTUNG_ENDPOINTS:
                        await websocket.send(config.BLITZORTUNG_INIT_MESSAGE)
                        logger.info("Sent Blitzortung init message", extra={"url": url})

                    if init_msg:
                        await websocket.send(init_msg)
                        logger.info("Sent init message", extra={"url": url})

                    logger.info("Connected to endpoint", extra={"url": url})
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            if self.message_queues[url].full():
                                logger.warning("MQ full, dropping message", extra={"endpoint": url})
                                try:
                                    self.message_queues[url].get_nowait()
                                except asyncio.QueueEmpty:
                                    pass
                            
                            await asyncio.wait_for(
                                self.message_callback(url, message),
                                timeout=5.0
                            )
                        except asyncio.TimeoutError:
                            logger.error("Message processing timeout", extra={"endpoint": url})
                        except Exception as e:
                            logger.error("Err processing message", extra={"endpoint": url, "error": str(e)}, exc_info=True)
                            
            except asyncio.CancelledError:
                logger.info("Connection task cancelled", extra={"url": url})
                break
            except WebSocketException as e:
                logger.error("WebSocket error", extra={"url": url, "error": str(e)})
                self.connections[url] = None
            except Exception as e:
                logger.error("Unexpected error", extra={"url": url, "error": str(e)}, exc_info=True)
                self.connections[url] = None
            
            if self.running:
                if config.MAX_RECONNECT_ATTEMPTS and attempt >= config.MAX_RECONNECT_ATTEMPTS:
                    logger.error("Max reconnection attempts reached", extra={"url": url})
                    break
                logger.info("Reconnecting", extra={"url": url, "delay": config.RECONNECT_DELAY_SECONDS})
                await asyncio.sleep(config.RECONNECT_DELAY_SECONDS)

    def get_connection_status(self) -> Dict[str, bool]:
        return {
            endpoint: conn is not None and not conn.closed
            for endpoint, conn in self.connections.items()
        }

    def get_queue_sizes(self) -> Dict[str, int]:
        return {
            endpoint: queue.qsize()
            for endpoint, queue in self.message_queues.items()
        }
