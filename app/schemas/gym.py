from typing import Optional
from sqlmodel import SQLModel


class GymBase(SQLModel):
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class GymCreate(GymBase):
    pass


class GymRead(GymBase):
    id: int
