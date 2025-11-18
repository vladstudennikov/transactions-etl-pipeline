"""
Agent Functions Package

Contains all the tools/functions available to the ReACT agent:
- parse_transaction: Parse ISO 20022 XML transactions
- get_client_by_iban: Look up clients in database
- score_transaction: Calculate fraud risk scores
- create_alert: Create fraud alerts in database
"""

from .parse_transaction import parse_transaction
from .get_client_by_iban import get_client_by_iban
from .score_transaction import score_transaction
from .create_alert import create_alert
from .agent_tools import TOOLS, run_tool

__all__ = [
    'parse_transaction',
    'get_client_by_iban',
    'score_transaction',
    'create_alert',
    'TOOLS',
    'run_tool'
]
