from pydantic import BaseModel, EmailStr
from typing import Optional


class ClientBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class ClientCreate(ClientBase):
    password: str


class ClientResponse(ClientBase):
    id: int
    is_active: bool
    
    class Config:
        orm_mode = True
        

class ClientLogin(BaseModel):
    username: str
    password: str
