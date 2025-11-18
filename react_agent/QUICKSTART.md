# Quick Start Guide - ReACT Agent

Get the ReACT fraud detection agent running in 5 minutes!

## Prerequisites

Before starting, make sure you have:

1. **Python 3.8+** installed
2. **Ollama** installed and running ([download here](https://ollama.ai))
3. **MySQL database** running (from bank_db component)

## Step 1: Start Ollama

```bash
# Install Ollama from https://ollama.ai if not already installed

# Pull a model (choose one):
ollama pull llama3.1
# or
ollama pull mistral

# Verify Ollama is running:
curl http://localhost:11434/api/tags
```

## Step 2: Start Database

```bash
# Navigate to bank_db directory
cd ../bank_db

# Start MySQL with Docker
docker-compose up -d

# Seed the database with sample parties
python seed.py
```

## Step 3: Install Agent Dependencies

### Windows
```bash
cd react_agent
setup.bat
```

### Linux/Mac
```bash
cd react_agent

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Test the Tools

```bash
python test_tools.py
```

You should see output like:
```
✓ Successfully parsed transaction XML
✓ Client found for IBAN: GB29NWBK60161331926819
✓ Transaction scored successfully
```

## Step 5: Run the Agent

### With example task
```bash
python run_agent.py
```

### With real transaction XML
```bash
python run_agent.py transaction_example.xml
```

## Expected Output

You'll see the agent reasoning through the task:

```
================================================================================
TASK: Analyze this banking transaction for fraud...
================================================================================

--- Iteration 1 ---

LLM Response:
Thought: I need to check if the debtor exists in our database
Action: get_client_by_iban(iban="GB29NWBK60161331926819")

Executing: get_client_by_iban({'iban': 'GB29NWBK60161331926819'})
Observation: {"found": true, "client": {"risk_score": 75, ...}}

--- Iteration 2 ---

LLM Response:
Thought: Client found with high risk score. Let me score this transaction...
Action: score_transaction(tx_json="...", client_json="...")

...

================================================================================
FINAL ANSWER: Transaction flagged as fraud (score: 85). Alert #123 created.
================================================================================
```

## Configuration

Edit `config.py` or set environment variables:

```bash
# Change the Ollama model
export OLLAMA_MODEL="mistral"

# Change max iterations
export MAX_ITERATIONS="15"

# Disable verbose output
export VERBOSE="false"
```

## Troubleshooting

### "Ollama API error"
- Make sure Ollama is running: `ollama serve`
- Check the URL: `curl http://localhost:11434/api/tags`

### "Database connection error"
- Start MySQL: `cd ../bank_db && docker-compose up -d`
- Check connection: `mysql -h localhost -u root -proot bankdb`

### "Client not found"
- Seed database: `cd ../bank_db && python seed.py`

### Agent loops without finishing
- Try a more powerful model: `ollama pull mixtral`
- Increase iterations: `export MAX_ITERATIONS="20"`

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Modify tasks in `run_agent.py` to test different scenarios
- Add custom tools in `agent_functions/`
- Experiment with different Ollama models

## Support

For issues or questions:
1. Check the [README.md](README.md) troubleshooting section
2. Review the main project documentation in `../CLAUDE.md`
3. Test individual tools with `test_tools.py`

Happy fraud detecting! 🔍
