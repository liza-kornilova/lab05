from pydantic import BaseModel
from typing import Optional, List


class BusBase(BaseModel):
    registration_number: str
    model: str
    capacity: int
    is_active: Optional[bool] = True


class BusCreate(BusBase):
    pass


class BusResponse(BusBase):
    id: int
    
    class Config:
        orm_mode = True


class BusWithAvailableSeats(BusResponse):
    available_seats: List[int]
