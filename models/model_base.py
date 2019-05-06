# Base Model class for other data models.

from dateutil import parser

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
default_date = parser.parse('1900-01-01 00:00:00')

