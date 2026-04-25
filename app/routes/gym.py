from fastapi import APIRouter
from sqlmodel import Session, select

from app.database.session import engine
from app.models.gym import Gym
from app.schemas.gym import GymRead

router = APIRouter(prefix="/gyms", tags=["gyms"])

@router.get("/", response_model=list[GymRead])
def list_gyms():
    with Session(engine) as session:
        statement = select(Gym)
        results = session.exec(statement).all()
        return results
