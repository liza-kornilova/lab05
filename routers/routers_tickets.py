from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import threading
import uuid

from database import get_db
from models import Ticket, Route, SeatReservation, Bus
from schemas.ticket import (
    TicketCreate, 
    TicketResponse, 
    TicketsBulkResponse,
    SeatReservationCreate,
    SeatReservationResponse
)
from utils.auth import get_current_client

router = APIRouter(prefix="/tickets", tags=["tickets"])

# Семафор для безпечного доступу до блокування місць
seat_lock = threading.Lock()


@router.post("/reserve-seat", response_model=SeatReservationResponse)
def reserve_seat(
    reservation: SeatReservationCreate,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)
):
    """Тимчасове блокування місця під час процесу купівлі квитка."""
    # Перевірка існування маршруту
    route = db.query(Route).filter(Route.id == reservation.route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Маршрут не знайдено"
        )
    
    # Перевірка існування автобуса
    bus = db.query(Bus).filter(Bus.id == reservation.bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Автобус не знайдено"
        )
    
    # Перевірка чи номер місця в межах кількості місць в автобусі
    if reservation.seat_number <= 0 or reservation.seat_number > bus.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неправильний номер місця. Доступні місця від 1 до {bus.capacity}"
        )
    
    # Блокування для безпечного доступу до місць
    with seat_lock:
        # Перевірка чи місце вже заброньоване або зайняте
        existing_ticket = db.query(Ticket).filter(
            Ticket.route_id == reservation.route_id,
            Ticket.travel_date == reservation.travel_date,
            Ticket.seat_number == reservation.seat_number,
            Ticket.is_active == True
        ).first()
        
        if existing_ticket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Це місце вже зайняте"
            )
        
        # Перевірка чи місце вже заблоковане
        existing_reservation = db.query(SeatReservation).filter(
            SeatReservation.route_id == reservation.route_id,
            SeatReservation.bus_id == reservation.bus_id,
            SeatReservation.seat_number == reservation.seat_number,
            SeatReservation.is_active == True,
            SeatReservation.expiry_time > datetime.utcnow()
        ).first()
        
        if existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Це місце зараз блокується іншим користувачем"
            )
        
        # Створення блокування місця на 10 хвилин
        reservation_time = datetime.utcnow()
        expiry_time = reservation_time + timedelta(minutes=10)
        
        # Створення нового тимчасового блокування
        new_reservation = SeatReservation(
            bus_id=reservation.bus_id,
            route_id=reservation.route_id,
            seat_number=reservation.seat_number,
            reservation_time=reservation_time,
            expiry_time=expiry_time,
            is_active=True
        )
        
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
        
        return new_reservation


def cancel_reservation(reservation_id: int, db: Session):
    """Скасування блокування місця."""
    reservation = db.query(SeatReservation).filter(
        SeatReservation.id == reservation_id
    ).first()
    
    if reservation:
        reservation.is_active = False
        db.commit()


@router.post("/buy", response_model=TicketsBulkResponse)
def buy_tickets(
    ticket_data: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)
):
    """Купівля одного або декількох квитків."""
    # Перевірка існування маршруту
    route = db.query(Route).filter(Route.id == ticket_data.route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Маршрут не знайдено"
        )
    
    # Перевірка станцій відправлення та прибуття
    if ticket_data.departure_station not in route.stations or ticket_data.arrival_station not in route.stations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вказані станції не належать до маршруту"
        )
    
    # Перевірка порядку станцій
    stations = route.stations
    dep_index = stations.index(ticket_data.departure_station)
    arr_index = stations.index(ticket_data.arrival_station)
    
    if dep_index >= arr_index:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Станція відправлення має бути раніше станції прибуття"
        )
    
    # Отримання автобуса для маршруту
    bus = db.query(Bus).filter(Bus.id == route.bus_id).first()
    
    # Перевірка доступності місць
    with seat_lock:
        purchased_tickets = []
        reservations_to_cancel = []
        total_price = 0.0  # Базова ціна для квитка
        
        # Перевірка всіх місць на доступність
        for seat_number in ticket_data.seats:
            # Перевірка чи місце вже зайняте
            existing_ticket = db.query(Ticket).filter(
                Ticket.route_id == ticket_data.route_id,
                Ticket.travel_date == ticket_data.travel_date,
                Ticket.seat_number == seat_number,
                Ticket.is_active == True
            ).first()
            
            if existing_ticket:
                # Скасування всіх створених блокувань
                for res_id in reservations_to_cancel:
                    cancel_reservation(res_id, db)
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Місце {seat_number} вже зайняте"
                )
            
            # Створення блокування місця
            reservation = SeatReservation(
                bus_id=bus.id,
                route_id=ticket_data.route_id,
                seat_number=seat_number,
                reservation_time=datetime.utcnow(),
                expiry_time=datetime.utcnow() + timedelta(minutes=10),
                is_active=True
            )
            
            db.add(reservation)
            db.flush()  # Оновлення ID резервації
            reservations_to_cancel.append(reservation.id)
        
        # Створення квитків
        for seat_number in ticket_data.seats:
            ticket = Ticket(
                client_id=current_client.id,
                route_id=ticket_data.route_id,
                bus_id=bus.id,
                departure_station=ticket_data.departure_station,
                arrival_station=ticket_data.arrival_station,
                seat_number=seat_number,
                purchase_date=datetime.utcnow(),
                travel_date=ticket_data.travel_date,
                is_active=True
            )
            
            db.add(ticket)
            db.flush()  # Оновлення ID квитка
            purchased_tickets.append(ticket)
            
            # Розрахунок ціни (наприклад, на основі відстані між станціями)
            price_per_ticket = 50.0 + (arr_index - dep_index) * 10.0  # Приклад розрахунку ціни
            total_price += price_per_ticket
        
        # Деактивація всіх блокувань
        for res_id in reservations_to_cancel:
            background_tasks.add_task(cancel_reservation, res_id, db)
        
        # Збереження змін
        db.commit()
        
        # Оновлення квитків після збереження
        for ticket in purchased_tickets:
            db.refresh(ticket)
        
        return {
            "tickets": purchased_tickets,
            "total_price": total_price
        }


@router.get("/my", response_model=List[TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client),
    skip: int = 0,
    limit: int = 100
):
    """Отримання списку квитків поточного користувача."""
    tickets = db.query(Ticket).filter(
        Ticket.client_id == current_client.id,
        Ticket.is_active == True
    ).offset(skip).limit(limit).all()
    
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)
):
    """Отримання інформації про конкретний квиток."""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.client_id == current_client.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Квиток не знайдено"
        )
    
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_client = Depends(get_current_client)
):
    """Скасування квитка."""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.client_id == current_client.id,
        Ticket.is_active == True
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Квиток не знайдено"
        )
    
    # Перевірка чи можна скасувати квиток (наприклад, якщо до відправлення більше 24 годин)
    time_to_departure = ticket.travel_date - datetime.utcnow()
    if time_to_departure.total_seconds() < 24 * 60 * 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Квиток можна скасувати тільки за 24 години до відправлення"
        )
    
    # Скасування квитка
    ticket.is_active = False
    db.commit()
    
    return None