# SQLAlchemy Models
# Models for Tool entities

from sqlalchemy import Column, Integer, Sequence, String

from process_tracker.models.model_base import Base


class Tool(Base):

    __tablename__ = "tool_lkup"

    tool_id = Column(Integer, Sequence('tool_lkup_tool_id_seq'), primary_key=True)
    tool_name = Column(String(250), nullable=False, unique=True)

    def __repr__(self):

        return "<Tool (name=%s)>" % self.tool_name
