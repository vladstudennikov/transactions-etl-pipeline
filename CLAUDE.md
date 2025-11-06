# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a banking transaction processing system with three main components:
- **bank_db**: MySQL database schema and seed data for banking parties
- **transaction_generator**: Component for generating synthetic transaction data
- **transaction_processor**: Component for processing and analyzing transactions
- **data_warehouse_creator**: Component for creating data warehouse structures

The system tracks banking parties (clients/companies) with IBANs across multiple European countries and processes their transactions for analysis and alerting.

## Database Architecture

### Core Models (bank_db/app/models.py)

- **Party**: Represents banking clients/entities with:
  - IBAN-based identification (unique constraint)
  - Country/currency (derived from IBAN country code)
  - Risk scoring and account status tracking
  - Transaction statistics (num_transactions, last_tx_date, annual_turnover)
  - Contact information and corporate vs individual classification

- **Alert**: Stores transaction anomaly alerts with:
  - JSON fields for transaction and client summaries
  - Freeform reason text
  - Created timestamp

### Database Connection

- Database URL configurable via `DATABASE_URL` environment variable
- Default: `mysql+mysqldb://root:root@localhost:3306/bankdb`
- Connection configured in `bank_db/app/db.py` with SQLAlchemy 1.4
- Uses `future=True` for forward compatibility with SQLAlchemy 2.0 patterns

## Common Commands

### Database Setup and Management

```bash
# Start MySQL database with Docker
cd bank_db
docker-compose up -d

# Install Python dependencies
cd bank_db
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
cd bank_db
alembic upgrade head

# Seed database with sample parties
cd bank_db
python seed.py

# Create new migration after model changes
cd bank_db
alembic revision --autogenerate -m "description of changes"

# Downgrade database by one revision
cd bank_db
alembic downgrade -1
```

### Docker Database Configuration

The MySQL container is configured in `bank_db/docker-compose.yaml`:
- Database: `bankdb`
- Root password: `root`
- App user: `appuser` / `apppass`
- Port: 3306 (mapped to host)
- Restart policy: `no` (manual start required)

## Key Data Flows

### Party Seeding Logic (bank_db/seed.py)

1. Reads hardcoded PARTIES_RAW list of (name, IBAN) tuples
2. Extracts country code from IBAN prefix (first 2 chars)
3. Maps country to currency (EUR for most eurozone, GBP/CHF/SEK/etc for others)
4. Generates synthetic metadata with Faker:
   - Account status (active/suspended/closed)
   - Risk score (0-100)
   - Annual turnover (10k-50M)
   - Transaction counts and dates
   - Contact info and addresses
5. Determines corporate vs individual based on name patterns
6. Handles duplicate IBANs gracefully with IntegrityError rollback

### Migration Management

Alembic is configured with:
- Script location: `migrations/` directory
- Target metadata: `app.models.Base.metadata`
- Current migration: `c45cf3521e8d_create_base_tables.py`
- Database URL in `alembic.ini` must match connection string

## Development Notes

### When adding new database models:
1. Update `bank_db/app/models.py` with new model class inheriting from `Base`
2. Run `alembic revision --autogenerate -m "add model_name"`
3. Review generated migration in `migrations/versions/`
4. Apply with `alembic upgrade head`

### When modifying Party or Alert models:
- Party IBAN field has unique constraint - ensure data migration preserves uniqueness
- Alert JSON fields store unstructured data - no schema validation at DB level
- Timestamps use `server_default=func.now()` - migrations may need `server_default` adjustments

### Reference Data
- Sample party data available in `data/parties.txt` (CSV format: name,IBAN)
- Seed script uses deterministic Faker seed (12345) for reproducibility

## ETL Pipeline Architecture

The system implements a complete ETL pipeline: **Transaction Generator → Kafka → Transaction Processor → ClickHouse DW**

### Transaction Generator (transaction_generator/)

Generates synthetic ISO 20022 pain.001.001.03 XML transactions and publishes to Kafka.

**Key features:**
- Reads parties from `data/parties.txt`
- Generates realistic transactions with random debtor/creditor pairs
- Publishes to Kafka topic `unprocessed`
- Configurable generation interval and max transactions via env vars

**Run command:**
```bash
cd transaction_generator
pip install -r requirements.txt
python generator.py
```

### Transaction Processor (transaction_processor/)

Consumes XML transactions from Kafka and loads to ClickHouse data warehouse.

**Key features:**
- Kafka consumer with configurable group ID
- Parses ISO 20022 XML format with namespace handling
- Loads to ClickHouse `transactions` fact table
- Updates `dim_parties` dimension table for both debtor and creditor
- Handles errors gracefully with separate success/failure counters

**Run command:**
```bash
cd transaction_processor
pip install -r requirements.txt
python processor.py
```

### Data Warehouse Schema (data_warehouse_creator/init-db.sql)

ClickHouse schema with:
- **transactions**: Fact table partitioned by month, ordered by timestamp
- **dim_parties**: ReplacingMergeTree dimension tracking party statistics
- **daily_transaction_summary**: Materialized view with SummingMergeTree
- **high_value_transactions**: Materialized view for amounts > 10,000

### Infrastructure (docker-compose.yaml)

Single compose file runs entire infrastructure:
- **Zookeeper**: Kafka coordination (port 2181)
- **Kafka**: Message broker (port 9092)
- **ClickHouse**: Data warehouse (HTTP 8123, Native 9000)

**Start all services:**
```bash
docker-compose up -d
```

## Common Commands - ETL Pipeline

### Start Full Pipeline

```bash
# Terminal 1: Start infrastructure
docker-compose up -d

# Terminal 2: Start generator
cd transaction_generator && python generator.py

# Terminal 3: Start processor
cd transaction_processor && python processor.py
```

### Query Data Warehouse

```bash
# Access ClickHouse client
docker exec -it clickhouse clickhouse-client

# Example queries
USE bank_dw;
SELECT count(*) FROM transactions;
SELECT * FROM daily_transaction_summary;
SELECT * FROM high_value_transactions LIMIT 10;
```

### Monitor Kafka

```bash
# List topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume messages
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic unprocessed --from-beginning
```

## Data Flow Details

### ISO 20022 XML Structure

Transactions follow pain.001.001.03 format with namespace `urn:iso:std:iso:20022:tech:xsd:pain.001.001.03`:

```
Document → CstmrCdtTrfInitn
  ├── GrpHdr (message metadata)
  └── PmtInf (payment information)
      ├── Dbtr/DbtrAcct (debtor IBAN)
      └── CdtTrfTxInf (transaction details)
          ├── Amt/InstdAmt (amount + currency)
          └── Cdtr/CdtrAcct (creditor IBAN)
```

### Processing Flow

1. **Generator** creates XML with random parties from `data/parties.txt`
2. **Kafka** buffers messages in `unprocessed` topic
3. **Processor** consumes messages, extracts data via ElementTree with namespace
4. **ClickHouse** stores in partitioned fact table and updates dimensions
5. **Materialized views** auto-populate for analytics

### Environment Variables

**Generator (transaction_generator/generator.py):**
- `KAFKA_BOOTSTRAP_SERVERS` (default: localhost:9092)
- `KAFKA_TOPIC` (default: unprocessed)
- `GENERATION_INTERVAL` (default: 2 seconds)
- `MAX_TRANSACTIONS` (default: 0 = unlimited)

**Processor (transaction_processor/processor.py):**
- `KAFKA_BOOTSTRAP_SERVERS` (default: localhost:9092)
- `KAFKA_TOPIC` (default: unprocessed)
- `KAFKA_GROUP_ID` (default: transaction-processor)
- `CLICKHOUSE_HOST` (default: localhost)
- `CLICKHOUSE_PORT` (default: 8123)
- `CLICKHOUSE_USER` (default: default)
- `CLICKHOUSE_PASSWORD` (default: empty)
