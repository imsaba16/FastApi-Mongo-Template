from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    status: bool
    status_code: int
    message: str
    data: Optional[T] = None


class User(BaseModel):
    name: Optional[str] = ""
    email: str
    phone: Optional[str] = ""
    password: str
    verified: Optional[bool] = False
    otp: Optional[int] = None
    token: Optional[str] = None

class AuthModel(BaseModel):
    email: str
    token: str