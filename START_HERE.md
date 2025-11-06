# 🚀 START HERE - 5 Minute Quick Test

Follow these steps to test the complete ETL pipeline:

## ⚡ Super Fast Test (Windows)

1. **Run the setup script:**
   ```cmd
   quick_start.bat
   ```

2. **Open TWO new command prompts**

3. **In Command Prompt #1 - Start Generator:**
   ```cmd
   cd transaction_generator
   venv\Scripts\activate
   SET MAX_TRANSACTIONS=20
   SET GENERATION_INTERVAL=1
   python generator.py
   ```

   Wait until you see "Reached max transactions (20). Stopping."

4. **In Command Prompt #2 - Start Processor:**
   ```cmd
   cd transaction_processor
   venv\Scripts\activate
   python processor.py
   ```

   You should see messages like "[1] ✓ Processed transaction from offset 0"

5. **Verify the results:**
   ```cmd
   docker exec -it clickhouse clickhouse-client --query "SELECT count(*) FROM bank_dw.transactions"
   ```

   You should see `20` (or the number of transactions you generated)

6. **View the data:**
   ```cmd
   docker exec -it clickhouse clickhouse-client
   ```

   Then run:
   ```sql
   USE bank_dw;

   SELECT
       transaction_id,
       amount,
       currency,
       debtor_name,
       creditor_name
   FROM transactions
   LIMIT 5;
   ```

## ✅ Success Indicators

You'll know it's working when you see:

**Generator output:**
```
[1] Sent transaction to unprocessed partition 0 offset 0
[2] Sent transaction to unprocessed partition 0 offset 1
[3] Sent transaction to unprocessed partition 0 offset 2
```

**Processor output:**
```
[1] ✓ Processed transaction from offset 0
[2] ✓ Processed transaction from offset 1
[3] ✓ Processed transaction from offset 2
```

**ClickHouse query result:**
```
20
```

## 🎯 What's Happening?

1. **Generator** creates fake bank transactions (XML) → sends to Kafka
2. **Kafka** queues the messages in the "unprocessed" topic
3. **Processor** reads from Kafka → parses XML → loads to ClickHouse
4. **ClickHouse** stores data and creates analytics views

## 🔍 Cool Queries to Try

```sql
-- Top 5 highest transactions
SELECT amount, debtor_name, creditor_name
FROM transactions
ORDER BY amount DESC
LIMIT 5;

-- Transactions by currency
SELECT currency, count(*) as count, sum(amount) as total
FROM transactions
GROUP BY currency;

-- Who sent/received the most?
SELECT party_name, total_transactions, total_sent, total_received
FROM dim_parties
ORDER BY total_transactions DESC;

-- Daily summary
SELECT * FROM daily_transaction_summary;
```

## 🛑 Stop Everything

1. Press `Ctrl+C` in both command prompts
2. Run: `docker-compose down`

## ❓ Problems?

See **[QUICKSTART.md](QUICKSTART.md)** for troubleshooting.

---

**🎉 That's it! You now have a working ETL pipeline processing bank transactions!**
