import json

def score_transaction(tx_json: str, client_json: str = None) -> str:
    tx = json.loads(tx_json)
    client = json.loads(client_json) if client_json else None

    amount = tx.get("amount") or 0.0
    reason_components = []
    score = 0.0

    if client and client.get("found"):
        c = client["client"]

        mean_sum = float(c.get("mean_sum") or 0.0)
        risk_score = float(c.get("risk_score") or 0.0)

        ratio = (amount / (mean_sum + 1e-9)) if mean_sum > 0 else (float("inf") if amount > 0 else 0.0)

        if ratio >= 10:
            score += 60
            reason_components.append(f"amount is {ratio:.1f}x mean_sum (very large)")
        elif ratio >= 4:
            score += 35
            reason_components.append(f"amount is {ratio:.1f}x mean_sum (large)")
        elif ratio >= 2:
            score += 15
            reason_components.append(f"amount is {ratio:.1f}x mean_sum (moderate)")

        score += min(30, risk_score * 0.3)

        if c.get("account_status") and str(c.get("account_status")).lower() in ("suspended","blocked","closed"):
            score += 25
            reason_components.append(f"account_status={c.get('account_status')}")

        if amount >= 10000:
            score += 20
            reason_components.append("absolute amount >= 10k")
    else:
        if amount >= 5000:
            score += 50
            reason_components.append("unknown client + amount >= 5k")
        elif amount >= 1000:
            score += 20
            reason_components.append("unknown client + amount >= 1k")

    score = min(100, score)
    classification = "fraud" if score >= 70 else ("suspicious" if score >= 35 else "ok")
    result = {
        "score": score,
        "classification": classification,
        "reasons": reason_components,
        "amount": amount
    }
    return json.dumps(result)