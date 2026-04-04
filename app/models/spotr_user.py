from typing import Optional
from sqlmodel import Field

from app.schemas.spotr_user import SpotrUserBase


class SpotrUser(SpotrUserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    #gym FK will be here
    # user doesn't need a gym but they can't see anybody
    # can't message either