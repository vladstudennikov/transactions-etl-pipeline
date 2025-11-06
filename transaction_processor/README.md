# Transaction Processor

Consumes XML transactions from Kafka and loads them into ClickHouse data warehouse.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python processor.py
```

### Configuration

Configure via environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `localhost:9092`)
- `KAFKA_TOPIC`: Source Kafka topic (default: `unprocessed`)
- `KAFKA_GROUP_ID`: Consumer group ID (default: `transaction-processor`)
- `CLICKHOUSE_HOST`: ClickHouse host (default: `localhost`)
- `CLICKHOUSE_PORT`: ClickHouse HTTP port (default: `8123`)
- `CLICKHOUSE_USER`: ClickHouse user (default: `default`)
- `CLICKHOUSE_PASSWORD`: ClickHouse password (default: empty)

### Examples

Connect to remote services:
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka-server:9092 \
CLICKHOUSE_HOST=clickhouse-server \
CLICKHOUSE_PASSWORD=secret \
python processor.py
```

Use custom consumer group:
```bash
KAFKA_GROUP_ID=processor-instance-1 python processor.py
```

## Processing Flow

1. Consumes XML messages from Kafka topic
2. Parses ISO 20022 pain.001.001.03 format
3. Extracts transaction details
4. Loads to ClickHouse `transactions` table
5. Updates `dim_parties` dimension table
6. Auto-populates materialized views

## Data Warehouse Schema

### Tables
- `transactions`: Main fact table with all transaction details
- `dim_parties`: Dimension table tracking party statistics
- `daily_transaction_summary`: Daily aggregated metrics
- `high_value_transactions`: Transactions over 10,000

## Requirements

- Python 3.7+
- Running Kafka broker with messages
- Running ClickHouse instance with initialized schema
