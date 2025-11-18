import json
from pathlib import Path
import pytest

from agent_functions.parse_transaction import parse_transaction

TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "tests_data"
XML_FILE = DATA_DIR / "transaction_example.xml"


@pytest.fixture
def example_xml_text() -> str:
    assert XML_FILE.exists(), f"Test data file missing: {XML_FILE}"
    return XML_FILE.read_text(encoding="utf-8")


def test_parse_transaction_happy_path(example_xml_text):
    out = parse_transaction(example_xml_text)
    assert isinstance(out, str), "parse_transaction should return a JSON string"
    parsed = json.loads(out)

    assert parsed["msg_id"] == "MSG-1"
    assert parsed["created_at"] == "2025-10-28T09:59:50Z"
    assert parsed["nb_of_txs"] == "1"
    assert parsed["ctrl_sum"] == "1214.15"
    assert parsed["initiating_party"] == "Lambda AB"

    assert parsed["pmt_inf_id"] == "PmtInf-1"
    assert parsed["debtor_name"] == "Lambda AB"
    assert parsed["debtor_iban"] == "NO9386011117947"
    assert parsed["creditor_name"] == "Pi Enterprises"
    assert parsed["creditor_iban"] == "PT50000201231234567890154"
    assert parsed["end_to_end_id"] == "E2E-1"

    assert isinstance(parsed["amount"], float)
    assert parsed["amount"] == pytest.approx(1214.15)
    assert parsed["currency"] == "EUR"


def test_parse_transaction_invalid_xml_returns_error():
    bad = "this is not xml"
    out = parse_transaction(bad)
    assert isinstance(out, str)
    parsed = json.loads(out)
    assert "error" in parsed
    assert parsed["error"].lower().startswith("xml parse error")


def test_parse_transaction_missing_amount():
    minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
      <CstmrCdtTrfInitn>
        <GrpHdr><MsgId>MSG-2</MsgId></GrpHdr>
        <PmtInf><PmtInfId>P-2</PmtInfId></PmtInf>
      </CstmrCdtTrfInitn>
    </Document>
    """
    out = parse_transaction(minimal_xml)
    parsed = json.loads(out)
    assert parsed["msg_id"] == "MSG-2"
    assert parsed["pmt_inf_id"] == "P-2"
    assert parsed["amount"] is None
    assert parsed["currency"] is None