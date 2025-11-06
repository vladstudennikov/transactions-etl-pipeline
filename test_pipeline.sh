#!/bin/bash
# Test script to verify the ETL pipeline is working

echo "=========================================="
echo "Testing Bank Transaction ETL Pipeline"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Test 1: Check if Docker containers are running
echo -e "${YELLOW}Test 1: Checking Docker containers...${NC}"
CONTAINERS=$(docker-compose ps -q | wc -l)
if [ "$CONTAINERS" -ge 3 ]; then
    echo -e "${GREEN}✓ All containers are running${NC}"
else
    echo -e "${RED}✗ Some containers are not running. Run: docker-compose up -d${NC}"
    exit 1
fi
echo ""

# Test 2: Check Kafka connectivity
echo -e "${YELLOW}Test 2: Checking Kafka connectivity...${NC}"
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Kafka is accessible${NC}"
else
    echo -e "${RED}✗ Kafka is not accessible${NC}"
    exit 1
fi
echo ""

# Test 3: Check ClickHouse connectivity
echo -e "${YELLOW}Test 3: Checking ClickHouse connectivity...${NC}"
docker exec clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ClickHouse is accessible${NC}"
else
    echo -e "${RED}✗ ClickHouse is not accessible${NC}"
    exit 1
fi
echo ""

# Test 4: Check if bank_dw database exists
echo -e "${YELLOW}Test 4: Checking ClickHouse database...${NC}"
DB_EXISTS=$(docker exec clickhouse clickhouse-client --query "SHOW DATABASES" | grep -c "bank_dw")
if [ "$DB_EXISTS" -eq 1 ]; then
    echo -e "${GREEN}✓ Database 'bank_dw' exists${NC}"
else
    echo -e "${RED}✗ Database 'bank_dw' does not exist${NC}"
    exit 1
fi
echo ""

# Test 5: Check if tables exist
echo -e "${YELLOW}Test 5: Checking ClickHouse tables...${NC}"
TABLES=$(docker exec clickhouse clickhouse-client --query "USE bank_dw; SHOW TABLES" | wc -l)
if [ "$TABLES" -ge 4 ]; then
    echo -e "${GREEN}✓ All required tables exist${NC}"
    docker exec clickhouse clickhouse-client --query "USE bank_dw; SHOW TABLES"
else
    echo -e "${RED}✗ Some tables are missing${NC}"
    exit 1
fi
echo ""

# Test 6: Check if Kafka topic exists
echo -e "${YELLOW}Test 6: Checking Kafka topics...${NC}"
TOPIC_EXISTS=$(docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list | grep -c "unprocessed")
if [ "$TOPIC_EXISTS" -ge 1 ]; then
    echo -e "${GREEN}✓ Topic 'unprocessed' exists${NC}"
else
    echo -e "${YELLOW}! Topic 'unprocessed' will be auto-created on first message${NC}"
fi
echo ""

# Test 7: Check transaction count (if any)
echo -e "${YELLOW}Test 7: Checking transaction count...${NC}"
TX_COUNT=$(docker exec clickhouse clickhouse-client --query "USE bank_dw; SELECT count(*) FROM transactions")
echo -e "${GREEN}✓ Transactions in warehouse: $TX_COUNT${NC}"
echo ""

# Test 8: Show sample data (if any)
if [ "$TX_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Test 8: Sample transaction data:${NC}"
    docker exec clickhouse clickhouse-client --query "USE bank_dw; SELECT transaction_id, amount, currency, debtor_name, creditor_name FROM transactions LIMIT 5 FORMAT Pretty"
    echo ""
fi

echo "=========================================="
echo -e "${GREEN}All Tests Passed!${NC}"
echo "=========================================="
echo ""
echo "Pipeline Status:"
echo "  - Infrastructure: Running"
echo "  - ClickHouse Database: Ready"
echo "  - Kafka Broker: Ready"
echo "  - Transactions Processed: $TX_COUNT"
echo ""
echo "Next steps:"
echo "  1. Start generator: cd transaction_generator && python generator.py"
echo "  2. Start processor: cd transaction_processor && python processor.py"
echo "  3. Watch transactions: docker exec -it clickhouse clickhouse-client"
echo ""
