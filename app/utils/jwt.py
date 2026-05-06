from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES"))

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set in environment variables.")

def create_access_token(data: dict) -> str:
    """
    Takes a dictionary of data you want to encode, adds an expiry timestamp to it,
    then signs the whole thing using your secret key and algorithm. The result is a 
    JWT string you hand back to the user.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRY_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """
    Does the reverse of above. It takes a token string,
    verifies the signature using your secret key,
    checks the expiry, and returns the payload dictionary.
    If the token is tampered with or expired,
    python-jose raises an exception automatically.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None