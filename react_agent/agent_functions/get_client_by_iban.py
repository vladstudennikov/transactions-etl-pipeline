from db.db import SessionLocal, engine
from db.models import Party
import json
from sqlalchemy.orm import Session

def get_client_by_iban(iban: str) -> str:
    if not iban:
        return json.dumps({"found": False, "error": "no iban provided"})
    session: Session = SessionLocal()
    try:
        party: Party | None = session.query(Party).filter(Party.iban == iban).one_or_none()
        if not party:
            return json.dumps({"found": False})
        client_obj = {}
        for col in Party.__table__.columns:
            val = getattr(party, col.name)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            client_obj[col.name] = float(val) if hasattr(val, "quantize") else val
        return json.dumps({"found": True, "client": client_obj})
    except Exception as e:
        return json.dumps({"found": False, "error": f"db error: {str(e)}"})
    finally:
        session.close()

if __name__ == "__main__":
    print(get_client_by_iban("NO9386011117947"))