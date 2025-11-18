from lxml import etree # type: ignore
import json
from pathlib import Path

def parse_transaction(xml_string: str) -> str:
    try:
        xml_string = xml_string.strip()
        root = etree.fromstring(xml_string.encode("utf-8"))
    except Exception as e:
        return json.dumps({"error": f"XML parse error: {str(e)}"})

    ns = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'}

    def t(xpath):
        el = root.find(xpath, namespaces=ns)
        return el.text if el is not None else None

    msg_id = t('.//ns:GrpHdr/ns:MsgId')
    cre_dt_tm = t('.//ns:GrpHdr/ns:CreDtTm')
    nb_of_txs = t('.//ns:GrpHdr/ns:NbOfTxs')
    ctrl_sum = t('.//ns:GrpHdr/ns:CtrlSum')
    initg_nm = t('.//ns:GrpHdr/ns:InitgPty/ns:Nm')

    pmt_inf_id = t('.//ns:PmtInf/ns:PmtInfId')
    dbtr_name = t('.//ns:Dbtr/ns:Nm')
    dbtr_iban = t('.//ns:DbtrAcct/ns:Id/ns:IBAN')
    cdtr_name = t('.//ns:CdtTrfTxInf/ns:Cdtr/ns:Nm')
    cdtr_iban = t('.//ns:CdtTrfTxInf/ns:CdtrAcct/ns:Id/ns:IBAN')
    end_to_end_id = t('.//ns:CdtTrfTxInf/ns:PmtId/ns:EndToEndId')

    amt = None
    amt_el = root.find('.//ns:CdtTrfTxInf//ns:InstdAmt', namespaces=ns)
    if amt_el is not None:
        amt = amt_el.text
        currency = amt_el.get("Ccy")
    else:
        currency = None

    summary = {
        "msg_id": msg_id,
        "created_at": cre_dt_tm,
        "nb_of_txs": nb_of_txs,
        "ctrl_sum": ctrl_sum,
        "initiating_party": initg_nm,
        "pmt_inf_id": pmt_inf_id,
        "debtor_name": dbtr_name,
        "debtor_iban": dbtr_iban,
        "creditor_name": cdtr_name,
        "creditor_iban": cdtr_iban,
        "end_to_end_id": end_to_end_id,
        "amount": float(amt) if amt else None,
        "currency": currency
    }
    return json.dumps(summary)


if __name__ == "__main__":
    xml_tx = Path(__file__).parent / "tests" / "tests_data" / "transaction_example.xml"
    xml_text = xml_tx.read_text(encoding="utf-8")
    print(parse_transaction(xml_text))