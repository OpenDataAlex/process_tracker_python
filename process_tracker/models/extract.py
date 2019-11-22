# SQLAlchemy Models
# Models for Extract (Data) entities

from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import Base


class ExtractStatus(Base):

    __tablename__ = "extract_status_lkup"
    __table_args__ = {"schema": "process_tracker"}

    extract_status_id = Column(
        Integer,
        Sequence("extract_status_lkup_extract_status_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    extract_status_name = Column(String(75), nullable=False, unique=True)

    extracts = relationship("ExtractProcess")

    def __repr__(self):

        return "<Extract Status id=%s, name=%s>" % (
            self.extract_status_id,
            self.extract_status_name,
        )


class ExtractCompressionType(Base):

    __tablename__ = "extract_compression_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    extract_compression_type_id = Column(
        Integer,
        Sequence(
            "extract_compression_type_extract_compression_type_id",
            schema="process_tracker",
        ),
        primary_key=True,
        nullable=False,
    )
    extract_compression_type = Column(String(25), unique=True, nullable=False)

    def __repr__(self):

        return "<Extract Compression Type name=%s>" % (self.extract_compression_type)


class ExtractFileType(Base):

    __tablename__ = "extract_filetype_lkup"
    __table_args__ = {"schema": "process_tracker"}

    extract_filetype_id = Column(
        Integer,
        Sequence("extract_filetype_extract_filetype_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    extract_filetype_code = Column(String(5), nullable=False)
    extract_filetype = Column(String(75), nullable=False, unique=True)
    delimiter_char = Column(String(1), nullable=True)
    quote_char = Column(String(1), nullable=True)
    escape_char = Column(String(1), nullable=True)

    def __repr__(self):

        return "<Extract Filetype code=%s, name=%s>" % (
            self.extract_filetype_code,
            self.extract_filetype,
        )


class Extract(Base):

    __tablename__ = "extract_tracking"
    __table_args__ = {"schema": "process_tracker"}

    extract_id = Column(
        Integer,
        Sequence("extract_tracking_extract_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    extract_filename = Column(String(750), nullable=False, unique=True)
    extract_location_id = Column(
        Integer, ForeignKey("process_tracker.location_lkup.location_id"), nullable=False
    )
    extract_status_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_status_lkup.extract_status_id"),
        nullable=False,
    )
    extract_registration_date_time = Column(
        DateTime, nullable=False, default=datetime.now()
    )
    extract_write_low_date_time = Column(DateTime, nullable=True)
    extract_write_high_date_time = Column(DateTime, nullable=True)
    extract_write_record_count = Column(Integer, nullable=True)
    extract_load_low_date_time = Column(DateTime, nullable=True)
    extract_load_high_date_time = Column(DateTime, nullable=True)
    extract_load_record_count = Column(Integer, nullable=True)
    extract_compression_type_id = Column(
        Integer,
        ForeignKey(
            "process_tracker.extract_compression_type_lkup.extract_compression_type_id"
        ),
        nullable=True,
    )
    extract_filetype_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_filetype_lkup.extract_filetype_id"),
        nullable=True,
    )
    extract_filesize = Column(Numeric, nullable=True)
    extract_filesize_type_id = Column(
        Integer,
        ForeignKey("process_tracker.filesize_type_lkup.filesize_type_id"),
        nullable=True,
    )

    compression_type = relationship("ExtractCompressionType")
    extract_filetype = relationship("ExtractFileType")
    extract_filesize_type = relationship("FileSizeType")
    extract_dataset_types = relationship(
        "ExtractDatasetType",
        back_populates="dataset_type_extracts",
        passive_deletes="all",
    )
    extract_process = relationship(
        "ExtractProcess", back_populates="process_extracts", passive_deletes="all"
    )
    extract_sources = relationship("ExtractSource")
    extract_status = relationship("ExtractStatus", foreign_keys=[extract_status_id])
    locations = relationship("Location", foreign_keys=[extract_location_id])

    def __repr__(self):

        return "<Extract id=%s, filename=%s, location=%s>" % (
            self.extract_id,
            self.extract_filename,
            self.extract_location_id,
        )

    def full_filepath(self):

        return str(Path(self.locations.location_path).joinpath(self.extract_filename))


class ExtractDatasetType(Base):

    __tablename__ = "extract_dataset_type"
    __table_args__ = {"schema": "process_tracker"}

    extract_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_tracking.extract_id"),
        nullable=False,
        primary_key=True,
    )
    dataset_type_id = Column(
        Integer,
        ForeignKey("process_tracker.dataset_type_lkup.dataset_type_id"),
        nullable=False,
        primary_key=True,
    )

    UniqueConstraint(extract_id, dataset_type_id)

    dataset_type_extracts = relationship("Extract")
    extract_dataset_types = relationship("DatasetType")

    def __repr__(self):
        return "<ExtractDatasetType extract_id=%s, dataset_type_id=%s>" % (
            self.extract_id,
            self.dataset_type_id,
        )


class ExtractDependency(Base):

    __tablename__ = "extract_dependency"
    __table_args__ = {"schema": "process_tracker"}

    parent_extract_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_tracking.extract_id"),
        primary_key=True,
        nullable=False,
    )
    child_extract_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_tracking.extract_id"),
        primary_key=True,
        nullable=False,
    )

    child_extract = relationship("Extract", foreign_keys=[child_extract_id])
    parent_extract = relationship("Extract", foreign_keys=[parent_extract_id])

    def __repr__(self):

        return "<ExtractDependency (parent_extract=%s, child_extract=%s)>" % (
            self.parent_extract_id,
            self.child_extract_id,
        )


class ExtractProcess(Base):

    __tablename__ = "extract_process_tracking"
    __table_args__ = {"schema": "process_tracker"}

    extract_tracking_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_tracking.extract_id"),
        primary_key=True,
        nullable=False,
    )
    process_tracking_id = Column(
        Integer,
        ForeignKey("process_tracker.process_tracking.process_tracking_id"),
        primary_key=True,
        nullable=False,
    )
    extract_process_status_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_status_lkup.extract_status_id"),
        nullable=False,
    )
    extract_process_event_date_time = Column(
        DateTime, nullable=False, default=datetime.now()
    )

    process_extracts = relationship("Extract", foreign_keys=[extract_tracking_id])
    extract_processes = relationship(
        "ProcessTracking", foreign_keys=[process_tracking_id]
    )

    def __repr__(self):

        return "<ExtractProcess extract=%s, process_run=%s, extract_status=%s>" % (
            self.extract_tracking_id,
            self.process_tracking_id,
            self.extract_process_status_id,
        )


class ExtractSource(Base):

    __tablename__ = "extract_source"
    __table_args__ = {"schema": "process_tracker"}

    extract_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_tracking.extract_id"),
        primary_key=True,
        nullable=False,
    )
    source_id = Column(
        Integer,
        ForeignKey("process_tracker.source_lkup.source_id"),
        primary_key=True,
        nullable=False,
    )

    UniqueConstraint(extract_id, source_id)

    extracts = relationship("Extract")
    sources = relationship("Source")

    def __repr__(self):

        return "<ExtractSource extract_id=%s, source_id=%s>" % (
            self.extract_id,
            self.source_id,
        )


class ExtractSourceObject(Base):

    __tablename__ = "extract_source_object"
    __table_args__ = {"schema": "process_tracker"}

    extract_id = Column(
        Integer,
        ForeignKey("process_tracker.extract_tracking.extract_id"),
        primary_key=True,
        nullable=False,
    )
    source_object_id = Column(
        Integer,
        ForeignKey("process_tracker.source_object_lkup.source_object_id"),
        primary_key=True,
        nullable=False,
    )

    UniqueConstraint(extract_id, source_object_id)

    extracts = relationship("Extract")
    source_objects = relationship("SourceObject")

    def __repr__(self):

        return "<ExtractSourceObject extract_id=%s, source_object_id=%s>" % (
            self.extract_id,
            self.source_object_id,
        )


class FileSizeType(Base):
    __tablename__ = "filesize_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    filesize_type_id = Column(
        Integer,
        Sequence("filesize_type_lkup_filesize_type_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    filesize_type_name = Column(String(75), nullable=False, unique=True)
    filesize_type_code = Column(String(2), nullable=False, unique=True)

    UniqueConstraint(filesize_type_code, filesize_type_name)

    def __repr__(self):

        return "<FilesizeType id=%s, code=%s, name=%s>" % (
            self.filesize_type_id,
            self.filesize_type_code,
            self.filesize_type_name,
        )


class LocationType(Base):

    __tablename__ = "location_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    location_type_id = Column(
        Integer,
        Sequence("location_type_lkup_location_type_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    location_type_name = Column(String(25), unique=True, nullable=False)

    locations = relationship(
        "Location", back_populates="location_types", passive_deletes="all"
    )

    def __repr__(self):

        return "<LocationType id=%s, name=%s>" % (
            self.location_type_id,
            self.location_type_name,
        )


class Location(Base):

    __tablename__ = "location_lkup"
    __table_args__ = {"schema": "process_tracker"}

    location_id = Column(
        Integer,
        Sequence("location_lkup_location_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    location_name = Column(String(750), nullable=False, unique=True)
    location_path = Column(String(750), nullable=False, unique=True)
    location_type_id = Column(
        Integer,
        ForeignKey("process_tracker.location_type_lkup.location_type_id"),
        nullable=False,
    )
    location_file_count = Column(Integer, nullable=True)
    location_bucket_name = Column(String(750), nullable=True, unique=False)

    extracts = relationship("Extract")

    location_types = relationship("LocationType", foreign_keys=[location_type_id])

    def __repr__(self):

        return "<Location id=%s, name=%s, type=%s>" % (
            self.location_id,
            self.location_name,
            self.location_path,
        )
