@echo off
REM Quick Start Script for Bank Transaction ETL Pipeline (Windows)

echo ==========================================
echo Bank Transaction ETL Pipeline Quick Start
echo ==========================================
echo.

REM Step 1: Check prerequisites
echo Step 1: Checking prerequisites...
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Docker is required but not installed.
    exit /b 1
)
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Docker Compose is required but not installed.
    exit /b 1
)
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Python is required but not installed.
    exit /b 1
)
echo √ All prerequisites found
echo.

REM Step 2: Start infrastructure
echo Step 2: Starting infrastructure (Kafka, Zookeeper, ClickHouse)...
docker-compose up -d
echo √ Infrastructure started
echo.

REM Step 3: Wait for services
echo Step 3: Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak >nul
echo √ Services should be ready
echo.

REM Step 4: Install generator dependencies
echo Step 4: Installing transaction generator dependencies...
cd transaction_generator
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
cd ..
echo √ Generator dependencies installed
echo.

REM Step 5: Install processor dependencies
echo Step 5: Installing transaction processor dependencies...
cd transaction_processor
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
cd ..
echo √ Processor dependencies installed
echo.

REM Step 6: Verify ClickHouse
echo Step 6: Verifying ClickHouse is running...
timeout /t 5 /nobreak >nul
docker exec clickhouse clickhouse-client --query "SHOW DATABASES"
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo To start the pipeline, open 2 separate command prompts:
echo.
echo Terminal 1 - Transaction Generator:
echo   cd transaction_generator
echo   venv\Scripts\activate.bat
echo   python generator.py
echo.
echo Terminal 2 - Transaction Processor:
echo   cd transaction_processor
echo   venv\Scripts\activate.bat
echo   python processor.py
echo.
echo To test the pipeline:
echo   docker exec -it clickhouse clickhouse-client
echo   Then run: USE bank_dw; SELECT count(*) FROM transactions;
echo.
echo To stop everything:
echo   Press Ctrl+C in both terminals
echo   docker-compose down
echo.
pause
