# SQLAlchemy Models
# Models for Process entities


from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import default_date, Base


class Cluster(Base):

    __tablename__ = "cluster_tracking"
    __table_args__ = {"schema": "process_tracker"}

    cluster_id = Column(
        Integer,
        Sequence("cluster_tracking_cluster_id_seq", schema="process_tracker"),
        primary_key=True,
    )
    cluster_name = Column(String(250), unique=True, nullable=False)
    cluster_max_memory = Column(Integer, nullable=False)
    cluster_max_memory_unit = Column(String(2), nullable=False)
    cluster_max_processing = Column(Integer, nullable=False)
    cluster_max_processing_unit = Column(String(3), nullable=False)
    cluster_current_memory_usage = Column(Integer)
    cluster_current_process_usage = Column(Integer)

    def __repr__(self):

        return "<Cluster (name=%s)>" % self.cluster_name


class ClusterProcess(Base):

    __tablename__ = "cluster_process"
    __table_args__ = {"schema": "process_tracker"}

    cluster_id = Column(
        Integer,
        ForeignKey("process_tracker.cluster_tracking.cluster_id"),
        primary_key=True,
    )
    process_id = Column(Integer, ForeignKey("process_tracker.process.process_id"))

    cluster_processes = relationship("Process", foreign_key=[process_id])
    process_clusters = relationship("Cluster", foreign_key=[cluster_id])

    def __repr__(self):

        return (
            "<ClusterProcess (cluster_id=%s, process_id=%s)" % self.cluster_id,
            self.process_id,
        )
