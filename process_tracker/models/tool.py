# SQLAlchemy Models
# Models for Tool entities

from sqlalchemy import Column, Integer, Sequence, String

from process_tracker.models.model_base import Base, BaseColumn


class Tool(Base, BaseColumn):

    __tablename__ = "tool_lkup"
    __table_args__ = {"schema": "process_tracker"}

    tool_id = Column(
        Integer,
        Sequence("tool_lkup_tool_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    tool_name = Column(String(250), nullable=False, unique=True)

    def __repr__(self):

        return "<Tool (name=%s)>" % self.tool_name
