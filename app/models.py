from app.db import Base
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime
from sqlalchemy import func


class APIKey(Base):
    __tablename__ = "api_keys"

    id : Mapped[int] = mapped_column(primary_key = True)
    key_hash : Mapped[str] = mapped_column(unique = True, index = True)
    key_prefix : Mapped[str] = mapped_column()
    name : Mapped[str] = mapped_column()
    is_active : Mapped[bool] = mapped_column(default = True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    rate_limit : Mapped[int] = mapped_column(default = 60)
    