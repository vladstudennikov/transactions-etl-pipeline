import json
from datetime import datetime
from sqlalchemy.orm import Session # type: ignore
from db.models import Alert
from db.db import engine

def create_alert(tx_json: str, client_json: str, reason: str) -> str:
    try:
        created_at = datetime.utcnow()

        alert = Alert(
            created_at=created_at,
            tx_summary=json.loads(tx_json),
            client_summary=json.loads(client_json) if client_json else {},
            reason=reason
        )

        with Session(engine) as session:
            session.add(alert)
            session.commit()
            session.refresh(alert)

        return json.dumps({
            "alert_id": alert.id,
            "created_at": created_at.isoformat() + "Z",
            "reason": reason
        })

    except Exception as e:
        return json.dumps({"error": f"create_alert failed: {str(e)}"})