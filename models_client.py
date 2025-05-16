from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from database import Base

# Налаштування хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    phone_number = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Зв'язок з квитками
    tickets = relationship("Ticket", back_populates="client")
    
    def verify_password(self, plain_password):
        """Перевірка пароля."""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def get_password_hash(password):
        """Отримання хешу пароля."""
        return pwd_context.hash(password)
