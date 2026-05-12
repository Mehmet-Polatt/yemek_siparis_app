
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error during checkpw: {e}")
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    pw = "test1234"
    hpw = get_password_hash(pw)
    print(f"Plain: {pw}")
    print(f"Hashed: {hpw}")
    print(f"Verify: {verify_password(pw, hpw)}")
    
    # Try with a real hash from DB (if I had one full one)
    # The one I saw was $2b$12$98g...
