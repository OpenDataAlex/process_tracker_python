# Base Model class for other data models.

from datetime import datetime
from dateutil import parser

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime

Base = declarative_base()
default_date = parser.parse("1900-01-01 00:00:00")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class BaseColumn(object):
    created_date_time = Column(DateTime, nullable=False, default=current_time)
    created_by = Column(DateTime, nullable=False, default=0)
    update_date_time = Column(
        DateTime, nullable=False, default=current_time, onupdate=current_time
    )
    updated_by = Column(DateTime, nullable=False, default=0)
