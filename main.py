from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import auth, buses, routes, tickets

# Створення таблиць в базі даних
Base.metadata.create_all(bind=engine)

# Створення екземпляру FastAPI
app = FastAPI(
    title="API компанії перевізника",
    description="API для роботи з компанією перевізником. Дозволяє купувати квитки на автобуси.",
    version="1.0.0",
)

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшен-режимі обмежте конкретними доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення роутерів
app.include_router(auth.router)
app.include_router(buses.router)
app.include_router(routes.router)
app.include_router(tickets.router)


@app.get("/")
def read_root():
    """Базовий ендпоінт для перевірки працездатності API."""
    return {
        "message": "API компанії перевізника працює",
        "docs": "/docs",
        "redoc": "/redoc"
    }
