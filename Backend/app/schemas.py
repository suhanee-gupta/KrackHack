from pydantic import BaseModel, EmailStr,model_validator, Field
from typing import Optional,Any
import re

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)

    @model_validator(mode="before")
    @classmethod
    def check_username_or_email(cls, values:dict[str,Any]):
        username = values.get("username")
        email = values.get("email")
        if not username and not email:
            raise ValueError("Either username or email must be provided.")
        return values
    
    @model_validator(mode="after")
    def validate_password(self) -> "UserCreate":
        # password = values.get("password")
        if not self.password:
            raise ValueError("Password is required.")
        
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(pattern, self.password):
            raise ValueError(
                "Password must have at least 8 characters, one uppercase, one lowercase, one number, and one special character."
            )
        return self

class UserDB(BaseModel):
    id: str
    username: str
    email: EmailStr
    hashed_password: str

    @model_validator(mode = "before")
    @classmethod
    def check_username_or_email(cls, values):
        if not values.get("username") and not values.get("email"):
            raise ValueError("UserDB must have either a username or email.")
        return values
    
class UserLoginSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    @model_validator(mode="before")
    # @classmethod
    def check_username_or_email(cls, values):
        username = values.get("username")
        email = values.get("email")
        if not username and not email:
            raise ValueError("Either username or email must be provided.")
        return values

class TokenSchema(BaseModel):
    access_token: str
    token_type: str
