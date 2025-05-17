from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.bus import Bus
from models.route import Route
from models.ticket import Ticket
from schemas.bus import BusCreate, BusResponse, BusWithAvailableSeats
from utils.auth import get_current_client

router = APIRouter(prefix="/buses", tags=["buses"])


@router.post("/", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
def create_bus(
    bus: BusCreate,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)  # Для адміністративного доступу
):
    """Створення нового автобуса (тільки для адміністраторів)."""
    # Перевірка унікальності реєстраційного номеру
    existing_bus = db.query(Bus).filter(Bus.registration_number == bus.registration_number).first()
    if existing_bus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Автобус з таким реєстраційним номером вже існує"
        )
    
    # Створення автобуса
    db_bus = Bus(
        registration_number=bus.registration_number,
        model=bus.model,
        capacity=bus.capacity,
        is_active=bus.is_active
    )
    
    db.add(db_bus)
    db.commit()
    db.refresh(db_bus)
    
    return db_bus


@router.get("/", response_model=List[BusResponse])
def get_buses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Отримання списку всіх автобусів."""
    buses = db.query(Bus).filter(Bus.is_active == True).offset(skip).limit(limit).all()
    return buses


@router.get("/{bus_id}", response_model=BusResponse)
def get_bus(
    bus_id: int,
    db: Session = Depends(get_db)
):
    """Отримання інформації про конкретний автобус."""
    bus = db.query(Bus).filter(Bus.id == bus_id, Bus.is_active == True).first()
    
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Автобус не знайдено"
        )
    
    return bus


@router.get("/{bus_id}/seats", response_model=BusWithAvailableSeats)
def get_bus_available_seats(
    bus_id: int,
    route_id: int,
    travel_date: str,  # Формат: "YYYY-MM-DD"
    db: Session = Depends(get_db)
):
    """Отримання списку доступних місць в автобусі на конкретну дату та маршрут."""
    # Перевірка існування автобуса
    bus = db.query(Bus).filter(Bus.id == bus_id, Bus.is_active == True).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Автобус не знайдено"
        )
    
    # Перевірка існування маршруту
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Маршрут не знайдено"
        )
    
    # Отримання зайнятих місць
    occupied_seats = [
        ticket.seat_number for ticket in db.query(Ticket).filter(
            Ticket.bus_id == bus_id,
            Ticket.route_id == route_id,
            Ticket.travel_date.like(f"{travel_date}%"),  # Порівняння з датою
            Ticket.is_active == True
        ).all()
    ]
    
    # Розрахунок доступних місць
    all_seats = list(range(1, bus.capacity + 1))
    available_seats = [seat for seat in all_seats if seat not in occupied_seats]
    
    # Створення відповіді
    response = {**bus.__dict__}
    response["available_seats"] = available_seats
    
    return response


@router.put("/{bus_id}", response_model=BusResponse)
def update_bus(
    bus_id: int,
    bus_update: BusCreate,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)  # Для адміністративного доступу
):
    """Оновлення інформації про автобус (тільки для адміністраторів)."""
    db_bus = db.query(Bus).filter(Bus.id == bus_id).first()
    
    if not db_bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Автобус не знайдено"
        )
    
    # Перевірка унікальності реєстраційного номеру
    if bus_update.registration_number != db_bus.registration_number:
        existing_bus = db.query(Bus).filter(
            Bus.registration_number == bus_update.registration_number
        ).first()
        
        if existing_bus:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Автобус з таким реєстраційним номером вже існує"
            )
    
    # Оновлення даних
    db_bus.registration_number = bus_update.registration_number
    db_bus.model = bus_update.model
    db_bus.capacity = bus_update.capacity
    db_bus.is_active = bus_update.is_active
    
    db.commit()
    db.refresh(db_bus)
    
    return db_bus


@router.delete("/{bus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)  # Для адміністративного доступу
):
    """Видалення автобуса (тільки для адміністраторів)."""
    db_bus = db.query(Bus).filter(Bus.id == bus_id).first()
    
    if not db_bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Автобус не знайдено"
        )
    
    # Деактивація замість видалення
    db_bus.is_active = False
    
    db.commit()
    
    return None