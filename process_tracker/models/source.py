# SQLAlchemy Models
# Models for Source entities

from sqlalchemy import Column, Integer, Sequence, String

from process_tracker.models.model_base import Base


class Source(Base):

    __tablename__ = "source_lkup"

    source_id = Column(Integer, Sequence('source_lkup_source_id_seq'), primary_key=True)
    source_name = Column(String(250), nullable=False, unique=True)

    def __repr__(self):

        return "<Source (name=%s)>" % self.source_name
