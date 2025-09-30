# entropy_processor.py
import hashlib
import random
import logging
from typing import List, Optional
from datetime import datetime
from collections import deque
import config

logger = logging.getLogger(__name__)

class EntropyProcessor:
    def __init__(self):
        self.message_buffer: deque = deque(maxlen=config.MESSAGE_BATCH_SIZE * 2)
        self.pepper_rounds = config.PEPPER_ROUNDS
        self.processed_count = 0

    def add_message(self, message: str) -> Optional[str]:
        try:
            if len(message) > 1024 * 1024:
                logger.warning("Too large, truncating", extra={"size": len(message)})
                message = message[:1024 * 1024]
            
            message_bytes = message.encode('utf-8', errors='ignore')
            self.message_buffer.append(message_bytes)
            
            if len(self.message_buffer) >= config.MESSAGE_BATCH_SIZE:
                batch = [self.message_buffer.popleft() for _ in range(min(config.MESSAGE_BATCH_SIZE, len(self.message_buffer)))]
                result = self._process_batch(batch)
                return result
            
            return None
        except Exception as e:
            logger.error("Err pushing", extra={"error": str(e)}, exc_info=True)
            return None

    def _process_batch(self, batch: List[bytes]) -> str:
        try:
            combined_data = b''.join(batch)
            
            seed_value = int(hashlib.sha256(combined_data).hexdigest()[:16], 16)
            rng = random.Random(seed_value)
            
            pepper_order = list(range(len(self.pepper_rounds)))
            rng.shuffle(pepper_order)
            
            current_hash = hashlib.sha512(combined_data).digest()
            
            for round_idx in pepper_order:
                pepper = self.pepper_rounds[round_idx].encode('utf-8')
                current_hash = hashlib.sha512(current_hash + pepper).digest()
            
            now = datetime.utcnow()
            timestamp_string = (
                f"{now.year}{now.month:02d}{now.day:02d}"
                f"{now.hour:02d}{now.minute:02d}{now.second:02d}"
                f"{now.microsecond:06d}"
            ).encode('utf-8')
            
            final_hash = hashlib.sha512(current_hash + timestamp_string).hexdigest()
            
            self.processed_count += 1
            logger.debug("Batch complete", extra={"batch_number": self.processed_count, "batch_size": len(batch)})
            
            return final_hash
        except Exception as e:
            logger.error("Err processing batch", extra={"error": str(e)}, exc_info=True)
            raise

    def get_buffer_size(self) -> int:
        return len(self.message_buffer)

    def clear_buffer(self):
        self.message_buffer.clear()
