# kafka_producer.py
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from typing import Optional
import config

logger = logging.getLogger(__name__)

class KafkaEntropyProducer:
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self.send_count = 0
        self.error_count = 0
        self._initialize_producer()

    def _initialize_producer(self):
        try:
            kafka_config = {
                'bootstrap_servers': config.KAFKA_BOOTSTRAP_SERVERS,
                'security_protocol': config.KAFKA_SECURITY_PROTOCOL,
                'sasl_mechanism': config.KAFKA_SASL_MECHANISM,
                'sasl_plain_username': config.KAFKA_SASL_USERNAME,
                'sasl_plain_password': config.KAFKA_SASL_PASSWORD,
                'batch_size': config.KAFKA_BATCH_SIZE,
                'linger_ms': config.KAFKA_LINGER_MS,
                'compression_type': config.KAFKA_COMPRESSION_TYPE,
                'max_in_flight_requests_per_connection': config.KAFKA_MAX_IN_FLIGHT_REQUESTS,
                'buffer_memory': config.KAFKA_BUFFER_MEMORY,
                'max_block_ms': config.KAFKA_MAX_BLOCK_MS,
                'acks': 'all',
                'retries': 3,
                'value_serializer': lambda v: v.encode('utf-8'),
                'api_version': (2, 5, 0),
            }
            
            self.producer = KafkaProducer(**kafka_config)
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error("Producer init fail", extra={"error": str(e)}, exc_info=True)
            raise

    def send(self, entropy_hash: str) -> bool:
        if not self.producer:
            logger.error("MQ producer not init")
            return False
        
        try:
            future = self.producer.send(config.KAFKA_TOPIC, value=entropy_hash)
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            return True
        except KafkaTimeoutError:
            logger.error("MQ send timeout")
            self.error_count += 1
            return False
        except Exception as e:
            logger.error("Err sending to MQ", extra={"error": str(e)}, exc_info=True)
            self.error_count += 1
            return False

    def _on_send_success(self, record_metadata):
        self.send_count += 1
        logger.debug("Message sent", extra={
            "topic": record_metadata.topic,
            "partition": record_metadata.partition,
            "offset": record_metadata.offset,
        })

    def _on_send_error(self, exc):
        self.error_count += 1
        logger.error("Err sending message", extra={"error": str(exc)})

    def flush(self, timeout: Optional[float] = None):
        if self.producer:
            try:
                self.producer.flush(timeout=timeout)
            except Exception as e:
                logger.error("Err flushing producer", extra={"error": str(e)}, exc_info=True)

    def close(self):
        if self.producer:
            try:
                self.producer.close(timeout=10)
                logger.info("Producer closed")
            except Exception as e:
                logger.error("Err closing producer", extra={"error": str(e)}, exc_info=True)

    def get_stats(self) -> dict:
        return {
            "sent": self.send_count,
            "errors": self.error_count,
            "success_rate": (self.send_count / (self.send_count + self.error_count) * 100) 
                           if (self.send_count + self.error_count) > 0 else 0
        }
