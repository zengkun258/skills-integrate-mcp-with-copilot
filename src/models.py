from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    activity_id: Optional[int] = Field(default=None, foreign_key="activity.id")
    # back-populates defined on Activity


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: int = 0
    participants: List[Participant] = Relationship(back_populates="activity")


# establish reverse relationship
Participant.__config__ = getattr(Participant, "__config__", None)
setattr(Participant, "activity", Relationship(back_populates="participants"))
