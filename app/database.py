from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL bağlantı adresin (aiomysql sürücüsü ile)
DATABASE_URL = "mysql+aiomysql://root:156473mP*@localhost/yemek_siparis_db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# DB Dependency (Endpoint'lerde kullanacağız)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session