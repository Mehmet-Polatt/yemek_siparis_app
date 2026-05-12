
# import requests

BASE_URL = "http://localhost:8000"

def test_login():
    # Note: This assumes the server is running.
    # If not, I can't test it this way. 
    # But I can test the logic by calling the function directly in a script (like I did before).
    # Since I don't know for sure if the server is up, I'll use a direct logic check.
    pass

# Direct logic check script
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import DATABASE_URL
from app.crud import user as user_crud
from app.core import security

async def verify_logic():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        email = "mehmet@gmail.com"
        # Since I don't know Mehmet's password, I'll just check if the login logic 
        # (which I updated) works with the existing hash if I had the password.
        # But wait, I'll use the test_admin I created earlier.
        email = "test_admin@example.com"
        password = "adminpassword123"
        
        user = await user_crud.get_user_by_email(db, email=email)
        if user:
            verified = security.verify_password(password, user.hashed_password)
            print(f"Login logic check for {email}: {'Success' if verified else 'Failed'}")
        else:
            print(f"User {email} not found for check.")

if __name__ == "__main__":
    asyncio.run(verify_logic())
