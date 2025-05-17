from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import uuid

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey("clients.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    bus_id = Column(Integer, ForeignKey("buses.id"))
    departure_station = Column(String)  # Станція відправлення
    arrival_station = Column(String)    # Станція прибуття
    seat_number = Column(Integer)       # Номер місця
    purchase_date = Column(DateTime)    # Дата покупки
    travel_date = Column(DateTime)      # Дата подорожі
    is_active = Column(Boolean, default=True)
    
    # Зв'язок з клієнтом, маршрутом та автобусом
    client = relationship("Client", back_populates="tickets")
    route = relationship("Route", back_populates="tickets")
    bus = relationship("Bus", back_populates="tickets")
    
    # Зв'язок з бронюванням місця
    seat_reservation = relationship("SeatReservation", back_populates="ticket", uselist=False)


class SeatReservation(Base):
    """Модель для блокування місця під час оформлення квитка."""
    __tablename__ = "seat_reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), unique=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    seat_number = Column(Integer)
    reservation_time = Column(DateTime)  # Час початку блокування
    expiry_time = Column(DateTime)       # Час закінчення блокування
    is_active = Column(Boolean, default=True)
    
    # Зв'язок з квитком
    ticket = relationship("Ticket", back_populates="seat_reservation")