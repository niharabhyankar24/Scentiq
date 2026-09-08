from pydantic import BaseModel, EmailStr, field_validator


# Password policy: reasonable, not draconian. Enough to block
# trivially weak passwords ("123456", "password") without
# frustrating legitimate users. Tuned for a consumer app, not
# a bank. If rejected, the message tells the user exactly what
# to fix — the frontend surfaces these strings.
_MIN_PASSWORD_LENGTH = 8


def _validate_password_strength(value: str) -> str:
    if len(value) < _MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
        )
    if not any(c.isalpha() for c in value):
        raise ValueError("Password must contain at least one letter.")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one number.")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str