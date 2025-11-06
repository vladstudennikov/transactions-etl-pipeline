-- ClickHouse Data Warehouse Schema for Bank Transactions

CREATE DATABASE IF NOT EXISTS bank_dw;

USE bank_dw;

-- Transactions fact table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id String,
    message_id String,
    end_to_end_id String,
    payment_info_id String,

    -- Timestamp
    created_datetime DateTime64(3),
    processing_datetime DateTime64(3) DEFAULT now64(3),

    -- Amount details
    amount Decimal(18, 2),
    currency String,

    -- Debtor (sender) information
    debtor_name String,
    debtor_iban String,
    debtor_country String,

    -- Creditor (receiver) information
    creditor_name String,
    creditor_iban String,
    creditor_country String,

    -- Payment details
    payment_method String,
    control_sum Decimal(18, 2),
    num_transactions UInt32,

    -- Metadata
    raw_xml String,
    processed_status String DEFAULT 'SUCCESS'
) ENGINE = MergeTree()
ORDER BY (created_datetime, transaction_id)
PARTITION BY toYYYYMM(created_datetime);

-- Parties dimension table (for analytical queries)
CREATE TABLE IF NOT EXISTS dim_parties (
    iban String,
    party_name String,
    country String,
    currency String,
    last_seen DateTime64(3),
    total_transactions UInt64,
    total_sent Decimal(18, 2) DEFAULT 0,
    total_received Decimal(18, 2) DEFAULT 0
) ENGINE = ReplacingMergeTree(last_seen)
ORDER BY iban;

-- Daily transaction summary materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_transaction_summary
ENGINE = SummingMergeTree()
ORDER BY (transaction_date, currency)
AS SELECT
    toDate(created_datetime) AS transaction_date,
    currency,
    count() AS transaction_count,
    sum(amount) AS total_amount,
    uniq(debtor_iban) AS unique_senders,
    uniq(creditor_iban) AS unique_receivers
FROM transactions
GROUP BY transaction_date, currency;

-- High-value transactions view (for monitoring)
CREATE MATERIALIZED VIEW IF NOT EXISTS high_value_transactions
ENGINE = MergeTree()
ORDER BY (created_datetime, amount)
AS SELECT
    transaction_id,
    created_datetime,
    amount,
    currency,
    debtor_name,
    creditor_name,
    debtor_iban,
    creditor_iban
FROM transactions
WHERE amount > 10000;
