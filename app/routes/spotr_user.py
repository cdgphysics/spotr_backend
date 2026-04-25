from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.dialects.postgresql import UUID

from app.database.session import engine
from app.models.spotr_user import SpotrUser
from app.models.gym import Gym
from app.models.user_gym import UserGym
from app.schemas.spotr_user import SpotrUserCreate, SpotrUserUpdate, SpotrUserRead
from app.schemas.gym import GymCreate, GymRead
from app.schemas.user_gym import UserGymCreate, UserGymRead

router = APIRouter(prefix="/spotr_user", tags=["spotr_user"])

@router.post("/spotr_user", response_model=SpotrUserRead)
def create_spotr_user(user: SpotrUserCreate):
    with Session(engine) as session:
        spotr_user = SpotrUser.model_validate(user)
        session.add(spotr_user)
        session.commit()
        session.refresh(spotr_user)
        return spotr_user

@router.get("/{id}", response_model=SpotrUserRead)
def get_spotr_user(id: int):
    with Session(engine) as session:
        spotr_user = session.get_one(SpotrUser.id, id)
        if not spotr_user:
            raise HTTPException(status_code=404, detail="User not found")
        return spotr_user

@router.patch("/{id}", response_model=SpotrUserRead)
def update_spotr_user(id: int, updated_spotr_user: SpotrUserUpdate):
    with Session(engine) as session:
        existing_spotr_user = session.get_one(SpotrUser.id, id)
        if not existing_spotr_user:
            raise HTTPException(status_code=404, detail="User not found")

        # model_dump --> turns the Pydantic/SQLModel object into a Python dict
        # exclude_unset = True --> if your request object doesn't include every field from SpotrUserUpdate
        # it won't append <fieldname> : None, it'll sanitize the object
        update_data = updated_spotr_user.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_spotr_user, key, value)

        # no need to run session.add(existing_spotr_user) since sqlAlchemy already keeps track of the changed
        # object and knows what fields change in that object based on setattr
        # commit flushes the changes and updates the DB
        session.commit()
        session.refresh(existing_spotr_user)
        return existing_spotr_user


@router.post("/{id}/gym", response_model=UserGymRead)
def add_gym_to_user(id: int, user_gym: UserGymCreate):
    with Session(engine) as session:
        gym_obj = session.get(Gym, user_gym.gym_id)
        if not gym_obj:
            raise HTTPException(status_code=404, detail="Gym not found")

        spotr_user = session.get_one(SpotrUser.id, id)
        if not spotr_user:
            raise HTTPException(status_code=404, detail="User not found")

        # create association via schema
        association = UserGym(user_id=spotr_user.id, gym_id=user_gym.gym_id)
        session.add(association)

        spotr_user.accountSetupComplete = "active"

        session.commit()
        session.refresh(association)
        return association


@router.get("/{id}/gyms", response_model=list[GymRead])
def list_user_gyms(id: int):
    with Session(engine) as session:
        statement = select(Gym).join(UserGym, Gym.id == UserGym.gym_id).where(UserGym.user_id == id)
        results = session.exec(statement).all()
        return results
