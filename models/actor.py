# SQLAlchemy Models
# Models for Actor entities

from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy_utils.types import uuid
from models.model_base import Base


class Actor(Base):

    __tablename__ = "actor_lkup"

    actor_uuid = Column(uuid.UUIDType, primary_key=True)
    actor_name = Column(String(250), nullable=False, unique=True)
