# ReACT AI Agent for Fraud Detection

A simple ReACT (Reasoning and Acting) AI agent that uses Ollama LLMs to analyze banking transactions and detect fraud.

## What is ReACT?

ReACT is an AI agent paradigm that combines **reasoning** and **acting**:

1. **Thought**: The agent reasons about what to do next
2. **Action**: The agent calls a tool/function
3. **Observation**: The agent receives the result
4. **Repeat**: Continue until the task is complete

This creates an autonomous agent that can break down complex tasks and use available tools to solve them.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       ReACT Agent                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │  1. Thought: "I need to parse the transaction"     │     │
│  │  2. Action: parse_transaction(xml_string="...")    │     │
│  │  3. Observation: {"amount": 25000, "iban": "..."}  │     │
│  │  4. Thought: "Now check if client exists..."       │     │
│  │  5. Action: get_client_by_iban(iban="...")         │     │
│  │  ... (continues until Final Answer)                │     │
│  └────────────────────────────────────────────────────┘     │
│                           ▼                                  │
│                    ┌──────────────┐                          │
│                    │ Ollama LLM   │                          │
│                    │ (llama3.1)   │                          │
│                    └──────────────┘                          │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Available Tools:                       │     │
│  │  • parse_transaction     (XML → JSON)               │     │
│  │  • get_client_by_iban    (DB lookup)                │     │
│  │  • score_transaction     (Risk scoring)             │     │
│  │  • create_alert          (Save alert to DB)         │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Available Tools

The agent has access to four pre-built functions:

### 1. `parse_transaction(xml_string)`
- Parses ISO 20022 XML transaction format
- Extracts: debtor/creditor IBANs, amount, currency, message ID, etc.
- Returns: JSON string with transaction details

### 2. `get_client_by_iban(iban)`
- Looks up client in MySQL database
- Returns: Client details including risk_score, mean_sum, account_status
- Returns: `{"found": false}` if client doesn't exist

### 3. `score_transaction(tx_json, client_json)`
- Calculates fraud risk score (0-100)
- Considers: amount vs historical average, client risk score, account status
- Returns: Score, classification (ok/suspicious/fraud), and reasons

### 4. `create_alert(tx_json, client_json, reason)`
- Saves fraud alert to database
- Returns: Alert ID and timestamp

## Setup

### Prerequisites

1. **Ollama installed and running**
   ```bash
   # Install Ollama from https://ollama.ai

   # Pull a model (choose one):
   ollama pull llama3.1
   ollama pull mistral
   ollama pull mixtral

   # Verify Ollama is running:
   curl http://localhost:11434/api/tags
   ```

2. **MySQL database running**
   ```bash
   cd ../bank_db
   docker-compose up -d
   ```

3. **Database seeded with parties**
   ```bash
   cd ../bank_db
   python seed.py
   ```

### Installation

```bash
cd react_agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python run_agent.py
```

This will run the agent with an example task (no real XML transaction).

### Analyze a Real Transaction

```bash
python run_agent.py transaction_example.xml
```

### Programmatic Usage

```python
from agent import ReACTAgent

# Initialize agent
agent = ReACTAgent(
    model="llama3.1",           # Ollama model name
    ollama_url="http://localhost:11434",
    max_iterations=10,           # Max reasoning loops
    verbose=True                 # Print detailed logs
)

# Define your task
task = """
Analyze this banking transaction for fraud:
<Document>...</Document>

Please parse the transaction, check client risk, score it, and create an alert if needed.
"""

# Run the agent
result = agent.run(task)
print(result)
```

## Configuration

You can configure the agent via environment variables:

```bash
# Ollama settings
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.1"

# Agent settings
export MAX_ITERATIONS="10"
export VERBOSE="true"

# Database settings
export DATABASE_URL="mysql+mysqldb://root:root@localhost:3306/bankdb"
```

Or edit `config.py` directly.

## Example Execution Flow

```
Task: "Analyze transaction from GB29... to FR14... for 25000 EUR"

Iteration 1:
  Thought: I need to check if the debtor exists in the database
  Action: get_client_by_iban(iban="GB29NWBK60161331926819")
  Observation: {"found": true, "client": {"risk_score": 75, "mean_sum": 5000, ...}}

Iteration 2:
  Thought: The client exists with high risk score. Let me create a transaction summary
  Action: [creates JSON summary]
  Observation: {...}

Iteration 3:
  Thought: Now I should score this transaction
  Action: score_transaction(tx_json="...", client_json="...")
  Observation: {"score": 85, "classification": "fraud", "reasons": [...]}

Iteration 4:
  Thought: Score is 85 (fraud level), I should create an alert
  Action: create_alert(tx_json="...", client_json="...", reason="High risk score")
  Observation: {"alert_id": 123, "created_at": "2024-11-18T10:30:00Z"}

Iteration 5:
  Thought: I have completed the analysis
  Final Answer: Transaction flagged as fraud (score: 85). Alert #123 created.
```

## How It Works

### 1. System Prompt
The agent is initialized with a detailed system prompt that:
- Describes all available tools and their parameters
- Explains the ReACT format (Thought → Action → Observation)
- Provides examples of proper tool usage
- Sets clear rules for the reasoning loop

### 2. ReACT Loop
```python
while not done and iterations < max_iterations:
    # Get LLM reasoning
    response = llm.generate(conversation_history)

    # Parse action from response
    if "Action:" in response:
        tool_name, params = parse_action(response)
        result = execute_tool(tool_name, params)

        # Add observation to conversation
        conversation_history.append(f"Observation: {result}")

    # Check for final answer
    if "Final Answer:" in response:
        return extract_final_answer(response)
```

### 3. Tool Execution
- Tools are registered in `agent_functions/agent_tools.py`
- Each tool returns JSON strings for structured data exchange
- Errors are caught and returned as JSON for the agent to handle

## Models

The agent works with any Ollama model. Recommended models:

- **llama3.1** (8B): Fast, good reasoning, recommended for development
- **mistral** (7B): Fast, concise responses
- **mixtral** (8x7B): More powerful, better for complex reasoning
- **llama3.1** (70B): Most powerful, slower but best results

```bash
# Pull and use a specific model
ollama pull mixtral
export OLLAMA_MODEL="mixtral"
python run_agent.py
```

## Extending the Agent

### Add a New Tool

1. Create your function in `agent_functions/`:
```python
# agent_functions/my_new_tool.py
def my_new_tool(param1: str) -> str:
    result = do_something(param1)
    return json.dumps(result)
```

2. Register in `agent_functions/agent_tools.py`:
```python
from agent_functions.my_new_tool import my_new_tool

TOOLS = {
    # ... existing tools
    "my_new_tool": my_new_tool
}
```

3. Add description in `agent.py` → `_build_tool_descriptions()`:
```python
descriptions.append("""
my_new_tool:
  Description: What this tool does
  Parameters:
    - param1 (str): Description
  Returns: JSON string with result
  Example: my_new_tool(param1="value")
""")
```

## Troubleshooting

### Ollama not responding
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Database connection errors
```bash
# Check MySQL is running
docker ps | grep mysql

# Test connection
mysql -h localhost -u root -proot bankdb
```

### Agent stuck in loop
- Increase `MAX_ITERATIONS` if task is complex
- Use a more powerful model (e.g., mixtral instead of llama3.1)
- Simplify the task description
- Check logs to see where reasoning fails

### Tool execution errors
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify database is seeded: `cd ../bank_db && python seed.py`
- Check tool functions individually in `agent_functions/tests/`

## Performance Tips

1. **Use faster models for simple tasks**: llama3.1:8b is sufficient for most fraud detection
2. **Lower temperature**: Set to 0.1 for more deterministic reasoning
3. **Clear task descriptions**: Be specific about what the agent should do
4. **Pre-validate inputs**: Check XML is valid before passing to agent
5. **Cache LLM responses**: For repeated similar tasks (not implemented yet)

## License

Part of the bank_project banking transaction processing system.
