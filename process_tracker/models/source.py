# SQLAlchemy Models
# Models for Source entities

from sqlalchemy import Column, ForeignKey, Integer, Sequence, String, UniqueConstraint
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import Base


class Source(Base):

    __tablename__ = "source_lkup"
    __table_args__ = {"schema": "process_tracker"}

    source_id = Column(
        Integer,
        Sequence("source_lkup_source_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    source_name = Column(String(250), nullable=False, unique=True)

    def __repr__(self):

        return "<Source (name=%s)>" % self.source_name


class SourceObject(Base):

    __tablename__ = "source_object_lkup"
    __table_args__ = {"schema": "process_tracker"}

    source_object_id = Column(
        Integer,
        Sequence("source_object_lkup_source_object_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    source_id = Column(
        Integer, ForeignKey("process_tracker.source_lkup.source_id"), nullable=False
    )
    source_object_name = Column(String(250), nullable=False)

    UniqueConstraint(source_id, source_object_name)

    source_processes = relationship(
        "ProcessSourceObject", back_populates="objects", passive_deletes="all"
    )
    target_processes = relationship(
        "ProcessTargetObject", back_populates="objects", passive_deletes="all"
    )

    def __repr__(self):

        return "<SourceObject (source_id=%s, source_object_name=%s)>" % (
            self.source_id,
            self.source_object_name,
        )
