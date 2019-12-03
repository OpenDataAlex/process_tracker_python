# SQLAlchemy Models
# Models for Schedule entities


from sqlalchemy import Column, Integer, Sequence, String

from process_tracker.models.model_base import Base


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
