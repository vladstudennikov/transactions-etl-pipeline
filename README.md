# Bank Transaction Processing ETL Pipeline

A complete ETL pipeline for processing banking transactions using Kafka and ClickHouse data warehouse.

## Architecture

```
┌─────────────────────┐       ┌─────────┐       ┌──────────────────┐       ┌────────────┐
│ Transaction         │──────>│  Kafka  │──────>│ Transaction      │──────>│ ClickHouse │
│ Generator           │ XML   │ (topic: │ XML   │ Processor        │ SQL   │ Data       │
│                     │       │unprocess│       │                  │       │ Warehouse  │
└─────────────────────┘       └─────────┘       └──────────────────┘       └────────────┘
```

## Components

### 1. Transaction Generator (`transaction_generator/`)
- Generates ISO 20022 XML transactions
- Publishes to Kafka topic `unprocessed`
- Uses parties from `data/parties.txt`

### 2. Transaction Processor (`transaction_processor/`)
- Consumes XML from Kafka
- Parses and transforms data
- Loads to ClickHouse data warehouse

### 3. Data Warehouse (ClickHouse)
- Stores transaction fact table
- Maintains party dimension table
- Provides materialized views for analytics

### 4. Bank Database (`bank_db/`)
- MySQL database with party master data
- Alembic migrations for schema management
- Seed script for sample data

## Quick Start

### Automated Setup (Recommended)

**Windows:**
```cmd
quick_start.bat
```

**Linux/Mac:**
```bash
chmod +x quick_start.sh
./quick_start.sh
```

Then follow the on-screen instructions to start the generator and processor.

### Manual Setup

See **[QUICKSTART.md](QUICKSTART.md)** for detailed step-by-step instructions.

### Rapid Test

```bash
# 1. Start everything
docker-compose up -d && sleep 30

# 2. Terminal 1: Generate 50 transactions
cd transaction_generator && pip install -r requirements.txt
MAX_TRANSACTIONS=50 GENERATION_INTERVAL=1 python generator.py

# 3. Terminal 2: Process transactions
cd transaction_processor && pip install -r requirements.txt
python processor.py

# 4. Terminal 3: Verify results
docker exec -it clickhouse clickhouse-client
# Then: USE bank_dw; SELECT count(*) FROM transactions;
```

## Configuration

### Kafka
- **Bootstrap Servers**: `localhost:9092`
- **Topic**: `unprocessed`
- **Zookeeper**: `localhost:2181`

### ClickHouse
- **HTTP Port**: `localhost:8123`
- **Native Port**: `localhost:9000`
- **Database**: `bank_dw`
- **User**: `default`

## Data Format

Transactions use ISO 20022 `pain.001.001.03` format (Customer Credit Transfer Initiation):
- Debtor/creditor party information
- IBAN-based account identification
- Amount and currency
- Unique transaction IDs
- Timestamps

## Development

### Bank Database Setup

```bash
cd bank_db
docker-compose up -d
pip install -r requirements.txt
alembic upgrade head
python seed.py
```

### Environment Variables

**Generator:**
- `GENERATION_INTERVAL`: Seconds between transactions (default: 2)
- `MAX_TRANSACTIONS`: Max to generate (default: unlimited)

**Processor:**
- `KAFKA_GROUP_ID`: Consumer group (default: transaction-processor)
- `CLICKHOUSE_HOST`: ClickHouse host (default: localhost)

## Monitoring

### Kafka Topics
```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic unprocessed --from-beginning
```

### ClickHouse Queries
```sql
-- Transaction volume by date
SELECT toDate(created_datetime) AS date, count(*) AS count
FROM transactions
GROUP BY date
ORDER BY date DESC;

-- Top parties by transaction volume
SELECT party_name, total_sent + total_received AS total_volume
FROM dim_parties
ORDER BY total_volume DESC
LIMIT 10;

-- High value transactions
SELECT * FROM high_value_transactions ORDER BY amount DESC LIMIT 10;
```

## Stopping Services

```bash
# Stop generators/processors with Ctrl+C

# Stop infrastructure
docker-compose down

# Clean up volumes
docker-compose down -v
```

## Project Structure

```
bank_project/
├── bank_db/                    # MySQL party database
├── transaction_generator/      # Kafka producer
├── transaction_processor/      # Kafka consumer + DW loader
├── data_warehouse_creator/     # ClickHouse schema
├── data/                       # Reference data
├── docker-compose.yaml         # Infrastructure services
└── README.md                   # This file
```
