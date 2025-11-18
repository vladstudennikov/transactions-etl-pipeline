from agent_functions.create_alert import create_alert
from agent_functions.get_client_by_iban import get_client_by_iban
from agent_functions.parse_transaction import parse_transaction
from agent_functions.score_transaction import score_transaction

TOOLS = {
    "get_client_by_iban": get_client_by_iban,
    "parse_transaction": parse_transaction,
    "score_transaction": score_transaction,
    "create_alert": create_alert
}

def run_tool(tool_name, *args, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Tool {tool_name} not found")
    return TOOLS[tool_name](*args, **kwargs)