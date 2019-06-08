# SQLAlchemy Models
# Models for System entities

from sqlalchemy import Column, Integer, Sequence, String

from process_tracker.models.model_base import Base


class System(Base):

    __tablename__ = "system_lkup"
    __table_args__ = {"schema": "process_tracker"}

    system_id = Column(
        Integer,
        Sequence("system_lkup_system_id_seq", schema="process_tracker"),
        primary_key=True,
    )
    system_key = Column(String(250), nullable=False, unique=True)
    system_value = Column(String(250), nullable=False)

    def __repr__(self):

        return "<System (system_key=%s)>" % self.system_key
