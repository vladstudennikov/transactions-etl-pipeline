#!/bin/bash
# Quick Start Script for Bank Transaction ETL Pipeline

set -e  # Exit on error

echo "=========================================="
echo "Bank Transaction ETL Pipeline Quick Start"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}✗ Docker is required but not installed.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}✗ Docker Compose is required but not installed.${NC}" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}✗ Python 3 is required but not installed.${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ All prerequisites found${NC}"
echo ""

# Step 2: Start infrastructure
echo -e "${YELLOW}Step 2: Starting infrastructure (Kafka, Zookeeper, ClickHouse)...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Infrastructure started${NC}"
echo ""

# Step 3: Wait for services to be ready
echo -e "${YELLOW}Step 3: Waiting for services to be ready (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✓ Services should be ready${NC}"
echo ""

# Step 4: Install generator dependencies
echo -e "${YELLOW}Step 4: Installing transaction generator dependencies...${NC}"
cd transaction_generator
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
cd ..
echo -e "${GREEN}✓ Generator dependencies installed${NC}"
echo ""

# Step 5: Install processor dependencies
echo -e "${YELLOW}Step 5: Installing transaction processor dependencies...${NC}"
cd transaction_processor
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
cd ..
echo -e "${GREEN}✓ Processor dependencies installed${NC}"
echo ""

# Step 6: Verify ClickHouse schema
echo -e "${YELLOW}Step 6: Verifying ClickHouse schema...${NC}"
sleep 5
docker exec clickhouse clickhouse-client --query "SHOW DATABASES" | grep -q "bank_dw" && \
    echo -e "${GREEN}✓ Database 'bank_dw' exists${NC}" || \
    echo -e "${RED}✗ Database 'bank_dw' not found. Check init-db.sql${NC}"
echo ""

# Instructions for running
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "To start the pipeline, open 2 separate terminals:"
echo ""
echo -e "${YELLOW}Terminal 1 - Transaction Generator:${NC}"
echo "  cd transaction_generator"
echo "  source venv/bin/activate"
echo "  python generator.py"
echo ""
echo -e "${YELLOW}Terminal 2 - Transaction Processor:${NC}"
echo "  cd transaction_processor"
echo "  source venv/bin/activate"
echo "  python processor.py"
echo ""
echo -e "${YELLOW}To test the pipeline:${NC}"
echo "  docker exec -it clickhouse clickhouse-client"
echo "  Then run: USE bank_dw; SELECT count(*) FROM transactions;"
echo ""
echo -e "${YELLOW}To stop everything:${NC}"
echo "  Press Ctrl+C in both terminals"
echo "  docker-compose down"
echo ""
