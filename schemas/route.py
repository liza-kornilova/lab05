from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RouteBase(BaseModel):
    name: str
    description: Optional[str] = None
    bus_id: int
    departure_time: datetime
    arrival_time: datetime
    stations: List[str]


class RouteCreate(RouteBase):
    pass


class RouteResponse(RouteBase):
    id: int
    
    class Config:
        orm_mode = True
        from_attributes = True


class RouteWithAvailableSeats(RouteResponse):
    available_seats: List[int]