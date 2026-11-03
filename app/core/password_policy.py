from pydantic import BaseModel, Field, field_validator

COMMON_PASSWORDS = {
    "password123456",
    "123456789012",
    "qwerty123456",
    "admin12345678",
}

def validate_password_strength(password: str) -> str:
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common")

    if password.isspace():
        raise ValueError("Password cannot contain only spaces")
    return password

class PasswordInput(BaseModel):
    password: str = Field(
        min_length=12,
        max_length=128,
    )

    @field_validator("password")
    @classmethod
    def validate_strength(cls, value: str) -> str:
        return validate_password_strength(value)
