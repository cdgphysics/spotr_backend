from typing import Optional
from sqlmodel import SQLModel, Field


class Gym(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
