import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, Party
from agent_functions.get_client_by_iban import get_client_by_iban

import csv
from pathlib import Path


@pytest.fixture(scope="module")
def test_db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    Base.metadata.create_all(engine)

    csv_path = Path(__file__).parent / "tests_data" / "parties_with_ibans.csv"
    with TestingSessionLocal() as session:
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for name, iban in reader:
                session.add(Party(name=name.strip(), iban=iban.strip(), mean_sum=1000))
        session.commit()

    yield TestingSessionLocal

    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def override_session(monkeypatch, test_db_session):
    import agent_functions.get_client_by_iban as module
    monkeypatch.setattr(module, "SessionLocal", test_db_session)
    yield


def test_get_client_by_iban_found():
    result = json.loads(get_client_by_iban("NO9386011117947"))
    assert result["found"] is True
    client = result["client"]
    assert client["name"] == "Lambda AB"
    assert client["iban"] == "NO9386011117947"
    assert client["account_status"] == "active"


def test_get_client_by_iban_not_found():
    result = json.loads(get_client_by_iban("NONEXISTENT123"))
    assert result["found"] is False
    assert "client" not in result


def test_get_client_by_iban_no_iban():
    result = json.loads(get_client_by_iban(""))
    assert result["found"] is False
    assert "no iban provided" in result["error"].lower()