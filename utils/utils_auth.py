from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.client import Client

# Налаштування JWT
SECRET_KEY = "ваш_секретний_ключ"  # В реальному проекті зберігайте в .env файлі
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Залежність для отримання токену
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Створення JWT токену."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def authenticate_client(db: Session, username: str, password: str):
    """Аутентифікація клієнта по логіну та паролю."""
    client = db.query(Client).filter(Client.username == username).first()
    
    if not client or not client.verify_password(password):
        return None
    
    return client


async def get_current_client(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """Отримання поточного аутентифікованого клієнта."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неможливо перевірити облікові дані",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодування токена
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Отримання клієнта з бази даних
    client = db.query(Client).filter(Client.username == username).first()
    
    if client is None:
        raise credentials_exception
    
    return client
