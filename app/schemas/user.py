from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=12, max_length=128)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime
