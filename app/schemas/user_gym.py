from sqlmodel import SQLModel


class UserGymBase(SQLModel):
    user_id: int
    gym_id: int


class UserGymCreate(UserGymBase):
    pass


class UserGymRead(UserGymBase):
    id: int
