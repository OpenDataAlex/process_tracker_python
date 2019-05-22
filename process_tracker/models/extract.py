# SQLAlchemy Models
# Models for Extract (Data) entities

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import Base


class ExtractStatus(Base):

    __tablename__ = "extract_status_lkup"

    extract_status_id = Column(Integer, Sequence('extract_status_lkup_extract_status_id_seq'), primary_key=True)
    extract_status_name = Column(String(75), nullable=False, unique=True)

    extracts = relationship("ExtractProcess")


class Extract(Base):

    __tablename__ = "extract_tracking"

    extract_id = Column(Integer, Sequence('extract_tracking_extract_id_seq'), primary_key=True)
    extract_filename = Column(String(750), nullable=False, unique=True)
    extract_location_id = Column(Integer, ForeignKey('location_lkup.location_id'))
    extract_status_id = Column(Integer, ForeignKey('extract_status_lkup.extract_status_id'))
    extract_registration_date_time = Column(DateTime, nullable=False, default=datetime.now())

    extract_process = relationship("ExtractProcess", back_populates='process_extracts')
    locations = relationship("Location", foreign_keys=[extract_location_id])


class ExtractProcess(Base):

    __tablename__ = "extract_process_tracking"

    extract_tracking_id = Column(Integer, ForeignKey("extract_tracking.extract_id"), primary_key=True)
    process_tracking_id = Column(Integer, ForeignKey("process_tracking.process_tracking_id"), primary_key=True)
    extract_process_status_id = Column(Integer, ForeignKey("extract_status_lkup.extract_status_id"))
    extract_process_event_date_time = Column(DateTime, nullable=False, default=datetime.now())

    process_extracts = relationship('Extract', foreign_keys=[extract_tracking_id])
    extract_processes = relationship('ProcessTracking', foreign_keys=[process_tracking_id])


class LocationType(Base):

    __tablename__ = "location_type_lkup"

    location_type_id = Column(Integer, Sequence('location_type_lkup_location_type_id_seq'), primary_key=True)
    location_type_name = Column(String(25), unique=True, nullable=False)

    locations = relationship('Location', back_populates='location_types')
    

class Location(Base):

    __tablename__ = "location_lkup"

    location_id = Column(Integer, Sequence('location_lkup_location_id_seq'), primary_key=True)
    location_name = Column(String(750), nullable=False, unique=True)
    location_path = Column(String(750), nullable=False, unique=True)
    location_type = Column(Integer, ForeignKey("location_type_lkup.location_type_id"))

    extracts = relationship("Extract")

    location_types = relationship('LocationType', foreign_keys=[location_type])
