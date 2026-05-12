import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.security import get_password_hash, verify_password

def test():
    password = "123456"
    print(f"Original password: {password}")
    
    hashed = get_password_hash(password)
    print(f"Hashed password: {hashed}")
    
    # Check if verify works
    is_correct = verify_password(password, hashed)
    print(f"Verification success: {is_correct}")
    
    # Check if wrong password fails
    is_wrong_correct = verify_password("wrong", hashed)
    print(f"Verification failure (correctly): {not is_wrong_correct}")

    if is_correct and not is_wrong_correct:
        print("TEST PASSED!")
    else:
        print("TEST FAILED!")

if __name__ == "__main__":
    test()
