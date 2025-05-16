from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String, unique=True, index=True)
    model = Column(String)
    capacity = Column(Integer)  # кількість місць в автобусі
    is_active = Column(Boolean, default=True)
    
    # Зв'язок з маршрутами та квитками
    routes = relationship("Route", back_populates="bus")
    tickets = relationship("Ticket", back_populates="bus")
