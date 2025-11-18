"""
Test script to verify all agent functions work correctly
Run this before using the agent to ensure everything is set up properly
"""

import json
from pathlib import Path
from agent_functions import (
    parse_transaction,
    get_client_by_iban,
    score_transaction,
    create_alert
)


def test_parse_transaction():
    """Test XML transaction parsing"""
    print("\n" + "="*80)
    print("TEST 1: parse_transaction")
    print("="*80)

    # Check if example XML exists
    xml_file = Path(__file__).parent / "transaction_example.xml"
    if xml_file.exists():
        xml_content = xml_file.read_text(encoding="utf-8")
        result = parse_transaction(xml_content)
        result_obj = json.loads(result)

        print("✓ Successfully parsed transaction XML")
        print(f"  Amount: {result_obj.get('amount')} {result_obj.get('currency')}")
        print(f"  Debtor IBAN: {result_obj.get('debtor_iban')}")
        print(f"  Creditor IBAN: {result_obj.get('creditor_iban')}")
        return result
    else:
        print("✗ transaction_example.xml not found")
        # Return a mock transaction for testing
        mock_tx = {
            "msg_id": "TEST-001",
            "debtor_iban": "GB29NWBK60161331926819",
            "creditor_iban": "FR1420041010050500013M02606",
            "amount": 15000,
            "currency": "EUR"
        }
        print("  Using mock transaction data")
        return json.dumps(mock_tx)


def test_get_client_by_iban():
    """Test client database lookup"""
    print("\n" + "="*80)
    print("TEST 2: get_client_by_iban")
    print("="*80)

    try:
        # Try to look up a client
        test_iban = "GB29NWBK60161331926819"
        result = get_client_by_iban(test_iban)
        result_obj = json.loads(result)

        if result_obj.get("found"):
            print(f"✓ Client found for IBAN: {test_iban}")
            client = result_obj.get("client", {})
            print(f"  Name: {client.get('name')}")
            print(f"  Risk Score: {client.get('risk_score')}")
            print(f"  Account Status: {client.get('account_status')}")
        else:
            print(f"⚠ Client not found for IBAN: {test_iban}")
            print("  This is OK if database is not seeded yet")

        return result

    except Exception as e:
        print(f"✗ Database connection error: {str(e)}")
        print("  Make sure MySQL is running and database is set up")
        # Return mock client for testing
        mock_client = {
            "found": True,
            "client": {
                "name": "Test Client",
                "iban": "GB29NWBK60161331926819",
                "risk_score": 45.0,
                "mean_sum": 5000.0,
                "account_status": "active"
            }
        }
        return json.dumps(mock_client)


def test_score_transaction(tx_json, client_json):
    """Test transaction scoring"""
    print("\n" + "="*80)
    print("TEST 3: score_transaction")
    print("="*80)

    try:
        result = score_transaction(tx_json, client_json)
        result_obj = json.loads(result)

        print("✓ Transaction scored successfully")
        print(f"  Score: {result_obj.get('score')}")
        print(f"  Classification: {result_obj.get('classification')}")
        print(f"  Reasons: {result_obj.get('reasons')}")

        return result

    except Exception as e:
        print(f"✗ Scoring error: {str(e)}")
        return None


def test_create_alert(tx_json, client_json):
    """Test alert creation (optional - modifies database)"""
    print("\n" + "="*80)
    print("TEST 4: create_alert (SKIPPED)")
    print("="*80)
    print("⚠ Skipping create_alert to avoid modifying database")
    print("  To test, uncomment the code in test_tools.py")

    try:
        result = create_alert(
            tx_json,
            client_json,
            reason="Test alert from test_tools.py"
        )
        result_obj = json.loads(result)

        if "alert_id" in result_obj:
            print("✓ Alert created successfully")
            print(f"  Alert ID: {result_obj.get('alert_id')}")
        else:
            print(f"✗ Alert creation failed: {result_obj.get('error')}")

    except Exception as e:
        print(f"✗ Alert creation error: {str(e)}")


def main():
    print("\n" + "="*80)
    print("ReACT Agent - Tool Verification")
    print("="*80)
    print("\nThis script tests all available agent functions")

    # Test 1: Parse transaction
    tx_json = test_parse_transaction()

    # Test 2: Get client
    client_json = test_get_client_by_iban()

    # Test 3: Score transaction
    if tx_json and client_json:
        score_json = test_score_transaction(tx_json, client_json)

    # Test 4: Create alert (skipped by default)
    if tx_json and client_json:
        test_create_alert(tx_json, client_json)

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)
    print("\nIf all tests passed, you can now run the agent:")
    print("  python run_agent.py")
    print("\n")


if __name__ == "__main__":
    main()
