from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.jwt import decode_access_token

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate the JWT from the Authorization header.
    Returns the authenticated user or raises 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    # The "sub" claim may be missing or non-numeric on a
    # malformed/forged token. Parse defensively so that turns
    # into a clean 401, not an uncaught 500.
    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        optional_bearer_scheme
    ),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Like get_current_user, but does not raise on missing or
    invalid credentials. Returns the authenticated User if
    the token is valid, or None otherwise.

    Use on public endpoints that behave differently when a
    valid token is present — for example, the semantic
    search endpoint, which is public but logs the query for
    authenticated users who have consented to search history.
    """
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    return db.query(User).filter(User.id == user_id).first()


def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures the current user is an admin.

    Builds on get_current_user (which verifies the JWT and
    loads the user). Then checks the is_admin flag and
    raises 403 if the user is not an admin.

    Use on any route that should be admin-only.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user