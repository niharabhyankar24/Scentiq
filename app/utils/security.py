from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PEPPER = os.getenv("PASSWORD_PEPPER")
if not PEPPER:
    raise RuntimeError("PASSWORD_PEPPER is not set in environment variables.")

def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt with pepper."""
    peppered = PEPPER + plain_password
    return pwd_context.hash(peppered)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash."""
    peppered = PEPPER + plain_password
    return pwd_context.verify(peppered, hashed_password)