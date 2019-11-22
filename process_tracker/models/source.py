# SQLAlchemy Models
# Models for Source entities

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from process_tracker.models.model_base import Base


class CharacterSet(Base):

    __tablename__ = "character_set_lkup"
    __table_args__ = {"schema": "process_tracker"}

    character_set_id = Column(
        Integer,
        Sequence("character_set_lkup.character_set_id", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    character_set_name = Column(String(75), unique=True, nullable=False)

    def __repr__(self):

        return "<CharacterSet id=%s, name=%s>" % (
            self.character_set_id,
            self.character_set_name,
        )


class DataType(Base):

    __tablename__ = "data_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    data_type_id = Column(
        Integer,
        Sequence("data_type_lkup_data_type_id", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    data_type = Column(String(75), unique=True, nullable=False)

    def __repr__(self):

        return "<DataType id=%s, name=%s>" % (self.data_type_id, self.data_type)


class DatasetType(Base):

    __tablename__ = "dataset_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    dataset_type_id = Column(
        Integer,
        Sequence("dataset_type_lkup_dataset_type_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    dataset_type = Column(String(250), nullable=False, unique=True)

    source_dataset_types = relationship(
        "SourceDatasetType", back_populates="dataset_types", passive_deletes="all"
    )
    source_object_dataset_types = relationship(
        "SourceObjectDatasetType", back_populates="dataset_types", passive_deletes="all"
    )

    def __repr__(self):

        return "<DatasetType %s>" % self.dataset_type


class FilterType(Base):

    __tablename__ = "filter_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    filter_type_id = Column(
        Integer,
        Sequence("filter_type_lkup_filter_type_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    filter_type_code = Column(String(3), nullable=False, unique=True)
    filter_type_name = Column(String(75), nullable=False, unique=True)

    def __repr__(self):

        return "<FilterType code=%s, name=%s>" % (
            self.filter_type_code,
            self.filter_type_name,
        )


class Source(Base):

    __tablename__ = "source_lkup"
    __table_args__ = {"schema": "process_tracker"}

    source_id = Column(
        Integer,
        Sequence("source_lkup_source_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    source_name = Column(String(250), nullable=False, unique=True)
    character_set_id = Column(
        Integer,
        ForeignKey("process_tracker.character_set_lkup.character_set_id"),
        nullable=True,
    )
    source_type_id = Column(
        Integer,
        ForeignKey("process_tracker.source_type_lkup.source_type_id"),
        nullable=True,
        default=1,
    )

    def __repr__(self):

        return "<Source (name=%s)>" % self.source_name


class SourceContact(Base):

    __tablename__ = "source_contact"
    __table_args__ = {"schema": "process_tracker"}

    source_id = Column(
        Integer,
        ForeignKey("process_tracker.source_lkup.source_id"),
        nullable=False,
        primary_key=True,
    )
    contact_id = Column(
        Integer,
        ForeignKey("process_tracker.contact_lkup.contact_id"),
        nullable=False,
        primary_key=True,
    )

    UniqueConstraint(source_id, contact_id)
    sources = relationship("Source")
    contacts = relationship("Contact")


class SourceDatasetType(Base):

    __tablename__ = "source_dataset_type"
    __table_args__ = {"schema": "process_tracker"}

    source_id = Column(
        Integer,
        ForeignKey("process_tracker.source_lkup.source_id"),
        nullable=False,
        primary_key=True,
    )
    dataset_type_id = Column(
        Integer,
        ForeignKey("process_tracker.dataset_type_lkup.dataset_type_id"),
        nullable=False,
        primary_key=True,
    )

    UniqueConstraint(source_id, dataset_type_id)

    sources = relationship("Source")
    dataset_types = relationship("DatasetType")

    def __repr__(self):

        return "<SourceDatasetType source_id=%s, dataset_type_id=%s>" % (
            self.source_id,
            self.dataset_type_id,
        )


class SourceLocation(Base):

    __tablename__ = "source_location"
    __table_args__ = {"schema": "process_tracker"}

    source_id = Column(
        Integer,
        ForeignKey("process_tracker.source_lkup.source_id"),
        nullable=False,
        primary_key=True,
    )
    location_id = Column(
        Integer,
        ForeignKey("process_tracker.location_lkup.location_id"),
        nullable=False,
        primary_key=True,
    )

    UniqueConstraint(source_id, location_id)

    sources = relationship("Source")
    locations = relationship("Location")

    def __repr__(self):

        return "<SourceLocation source_id=%s, location_id=%s>" % (
            self.source_id,
            self.location_id,
        )


class SourceObject(Base):

    __tablename__ = "source_object_lkup"
    __table_args__ = {"schema": "process_tracker"}

    source_object_id = Column(
        Integer,
        Sequence("source_object_lkup_source_object_id_seq", schema="process_tracker"),
        primary_key=True,
        nullable=False,
    )
    source_id = Column(
        Integer, ForeignKey("process_tracker.source_lkup.source_id"), nullable=False
    )
    source_object_name = Column(String(250), nullable=False)
    character_set_id = Column(
        Integer,
        ForeignKey("process_tracker.character_set_lkup.character_set_id"),
        nullable=True,
    )

    UniqueConstraint(source_id, source_object_name)

    source_processes = relationship(
        "ProcessSourceObject", back_populates="objects", passive_deletes="all"
    )
    target_processes = relationship(
        "ProcessTargetObject", back_populates="objects", passive_deletes="all"
    )

    object_dataset_types = relationship(
        "SourceObjectDatasetType",
        back_populates="source_objects",
        passive_deletes="all",
    )

    sources = relationship("Source")

    def __repr__(self):

        return "<SourceObject (source_id=%s, source_object_name=%s)>" % (
            self.source_id,
            self.source_object_name,
        )


class SourceObjectLocation(Base):
    __tablename__ = "source_object_location"
    __table_args__ = {"schema": "process_tracker"}

    source_object_id = Column(
        Integer,
        ForeignKey("process_tracker.source_object_lkup.source_object_id"),
        nullable=False,
        primary_key=True,
    )
    location_id = Column(
        Integer,
        ForeignKey("process_tracker.location_lkup.location_id"),
        nullable=False,
        primary_key=True,
    )

    UniqueConstraint(source_object_id, location_id)

    source_objects = relationship("SourceObject")
    locations = relationship("Location")

    def __repr__(self):
        return "<SourceObjectLocation source_object_id=%s, location_id=%s>" % (
            self.source_object_id,
            self.location_id,
        )


class SourceObjectAttribute(Base):

    __tablename__ = "source_object_attribute_lkup"
    __table_args__ = {"schema": "process_tracker"}

    source_object_attribute_id = Column(
        Integer,
        Sequence(
            "source_object_attribute_lkup_source_object_attribute_id_seq",
            schema="process_tracker",
        ),
        primary_key=True,
        nullable=False,
    )
    source_object_attribute_name = Column(String(250), nullable=False)
    source_object_id = Column(
        Integer,
        ForeignKey("process_tracker.source_object_lkup.source_object_id"),
        nullable=False,
    )
    attribute_path = Column(String(750), nullable=True)
    data_type_id = Column(
        Integer,
        ForeignKey("process_tracker.data_type_lkup.data_type_id"),
        nullable=True,
    )
    data_length = Column(Integer, nullable=True)
    data_decimal = Column(Integer, nullable=True)
    is_pii = Column(Boolean, nullable=False, default=False)
    default_value_string = Column(String(250), nullable=True)
    default_value_number = Column(Numeric, nullable=True)
    is_key = Column(Boolean, nullable=False, default=False)
    is_filter = Column(Boolean, nullable=False, default=False)
    is_partition = Column(Boolean, nullable=False, default=False)

    UniqueConstraint(source_object_id, source_object_attribute_name)

    source_objects = relationship("SourceObject")

    def __repr__(self):

        return "<Source Object Attribute id=%s, name=%s, source_object=%s>" % (
            self.source_object_attribute_id,
            self.source_object_attribute_name,
            self.source_object_id,
        )


class SourceObjectDatasetType(Base):

    __tablename__ = "source_object_dataset_type"
    __table_args__ = {"schema": "process_tracker"}

    source_object_id = Column(
        Integer,
        ForeignKey("process_tracker.source_object_lkup.source_object_id"),
        nullable=False,
        primary_key=True,
    )
    dataset_type_id = Column(
        Integer,
        ForeignKey("process_tracker.dataset_type_lkup.dataset_type_id"),
        nullable=False,
        primary_key=True,
    )

    UniqueConstraint(source_object_id, dataset_type_id)

    source_objects = relationship("SourceObject")
    dataset_types = relationship("DatasetType")

    def __repr__(self):

        return "<SourceObjectDatasetType source_object_id=%s, dataset_type_id=%s>" % (
            self.source_object_id,
            self.dataset_type_id,
        )


class SourceType(Base):

    __tablename__ = "source_type_lkup"
    __table_args__ = {"schema": "process_tracker"}

    source_type_id = Column(Integer, primary_key=True, nullable=False)
    source_type_name = Column(String(75), nullable=False, unique=True)

    def __repr__(self):

        return "<SourceType id=%s, name=%s>" % (
            self.source_type_id,
            self.source_type_name,
        )
