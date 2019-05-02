# SQLAlchemy Models
# Models for Process entities

from dateutil import parser

from sqlalchemy import Column, ForeignKey, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import uuid

Base = declarative_base()
default_date = parser.parse('1900-01-01 00:00:00')


class ProcessType(Base):
    __tablename__ = 'process_type'



class Process(Base):
    __tablename__ = 'process'
    process_uuid = Column(uuid.UUIDType(binary=False), primary_key=True)
    process_name = Column(String(250), nullable=False, unique=True)
    latest_run_low_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
    latest_run_high_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
    latest_run_id = Column(Integer, nullable=False, default=0)
    latest_run_start_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
    latest_run_end_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
    latest_run_process_status = Column(Integer, nullable=False, default=0)
    latest_run_record_count = Column(Integer, nullable=False, default=0)
    total_record_count = Column(Integer, nullable=False, default=0)
    latest_run_actor_id = Column()
    process_type_id = Column()
    last_failed_run_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
