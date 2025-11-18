# ReACT Agent - Project Summary

## Overview

This is a complete **ReACT (Reasoning and Acting)** AI agent implementation for fraud detection in banking transactions. The agent uses **Ollama** (local LLM) to autonomously analyze transactions, query databases, calculate risk scores, and create alerts.

## Complete File Structure

```
react_agent/
├── agent.py                    # Core ReACT agent implementation
├── config.py                   # Configuration settings
├── run_agent.py                # Main runner script
├── test_tools.py               # Tool verification script
├── requirements.txt            # Python dependencies
├── setup.bat                   # Windows setup script
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Detailed documentation
├── QUICKSTART.md               # Quick start guide
├── PROJECT_SUMMARY.md          # This file
├── transaction_example.xml     # Sample transaction for testing
│
├── db/                         # Database models
│   ├── __init__.py
│   ├── db.py                   # SQLAlchemy session factory
│   └── models.py               # Party and Alert models
│
└── agent_functions/            # Available tools/functions
    ├── __init__.py
    ├── agent_tools.py          # Tool registry
    ├── parse_transaction.py    # XML transaction parser
    ├── get_client_by_iban.py   # Database client lookup
    ├── score_transaction.py    # Fraud risk scoring
    ├── create_alert.py         # Alert creation
    └── tests/                  # Unit tests for functions
        ├── test_parse_transactions.py
        ├── test_get_client_by_iban.py
        ├── test_score_transaction.py
        ├── test_create_alert.py
        └── tests_data/
            ├── transaction_example.xml
            ├── transaction_data.json
            ├── client_data.json
            └── parties_with_ibans.csv
```

## Key Components

### 1. agent.py - Core ReACT Agent

The heart of the system. Implements:
- **ReACT loop**: Thought → Action → Observation → Repeat
- **Ollama integration**: Calls local LLM via HTTP API
- **Tool execution**: Parses LLM actions and executes functions
- **Conversation management**: Maintains context across iterations

Key methods:
- `__init__()`: Initialize agent with model, URL, max iterations
- `_build_system_prompt()`: Creates detailed instructions for LLM
- `_call_ollama()`: Makes HTTP requests to Ollama API
- `_parse_action()`: Extracts tool calls from LLM responses
- `_execute_action()`: Runs the requested tool
- `run(task)`: Main execution loop

### 2. agent_functions/ - Available Tools

Four pre-built functions that the agent can call:

#### parse_transaction
- **Purpose**: Parse ISO 20022 XML transactions
- **Input**: XML string
- **Output**: JSON with debtor/creditor IBANs, amount, currency, etc.
- **Use case**: Extract structured data from transaction messages

#### get_client_by_iban
- **Purpose**: Look up client in MySQL database
- **Input**: IBAN string
- **Output**: JSON with client details (risk_score, mean_sum, account_status)
- **Use case**: Retrieve historical client data for risk assessment

#### score_transaction
- **Purpose**: Calculate fraud risk score (0-100)
- **Input**: Transaction JSON, client JSON (optional)
- **Output**: Score, classification (ok/suspicious/fraud), reasons
- **Use case**: Determine if transaction is risky based on multiple factors

#### create_alert
- **Purpose**: Save fraud alert to database
- **Input**: Transaction JSON, client JSON, reason string
- **Output**: Alert ID and timestamp
- **Use case**: Record suspicious transactions for investigation

### 3. config.py - Configuration

Centralized configuration from environment variables:
- `OLLAMA_URL`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model name (default: llama3.1)
- `MAX_ITERATIONS`: Max reasoning loops (default: 10)
- `VERBOSE`: Enable detailed logging (default: true)
- `DATABASE_URL`: MySQL connection string

### 4. run_agent.py - Main Runner

Example script showing how to use the agent:
- Reads transaction XML from file or uses example task
- Initializes agent with config
- Runs the agent and displays results
- Can be called with: `python run_agent.py [transaction.xml]`

### 5. test_tools.py - Verification Script

Tests each tool individually:
- Parses sample transaction
- Looks up client in database
- Calculates fraud score
- (Optionally) Creates alert

Run before first use: `python test_tools.py`

## How It Works

### ReACT Loop Example

```
User Task: "Analyze transaction from GB29... to FR14... for 25000 EUR"

┌─────────────────────────────────────────────────────────────┐
│ Iteration 1                                                  │
├─────────────────────────────────────────────────────────────┤
│ Thought: I need to check if the debtor exists              │
│ Action: get_client_by_iban(iban="GB29...")                 │
│ → Agent executes get_client_by_iban                        │
│ Observation: {"found": true, "risk_score": 75, ...}        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Iteration 2                                                  │
├─────────────────────────────────────────────────────────────┤
│ Thought: Client exists with high risk. Check creditor      │
│ Action: get_client_by_iban(iban="FR14...")                 │
│ → Agent executes get_client_by_iban                        │
│ Observation: {"found": false}                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Iteration 3                                                  │
├─────────────────────────────────────────────────────────────┤
│ Thought: Let me create transaction summary and score it    │
│ Action: score_transaction(tx_json="...", client_json="...") │
│ → Agent executes score_transaction                         │
│ Observation: {"score": 85, "classification": "fraud", ...}  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Iteration 4                                                  │
├─────────────────────────────────────────────────────────────┤
│ Thought: Score is 85 (fraud), create alert                 │
│ Action: create_alert(tx_json="...", reason="High risk")    │
│ → Agent executes create_alert                              │
│ Observation: {"alert_id": 123, "created_at": "..."}        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Iteration 5                                                  │
├─────────────────────────────────────────────────────────────┤
│ Thought: Analysis complete                                 │
│ Final Answer: Transaction flagged as fraud (score: 85).    │
│               Alert #123 created.                           │
└─────────────────────────────────────────────────────────────┘
```

### System Prompt Strategy

The agent is given detailed instructions including:

1. **Tool descriptions**: Exact parameter names and types
2. **Format rules**: How to structure Thought/Action/Observation
3. **Examples**: Sample execution flows
4. **Constraints**: One action at a time, wait for observations

This ensures the LLM understands:
- What tools are available
- How to call them correctly
- What to expect in return
- When to stop (Final Answer)

## Quick Start

### 1. Prerequisites
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1

# Start database
cd ../bank_db && docker-compose up -d
```

### 2. Setup
```bash
cd react_agent

# Windows
setup.bat

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Test
```bash
python test_tools.py
```

### 4. Run
```bash
# With example task
python run_agent.py

# With real transaction
python run_agent.py transaction_example.xml
```

## Extending the Agent

### Add a New Tool

1. **Create function** in `agent_functions/my_tool.py`:
```python
import json

def my_tool(param1: str, param2: int) -> str:
    result = {"output": f"Processed {param1} with {param2}"}
    return json.dumps(result)
```

2. **Register tool** in `agent_functions/agent_tools.py`:
```python
from agent_functions.my_tool import my_tool

TOOLS = {
    # ... existing tools
    "my_tool": my_tool
}
```

3. **Add description** in `agent.py` → `_build_tool_descriptions()`:
```python
descriptions.append("""
my_tool:
  Description: Does something useful
  Parameters:
    - param1 (str): First parameter
    - param2 (int): Second parameter
  Returns: JSON string with result
  Example: my_tool(param1="test", param2="42")
""")
```

4. **Test it**:
```python
agent = ReACTAgent()
result = agent.run("Use my_tool to process 'hello' with value 42")
```

### Change the LLM Model

```bash
# Pull a different model
ollama pull mixtral
ollama pull mistral
ollama pull llama3.1:70b

# Use it
export OLLAMA_MODEL="mixtral"
python run_agent.py
```

### Modify Scoring Logic

Edit `agent_functions/score_transaction.py`:
- Adjust score thresholds
- Add new risk factors
- Change classification rules

## Technical Details

### Dependencies
- **requests**: HTTP calls to Ollama API
- **lxml**: XML parsing for ISO 20022 transactions
- **sqlalchemy**: Database ORM
- **mysqlclient**: MySQL database driver

### Ollama API
The agent uses Ollama's `/api/chat` endpoint:
```python
POST http://localhost:11434/api/chat
{
  "model": "llama3.1",
  "messages": [...],
  "stream": false,
  "options": {"temperature": 0.1}
}
```

Low temperature (0.1) ensures deterministic, logical reasoning.

### Error Handling
- Tool execution errors return JSON: `{"error": "..."}`
- Database errors are caught and returned as observations
- LLM can see errors and adapt (retry, use different tool, etc.)

### Performance
- **llama3.1** (8B): ~2-3 seconds per iteration
- **mixtral** (8x7B): ~5-8 seconds per iteration
- **llama3.1** (70B): ~15-30 seconds per iteration

Typical fraud analysis: 4-6 iterations = 10-20 seconds with llama3.1:8B

## Use Cases

### 1. Real-time Transaction Monitoring
```python
# Process transactions from Kafka
for transaction_xml in kafka_consumer:
    task = f"Analyze this transaction: {transaction_xml}"
    result = agent.run(task)
    if "fraud" in result.lower():
        notify_compliance_team(result)
```

### 2. Batch Analysis
```python
# Analyze historical transactions
for tx_file in glob("transactions/*.xml"):
    xml_content = Path(tx_file).read_text()
    result = agent.run(f"Analyze: {xml_content}")
    save_results(tx_file, result)
```

### 3. Interactive Investigation
```python
# Investigator asks questions
while True:
    question = input("Investigate: ")
    answer = agent.run(question)
    print(f"Finding: {answer}")
```

## Future Enhancements

Potential improvements:

1. **Multi-agent**: Multiple agents with different specializations
2. **Memory**: Long-term memory for learning patterns
3. **Streaming**: Stream LLM responses for faster UX
4. **Caching**: Cache LLM calls for repeated scenarios
5. **Async**: Asyncio for parallel tool execution
6. **Web UI**: Gradio/Streamlit interface
7. **More tools**: Add regulatory lookup, geo-location, graph analysis
8. **Self-improvement**: Agent learns from feedback

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not responding | Check `ollama serve`, verify port 11434 |
| Database errors | Ensure MySQL running, database seeded |
| Agent loops forever | Increase MAX_ITERATIONS, use stronger model |
| Low quality reasoning | Switch to mixtral or llama3.1:70b |
| Slow execution | Use smaller model (mistral) or increase timeout |

## Summary

This ReACT agent demonstrates:
- ✅ Autonomous reasoning with local LLMs (Ollama)
- ✅ Tool use (parse XML, query DB, score risk, create alerts)
- ✅ Iterative problem solving (thought → action → observation)
- ✅ Production-ready structure (config, tests, documentation)
- ✅ Extensible design (easy to add new tools)
- ✅ Privacy-focused (runs entirely locally, no cloud APIs)

Perfect for:
- Fraud detection systems
- Automated compliance checks
- Transaction monitoring
- Research and learning about AI agents

---

**Next Steps:**
1. Read [QUICKSTART.md](QUICKSTART.md) to get running
2. Read [README.md](README.md) for detailed docs
3. Experiment with different tasks
4. Add your own custom tools
5. Try different Ollama models

Happy building! 🚀
