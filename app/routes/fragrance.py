"""
Password hashing.

We pepper passwords with a server-side secret AND hash with
bcrypt. The subtlety: bcrypt only reads the first 72 BYTES of
its input. The old scheme prepended the pepper to the password
(PEPPER + password) and hashed that directly — which meant a
long pepper ate into the 72-byte budget, silently truncating
the actual password. Two different passwords sharing a prefix
could then collide (and very long passwords could error).

Fix: HMAC-SHA256 the password using the pepper as the key,
then base64 the digest. That produces a FIXED 44-character
input to bcrypt no matter how long the password or pepper is —
so bcrypt never truncates anything meaningful, and the pepper
is still mixed in cryptographically.

Note: this changes the hashing scheme, so hashes produced by
the old code will NOT verify against the new code. With a small
user base the simplest path is a forced password reset. If that
isn't acceptable, add a hash_version column and re-hash on next
successful login.
"""

import os
import hmac
import base64
import hashlib

from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PEPPER = os.getenv("PASSWORD_PEPPER")
if not PEPPER:
    raise RuntimeError(
        "PASSWORD_PEPPER is not set in environment variables."
    )


def _prehash(plain_password: str) -> str:
    """
    HMAC-SHA256 the password with the pepper as key, base64 the
    result. Always returns 44 chars — well under bcrypt's 72-byte
    limit — regardless of input length. This is what actually
    gets bcrypt-hashed.
    """
    digest = hmac.new(
        PEPPER.encode("utf-8"),
        plain_password.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def hash_password(plain_password: str) -> str:
    """Hash a plain text password (peppered via HMAC) with bcrypt."""
    return pwd_context.hash(_prehash(plain_password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash."""
    return pwd_context.verify(_prehash(plain_password), hashed_password)