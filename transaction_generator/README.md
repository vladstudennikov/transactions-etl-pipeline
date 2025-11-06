# Transaction Generator

Generates ISO 20022 pain.001.001.03 format XML transactions and publishes them to Kafka.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python generator.py
```

### Configuration

Configure via environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `localhost:9092`)
- `KAFKA_TOPIC`: Target Kafka topic (default: `unprocessed`)
- `GENERATION_INTERVAL`: Seconds between transactions (default: `2`)
- `MAX_TRANSACTIONS`: Max transactions to generate, 0=infinite (default: `0`)

### Examples

Generate transactions every 5 seconds:
```bash
GENERATION_INTERVAL=5 python generator.py
```

Generate only 100 transactions:
```bash
MAX_TRANSACTIONS=100 python generator.py
```

Connect to remote Kafka:
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka-server:9092 python generator.py
```

## Transaction Format

Generates ISO 20022 `pain.001.001.03` (Customer Credit Transfer Initiation) with:
- Random debtor/creditor from `data/parties.txt`
- Random amounts between 10.00 and 50,000.00
- Multiple currencies (EUR, USD, GBP, CHF, etc.)
- Unique message IDs and end-to-end IDs
- Timestamps within last 24 hours

## Requirements

- Python 3.7+
- Running Kafka broker
- `data/parties.txt` file with party data
