# SQLAlchemy Models
# Models for Process entities


from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import default_date, Base


class ErrorType(Base):

    __tablename__ = "error_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    error_type_id = Column(
        Integer,
        Sequence("error_type_lkup_error_type_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    error_type_name = Column(String(250), unique=True, nullable=False)

    process_errors = relationship("ErrorTracking", passive_deletes="all")

    def __repr__(self):

        return "<ErrorType (name=%s)>" % self.error_type_name


class ErrorTracking(Base):

    __tablename__ = "error_tracking"
    __table_args__ = {"schema": "process_tracker"}

    error_tracking_id = Column(
        Integer,
        Sequence("error_tracking_error_tracking_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    error_type_id = Column(
        Integer,
        ForeignKey("process_tracker.error_type_lkup.error_type_id"),
        nullable=False,
    )
    error_description = Column(String(750))
    error_occurrence_date_time = Column(DateTime, nullable=False)
    process_tracking_id = Column(
        Integer,
        ForeignKey("process_tracker.process_tracking.process_tracking_id"),
        nullable=False,
    )

    error_tracking = relationship("ProcessTracking")

    def __repr__(self):

        return (
            "<ErrorTracking (id=%s, type=%s, description=%s"
            ", occurrence_date=%s)>"
            % (
                self.error_tracking_id,
                self.error_type_id,
                self.error_description,
                self.error_occurrence_date_time,
            )
        )


class ProcessStatus(Base):

    __tablename__ = "process_status_lkup"
    __table_args__ = {"schema": "process_tracker"}

    process_status_id = Column(
        Integer,
        Sequence("process_status_lkup_process_status_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    process_status_name = Column(String(75), nullable=False, unique=True)

    process_runs = relationship("ProcessTracking")

    def __repr__(self):

        return "<ProcessStatus (id=%s, process_status_name=%s)>" % (
            self.process_status_id,
            self.process_status_name,
        )


class ProcessType(Base):

    __tablename__ = "process_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    process_type_id = Column(
        Integer,
        Sequence("process_type_lkup_process_type_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    process_type_name = Column(String(250), nullable=False)

    processes = relationship("Process", passive_deletes="all")

    def __repr__(self):

        return "<ProcessType (id=%s, process_type=%s)>" % (
            self.process_type_id,
            self.process_type_name,
        )


class Process(Base):

    __tablename__ = "process"
    __table_args__ = {"schema": "process_tracker"}

    process_id = Column(
        Integer,
        Sequence("process_process_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    process_name = Column(String(250), nullable=False, unique=True)
    total_record_count = Column(Integer, nullable=False, default=0)
    process_type_id = Column(
        Integer,
        ForeignKey("process_tracker.process_type_lkup.process_type_id"),
        nullable=False,
    )
    process_tool_id = Column(
        Integer, ForeignKey("process_tracker.tool_lkup.tool_id"), nullable=False
    )
    last_failed_run_date_time = Column(
        DateTime(timezone=True), nullable=False, default=default_date
    )

    cluster_processes = relationship("ClusterProcess", passive_deletes="all")
    process_tracking = relationship("ProcessTracking", passive_deletes="all")
    process_type = relationship("ProcessType", back_populates="processes")
    sources = relationship("ProcessSource", passive_deletes="all")
    targets = relationship("ProcessTarget", passive_deletes="all")
    tool = relationship("Tool")

    def __repr__(self):

        return "<Process (id=%s, name=%s, type=%s)>" % (
            self.process_id,
            self.process_name,
            self.process_type_id,
        )


class ProcessDatasetType(Base):

    __tablename__ = "process_dataset_type"
    __table_args__ = {"schema": "process_tracker"}

    process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )
    dataset_type_id = Column(
        Integer,
        ForeignKey("process_tracker.dataset_type_lkup.dataset_type_id"),
        primary_key=True,
        nullable=False,
    )

    UniqueConstraint(process_id, dataset_type_id)

    dataset_type_processes = relationship("Process", passive_deletes="all")
    process_dataset_types = relationship("DatasetType", passive_deletes="all")

    def __repr__(self):

        return "<ProcessDatasetType process_id=%s, dataset_type_id=%s>" % (
            self.process_id,
            self.dataset_type_id,
        )


class ProcessSource(Base):

    __tablename__ = "process_source"
    __table_args__ = {"schema": "process_tracker"}

    source_id = Column(
        Integer,
        ForeignKey("process_tracker.source_lkup.source_id"),
        primary_key=True,
        nullable=False,
    )
    process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )

    processes = relationship("Process")
    sources = relationship("Source")

    def __repr__(self):

        return "<ProcessSource (process=%s, source=%s)>" % (
            self.process_id,
            self.source_id,
        )


class ProcessSourceObject(Base):
    __tablename__ = "process_source_object"
    __table_args__ = {"schema": "process_tracker"}

    process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )
    source_object_id = Column(
        Integer,
        ForeignKey("process_tracker.source_object_lkup.source_object_id"),
        primary_key=True,
        nullable=False,
    )

    objects = relationship("SourceObject")
    processes = relationship("Process")

    def __repr__(self):
        return "<ProcessSourceObject (process_id=%s, source_object=%s)>" % (
            self.process_id,
            self.source_object_id,
        )


class ProcessTarget(Base):
    __tablename__ = "process_target"
    __table_args__ = {"schema": "process_tracker"}

    target_source_id = Column(
        Integer,
        ForeignKey("process_tracker.source_lkup.source_id"),
        primary_key=True,
        nullable=False,
    )
    process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )

    processes = relationship("Process")
    targets = relationship("Source")

    def __repr__(self):
        return "<ProcessSource (process=%s, target_source=%s)>" % (
            self.process_id,
            self.target_source_id,
        )


class ProcessTargetObject(Base):

    __tablename__ = "process_target_object"
    __table_args__ = {"schema": "process_tracker"}

    process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )
    target_object_id = Column(
        Integer,
        ForeignKey("process_tracker.source_object_lkup.source_object_id"),
        primary_key=True,
        nullable=False,
    )

    objects = relationship("SourceObject")
    processes = relationship("Process")

    def __repr__(self):
        return "<ProcessTargetObject (process_id=%s, target_object=%s)>" % (
            self.process_id,
            self.target_object_id,
        )


class ProcessDependency(Base):

    __tablename__ = "process_dependency"
    __table_args__ = {"schema": "process_tracker"}

    parent_process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )
    child_process_id = Column(
        Integer,
        ForeignKey("process_tracker.process.process_id"),
        primary_key=True,
        nullable=False,
    )

    child_process = relationship("Process", foreign_keys=[child_process_id])
    parent_process = relationship("Process", foreign_keys=[parent_process_id])

    def __repr__(self):

        return "<ProcessDependency (parent_process=%s, child_process=%s)>" % (
            self.parent_process_id,
            self.child_process_id,
        )


class ProcessTracking(Base):

    __tablename__ = "process_tracking"
    __table_args__ = {"schema": "process_tracker"}

    process_tracking_id = Column(
        Integer,
        Sequence("process_tracking_process_tracking_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    process_id = Column(Integer, ForeignKey("process_tracker.process.process_id"))
    process_status_id = Column(
        Integer,
        ForeignKey("process_tracker.process_status_lkup.process_status_id"),
        nullable=False,
    )
    process_run_id = Column(Integer, nullable=False)
    process_run_low_date_time = Column(DateTime, nullable=True)
    process_run_high_date_time = Column(DateTime, nullable=True)
    process_run_start_date_time = Column(DateTime, nullable=False)
    process_run_end_date_time = Column(DateTime, nullable=True)
    process_run_record_count = Column(Integer, nullable=False, default=0)
    process_run_actor_id = Column(
        Integer, ForeignKey("process_tracker.actor_lkup.actor_id"), nullable=False
    )
    is_latest_run = Column(Boolean, nullable=False, default=False)

    errors = relationship(
        "ErrorTracking", back_populates="error_tracking", passive_deletes="all"
    )
    extracts = relationship(
        "ExtractProcess", back_populates="extract_processes", passive_deletes="all"
    )
    process = relationship("Process", back_populates="process_tracking")

    status = relationship("ProcessStatus")

    def __repr__(self):

        return "<ProcessTracking id=%s, process=%s, process_status=%s)>" % (
            self.process_tracking_id,
            self.process_id,
            self.process_status_id,
        )
