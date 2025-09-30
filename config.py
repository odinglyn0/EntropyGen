# config.py
import os

WEBSOCKET_ENDPOINTS = [
    "wss://stream.binance.com:9443/ws/btcusdt@trade",
    "wss://stream.binance.com:9443/ws/ethusdt@trade",
    "wss://stream.binance.com:443/stream?streams=btcusdt@trade/ethusdt@trade/bnbusdt@trade",
    "wss://stream.binance.com:9443/ws/btcusdt@depth",
    "wss://fstream.binance.com/ws/btcusdt@aggTrade",
    "wss://advanced-trade-ws.coinbase.com",
    "wss://ws.kraken.com/",
    "wss://ws.okx.com:8443/ws/v5/public",
    "wss://stream.bybit.com/v5/public/spot",
    "wss://ws.blockchain.info/inv",
    "wss://ws.blockchain.info/blocks",
    "wss://stream.binance.com:9443/ws/!ticker@arr",
    "wss://stream.binance.com:9443/ws/!miniTicker@arr",
    "wss://stream.binance.com:9443/ws/btcusdt@kline_1s",
    "wss://ws1.blitzortung.org",
    "wss://ws7.blitzortung.org",
    "wss://ws8.blitzortung.org",
    "wss://www.seismicportal.eu/standing_order/websocket",
    "wss://certstream.calidog.io/"
]

BLITZORTUNG_ENDPOINTS = [
    "wss://ws1.blitzortung.org",
    "wss://ws7.blitzortung.org",
    "wss://ws8.blitzortung.org",
]

BLITZORTUNG_INIT_MESSAGE = '{"a": 111}'

PEPPER_ROUNDS = [
    "PEPPER_ROUND_A", # Just make these jargon
    "PEPPER_ROUND_B",
    "PEPPER_ROUND_C",
    "PEPPER_ROUND_D",
    "PEPPER_ROUND_E",
    "PEPPER_ROUND_F",
    "PEPPER_ROUND_G",
    "PEPPER_ROUND_H",
    "PEPPER_ROUND_I",
    "PEPPER_ROUND_J",
]

MESSAGE_BATCH_SIZE = 10 # Leave

###
DEDUPLICATION_BUFFER_MAX_SIZE_GB = 2    # Ajust these 2 based on compute
DEDUPLICATION_MAX_ENTRIES = 50_000_000  # Ajust these 2 based on compute
###

MESSAGE_QUEUE_MAX_SIZE = 100_000_000
MESSAGE_PROCESSING_BATCH = 1000

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "EntropyGen-RAWHashes_Topic1")
KAFKA_SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME", "")  # If using Confluent this would be your API_KEY
KAFKA_SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD", "")  # If using Confluent this would be your API_KEY_SECRET
KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL") # Use PLAINTEXT if no auth
KAFKA_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN") # Use PLAIN for Confluent

KAFKA_BATCH_SIZE = 16384
KAFKA_LINGER_MS = 0 # Drop to 0 or push to 100 based on workload
KAFKA_COMPRESSION_TYPE = "snappy" # Use snappy if CPU is suboptimal
KAFKA_MAX_IN_FLIGHT_REQUESTS = 1000
KAFKA_BUFFER_MEMORY = 67108864
KAFKA_MAX_BLOCK_MS = 10000

RECONNECT_DELAY_SECONDS = 5
MAX_RECONNECT_ATTEMPTS = None

MEMORY_CHECK_INTERVAL_SECONDS = 60
MEMORY_THRESHOLD_PERCENT = 85
MEMORY_CRITICAL_PERCENT = 95

STATS_LOG_INTERVAL_MESSAGES = 1000

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MAX_BYTES = 100 * 1024 * 1024
LOG_BACKUP_COUNT = 5
