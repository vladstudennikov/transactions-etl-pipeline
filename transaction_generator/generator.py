#!/usr/bin/env python3
"""
Transaction Generator - Generates ISO 20022 XML transactions and sends to Kafka
"""

import os
import sys
import time
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from kafka import KafkaProducer
from kafka.errors import KafkaError


class TransactionGenerator:
    """Generates ISO 20022 pain.001.001.03 transactions"""

    def __init__(self, parties_file='../data/parties.txt'):
        self.parties = self._load_parties(parties_file)
        self.namespace = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
        self.message_counter = 0

    def _load_parties(self, parties_file):
        """Load parties from CSV file"""
        parties = []
        try:
            with open(parties_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        name, iban = line.split(',')
                        parties.append({
                            'name': name.strip(),
                            'iban': iban.strip(),
                            'country': iban[:2] if len(iban) >= 2 else 'XX',
                            'currency': self._currency_from_country(iban[:2] if len(iban) >= 2 else 'XX')
                        })
        except FileNotFoundError:
            print(f"Error: Parties file not found at {parties_file}")
            sys.exit(1)

        if not parties:
            print("Error: No parties loaded from file")
            sys.exit(1)

        print(f"Loaded {len(parties)} parties")
        return parties

    def _currency_from_country(self, country_iso):
        """Map country code to currency"""
        mapping = {
            "DE": "EUR", "GB": "GBP", "FR": "EUR", "ES": "EUR", "AT": "EUR",
            "BE": "EUR", "NL": "EUR", "FI": "EUR", "IT": "EUR", "CH": "CHF",
            "SE": "SEK", "DK": "DKK", "NO": "NOK", "PL": "PLN", "CZ": "CZK",
            "HU": "HUF", "GR": "EUR", "PT": "EUR", "IE": "EUR", "LU": "EUR"
        }
        return mapping.get(country_iso, "EUR")

    def generate_transaction_xml(self):
        """Generate a single transaction in ISO 20022 XML format"""
        self.message_counter += 1

        # Select random debtor and creditor
        debtor = random.choice(self.parties)
        creditor = random.choice([p for p in self.parties if p['iban'] != debtor['iban']])

        # Generate transaction details
        # 90% of transactions: around 1000 with noise +-300-600
        # 10% of transactions: really big amounts (10,000 - 100,000)
        if random.random() < 0.9:
            noise = random.uniform(300, 600)
            if random.random() < 0.5:
                amount = round(1000 + noise, 2)
            else:
                amount = round(1000 - noise, 2)
        else:
            amount = round(random.uniform(10000.0, 100000.0), 2)

        currency = random.choice(["EUR", "USD", "GBP", "CHF", debtor['currency']])
        timestamp = datetime.utcnow() - timedelta(seconds=random.randint(0, 86400))

        msg_id = f"MSG-{uuid.uuid4().hex[:8]}"
        pmt_inf_id = f"PmtInf-{self.message_counter}"
        e2e_id = f"E2E-{uuid.uuid4().hex[:12]}"

        # Build XML structure
        root = Element('Document', xmlns=self.namespace)
        cstmr = SubElement(root, 'CstmrCdtTrfInitn')

        # Group Header
        grp_hdr = SubElement(cstmr, 'GrpHdr')
        SubElement(grp_hdr, 'MsgId').text = msg_id
        SubElement(grp_hdr, 'CreDtTm').text = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        SubElement(grp_hdr, 'NbOfTxs').text = '1'
        SubElement(grp_hdr, 'CtrlSum').text = str(amount)
        initg_pty = SubElement(grp_hdr, 'InitgPty')
        SubElement(initg_pty, 'Nm').text = debtor['name']

        # Payment Information
        pmt_inf = SubElement(cstmr, 'PmtInf')
        SubElement(pmt_inf, 'PmtInfId').text = pmt_inf_id
        SubElement(pmt_inf, 'PmtMtd').text = 'TRF'
        SubElement(pmt_inf, 'NbOfTxs').text = '1'
        SubElement(pmt_inf, 'CtrlSum').text = str(amount)

        # Debtor
        dbtr = SubElement(pmt_inf, 'Dbtr')
        SubElement(dbtr, 'Nm').text = debtor['name']
        dbtr_acct = SubElement(pmt_inf, 'DbtrAcct')
        dbtr_id = SubElement(dbtr_acct, 'Id')
        SubElement(dbtr_id, 'IBAN').text = debtor['iban']

        # Credit Transfer Transaction Information
        cdt_trf = SubElement(pmt_inf, 'CdtTrfTxInf')
        pmt_id = SubElement(cdt_trf, 'PmtId')
        SubElement(pmt_id, 'EndToEndId').text = e2e_id

        # Amount
        amt = SubElement(cdt_trf, 'Amt')
        instd_amt = SubElement(amt, 'InstdAmt', Ccy=currency)
        instd_amt.text = str(amount)

        # Creditor
        cdtr = SubElement(cdt_trf, 'Cdtr')
        SubElement(cdtr, 'Nm').text = creditor['name']
        cdtr_acct = SubElement(cdt_trf, 'CdtrAcct')
        cdtr_id = SubElement(cdtr_acct, 'Id')
        SubElement(cdtr_id, 'IBAN').text = creditor['iban']

        # Convert to pretty XML string
        xml_str = minidom.parseString(tostring(root, encoding='utf-8')).toprettyxml(indent="  ")

        return xml_str


def main():
    """Main entry point"""
    # Configuration
    kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    kafka_topic = os.environ.get('KAFKA_TOPIC', 'unprocessed')
    generation_interval = float(os.environ.get('GENERATION_INTERVAL', '2'))  # seconds
    max_transactions = int(os.environ.get('MAX_TRANSACTIONS', '0'))  # 0 = infinite

    print("=" * 60)
    print("Transaction Generator Starting")
    print("=" * 60)
    print(f"Kafka Servers: {kafka_bootstrap_servers}")
    print(f"Topic: {kafka_topic}")
    print(f"Interval: {generation_interval}s")
    print(f"Max Transactions: {'infinite' if max_transactions == 0 else max_transactions}")
    print("=" * 60)

    # Initialize generator
    generator = TransactionGenerator()

    # Initialize Kafka producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: v.encode('utf-8'),
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        print("✓ Connected to Kafka")
    except Exception as e:
        print(f"✗ Failed to connect to Kafka: {e}")
        sys.exit(1)

    # Generate and send transactions
    transactions_sent = 0
    try:
        while True:
            # Generate transaction
            xml_transaction = generator.generate_transaction_xml()

            # Send to Kafka
            try:
                future = producer.send(kafka_topic, value=xml_transaction)
                record_metadata = future.get(timeout=10)
                transactions_sent += 1

                print(f"[{transactions_sent}] Sent transaction to {record_metadata.topic} "
                      f"partition {record_metadata.partition} offset {record_metadata.offset}")

            except KafkaError as e:
                print(f"✗ Failed to send transaction: {e}")

            # Check if we've reached max transactions
            if max_transactions > 0 and transactions_sent >= max_transactions:
                print(f"\n✓ Reached max transactions ({max_transactions}). Stopping.")
                break

            # Wait before next transaction
            time.sleep(generation_interval)

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    finally:
        producer.flush()
        producer.close()
        print(f"✓ Sent {transactions_sent} transactions total")


if __name__ == '__main__':
    main()
