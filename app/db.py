

from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
engine = create_async_engine(settings.database_url,connect_args = {"ssl" : "require", "statement_cache_size" : 0}) # creating engine



AsyncSessionLocal = async_sessionmaker( #creating session maker
    engine, 
    expire_on_commit=False,
)




class Base(DeclarativeBase): # creating base class for models
    pass
