from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database.session import create_db_and_tables
from app.routes.spotr_user import router as user_router
from app.routes.health import router as health_router
from app.routes.gym import router as gym_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting app…")
    # e.g., connect to DB, initialize cache
    await create_db_and_tables()
    app.include_router(user_router)
    app.include_router(health_router)
    app.include_router(gym_router)
    yield
    # Shutdown logic
    print("Stopping app…")


app = FastAPI(lifespan=lifespan)