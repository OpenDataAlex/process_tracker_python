# SQLAlchemy Models
# Models for Process entities


from sqlalchemy import Column, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import Base, BaseColumn


class Cluster(Base, BaseColumn):

    __tablename__ = "cluster_tracking_lkup"
    __table_args__ = {"schema": "process_tracker"}

    cluster_id = Column(
        Integer,
        Sequence("cluster_tracking_lkup_cluster_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    cluster_name = Column(String(250), unique=True, nullable=False)
    cluster_max_memory = Column(Integer, nullable=True)
    cluster_max_memory_unit = Column(String(2), nullable=True)
    cluster_max_processing = Column(Integer, nullable=True)
    cluster_max_processing_unit = Column(String(3), nullable=True)
    cluster_current_memory_usage = Column(Integer)
    cluster_current_process_usage = Column(Integer)

    process_clusters = relationship("ClusterProcess", passive_deletes="all")

    def __repr__(self):

        return "<Cluster (name=%s)>" % self.cluster_name


class ClusterProcess(Base, BaseColumn):

    __tablename__ = "cluster_process"
    __table_args__ = {"schema": "process_tracker"}

    cluster_id = Column(
        Integer,
        ForeignKey("process_tracker.cluster_tracking_lkup.cluster_id"),
        primary_key=True,
        nullable=False,
    )
    process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )

    processes = relationship("Process", back_populates="cluster_processes")
    clusters = relationship("Cluster", back_populates="process_clusters")

    def __repr__(self):

        return "<ClusterProcess (cluster_id=%s, process_id=%s)" % (
            self.cluster_id,
            self.process_id,
        )
