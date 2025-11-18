import json
import os
import pytest

from agent_functions.score_transaction import score_transaction

DATA_DIR = os.path.join(os.path.dirname(__file__), "tests_data")
CLIENT_PATH = os.path.join(DATA_DIR, "client_data.json")
TRANSACTION_PATH = os.path.join(DATA_DIR, "transaction_data.json")


@pytest.fixture
def client_data():
    with open(CLIENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def transaction_data():
    with open(TRANSACTION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_score_transaction_basic(client_data, transaction_data):
    tx_json = json.dumps(transaction_data)
    client_json = json.dumps(client_data)

    result = json.loads(score_transaction(tx_json, client_json))

    assert "score" in result
    assert "classification" in result
    assert "reasons" in result
    assert "amount" in result

    assert isinstance(result["score"], (int, float))
    assert isinstance(result["classification"], str)
    assert isinstance(result["reasons"], list)

    assert 0 <= result["score"] <= 100
    if result["score"] >= 70:
        assert result["classification"] == "fraud"
    elif result["score"] >= 35:
        assert result["classification"] == "suspicious"
    else:
        assert result["classification"] == "ok"


def test_high_amount_triggers_high_score(client_data):
    tx = {
        "amount": 15000,
        "currency": "EUR",
        "creditor_name": "High Value Ltd",
        "debtor_name": "Lambda AB"
    }

    result = json.loads(score_transaction(json.dumps(tx), json.dumps(client_data)))
    assert result["score"] >= 35
    assert any("absolute amount" in r for r in result["reasons"])


def test_unknown_client_high_amount():
    tx = {"amount": 7000, "currency": "USD"}
    result = json.loads(score_transaction(json.dumps(tx)))
    assert result["classification"] in ("suspicious", "fraud")
    assert any("unknown client" in r for r in result["reasons"])


def test_small_amount_known_client(client_data):
    tx = {"amount": 50, "currency": "EUR"}
    result = json.loads(score_transaction(json.dumps(tx), json.dumps(client_data)))
    assert result["classification"] == "ok"
    assert result["score"] < 35


def test_extreme_ratio(client_data):
    tx = {"amount": 20000, "currency": "EUR"}
    result = json.loads(score_transaction(json.dumps(tx), json.dumps(client_data)))
    assert result["score"] >= 70
    assert "very large" in " ".join(result["reasons"])