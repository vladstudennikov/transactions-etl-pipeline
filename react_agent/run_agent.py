"""
Example runner for the ReACT Agent
Demonstrates how to use the agent with real transaction data
"""

import sys
from pathlib import Path
from agent import ReACTAgent
import config


def read_transaction_xml(file_path: str) -> str:
    """Read transaction XML from file"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Transaction file not found: {file_path}")
    return path.read_text(encoding="utf-8")


def main():
    print("="*80)
    print("ReACT Fraud Detection Agent")
    print("="*80)

    # Initialize agent with configuration
    agent = ReACTAgent(
        model=config.OLLAMA_MODEL,
        ollama_url=config.OLLAMA_URL,
        max_iterations=config.MAX_ITERATIONS,
        verbose=config.VERBOSE,
        api_key=config.OLLAMA_API_KEY
    )

    # Check if transaction XML file is provided
    if len(sys.argv) > 1:
        # Use provided XML file
        xml_file = sys.argv[1]
        print(f"\nLoading transaction from: {xml_file}")
        transaction_xml = read_transaction_xml(xml_file)

        task = f"""
Analyze this banking transaction for fraud:

{transaction_xml}

Please:
1. Parse the XML transaction to extract details
2. Check if the debtor client exists in our database using their IBAN
3. Check if the creditor client exists in our database using their IBAN
4. Calculate a fraud risk score for this transaction
5. If the score indicates 'suspicious' or 'fraud' classification, create an alert in the database
6. Provide a summary of your findings
"""
    else:
        # Use default example task
        print("\nNo transaction file provided. Using example task.")
        print("Usage: python run_agent.py <path_to_transaction.xml>")
        print("\nRunning with example task...\n")

        task = """
Analyze a hypothetical banking transaction for fraud:

Transaction details:
- Message ID: MSG-2024-001
- Debtor: John Smith
- Debtor IBAN: GB29NWBK60161331926819
- Creditor: Acme Corp
- Creditor IBAN: FR1420041010050500013M02606
- Amount: 25000 EUR
- Date: 2024-11-18

Please:
1. Check if the debtor (GB29NWBK60161331926819) exists in our database
2. Check if the creditor (FR1420041010050500013M02606) exists in our database
3. Create a mock transaction summary in JSON format
4. Calculate a fraud risk score based on the amount and any client data found
5. If the score is concerning, create an alert
6. Provide a summary of your findings
"""

    # Run the agent
    result = agent.run(task)

    print("\n" + "="*80)
    print("EXECUTION COMPLETE")
    print("="*80)
    print(f"\nResult: {result}\n")


if __name__ == "__main__":
    main()
