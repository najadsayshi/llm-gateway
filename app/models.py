from app.db import Base
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, ForeignKey, Numeric, DateTime

class APIKey(Base):
    __tablename__ = "api_keys"

    id : Mapped[int] = mapped_column(primary_key = True)
    key_hash : Mapped[str] = mapped_column(unique = True, index = True)
    key_prefix : Mapped[str] = mapped_column()
    name : Mapped[str] = mapped_column()
    is_active : Mapped[bool] = mapped_column(default = True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rate_limit : Mapped[int] = mapped_column(default = 60)

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id : Mapped[int] = mapped_column(primary_key = True)
    api_key_id : Mapped[int] = mapped_column(ForeignKey("api_keys.id"), index = True)
    model : Mapped[str] = mapped_column()
    provider : Mapped[str] = mapped_column()
    prompt_tokens : Mapped[int] = mapped_column()
    completion_tokens : Mapped[int] = mapped_column()
    total_tokens : Mapped[int] = mapped_column()
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 12))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


