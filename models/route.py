from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    stations = Column(JSON)  # Зберігає список станцій маршруту як JSON
    
    # Зв'язок з автобусом та квитками
    bus = relationship("Bus", back_populates="routes")
    tickets = relationship("Ticket", back_populates="route")