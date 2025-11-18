@echo off
echo ========================================
echo ReACT Agent Setup
echo ========================================
echo.

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Pull a model: ollama pull llama3.1
echo 3. Make sure MySQL is running: cd ../bank_db ^&^& docker-compose up -d
echo 4. Test tools: python test_tools.py
echo 5. Run agent: python run_agent.py
echo.
pause
