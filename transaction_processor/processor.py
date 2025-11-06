#!/usr/bin/env python3
"""
Transaction Processor - Consumes transactions from Kafka and loads to ClickHouse DW
"""

import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import clickhouse_connect


class TransactionProcessor:
    """Processes XML transactions and loads to data warehouse"""

    def __init__(self, clickhouse_host, clickhouse_port, clickhouse_user, clickhouse_password):
        self.namespace = {"ns": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"}
        self.client = self._connect_clickhouse(clickhouse_host, clickhouse_port,
                                                clickhouse_user, clickhouse_password)

    def _connect_clickhouse(self, host, port, user, password):
        """Connect to ClickHouse data warehouse"""
        try:
            client = clickhouse_connect.get_client(
                host=host,
                port=port,
                username=user,
                password=password,
                database='bank_dw'
            )
            print("✓ Connected to ClickHouse")
            return client
        except Exception as e:
            print(f"✗ Failed to connect to ClickHouse: {e}")
            sys.exit(1)

    def parse_transaction(self, xml_string):
        """Parse ISO 20022 XML transaction"""
        try:
            root = ET.fromstring(xml_string)

            # Navigate through the XML structure
            cstmr = root.find('ns:CstmrCdtTrfInitn', self.namespace)
            if cstmr is None:
                raise ValueError("Invalid XML structure: CstmrCdtTrfInitn not found")

            # Parse Group Header
            grp_hdr = cstmr.find('ns:GrpHdr', self.namespace)
            msg_id = grp_hdr.find('ns:MsgId', self.namespace).text
            cre_dt_tm = grp_hdr.find('ns:CreDtTm', self.namespace).text
            nb_of_txs = int(grp_hdr.find('ns:NbOfTxs', self.namespace).text)
            ctrl_sum = Decimal(grp_hdr.find('ns:CtrlSum', self.namespace).text)

            # Parse Payment Information
            pmt_inf = cstmr.find('ns:PmtInf', self.namespace)
            pmt_inf_id = pmt_inf.find('ns:PmtInfId', self.namespace).text
            pmt_mtd = pmt_inf.find('ns:PmtMtd', self.namespace).text

            # Parse Debtor
            dbtr = pmt_inf.find('ns:Dbtr', self.namespace)
            dbtr_name = dbtr.find('ns:Nm', self.namespace).text
            dbtr_acct = pmt_inf.find('ns:DbtrAcct', self.namespace)
            dbtr_iban = dbtr_acct.find('ns:Id/ns:IBAN', self.namespace).text

            # Parse Credit Transfer Transaction Info
            cdt_trf = pmt_inf.find('ns:CdtTrfTxInf', self.namespace)
            pmt_id = cdt_trf.find('ns:PmtId', self.namespace)
            e2e_id = pmt_id.find('ns:EndToEndId', self.namespace).text

            # Parse Amount
            amt = cdt_trf.find('ns:Amt/ns:InstdAmt', self.namespace)
            amount = Decimal(amt.text)
            currency = amt.get('Ccy')

            # Parse Creditor
            cdtr = cdt_trf.find('ns:Cdtr', self.namespace)
            cdtr_name = cdtr.find('ns:Nm', self.namespace).text
            cdtr_acct = cdt_trf.find('ns:CdtrAcct', self.namespace)
            cdtr_iban = cdtr_acct.find('ns:Id/ns:IBAN', self.namespace).text

            # Parse timestamp
            created_datetime = datetime.strptime(cre_dt_tm, '%Y-%m-%dT%H:%M:%SZ')

            # Extract country codes from IBANs
            debtor_country = dbtr_iban[:2] if len(dbtr_iban) >= 2 else 'XX'
            creditor_country = cdtr_iban[:2] if len(cdtr_iban) >= 2 else 'XX'

            return {
                'transaction_id': e2e_id,
                'message_id': msg_id,
                'end_to_end_id': e2e_id,
                'payment_info_id': pmt_inf_id,
                'created_datetime': created_datetime,
                'processing_datetime': datetime.utcnow(),
                'amount': float(amount),
                'currency': currency,
                'debtor_name': dbtr_name,
                'debtor_iban': dbtr_iban,
                'debtor_country': debtor_country,
                'creditor_name': cdtr_name,
                'creditor_iban': cdtr_iban,
                'creditor_country': creditor_country,
                'payment_method': pmt_mtd,
                'control_sum': float(ctrl_sum),
                'num_transactions': nb_of_txs,
                'raw_xml': xml_string,
                'processed_status': 'SUCCESS'
            }

        except Exception as e:
            print(f"✗ Error parsing transaction: {e}")
            return None

    def load_to_warehouse(self, transaction_data):
        """Load parsed transaction to ClickHouse"""
        try:
            # Insert transaction
            self.client.insert('transactions', [list(transaction_data.values())],
                             column_names=list(transaction_data.keys()))

            # Update dimension tables
            self._update_party_dimension(transaction_data)

            return True
        except Exception as e:
            print(f"✗ Error loading to warehouse: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_party_dimension(self, tx_data):
        """Update or insert party dimension data"""
        now = datetime.utcnow()

        # Update debtor
        debtor_data = {
            'iban': tx_data['debtor_iban'],
            'party_name': tx_data['debtor_name'],
            'country': tx_data['debtor_country'],
            'currency': tx_data['currency'],
            'last_seen': now,
            'total_transactions': 1,
            'total_sent': tx_data['amount'],
            'total_received': 0
        }
        self.client.insert('dim_parties', [list(debtor_data.values())],
                          column_names=list(debtor_data.keys()))

        # Update creditor
        creditor_data = {
            'iban': tx_data['creditor_iban'],
            'party_name': tx_data['creditor_name'],
            'country': tx_data['creditor_country'],
            'currency': tx_data['currency'],
            'last_seen': now,
            'total_transactions': 1,
            'total_sent': 0,
            'total_received': tx_data['amount']
        }
        self.client.insert('dim_parties', [list(creditor_data.values())],
                          column_names=list(creditor_data.keys()))

    def process_message(self, xml_message):
        """Process a single transaction message"""
        # Parse transaction
        transaction_data = self.parse_transaction(xml_message)
        if transaction_data is None:
            return False

        # Load to warehouse
        success = self.load_to_warehouse(transaction_data)
        return success


def main():
    """Main entry point"""
    # Configuration
    kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    kafka_topic = os.environ.get('KAFKA_TOPIC', 'unprocessed')
    kafka_group_id = os.environ.get('KAFKA_GROUP_ID', 'transaction-processor')

    clickhouse_host = os.environ.get('CLICKHOUSE_HOST', 'localhost')
    clickhouse_port = int(os.environ.get('CLICKHOUSE_PORT', '8123'))
    clickhouse_user = os.environ.get('CLICKHOUSE_USER', 'dwuser')
    clickhouse_password = os.environ.get('CLICKHOUSE_PASSWORD', 'dwpass')

    print("=" * 60)
    print("Transaction Processor Starting")
    print("=" * 60)
    print(f"Kafka Servers: {kafka_bootstrap_servers}")
    print(f"Topic: {kafka_topic}")
    print(f"Group ID: {kafka_group_id}")
    print(f"ClickHouse: {clickhouse_host}:{clickhouse_port}")
    print("=" * 60)

    # Initialize processor
    processor = TransactionProcessor(clickhouse_host, clickhouse_port,
                                     clickhouse_user, clickhouse_password)

    # Initialize Kafka consumer
    try:
        consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=kafka_group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode('utf-8')
        )
        print("✓ Connected to Kafka")
        print("Waiting for messages...\n")
    except Exception as e:
        print(f"✗ Failed to connect to Kafka: {e}")
        sys.exit(1)

    # Process messages
    messages_processed = 0
    messages_failed = 0

    try:
        for message in consumer:
            try:
                xml_transaction = message.value
                success = processor.process_message(xml_transaction)

                if success:
                    messages_processed += 1
                    print(f"[{messages_processed}] ✓ Processed transaction from offset {message.offset}")
                else:
                    messages_failed += 1
                    print(f"✗ Failed to process transaction from offset {message.offset}")

            except Exception as e:
                messages_failed += 1
                print(f"✗ Error processing message: {e}")

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    finally:
        consumer.close()
        processor.client.close()
        print(f"\n✓ Processed {messages_processed} transactions")
        print(f"✗ Failed {messages_failed} transactions")


if __name__ == '__main__':
    main()
