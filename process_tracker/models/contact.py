# SQLAlchemy Models
# Models for Contact entities

from sqlalchemy import Column, Integer, Sequence, String
from process_tracker.models.model_base import Base


class Contact(Base):

    __tablename__ = "contact_lkup"
    __table_args__ = {"schema": "process_tracker"}

    contact_id = Column(
        Integer,
        Sequence("contact_lkup_contact_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    contact_name = Column(String(250), nullable=False, unique=True)
    contact_email = Column(String(750), nullable=True, unique=True)

    def __repr__(self):
        return "<Contact id=%s, name=%s>" % (self.contact_id, self.contact_name)
