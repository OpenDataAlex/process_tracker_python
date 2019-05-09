# SQLAlchemy Models
# Models for Extract (Data) entities

from sqlalchemy import Column, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from models.model_base import Base


class ExtractStatus(Base):

    __tablename__ = "extract_status_lkup"

    extract_status_id = Column(Integer, Sequence('extract_status_lkup_status_id_seq'), primary_key=True)
    extract_status_name = Column(String(75), nullable=False, unique=True)

    extracts = relationship("Extract")


class Extract(Base):

    __tablename__ = "extract_tracking"

    extract_id = Column(Integer, Sequence('extract_tracking_extract_id_seq'), primary_key=True)
    extract_source_id = Column(Integer, ForeignKey("source_lkup.source_id"))
    extract_filename = Column(String(750), nullable=False, unique=True)
    extract_location_id = Column(Integer, ForeignKey('location_lkup.location_id'))
    extract_process_run_id = Column(Integer, ForeignKey('process_tracking.process_tracking_id'))
    extract_status_id = Column(Integer, ForeignKey('extract_status_lkup.extract_status_id'))

    process_tracking = relationship("ProcessTracking")


class Location(Base):

    __tablename__ = "location_lkup"

    location_id = Column(Integer, Sequence('location_lkup_location_id_seq'), primary_key=True)
    location_name = Column(String(750), nullable=False, unique=True)
    location_path = Column(String(750), nullable=False, unique=True)

    extracts = relationship("Extract")
