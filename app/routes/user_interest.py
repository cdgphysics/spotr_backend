from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
import json

from app.database.session import engine
from app.models.user_interest import UserInterest
from app.schemas.user_interest import UserInterestCreate, UserInterestRead
from app.models.spotr_user import SpotrUser

router = APIRouter(prefix="/user_interest", tags=["user_interest"])

@router.post("/", response_model=UserInterestRead)
def create_user_interest(interest: UserInterestCreate):
    with Session(engine) as session:
        # validate user exists
        user = session.get(SpotrUser, interest.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        data = interest.model_dump()
        if data.get("workout_types") is not None:
            data["workout_types"] = json.dumps(data["workout_types"])

        ui = UserInterest(**data)
        session.add(ui)
        session.commit()
        session.refresh(ui)

        ui_dict = ui.model_dump()
        if ui_dict.get("workout_types") is not None:
            ui_dict["workout_types"] = json.loads(ui_dict["workout_types"])
        return ui_dict


@router.get("/{id}", response_model=UserInterestRead)
def get_user_interest(id: int):
    with Session(engine) as session:
        ui = session.get(UserInterest, id)
        if not ui:
            raise HTTPException(status_code=404, detail="UserInterest not found")

        ui_dict = ui.model_dump()
        if ui_dict.get("workout_types") is not None:
            ui_dict["workout_types"] = json.loads(ui_dict["workout_types"])
        return ui_dict


@router.get("/user/{user_id}", response_model=list[UserInterestRead])
def list_user_interests(user_id: int):
    with Session(engine) as session:
        statement = select(UserInterest).where(UserInterest.user_id == user_id)
        results = session.exec(statement).all()

        out = []
        for ui in results:
            ui_dict = ui.model_dump()
            if ui_dict.get("workout_types") is not None:
                ui_dict["workout_types"] = json.loads(ui_dict["workout_types"])
            out.append(ui_dict)
        return out
