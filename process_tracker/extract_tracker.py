# Extract Tracking
# Used in the creation and editing of extract records.  Used in conjunction with process tracking.
from datetime import datetime
import logging
import os
from pathlib import Path

from sqlalchemy.orm import aliased

from process_tracker.location_tracker import LocationTracker
from process_tracker.utilities.settings import SettingsManager
from process_tracker.utilities import utilities
from process_tracker.models.extract import (
    Extract,
    ExtractCompressionType,
    ExtractFileType,
    ExtractDatasetType,
    ExtractDependency,
    ExtractProcess,
    ExtractSource,
    ExtractSourceObject,
    ExtractStatus,
)
from process_tracker.models.source import (
    SourceLocation,
    SourceObjectAttribute,
    SourceObjectLocation,
)


class ExtractTracker:
    def __init__(
        self,
        process_run,
        filename,
        location=None,
        location_name=None,
        location_path=None,
        status=None,
        compression_type=None,
        filetype=None,
        config_location=None,
    ):
        """
        ExtractTracker is the primary engine for tracking data extracts
        :param process_run: The process object working with extracts (either creating or consuming)
        :type process_run: ProcessTracker object
        :param filename: Name of the data extract file.
        :type filename:  string
        :param location: SQLAlchemy Location object
        :param location_path: Location (filepath, s3 bucket, etc.) where the file is stored
        :type location_path: string
        :param location_name: Optional parameter to provide a specific name for the location.  If not provided, will use
                              the last directory in the path as the location name.  If type of location can be
                              determined (i.e. S3 bucket), the location type will be prepended.
        :type location_name: string
        :param status: Optional if status does not need to be 'initializing', which is default.
        :type status: string
        :param compression_type: Optional compression format of the extract.
        :type compression_type: String
        :param filetype: Optional file type of the extract. Will try to be derived from the filename if not provided.
        :type filetype: string
        :param config_location: Optional location for the process_tracker configuration file.
        :type config_location: string
        """
        log_level = SettingsManager(
            config_location=config_location
        ).determine_log_level()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self.process_run = process_run

        self.data_store = self.process_run.data_store
        self.session = self.process_run.session

        self.filename = filename

        if location is not None:
            self.logger.info("Location object provided.")
            self.location = location
        elif location_path is not None:
            self.logger.info("Location path provided.  Creating Location object.")
            self.location = LocationTracker(
                location_name=location_name,
                location_path=location_path,
                data_store=self.data_store,
            )
        else:
            raise Exception("A location object or location_path must be provided.")

        if compression_type is not None:
            self.logger.info("Finding compression type.")
            try:
                self.compression_type = self.data_store.get_or_create_item(
                    model=ExtractCompressionType,
                    create=False,
                    extract_compression_type=compression_type,
                )
            except Exception:
                error_msg = "%s is not a valid compression type." % compression_type
                self.logger.error(error_msg)
                raise Exception(error_msg)

            self.compression_type_id = self.compression_type.extract_compression_type_id
        else:
            self.compression_type_id = None

        if filetype is not None:
            self.logger.info("File type provided.  Verifying it is a valid filetype.")
            try:
                self.filetype = self.data_store.get_or_create_item(
                    model=ExtractFileType, create=False, extract_filetype=filetype
                )
            except Exception:
                error_msg = "%s is not a valid file type." % filetype
                self.logger.error(error_msg)
                raise Exception(error_msg)
        else:
            # Need to try to determine the filetype based on the extension of the filename.
            file_extension = os.path.splitext(filename)[1]
            file_extension = file_extension.replace(".", "")
            self.logger.info(
                "Trying to find record for file extension: %s" % file_extension
            )
            self.filetype = self.data_store.get_or_create_item(
                model=ExtractFileType,
                create=False,
                extract_filetype_code=file_extension,
            )

        self.logger.info("Registering extract.")

        self.extract = self.data_store.get_or_create_item(
            model=Extract,
            extract_filename=filename,
            extract_location_id=self.location.location.location_id,
            extract_compression_type_id=self.compression_type_id,
            extract_filetype_id=self.filetype.extract_filetype_id,
        )

        if location_path is not None:
            self.logger.info(
                "Location path was provided so building file path from it."
            )

            self.full_filename = str(Path(location_path).joinpath(filename))
        else:
            self.logger.info("Location provided so building file path from it.")

            self.full_filename = str(
                Path(self.location.location_path).joinpath(
                    self.extract.extract_filename
                )
            )

        if self.process_run.dataset_types is not None:
            self.logger.info("Associating dataset type(s) with extract.")
            self.dataset_types = self.register_extract_dataset_types(
                dataset_types=self.process_run.dataset_types
            )
        else:
            self.dataset_types = None

        if self.process_run.process.sources is not None:
            self.logger.info("Associating source system(s) with extract and location.")
            self.sources = self.register_extract_sources(
                sources=self.process_run.process.sources
            )
        else:
            self.logger.info("No source system(s) to associate to.")
            self.sources = None

        # Getting all status types in the event there are custom status types added later.
        self.extract_status_types = self.get_extract_status_types()

        # For specific status types, need to retrieve their ids to be used for those status types' logic.

        self.extract_status_initializing = self.extract_status_types["initializing"]
        self.extract_status_ready = self.extract_status_types["ready"]
        self.extract_status_loading = self.extract_status_types["loading"]
        self.extract_status_loaded = self.extract_status_types["loaded"]
        self.extract_status_archived = self.extract_status_types["archived"]
        self.extract_status_deleted = self.extract_status_types["deleted"]
        self.extract_status_error = self.extract_status_types["error"]

        self.extract_process = self.retrieve_extract_process()

        if status is not None:
            self.logger.info("Status was provided by user.")
            self.change_extract_status(new_status=status)
        else:
            self.logger.info("Status was not provided.  Initializing.")
            self.extract.extract_status_id = self.extract_status_initializing

        self.session.commit()

    def add_dependency(self, dependency_type, dependency):
        """
        Add a parent or child dependency on the given extract file.
        :param dependency_type: dependency type.  Valid values:  parent, child
        :type dependency_type: string
        :param dependency: dependent extract
        :type dependency: SQLAlchemy Extract object
        :return:
        """

        if dependency_type == "parent":
            dependency = ExtractDependency(
                child_extract_id=self.extract.extract_id,
                parent_extract_id=dependency.extract.extract_id,
            )

        elif dependency_type == "child":
            dependency = ExtractDependency(
                child_extract_id=dependency.extract.extract_id,
                parent_extract_id=self.extract.extract_id,
            )
        else:
            self.logger.error("Invalid extract dependency type.")
            raise Exception(
                "%s is an invalid extract dependency type." % dependency_type
            )

        self.session.add(dependency)
        self.session.commit()

        self.logger.info("Extract %s dependency added." % dependency_type)

    def change_extract_status(self, new_status, extracts=None):
        """
        Change an extract record status.
        :param new_status: The name of the status the extract is to be updated to.
        :type new_status: str
        :param extracts: List of Extract SQLAlchemy objects. Used for dependency check.
        :return:
        """
        status_date = datetime.now()
        if new_status in self.extract_status_types:

            if new_status == "loading":

                self.extract_dependency_check(extracts=extracts)

            self.logger.info("Setting extract status to %s" % new_status)

            new_status = self.extract_status_types[new_status]

            self.extract.extract_status_id = new_status

            self.extract_process.extract_process_status_id = new_status
            self.extract_process.extract_process_event_date_time = status_date

            self.session.commit()

        else:
            self.logger.error("%s is not a valid extract status type." % new_status)
            raise Exception(
                "%s is not a valid extract status type.  "
                "Please add the status to extract_status_lkup" % new_status
            )

    def extract_dependency_check(self, extracts=None):
        """
        Determine if the extract file has any unloaded dependencies before trying to load the file.
        :param extracts: List of ExtractTracking SQLAlchemy objects, provided if bulk updating status.
        :return:
        """
        child = aliased(Extract)
        parent = aliased(Extract)
        dependency_hold = 0

        if extracts is not None:

            parent_files_hold = (
                self.session.query(parent)
                .join(parent, ExtractDependency.parent_extract)
                .join(child, ExtractDependency.child_extract)
                .join(Extract, Extract.extract_id == parent.extract_id)
                .join(
                    ExtractStatus,
                    ExtractStatus.extract_status_id == Extract.extract_status_id,
                )
                .filter(child.extract_id == self.extract.extract_id)
                .filter(
                    ExtractStatus.extract_status_name.in_(
                        ("loading", "initializing", "ready")
                    )
                )
            )
            extract_names = list()
            for extract in extracts:
                self.logger.debug(
                    "Extracts being compared to %s" % extract.extract.full_filepath()
                )
                extract_names.append(extract.extract.full_filepath())

            for extract in parent_files_hold:

                self.logger.debug("Testing if %s is in extracts." % extract)

                if extract.full_filepath() not in extract_names:
                    self.logger.debug("Extract not found.")
                    dependency_hold += 1

            self.logger.debug(
                "We found %s dependencies that will block using this extract."
                % dependency_hold
            )
        else:
            dependency_hold = (
                self.session.query(ExtractDependency)
                .join(parent, ExtractDependency.parent_extract)
                .join(child, ExtractDependency.child_extract)
                .join(Extract, Extract.extract_id == parent.extract_id)
                .join(
                    ExtractStatus,
                    ExtractStatus.extract_status_id == Extract.extract_status_id,
                )
                .filter(child.extract_id == self.extract.extract_id)
                .filter(
                    ExtractStatus.extract_status_name.in_(
                        ("loading", "initializing", "ready")
                    )
                )
            ).count()

            self.logger.debug(
                "We found %s dependencies that will block using this extract."
                % dependency_hold
            )

        self.logger.debug("Dependency hold is %s" % dependency_hold)

        if dependency_hold > 0:
            self.logger.error(
                "Extract files that extract %s is dependent on have not been loaded, are being "
                "created, or are in the process of loading." % self.full_filename
            )
            raise Exception(
                "Extract files that extract %s is dependent on have not been loaded, are being "
                "created, or are in the process of loading." % self.full_filename
            )

        else:
            return False

    def get_extract_status_types(self):
        """
        Get list of process status types and return dictionary.
        :return:
        """
        self.logger.info("Obtaining extract status types.")

        status_types = dict()

        for record in self.session.query(ExtractStatus):
            status_types[record.extract_status_name] = record.extract_status_id

        return status_types

    def register_extract_dataset_types(self, dataset_types):
        """
        For the provided dataset types from process_run instance, associate with given Extract instance.
        :return:
        """

        for dataset_type in dataset_types:

            self.data_store.get_or_create_item(
                model=ExtractDatasetType,
                extract_id=self.extract.extract_id,
                dataset_type_id=dataset_type.dataset_type_id,
            )

        return dataset_types

    def register_extract_sources(self, sources):
        """
        For the provided sources from process_run instance, associate with given Extract instance.
        :param sources: List of sources from process_run record.
        :return:
        """

        for source in sources:
            source_type = source.__tablename__

            self.logger.debug("Referencing %s to extract." % source_type)

            if source_type == "process_source_object":
                self.logger.debug("Source type is of type source object.")
                self.logger.debug(
                    "Associating extract %s to source object %s."
                    % (self.extract.extract_id, source.source_object_id)
                )
                self.data_store.get_or_create_item(
                    model=ExtractSourceObject,
                    extract_id=self.extract.extract_id,
                    source_object_id=source.source_object_id,
                )

                self.data_store.get_or_create_item(
                    model=SourceObjectLocation,
                    source_object_id=source.source_object_id,
                    location_id=self.extract.extract_location_id,
                )

            elif source_type == "process_source":
                self.logger.debug("Source is of type source.")
                self.logger.debug(
                    "Associating extract %s to source %s."
                    % (self.extract.extract_id, source.source_id)
                )
                extract_source = self.data_store.get_or_create_item(
                    model=ExtractSource,
                    extract_id=self.extract.extract_id,
                    source_id=source.source_id,
                )

                self.logger.debug("Extract source record created. %s" % extract_source)

                self.data_store.get_or_create_item(
                    model=SourceLocation,
                    source_id=source.source_id,
                    location_id=self.extract.extract_location_id,
                )

        return sources

    def retrieve_extract_process(self):
        """
        Create and initialize or retrieve the process/extract relationship.
        :return:
        """

        self.logger.info("Associating extract to given process.")

        extract_process = self.data_store.get_or_create_item(
            model=ExtractProcess,
            extract_tracking_id=self.extract.extract_id,
            process_tracking_id=self.process_run.process_tracking_run.process_tracking_id,
        )

        # Only need to set to 'initializing' when it's the first time a process run is trying to work with files.
        if extract_process.extract_process_status_id is None:
            self.logger.info("Extract process status must also be set.  Initializing.")
            extract_process.extract_process_status_id = self.extract_status_initializing
            self.session.commit()

        return extract_process

    def set_extract_low_high_dates(self, low_date, high_date, audit_type="load"):
        """
        For the given extract, find the low and high date_times while writing or loading.
        :param low_date: The low date of the data set.
        :type low_date: Datetime/timestamp
        :param high_date: The high date of the data set.
        :type high_date: Datetime/timestamp.
        :param audit_type: The type of audit fields being populated.  Valid types:  write, load
        :type audittype: String
        :return:
        """

        if audit_type == "write":

            previous_low_date_time = self.extract.extract_write_low_date_time
            previous_high_date_time = self.extract.extract_write_high_date_time

            if utilities.determine_low_high_date(
                date=low_date, previous_date=previous_low_date_time, date_type="low"
            ):
                self.extract.extract_write_low_date_time = low_date

            if utilities.determine_low_high_date(
                date=high_date, previous_date=previous_high_date_time, date_type="high"
            ):
                self.extract.extract_write_high_date_time = high_date

        elif audit_type == "load":

            previous_low_date_time = self.extract.extract_load_low_date_time
            previous_high_date_time = self.extract.extract_load_high_date_time

            if utilities.determine_low_high_date(
                date=low_date, previous_date=previous_low_date_time, date_type="low"
            ):
                self.extract.extract_load_low_date_time = low_date

            if utilities.determine_low_high_date(
                date=high_date, previous_date=previous_high_date_time, date_type="high"
            ):
                self.extract.extract_load_high_date_time = high_date

        else:
            self.logger.error("%s is not a valid audit_type." % audit_type)
            raise Exception("%s is not a valid audit_type." % audit_type)

        self.session.commit()

    def set_extract_record_count(self, num_records, audit_type="load"):
        """
        For the given audit type, set the number of records for the given extract.
        :param num_records: Number of records tracked in extract
        :type num_records: int
        :param audit_type: The type of audit being populated.  Valid types:  write, load.
        :type audit_type: str
        :return:
        """

        if audit_type == "write":

            self.extract.extract_write_record_count = num_records

        elif audit_type == "load":

            self.extract.extract_load_record_count = num_records

        else:
            self.logger.error("%s is not a valid audit_type." % audit_type)
            raise Exception("%s is not a valid audit_type." % audit_type)

        self.session.commit()
