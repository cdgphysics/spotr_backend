from typing import Optional
from sqlmodel import SQLModel, Field


class UserInterest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="spotruser.id")

    # days as comma-separated weekdays, e.g. "mon,tue,wed"
    days: Optional[str] = None

    # time range as HH:MM strings
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    # workout types as comma-separated values: weights,cardio,calisthenics,sports,other
    workout_types: Optional[str] = None

    # preferred partner/peer age range
    min_age: Optional[int] = None
    max_age: Optional[int] = None
