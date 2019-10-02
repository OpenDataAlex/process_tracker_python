# SQLAlchemy Models
# Models for Schedule entities


from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import default_date, Base


class ScheduleFrequency(Base):

    __tablename__ = "schedule_frequency_lkup"
    __table_args__ = {"schema": "process_tracker"}

    schedule_frequency_id = Column(
        Integer,
        Sequence("schedule_frequency_schedule_frequency_id", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    schedule_frequency_name = Column(String(25), unique=True, nullable=False)
