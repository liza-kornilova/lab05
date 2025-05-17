from pydantic import BaseModel, Field
from typing import Optional


class ClientBase(BaseModel):
    username: str
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")  # Простий патерн для валідації email
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class ClientCreate(ClientBase):
    password: str


class ClientResponse(ClientBase):
    id: int
    is_active: bool
    
    class Config:
        orm_mode = True
        from_attributes = True
        

class ClientLogin(BaseModel):
    username: str
    password: str