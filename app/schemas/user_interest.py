from typing import Optional
from sqlmodel import SQLModel


class UserInterestBase(SQLModel):
    user_id: int
    days: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    workout_types: Optional[list[str]] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None


class UserInterestCreate(UserInterestBase):
    pass


class UserInterestRead(UserInterestBase):
    id: int
