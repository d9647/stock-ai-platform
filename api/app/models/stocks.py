"""
Stock and company information models.
"""
from sqlalchemy import Column, String, Float, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class Stock(Base):
    """
    Stock company information (mostly static).
    Can be updated as company info changes.
    """
    __tablename__ = "stocks"
    __table_args__ = (
        {"schema": "market_data"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Float)
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Stock(ticker={self.ticker}, company={self.company_name})>"
