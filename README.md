# EntropyGen

**A real-time, Kafka based Python system for collecting unpredictable real-time data from unpredictable sources and generating cryptographically secure entropy hashes for Kafka.**

## Why Not Just Use Random.org API?

**Random.org and quantum RNG services provide true randomness but are rate-limited and aren't designed for a high throughput, high bandwith level of entropy at scale, while this tool prioritizes throughput and diversity, aggregating multiple independent entropy sources simultaneously with hundreds of messages per second. Choose quantum RNGs for cryptographic key generation where provable randomness matters, choose this for high-volume entropy collection where speed and source diversity are critical.

## Features

* **18 concurrent WebSocket streams**: Lightning strikes, earthquakes, crypto markets, blockchain (pure, unpredictable, real-time data)
* **Memory-safe deduplication**: 50M (unless changed) entry cache with automatic eviction
* **Cryptographic hashing**: SHA-512 with configurable pepper rounds
* **High-throughput Kafka delivery**: Batching, compression, SASL_SSL authentication (unless changed)
* **Memory monitoring**: Automatic GC and buffer clearing at thresholds
* **Production logging**: Rotating file logs with stats tracking

## Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd entropy-stream-system
pip install -r requirements.txt
```

## Usage

**Environment Setup**

```bash
export KAFKA_BOOTSTRAP_SERVERS="kafka:9092"
export KAFKA_SASL_USERNAME="your-username"
export KAFKA_SASL_PASSWORD="your-password"
export KAFKA_TOPIC="entropy_stream"
```

**Run**

```bash
python main.py
```

**Configure**

Edit `config.py` to customize pepper rounds, batch sizes, memory limits, and Kafka settings.

## Output Format

Each Kafka message is a 128-character SHA-512 hash combining 10 deduplicated messages, 10 pepper rounds (mixed in data-seeded random order), and microsecond-precision timestamp.

Example: `a3f5c8d9e2b1f4a6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0...`

## License

MIT