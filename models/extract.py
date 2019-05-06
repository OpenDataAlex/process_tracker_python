# SQLAlchemy Models
# Models for Extract (Data) entities

from sqlalchemy import Column, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from models.model_base import Base


class Extract(Base):

    __tablename__ = "extract_tracking"

    extract_id = Column(Integer, Sequence('extract_tracking_extract_id_seq01'), primary_key=True)
    extract_source_id = Column(Integer, ForeignKey("source_lkup.source_id"))
    extract_filename = Column(String(750), nullable=False, unique=True)
    extract_location_id = Column(Integer, ForeignKey('location_lkup.location_id'))


class Location(Base):

    __tablename__ = "location_lkup"

    location_id = Column(Integer, Sequence('location_lkup_location_id_seq01'), primary_key=True)
    location_name = Column(String(250), nullable=False, unique=True)
    location_path = Column(String(250), nullable=False, unique=True)

    extracts = relationship("Extract")
