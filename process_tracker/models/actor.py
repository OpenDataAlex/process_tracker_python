# SQLAlchemy Models
# Models for Actor entities

from sqlalchemy import Column, Integer, Sequence, String
from process_tracker.models.model_base import Base


class Actor(Base):

    __tablename__ = "actor_lkup"

    actor_id = Column(Integer, Sequence('actor_lkup_actor_id_seq'), primary_key=True)
    actor_name = Column(String(250), nullable=False, unique=True)
