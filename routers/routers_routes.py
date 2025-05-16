from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import Route, Bus, Ticket
from schemas.route import RouteCreate, RouteResponse, RouteWithAvailableSeats
from utils.auth import get_current_client

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)  # Для адміністративного доступу
):
    """Створення нового маршруту (тільки для адміністраторів)."""
    # Перевірка наявності автобуса
    bus = db.query(Bus).filter(Bus.id == route.bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Автобус не знайдено"
        )
    
    # Створення маршруту
    db_route = Route(
        name=route.name,
        description=route.description,
        bus_id=route.bus_id,
        departure_time=route.departure_time,
        arrival_time=route.arrival_time,
        stations=route.stations
    )
    
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    
    return db_route


@router.get("/", response_model=List[RouteResponse])
def get_routes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Отримання списку всіх маршрутів."""
    routes = db.query(Route).offset(skip).limit(limit).all()
    return routes


@router.get("/{route_id}", response_model=RouteWithAvailableSeats)
def get_route(
    route_id: int,
    travel_date: datetime,
    db: Session = Depends(get_db)
):
    """Отримання маршруту по ID з доступними місцями на вказану дату."""
    route = db.query(Route).filter(Route.id == route_id).first()
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Маршрут не знайдено"
        )
    
    # Отримання автобуса
    bus = db.query(Bus).filter(Bus.id == route.bus_id).first()
    
    # Отримання зайнятих місць на цю дату
    occupied_seats = [
        ticket.seat_number for ticket in db.query(Ticket).filter(
            Ticket.route_id == route_id,
            Ticket.travel_date == travel_date,
            Ticket.is_active == True
        ).all()
    ]
    
    # Розрахунок доступних місць
    all_seats = list(range(1, bus.capacity + 1))
    available_seats = [seat for seat in all_seats if seat not in occupied_seats]
    
    # Додавання доступних місць до відповіді
    route_with_seats = {**route.__dict__}
    route_with_seats["available_seats"] = available_seats
    
    return route_with_seats


@router.get("/by-stations", response_model=List[RouteResponse])
def get_routes_by_stations(
    departure_station: str,
    arrival_station: str,
    travel_date: datetime,
    db: Session = Depends(get_db)
):
    """Пошук маршрутів за станціями відправлення та прибуття."""
    # Отримання всіх маршрутів
    routes = db.query(Route).all()
    
    # Фільтрація маршрутів за станціями
    matching_routes = []
    for route in routes:
        stations = route.stations
        if departure_station in stations and arrival_station in stations:
            # Перевірка порядку станцій (відправлення має бути раніше прибуття)
            dep_index = stations.index(departure_station)
            arr_index = stations.index(arrival_station)
            
            if dep_index < arr_index:
                matching_routes.append(route)
    
    return matching_routes
