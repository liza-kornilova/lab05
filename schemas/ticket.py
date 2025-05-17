from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TicketBase(BaseModel):
    route_id: int
    departure_station: str
    arrival_station: str
    travel_date: datetime


class TicketCreate(TicketBase):
    seats: List[int]  # Список номерів місць для бронювання


class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    client_id: int
    bus_id: int
    seat_number: int
    purchase_date: datetime
    is_active: bool
    
    class Config:
        orm_mode = True
        from_attributes = True


class TicketsBulkResponse(BaseModel):
    tickets: List[TicketResponse]
    total_price: float


class SeatReservationCreate(BaseModel):
    route_id: int
    bus_id: int
    seat_number: int
    travel_date: datetime


class SeatReservationResponse(BaseModel):
    id: int
    bus_id: int
    route_id: int
    seat_number: int
    reservation_time: datetime
    expiry_time: datetime
    is_active: bool
    
    class Config:
        orm_mode = True
        from_attributes = True