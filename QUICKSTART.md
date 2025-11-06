# Quick Start Guide

Get the ETL pipeline running in **5 minutes**!

## Prerequisites

- Docker & Docker Compose installed
- Python 3.7+ installed
- 4GB RAM available for Docker

## Option 1: Automated Setup (Recommended)

### Windows:
```cmd
quick_start.bat
```

### Linux/Mac:
```bash
chmod +x quick_start.sh
./quick_start.sh
```

## Option 2: Manual Setup (Step by Step)

### 1. Start Infrastructure (30 seconds)

```bash
# Start Kafka, Zookeeper, and ClickHouse
docker-compose up -d

# Wait for services to initialize
# Windows: timeout /t 30
# Linux/Mac: sleep 30
```

**Verify services are running:**
```bash
docker-compose ps
```

You should see 3 containers: `zookeeper`, `kafka`, `clickhouse`

### 2. Setup Transaction Generator

```bash
cd transaction_generator

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Transaction Processor

Open a **new terminal**:

```bash
cd transaction_processor

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start the Pipeline

**Terminal 1 - Generator:**
```bash
cd transaction_generator
# (activate venv if not already active)
python generator.py
```

You should see:
```
Transaction Generator Starting
Kafka Servers: localhost:9092
Topic: unprocessed
✓ Connected to Kafka
[1] Sent transaction to unprocessed partition 0 offset 0
[2] Sent transaction to unprocessed partition 0 offset 1
```

**Terminal 2 - Processor:**
```bash
cd transaction_processor
# (activate venv if not already active)
python processor.py
```

You should see:
```
Transaction Processor Starting
✓ Connected to ClickHouse
✓ Connected to Kafka
Waiting for messages...
[1] ✓ Processed transaction from offset 0
[2] ✓ Processed transaction from offset 1
```

### 5. Verify Data in Warehouse

Open a **third terminal**:

```bash
# Access ClickHouse client
docker exec -it clickhouse clickhouse-client

# Run queries
USE bank_dw;

-- Check transaction count
SELECT count(*) FROM transactions;

-- View recent transactions
SELECT
    transaction_id,
    amount,
    currency,
    debtor_name,
    creditor_name,
    created_datetime
FROM transactions
ORDER BY created_datetime DESC
LIMIT 10;

-- Daily summary
SELECT * FROM daily_transaction_summary;

-- High value transactions
SELECT * FROM high_value_transactions ORDER BY amount DESC LIMIT 5;

-- Party statistics
SELECT
    party_name,
    total_transactions,
    total_sent,
    total_received
FROM dim_parties
ORDER BY total_transactions DESC
LIMIT 10;
```

## Testing the Pipeline

Run the automated test script:

**Linux/Mac:**
```bash
chmod +x test_pipeline.sh
./test_pipeline.sh
```

This will verify:
- ✓ Docker containers are running
- ✓ Kafka is accessible
- ✓ ClickHouse is accessible
- ✓ Database and tables exist
- ✓ Show transaction count

## Troubleshooting

### Problem: Kafka connection refused

**Solution:**
```bash
# Wait longer for Kafka to start
docker logs kafka

# Restart Kafka
docker-compose restart kafka
sleep 20
```

### Problem: ClickHouse database not found

**Solution:**
```bash
# Check if init-db.sql was loaded
docker logs clickhouse

# Manually create schema
docker exec -it clickhouse clickhouse-client < data_warehouse_creator/init-db.sql
```

### Problem: Generator can't find parties.txt

**Solution:**
```bash
# Make sure you're in transaction_generator directory
cd transaction_generator

# Verify file exists
ls ../data/parties.txt

# Or use absolute path in generator.py
```

### Problem: Port already in use (9092, 8123, etc.)

**Solution:**
```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :9092

# Linux/Mac:
lsof -i :9092

# Either stop that service or modify docker-compose.yaml to use different ports
```

## Configuration Tips

### Generate transactions faster:
```bash
GENERATION_INTERVAL=0.5 python generator.py
```

### Generate limited number of transactions:
```bash
MAX_TRANSACTIONS=100 python generator.py
```

### Use multiple processors for parallel processing:
```bash
# Terminal 2
KAFKA_GROUP_ID=processor-1 python processor.py

# Terminal 3
KAFKA_GROUP_ID=processor-1 python processor.py
```

## Monitoring Tips

### Watch Kafka messages in real-time:
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic unprocessed \
  --from-beginning
```

### Monitor ClickHouse in real-time:
```bash
# In clickhouse-client
USE bank_dw;
SELECT count(*) FROM transactions; -- Run this repeatedly
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f kafka
docker-compose logs -f clickhouse
```

## Stopping the Pipeline

1. **Stop generators/processors**: Press `Ctrl+C` in their terminals

2. **Stop infrastructure**:
   ```bash
   docker-compose down
   ```

3. **Clean up everything (including data)**:
   ```bash
   docker-compose down -v
   ```

## Next Steps

Once you've verified everything works:

1. **Experiment with configurations** (intervals, transaction amounts)
2. **Create custom ClickHouse queries** for analysis
3. **Add alerting logic** in the processor
4. **Scale up** with multiple processor instances
5. **Integrate with the bank_db** MySQL database for party validation

Happy testing! 🚀
