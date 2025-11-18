import json
import pytest # type: ignore
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import Session, sessionmaker, declarative_base # type: ignore
from sqlalchemy import Column, Integer, DateTime, JSON, String # type: ignore
from db.models import Alert, Base
from agent_functions.create_alert import create_alert

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def session(test_engine):
    with Session(test_engine) as s:
        yield s


@pytest.fixture()
def load_test_data():
    base_path = Path(__file__).parent.parent / "tests" / "tests_data"

    tx_json = (base_path / "transaction_data.json").read_text(encoding="utf-8")
    client_json = (base_path / "client_data.json").read_text(encoding="utf-8")

    return tx_json, client_json


def test_create_alert_success(monkeypatch, test_engine, load_test_data):
    """Should create an alert successfully and return proper JSON."""

    tx_json, client_json = load_test_data

    monkeypatch.setattr("agent_functions.create_alert.engine", test_engine)
    monkeypatch.setattr("agent_functions.create_alert.Alert", Alert)

    reason = "Suspicious transaction"

    result_json = create_alert(tx_json, client_json, reason)
    result = json.loads(result_json)

    assert "alert_id" in result
    assert "created_at" in result
    assert result["reason"] == reason

    with Session(test_engine) as session:
        alerts = session.query(Alert).all()
        assert len(alerts) == 1
        a = alerts[0]
        assert a.reason == reason
        assert isinstance(a.created_at, datetime)
        assert isinstance(a.tx_summary, dict)
        assert isinstance(a.client_summary, dict)


def test_create_alert_without_client_json(monkeypatch, test_engine, load_test_data):
    tx_json, _ = load_test_data

    monkeypatch.setattr("agent_functions.create_alert.engine", test_engine)
    monkeypatch.setattr("agent_functions.create_alert.Alert", Alert)

    reason = "No client info"
    result_json = create_alert(tx_json, "", reason)
    result = json.loads(result_json)

    assert "alert_id" in result
    assert result["reason"] == reason

    with Session(test_engine) as session:
        a = session.query(Alert).order_by(Alert.id.desc()).first()
        assert a.client_summary == {}


def test_create_alert_invalid_json(monkeypatch, test_engine):
    monkeypatch.setattr("agent_functions.create_alert.engine", test_engine)
    monkeypatch.setattr("agent_functions.create_alert.Alert", Alert)

    result_json = create_alert("{invalid json}", "{}", "bad json")
    result = json.loads(result_json)

    assert "error" in result
    assert "create_alert failed" in result["error"]