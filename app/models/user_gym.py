from typing import Optional
from sqlmodel import SQLModel, Field


class UserGym(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="spotruser.id")
    gym_id: int = Field(foreign_key="gym.id")
