from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Text, Boolean, Float, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    iban = Column(String(64), nullable=False, unique=True, index=True)
    mean_sum = Column(Numeric(precision=14, scale=2), nullable=False, default=0)

    country = Column(String(3), nullable=True, index=True)
    currency = Column(String(8), nullable=True)
    account_status = Column(String(32), nullable=False, default="active")  # active/suspended/closed
    risk_score = Column(Float, nullable=False, default=0.0)  # 0..100
    annual_turnover = Column(Numeric(precision=16, scale=2), nullable=True)
    num_transactions = Column(Integer, nullable=False, default=0)
    last_tx_date = Column(DateTime(timezone=True), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(64), nullable=True)
    address = Column(String(400), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    notes = Column(Text, nullable=True)
    is_corporate = Column(Boolean, nullable=False, default=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tx_summary = Column(JSON)
    client_summary = Column(JSON)
    reason = Column(Text)