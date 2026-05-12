
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import DATABASE_URL
from app.crud import user as user_crud
from app.schemas import schemas
from app.core import security
from app.models.models import UserRole

async def test_flow():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        email = "test_admin@example.com"
        password = "adminpassword123"
        
        # 1. Register
        user_in = schemas.UserCreate(
            first_name="Test",
            last_name="Admin",
            email=email,
            password=password,
            role=UserRole.admin
        )
        
        # Check if exists
        existing = await user_crud.get_user_by_email(db, email=email)
        if not existing:
            print("Creating user...")
            await user_crud.create_user(db, user=user_in)
        else:
            print("User already exists.")
            
        # 2. Try Login (simulating the logic in auth.py)
        user = await user_crud.get_user_by_email(db, email=email)
        print(f"Found user: {user.email}")
        
        verified = security.verify_password(password, user.hashed_password)
        print(f"Password verified: {verified}")
        
        if not verified:
            print(f"DEBUG: Hashed password in DB: {user.hashed_password}")
            new_hash = security.get_password_hash(password)
            print(f"DEBUG: Newly generated hash: {new_hash}")
            print(f"DEBUG: Verification of new hash: {security.verify_password(password, new_hash)}")

if __name__ == "__main__":
    asyncio.run(test_flow())
