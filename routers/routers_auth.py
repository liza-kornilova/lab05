from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from models.client import Client
from schemas.client import ClientCreate, ClientResponse
from utils.auth import authenticate_client, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def register_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Реєстрація нового клієнта."""
    # Перевірка, чи існує клієнт з таким username або email
    db_client = db.query(Client).filter(
        (Client.username == client.username) | (Client.email == client.email)
    ).first()
    
    if db_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Клієнт з таким іменем користувача або email вже існує",
        )
    
    # Створення нового клієнта
    hashed_password = Client.get_password_hash(client.password)
    db_client = Client(
        username=client.username,
        email=client.email,
        hashed_password=hashed_password,
        full_name=client.full_name,
        phone_number=client.phone_number,
    )
    
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    return db_client


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Авторизація клієнта та отримання JWT токену."""
    client = authenticate_client(db, form_data.username, form_data.password)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірне ім'я користувача або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Створення JWT токену
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": client.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
