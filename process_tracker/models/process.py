# SQLAlchemy Models
# Models for Process entities


from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import default_date, Base


class ErrorType(Base):

    __tablename__ = 'error_type_lkup'

    error_type_id = Column(Integer, Sequence('error_type_lkup_error_type_id_seq'), primary_key=True)
    error_type_name = Column(String(250), unique=True, nullable=False)

    process_errors = relationship("ErrorTracking")

    def __repr__(self):

        return "<ErrorType (name=%s)>" % self.error_type_name


class ErrorTracking(Base):

    __tablename__ = 'error_tracking'

    error_tracking_id = Column(Integer, Sequence('error_tracking_error_tracking_id_seq'), primary_key=True)
    error_type_id = Column(Integer, ForeignKey('error_type_lkup.error_type_id'))
    error_description = Column(String(750))
    error_occurrence_date_time = Column(DateTime, nullable=False)
    process_tracking_id = Column(Integer, ForeignKey('process_tracking.process_tracking_id'))

    error_tracking = relationship("ProcessTracking")

    def __repr__(self):

        return "<ErrorTracking (id=%s, type=%s, description=%s" \
               ", occurrence_date=%s)>" % (self.error_tracking_id
                                          , self.error_type_id
                                          , self.error_description
                                          , self.error_occurrence_date_time)


class ProcessStatus(Base):

    __tablename__ = 'process_status_lkup'

    process_status_id = Column(Integer, primary_key=True)
    process_status_name = Column(String(75), nullable=False, unique=True)

    def __repr__(self):

        return "<ProcessStatus (id=%s, process_status_name=%s)>" % (self.process_status_id, self.process_status_name)


class ProcessType(Base):

    __tablename__ = 'process_type_lkup'

    process_type_id = Column(Integer, Sequence('process_type_lkup_process_type_id_seq'), primary_key=True)
    process_type_name = Column(String(250), nullable=False)

    processes = relationship("Process")

    def __repr__(self):

        return "<ProcessType (id=%s, process_type=%s)>" % (self.process_type_id, self.process_type_name)


class Process(Base):

    __tablename__ = 'process'

    process_id = Column(Integer, Sequence('process_process_id_seq'), primary_key=True)
    process_name = Column(String(250), nullable=False, unique=True)
    process_source_id = Column(Integer, ForeignKey('source_lkup.source_id'))
#    latest_run_low_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
#    latest_run_high_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
#    latest_run_id = Column(Integer, nullable=False, default=0)
#    latest_run_start_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
#    latest_run_end_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)
#    latest_run_process_status = Column(Integer, nullable=False, default=0)
#    latest_run_record_count = Column(Integer, nullable=False, default=0)
    total_record_count = Column(Integer, nullable=False, default=0)
#    latest_run_actor_id = Column(id.idType, ForeignKey('actor.actor_id'))
    process_type_id = Column(Integer, ForeignKey('process_type_lkup.process_type_id'))
    process_tool_id = Column(Integer, ForeignKey('tool_lkup.tool_id'))
    last_failed_run_date_time = Column(DateTime(timezone=True), nullable=False, default=default_date)

    process_tracking = relationship("ProcessTracking")
    process_type = relationship("ProcessType", back_populates="processes")
    source = relationship("Source")
    tool = relationship("Tool")

    def __repr__(self):

        return "<Process (id=%s, name=%s, source=%s, type=%s)>" % (self.process_id
                                                                     , self.process_name
                                                                     , self.process_source_id
                                                                     , self.process_type_id)


class ProcessDependency(Base):

    __tablename__ = 'process_dependency'

    parent_process_id = Column(Integer, ForeignKey('process.process_id'), primary_key=True)
    child_process_id = Column(Integer, ForeignKey('process.process_id'), primary_key=True)

    child_process = relationship('Process', foreign_keys=[child_process_id])
    parent_process = relationship('Process', foreign_keys=[parent_process_id])

    def __repr__(self):

        return "<ProcessDependency (parent_process=%s, child_process=%s)>" % (self.parent_process_id
                                                                              , self.child_process_id)


class ProcessTracking(Base):

    __tablename__ = 'process_tracking'

    process_tracking_id = Column(Integer, Sequence('process_tracking_process_tracking_id_seq'), primary_key=True)
    process_id = Column(Integer, ForeignKey('process.process_id'))
    process_status_id = Column(Integer, ForeignKey('process_status_lkup.process_status_id'))
    process_run_id = Column(Integer, nullable=False)
    process_run_low_date_time = Column(DateTime, nullable=True)
    process_run_high_date_time = Column(DateTime, nullable=True)
    process_run_start_date_time = Column(DateTime, nullable=False)
    process_run_end_date_time = Column(DateTime, nullable=True)
    process_run_record_count = Column(Integer, nullable=False, default=0)
    process_run_actor_id = Column(Integer, ForeignKey('actor_lkup.actor_id'))
    is_latest_run = Column(Boolean, nullable=False, default=False)

    errors = relationship("ErrorTracking", back_populates="error_tracking")
    extracts = relationship("ExtractProcess", back_populates="extract_processes")
    process = relationship("Process", back_populates="process_tracking")

    def __repr__(self):

        return "<ProcessTracking id=%s, process=%s, process_status=%s)>" % (self.process_tracking_id
                                                                            , self.process_id
                                                                            , self.process_status_id)
