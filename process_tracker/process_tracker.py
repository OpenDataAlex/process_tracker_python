# Process Tracking
# Used in the creation and editing of process tracking records.

from datetime import datetime
import logging
import os

from sqlalchemy.orm import aliased

from process_tracker.utilities.data_store import DataStore
from process_tracker.extract_tracker import ExtractTracker
from process_tracker.location_tracker import LocationTracker
from process_tracker.utilities.aws_utilities import AwsUtilities
from process_tracker.utilities.logging import console
from process_tracker.utilities.settings import SettingsManager
from process_tracker.utilities import utilities

from process_tracker.models.actor import Actor
from process_tracker.models.contact import Contact
from process_tracker.models.extract import (
    Extract,
    ExtractProcess,
    ExtractStatus,
    Location,
)
from process_tracker.models.process import (
    ErrorTracking,
    ErrorType,
    Process,
    ProcessContact,
    ProcessDatasetType,
    ProcessDependency,
    ProcessFilter,
    ProcessTracking,
    ProcessStatus,
    ProcessSource,
    ProcessSourceObject,
    ProcessSourceObjectAttribute,
    ProcessTarget,
    ProcessTargetObject,
    ProcessTargetObjectAttribute,
    ProcessType,
)
from process_tracker.models.schedule import ScheduleFrequency
from process_tracker.models.source import (
    DatasetType,
    FilterType,
    Source,
    SourceContact,
    SourceDatasetType,
    SourceObject,
    SourceObjectAttribute,
    SourceObjectDatasetType,
    SourceType,
)
from process_tracker.models.tool import Tool


class ProcessTracker:
    def __init__(
        self,
        process_name=None,
        process_run_name=None,
        process_type=None,
        actor_name=None,
        tool_name=None,
        sources=None,
        targets=None,
        source_objects=None,
        target_objects=None,
        source_object_attributes=None,
        target_object_attributes=None,
        config_location=None,
        dataset_types=None,
        schedule_frequency=None,
        process_run_id=None,
    ):
        """
        ProcessTracker is the primary engine for tracking data integration processes.
        :param process_name: Name of the process being tracked.
        :param process_run_name: Optional name of the process run.
        :param actor_name: Name of the person or environment runnning the process.
        :param tool_name: Name of the tool used to run the process.
        :param sources: A single source name or list of source names for the given process. If source_objects is set,
                        sources is ignored. Optional.
        :type sources: list
        :param targets: A single target name or list of target names for the given process. If target_objects is set,
                        targets is ignored. Optional.
        :type targets: list
        :param source_objects: Finer grained list of sources, including source objects (i.e. tables). Optional.
        :type source_objects: dict of lists
        :param target_objects: Finer grained list of targets, including target objects (i.e. tables). Optional.
        :type target_objects: dict of lists
        :param source_object_attributes: Even finer grained list of sources, including source objects (i.e. tables) and their attributes.  Optional.
        :type source_object_attributes: dict of lists
        :param target_object_attributes: Even finer grained list of targets, including target objects (i.e. tables) and their attributes.  Optional.
        :type target_object_attributes: dict of lists
        :param config_location: Location where Process Tracker configuration file is. If not set, will use local home
                                directory.
        :type config_location: file path
        :param dataset_types: A single dataset category type or list of dataset category types for the given process.
        :type dataset_types: list
        :param schedule_frequency: The general scheduling frequency for the process (i.e. hourly)
        :type schedule_frequency: string
        :param process_run_id: If trying to access an already running process, provide the process run's id.  Object will be built for that specific process run.
        :type process_run_id: int
        """
        self.config_location = config_location
        self.config = SettingsManager(config_location=self.config_location)
        log_level = self.config.determine_log_level()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        self.logger.addHandler(console)

        self.data_store = DataStore(config_location=config_location)
        self.session = self.data_store.session

        # Getting all status types in the event there are custom status types added later.
        self.process_status_types = self.get_process_status_types()

        # For specific status types, need to retrieve their ids to be used for those status types' logic.
        self.process_status_running = self.process_status_types["running"]
        self.process_status_complete = self.process_status_types["completed"]
        self.process_status_failed = self.process_status_types["failed"]
        self.process_status_hold = self.process_status_types["on hold"]

        if process_run_id is not None:
            self.logger.info("Process run id provided.  Checking if exists.")

            process_run = self.data_store.get_or_create_item(
                model=ProcessTracking, process_tracking_id=process_run_id, create=False
            )

            if process_run is not None:
                # Setting all necessary objects based on the process run/process provided.
                self.actor = process_run.actor
                self.process_type = process_run.process.process_type
                self.tool = process_run.process.tool
                self.schedule_frequency = process_run.process.schedule_frequency
                self.process = process_run.process

                self.dataset_types = process_run.process.dataset_types
                self.sources = self.determine_process_sources(
                    process_run_id=process_run_id
                )
                self.targets = self.determine_process_targets(
                    process_run_id=process_run_id
                )

                self.process_name = process_run.process.process_name
                self.process_tracking_run = process_run
                self.process_run_name = process_run.process_run_name

            else:
                error_msg = "Process run not found based on id %s." % process_run_id
                self.logger.error(error_msg)
                raise Exception(error_msg)
        else:
            if process_name is None or process_type is None:
                error_msg = "process_name and process_type must be set."
                self.logger.error(error_msg)
                raise Exception(error_msg)

            self.actor = self.data_store.get_or_create_item(
                model=Actor, actor_name=actor_name
            )
            self.process_type = self.data_store.get_or_create_item(
                model=ProcessType, process_type_name=process_type
            )
            self.tool = self.data_store.get_or_create_item(
                model=Tool, tool_name=tool_name
            )

            if schedule_frequency is None:
                self.schedule_frequency = self.data_store.get_or_create_item(
                    model=ScheduleFrequency, schedule_frequency_name="unscheduled"
                )
            else:
                self.schedule_frequency = self.data_store.get_or_create_item(
                    model=ScheduleFrequency, schedule_frequency_name=schedule_frequency
                )

            self.process = self.data_store.get_or_create_item(
                model=Process,
                process_name=process_name,
                process_type_id=self.process_type.process_type_id,
                process_tool_id=self.tool.tool_id,
                schedule_frequency_id=self.schedule_frequency.schedule_frequency_id,
            )

            # Dataset types should be loaded before source and target because they are also used there.

            if dataset_types is not None:
                self.dataset_types = self.register_process_dataset_types(
                    dataset_types=dataset_types
                )
            else:
                self.dataset_types = None

            # sources, source_objects, or source_object_attributes should be set, not multiple.  Always go with lower grain if possible.

            self.source_object_attributes = None
            self.source_objects = None

            if source_object_attributes is not None:
                self.source_object_attributes = self.register_process_sources(
                    source_object_attributes=source_object_attributes
                )
                self.sources = self.source_object_attributes
            elif source_objects is not None:
                self.source_objects = self.register_process_sources(
                    source_objects=source_objects
                )
                self.sources = self.source_objects
            elif sources is not None:
                self.sources = self.register_process_sources(sources=sources)
            else:
                self.sources = None

            # targets, target_objects, or target_object_attributes should be set, not multiple.  Always go with lower grain if possible.

            if target_object_attributes is not None:
                self.targets = self.register_process_targets(
                    target_object_attributes=target_object_attributes
                )
            elif target_objects is not None:
                self.targets = self.register_process_targets(
                    target_objects=target_objects
                )
            elif targets is not None:
                self.targets = self.register_process_targets(targets=targets)
            else:
                self.targets = None

            self.process_name = process_name
            self.process_run_name = process_run_name

            self.process_tracking_run = self.register_new_process_run()

    @staticmethod
    def bulk_change_extract_status(extracts, extract_status):
        """
        Given a set of extract objects, update the extract process record to reflect the association and updated status
        as well as the extract record's' status.
        :param extracts: List of ExtractTracking SQLAlchemy objects to be bulk updated.
        :param extract_status: The status to change the extract files to.
        :type extract_status: str
        :return:
        """

        for extract in extracts:

            extract.change_extract_status(new_status=extract_status)

    def change_run_status(self, new_status, end_date=None):
        """
        Change a process tracking run record from 'running' to another status.
        :param new_status: The name of the status that the run is being switched to.
        :type new_status: string
        :param end_date:  If there is a specific time required (i.e. to keep timestamps consistent between log and data
        store)
        :type end_date: datetime
        :return:
        """
        if end_date is None:
            end_date = datetime.now()

        if new_status in self.process_status_types.keys():

            self.process_tracking_run.process_status_id = self.process_status_types[
                new_status
            ]

            if self.process_status_types[new_status] == self.process_status_complete:
                self.logger.info("Process status changing to completed.")
                self.process.last_completed_run_date_time = end_date
                self.process_tracking_run.process_run_end_date_time = end_date

            elif self.process_status_types[new_status] == self.process_status_failed:

                self.logger.info(
                    "Process recording as failed.  Setting process last_failed_run_date_time."
                )

                self.process.last_failed_run_date_time = end_date
                self.process_tracking_run.process_run_end_date_time = end_date

            self.session.commit()

            if (
                self.process_status_types[new_status] == self.process_status_complete
            ) or (self.process_status_types[new_status] == self.process_status_failed):
                self.session.close()

        else:
            raise Exception("The provided status type %s is invalid." % new_status)

    def create_extract_tracker_objects(self, files):
        """
        For extract finders, take the file list and create an array of extract tracker objects from it.
        :param files: SQLAlchemy list of extract file records.
        :return: Array of extract tracker objects.
        """
        file_list = list()

        for file in files:
            self.logger.debug("Adding %s to file_list." % file.extract_filename)
            file_list.append(
                ExtractTracker(
                    process_run=self,
                    filename=file.extract_filename,
                    location_name=file.locations.location_name,
                    location_path=file.locations.location_path,
                )
            )

        return file_list

    def determine_hold_status(self, last_run_status, last_run_id):
        """
        Based on the setting 'max_concurrent_failures', count the number of failures for that number of process runs.
        If the counts match, process will remain on hold.  If last run is 'on_hold' process will remain on hold.
        :param last_run_status: The status of the previous run
        :param last_run_id:  The process_run_id of the previous run
        :return:
        """
        self.logger.debug("Determining if process should be put on or remain on hold.")

        max_concurrent_failures = int(
            self.config.config["DEFAULT"]["max_concurrent_failures"]
        )

        self.logger.debug("Max Concurrent failures is %s" % max_concurrent_failures)

        failure_count = (
            self.session.query(ProcessTracking)
            .join(Process)
            .filter(Process.process_name == self.process_name)
            .filter(
                ProcessTracking.process_run_id > (last_run_id - max_concurrent_failures)
            )
            .filter(ProcessTracking.process_status_id == self.process_status_failed)
            .count()
        )

        self.logger.debug("Number of failures in past runs is %s" % failure_count)

        if last_run_status == self.process_status_hold:
            self.logger.error("Last run still in hold status.  Need to remain in hold.")
            return True
        elif failure_count == max_concurrent_failures:
            self.logger.error(
                "Number of failures has reached max_concurrent_failures.  Putting process on hold until resolved."
            )
            return True
        else:
            return False

    def determine_process_sources(self, process_run_id):
        """
        Based on the process_run_id, find the given process' sources - either at the attribute, object, or source level
        :param process_run_id: Process run identifier
        :type process_run_id: int
        :return: Array of source objects at lowest granularity.
        """
        source_list = list()
        self.logger.info("Checking for attributes.")
        attributes = (
            self.session.query(SourceObjectAttribute)
            .join(ProcessSourceObjectAttribute)
            .join(Process)
            .join(ProcessTracking)
            .filter(ProcessTracking.process_tracking_id == process_run_id)
        )

        if attributes.count() >= 1:
            self.logger.info("Attributes were not empty.")
            for attribute in attributes:
                self.logger.debug("Adding attribute %s " % attribute)
                source_list.append(attribute)

            return source_list

        self.logger.info("Checking for objects.")
        objects = (
            self.session.query(SourceObject)
            .join(ProcessSourceObject)
            .join(Process)
            .join(ProcessTracking)
            .filter(ProcessTracking.process_tracking_id == process_run_id)
        )

        if objects.count() >= 1:
            self.logger.info("Objects were not empty.")
            for object in objects:
                self.logger.debug("Adding object %s " % object)
                source_list.append(object)

            return source_list

        self.logger.info("Checking for sources.")
        sources = (
            self.session.query(Source)
            .join(ProcessSource)
            .join(Process)
            .join(ProcessTracking)
            .filter(ProcessTracking.process_tracking_id == process_run_id)
        )

        if sources.count() >= 1:
            self.logger.info("Sources were not empty.")
            for source in sources:
                self.logger.debug("Adding source %s " % source)
                source_list.append(source)
            return source_list

        self.logger.info(
            "No source, source object, or source object attribute has been associated with this process."
        )
        return None

    def determine_process_targets(self, process_run_id):
        """
        Based on the process_run_id, find the given process' targets - either at the attribute, object, or source level
        :param process_run_id: Process run identifier
        :type process_run_id: int
        :return: Array of source objects used as target for the process at lowest granularity.
        """

        attributes = (
            self.session.query(SourceObjectAttribute)
            .join(ProcessTargetObjectAttribute)
            .join(Process)
            .join(ProcessTracking)
            .filter(ProcessTracking.process_tracking_id == process_run_id)
        )

        if attributes is not None:
            return attributes

        objects = (
            self.session.query(SourceObject)
            .join(ProcessTargetObject)
            .join(Process)
            .join(ProcessTracking)
            .filter(ProcessTracking.process_tracking_id == process_run_id)
        )

        if objects is not None:
            return objects

        sources = (
            self.session.query(Source)
            .join(ProcessTarget)
            .join(Process)
            .join(ProcessTracking)
            .filter(ProcessTracking.process_tracking_id == process_run_id)
        )

        if sources is not None:
            return sources

        self.logger.info(
            "No target, target object, or target object attribute has been associated with this process."
        )
        return None

    def find_extracts_by_filename(self, filename, status="ready"):
        """
        For the given filename, or filename part, find all matching extracts that are ready for processing.
        :param filename: Filename or part of filename.
        :type filename: str
        :param status: Name of the status type for files being searched.  Default 'ready'.
        :type status: str
        :return: List of Extract SQLAlchemy objects.
        """

        process_files = (
            self.session.query(Extract)
            .join(ExtractStatus)
            .filter(Extract.extract_filename.like("%" + filename + "%"))
            .filter(ExtractStatus.extract_status_name == status)
            .order_by(Extract.extract_registration_date_time)
            .order_by(Extract.extract_id)
            .all()
        )

        self.logger.info("Processing file records to extract tracker objects")

        process_files = self.create_extract_tracker_objects(files=process_files)

        self.logger.info("Returning extract files by filename.")

        return process_files

    def find_extracts_by_location(
        self, location_name=None, location_path=None, status="ready"
    ):
        """
        For the given location path or location name, find all matching extracts that are ready for processing
        :param location_name: The name of the location
        :type location_name: str
        :param location_path: The path of the location
        :type location_path: str
        :param status: Name of the status type for files being searched.  Default 'ready'.
        :type status: str
        :return: List of Extract SQLAlchemy objects.
        """

        if location_path is not None:
            process_files = (
                self.session.query(Extract)
                .join(Location)
                .join(ExtractStatus)
                .filter(ExtractStatus.extract_status_name == status)
                .filter(Location.location_path == location_path)
                .order_by(Extract.extract_registration_date_time)
                .order_by(Extract.extract_id)
                .all()
            )
        elif location_name is not None:
            process_files = (
                self.session.query(Extract)
                .join(Location)
                .join(ExtractStatus)
                .filter(ExtractStatus.extract_status_name == status)
                .filter(Location.location_name == location_name)
                .order_by(Extract.extract_registration_date_time)
                .order_by(Extract.extract_id)
                .all()
            )
        else:
            self.logger.error(
                "A location name or path must be provided.  Please try again."
            )
            raise Exception(
                "A location name or path must be provided.  Please try again."
            )

        self.logger.info("Processing file records to extract tracker objects")

        process_files = self.create_extract_tracker_objects(files=process_files)

        self.logger.info("Returning extract files by location.")
        return process_files

    def find_extracts_by_process(self, extract_process_name, status="ready"):
        """
        For the given named process, find the extracts that are ready for processing.
        :param extract_process_name: Name of the process that is associated with extracts
        :type extract_process_name: str
        :param status: Name of the status type for files being searched.  Default 'ready'.
        :type status: str
        :return: List of Extract SQLAlchemy objects.
        """

        process_files = (
            self.session.query(Extract)
            .join(
                ExtractStatus,
                Extract.extract_status_id == ExtractStatus.extract_status_id,
            )
            .join(Location, Extract.extract_location_id == Location.location_id)
            .join(
                ExtractProcess, Extract.extract_id == ExtractProcess.extract_tracking_id
            )
            .join(ProcessTracking)
            .join(Process)
            .filter(
                Process.process_name == extract_process_name,
                ExtractStatus.extract_status_name == status,
            )
            .order_by(Extract.extract_registration_date_time)
            .all()
        )

        self.logger.info("Processing file records to extract tracker objects")

        process_files = self.create_extract_tracker_objects(files=process_files)

        self.logger.info("Returning extract files by process.")

        return process_files

    def find_process_contacts(self, process):
        """
        Based on the process, find the process' contacts as well as the contacts for any sources used and return them
        as a list.
        :param process: The process' process_id
        :type process: int
        :return:
        """
        contacts = list()

        result = (
            self.session.query(Contact.contact_name, Contact.contact_email)
            .join(SourceContact)
            .join(Source)
            .join(ProcessSource)
            .join(Process)
            .filter(Process.process_id == process)
        )

        for contact in result:
            contacts.append(
                {
                    "contact_name": contact.contact_name,
                    "contact_email": contact.contact_email,
                    "contact_type": "source",
                }
            )

        result = (
            self.session.query(Contact.contact_name, Contact.contact_email)
            .join(ProcessContact)
            .join(Process)
            .filter(Process.process_id == process)
        )

        for contact in result:
            contacts.append(
                {
                    "contact_name": contact.contact_name,
                    "contact_email": contact.contact_email,
                    "contact_type": "process",
                }
            )

        return contacts

    def find_process_by_schedule_frequency(self, frequency="daily"):
        """
        For the given schedule frequency, find the processed on that schedule frequency.
        :param frequency: The desired frequency with which to retrieve processes.
        :return:
        """
        process_list = list()

        processes = (
            self.data_store.session.query(Process.process_id)
            .join(ScheduleFrequency)
            .filter(ScheduleFrequency.schedule_frequency_name == frequency)
        )

        for process in processes:
            process_list.append(process.process_id)

        return process_list

    def find_process_filters(self, process):
        """
        For the given process, find the filters required for querying the source system.
        :param process: The process' process id.
        :type process: integer
        """

        filter_list = list()

        filters = (
            self.session.query(
                Source.source_name,
                SourceObject.source_object_name,
                SourceObjectAttribute.source_object_attribute_name,
                FilterType.filter_type_code,
                ProcessFilter.filter_value_numeric,
                ProcessFilter.filter_value_string,
            )
            .join(SourceObjectAttribute, ProcessFilter.attributes)
            .join(SourceObject, SourceObjectAttribute.source_objects)
            .join(Source)
            .join(FilterType)
            .filter(ProcessFilter.process_id == process)
            .order_by(
                Source.source_name,
                SourceObject.source_object_name,
                SourceObjectAttribute.source_object_attribute_name,
            )
        )

        for filter in filters:
            filter_list.append(
                {
                    "source_name": filter.source_name,
                    "source_object_name": filter.source_object_name,
                    "source_object_attribute_name": filter.source_object_attribute_name,
                    "filter_type_code": filter.filter_type_code,
                    "filter_value_numeric": filter.filter_value_numeric,
                    "filter_value_string": filter.filter_value_string,
                }
            )

        return filter_list

    def find_process_source_attributes(self, process):
        """
        For the given process, find the attributes used for process sources.
        :param process:
        :return:
        """

        source_attribute_list = list()

        source_attributes = (
            self.session.query(
                Source.source_name,
                SourceType.source_type_name,
                SourceObject.source_object_name,
                SourceObjectAttribute.source_object_attribute_name,
                SourceObjectAttribute.is_key,
                SourceObjectAttribute.is_filter,
                SourceObjectAttribute.is_partition,
            )
            .join(SourceObject, SourceObjectAttribute.source_objects)
            .join(Source, SourceObject.sources)
            .join(SourceType)
            .join(ProcessSourceObjectAttribute)
            .filter(ProcessSourceObjectAttribute.process_id == process)
            .order_by(
                Source.source_name,
                SourceObject.source_object_name,
                SourceObjectAttribute.source_object_attribute_name,
            )
        )

        for attribute in source_attributes:
            source_attribute_list.append(
                {
                    "source_name": attribute.source_name,
                    "source_type": attribute.source_type_name,
                    "source_object_name": attribute.source_object_name,
                    "source_object_attribute_name": attribute.source_object_attribute_name,
                    "is_key": attribute.is_key,
                    "is_filter": attribute.is_filter,
                    "is_partition": attribute.is_partition,
                }
            )

        return source_attribute_list

    def find_process_target_attributes(self, process):
        """
        For the given process, find the attributes used for process targets.
        :param process:
        :return:
        """

        target_attribute_list = list()

        source_attributes = (
            self.session.query(
                Source.source_name,
                SourceType.source_type_name,
                SourceObject.source_object_name,
                SourceObjectAttribute.source_object_attribute_name,
                SourceObjectAttribute.is_key,
                SourceObjectAttribute.is_filter,
                SourceObjectAttribute.is_partition,
            )
            .join(SourceObject, SourceObjectAttribute.source_objects)
            .join(Source, SourceObject.sources)
            .join(SourceType)
            .join(ProcessTargetObjectAttribute)
            .filter(ProcessTargetObjectAttribute.process_id == process)
            .order_by(
                Source.source_name,
                SourceObject.source_object_name,
                SourceObjectAttribute.source_object_attribute_name,
            )
        )

        for attribute in source_attributes:
            target_attribute_list.append(
                {
                    "target_name": attribute.source_name,
                    "target_type": attribute.source_type_name,
                    "target_object_name": attribute.source_object_name,
                    "target_object_attribute_name": attribute.source_object_attribute_name,
                    "is_key": attribute.is_key,
                    "is_filter": attribute.is_filter,
                    "is_partition": attribute.is_partition,
                }
            )

        return target_attribute_list

    def get_latest_tracking_record(self, process):
        """
        For the given process, find the latest tracking record.
        :param process: The process' process_id.
        :type process: integer
        :return:
        """

        instance = (
            self.session.query(ProcessTracking)
            .filter(ProcessTracking.process_id == process.process_id)
            .order_by(ProcessTracking.process_run_id.desc())
            .first()
        )

        return instance

    def get_process_status_types(self):
        """
        Get list of process status types and return dictionary.
        :return:
        """
        status_types = {}

        for record in self.session.query(ProcessStatus):
            status_types[record.process_status_name] = record.process_status_id

        return status_types

    def raise_run_error(
        self, error_type_name, error_description=None, fail_run=False, end_date=None
    ):
        """
        Raise a runtime error and fail the process run if the error is severe enough. The error also is recorded in
        error_tracking.
        :param error_type_name: The name of the type of error being triggered.
        :param error_description: The description of the error to store in error tracking.
        :param fail_run:  Flag for triggering a run failure, default False
        :type fail_run: Boolean
        :param end_date: If a specific datetime is required for the process_tracking end datetime.
        :type end_date: datetime
        :return:
        """
        if end_date is None:
            end_date = (
                datetime.now()
            )  # Need the date to match across all parts of the event in case the run is failed.

        if error_description is None:
            error_description = "Unspecified error."

        error_type = self.data_store.get_or_create_item(
            model=ErrorType, create=False, error_type_name=error_type_name
        )

        run_error = ErrorTracking(
            error_type_id=error_type.error_type_id,
            error_description=error_description,
            process_tracking_id=self.process_tracking_run.process_tracking_id,
            error_occurrence_date_time=end_date,
        )

        self.logger.error(
            "%s - %s - %s" % (self.process_name, error_type_name, error_description)
        )
        self.session.add(run_error)
        self.session.commit()

        if fail_run:
            self.change_run_status(new_status="failed", end_date=end_date)

            raise Exception("Process halting.  An error triggered the process to fail.")

    def register_extracts_by_location(self, location_path, location_name=None):
        """
        For a given location, find all files and attempt to register them.
        :param location_name: Name of the location
        :param location_path: Path of the location
        :return:
        """
        location = LocationTracker(
            location_path=location_path,
            location_name=location_name,
            data_store=self.data_store,
        )

        file_count = 0

        if location.location_type.location_type_name == "s3":
            aws_util = AwsUtilities()

            path = location.location_path

            bucket = aws_util.get_s3_bucket(path=path)

            for file in bucket.objects.all():
                file_count += 1

                self.logger.debug("Registering file %s." % file.key)
                ExtractTracker(
                    process_run=self,
                    filename=file.key,
                    location=location,
                    status="ready",
                    config_location=self.config_location,
                )
        else:
            for file in os.listdir(location_path):
                file_count += 1

                self.logger.debug("Registering file %s." % file)
                ExtractTracker(
                    process_run=self,
                    filename=file,
                    location=location,
                    status="ready",
                    config_location=self.config_location,
                )

        if file_count != 0:
            self.logger.debug("File count is %s!" % file_count)
            # Only want to register the file count for a given location if files actually there.
            location.register_file_count(file_count=file_count)

    def register_new_process_run(self):
        """
        When a new process instance is starting, register the run in process tracking.
        :return:
        """
        child_process = aliased(Process)
        parent_process = aliased(Process)

        last_run = self.get_latest_tracking_record(process=self.process)

        new_run_flag = True
        new_run_id = 1

        # Need to check the status of any dependencies.  If dependencies are running or failed, halt this process.

        dependency_hold = (
            self.session.query(ProcessDependency)
            .join(
                parent_process,
                ProcessDependency.parent_process_id == parent_process.process_id,
            )
            .join(
                child_process,
                ProcessDependency.child_process_id == child_process.process_id,
            )
            .join(
                ProcessTracking, ProcessTracking.process_id == parent_process.process_id
            )
            .join(
                ProcessStatus,
                ProcessStatus.process_status_id == ProcessTracking.process_status_id,
            )
            .filter(child_process.process_id == self.process.process_id)
            .filter(ProcessStatus.process_status_name.in_(("running", "failed")))
            .count()
        )

        if dependency_hold > 0:
            raise Exception(
                "Processes that this process is dependent on are running or failed."
            )

        if last_run is not None and last_run:
            # Must validate that the process is not currently running.

            if (
                last_run.process_status_id != self.process_status_running
                and last_run.process_status_id != self.process_status_hold
            ):
                last_run.is_latest_run = False
                new_run_flag = True
                new_run_id = last_run.process_run_id + 1
            else:
                new_run_flag = False

            if self.determine_hold_status(
                last_run_status=last_run.process_status_id,
                last_run_id=last_run.process_run_id,
            ):
                self.logger.error(
                    "Process is on hold due to number of concurrent failures or previous run is in on-hold status."
                )
                new_run_flag = False

        if new_run_flag:
            new_run = ProcessTracking(
                process_id=self.process.process_id,
                process_status_id=self.process_status_running,
                process_run_id=new_run_id,
                process_run_start_date_time=datetime.now(),
                process_run_actor_id=self.actor.actor_id,
                is_latest_run=True,
                process_run_name=self.process_run_name,
            )

            self.session.add(new_run)
            self.session.commit()

            self.logger.info("Process tracking record added for %s" % self.process_name)

            return new_run

        else:
            raise Exception(
                "The process %s is currently %s."
                % (self.process_name, last_run.status.process_status_name)
            )

    def register_process_dataset_types(self, dataset_types):
        """
        If dataset category types are provided, register them to the process.
        :param dataset_types:
        :return:
        """

        dataset_type_list = list()

        if not isinstance(dataset_types, list):
            dataset_types = [dataset_types]

        for dataset_type in dataset_types:
            self.logger.debug("Registering dataset_type %s to process." % dataset_type)
            dataset_type = self.data_store.get_or_create_item(
                model=DatasetType, dataset_type=dataset_type
            )

            self.data_store.get_or_create_item(
                model=ProcessDatasetType,
                process_id=self.process.process_id,
                dataset_type_id=dataset_type.dataset_type_id,
            )

            dataset_type_list.append(dataset_type)

        return dataset_type_list

    def register_process_sources(
        self, sources=None, source_objects=None, source_object_attributes=None
    ):
        """
        Register source(s) to a given process.
        :param sources: List of source name(s)  If source_objects is set, sources is ignored.
        :type sources: list
        :param source_objects: Finer grained list of source name(s) and their objects used in this process.
        :type source_objects: dict of lists
        :param source_object_attributes: Even finer grained list of source name(s), their objects, and their attributes used in this process.
        :return: List of source, source object, or source object attribute SQLAlchemy objects.
        """
        source_list = list()

        if source_object_attributes is not None:
            if isinstance(source_object_attributes, dict):
                for source, objects in source_object_attributes.items():
                    self.logger.debug("Working on source %s" % source)
                    source = self.data_store.get_or_create_item(
                        model=Source, source_name=source
                    )

                    for source_object, attributes in objects.items():
                        self.logger.debug("Working on object %s" % source_object)
                        source_object = self.data_store.get_or_create_item(
                            model=SourceObject,
                            source_id=source.source_id,
                            source_object_name=source_object,
                        )

                        for attribute in attributes:
                            self.logger.debug("Working on attribute %s" % attribute)
                            object_attribute = self.data_store.get_or_create_item(
                                model=SourceObjectAttribute,
                                source_object_id=source_object.source_object_id,
                                source_object_attribute_name=attribute,
                            )

                            self.logger.debug(
                                "Associating process %s with %s"
                                % (
                                    self.process.process_name,
                                    object_attribute.source_object_attribute_name,
                                )
                            )

                            self.data_store.get_or_create_item(
                                model=ProcessSourceObjectAttribute,
                                source_object_attribute_id=object_attribute.source_object_attribute_id,
                                process_id=self.process.process_id,
                            )

                            source_list.append(object_attribute)
            else:
                error_msg = "source_object_attributes is not a dictionary."
                self.logger.error(error_msg)
                raise Exception(error_msg)

        elif source_objects is not None:
            if isinstance(source_objects, dict):
                for source, objects in source_objects.items():

                    source = self.data_store.get_or_create_item(
                        model=Source, source_name=source
                    )

                    self.data_store.get_or_create_item(
                        model=ProcessSource,
                        source_id=source.source_id,
                        process_id=self.process.process_id,
                    )

                    if self.dataset_types is not None:
                        for dataset_type in self.dataset_types:
                            self.data_store.get_or_create_item(
                                model=SourceDatasetType,
                                source_id=source.source_id,
                                dataset_type_id=dataset_type.dataset_type_id,
                            )

                    for item in objects:

                        source_object = self.data_store.get_or_create_item(
                            model=SourceObject,
                            source_id=source.source_id,
                            source_object_name=item,
                        )

                        if self.dataset_types is not None:
                            for dataset_type in self.dataset_types:
                                self.data_store.get_or_create_item(
                                    model=SourceObjectDatasetType,
                                    source_object_id=source_object.source_object_id,
                                    dataset_type_id=dataset_type.dataset_type_id,
                                )

                        self.data_store.get_or_create_item(
                            model=ProcessSourceObject,
                            process_id=self.process.process_id,
                            source_object_id=source_object.source_object_id,
                        )

                        source_list.append(source_object)
            else:
                self.logger.error("It appears source_objects is not a dictionary.")
                raise Exception("It appears source_objects is not a dictionary.")

        elif sources is not None:
            if isinstance(sources, str):
                sources = [sources]

            for source in sources:
                source = self.data_store.get_or_create_item(
                    model=Source, source_name=source
                )

                if self.dataset_types is not None:
                    for dataset_type in self.dataset_types:
                        self.data_store.get_or_create_item(
                            model=SourceDatasetType,
                            source_id=source.source_id,
                            dataset_type_id=dataset_type.dataset_type_id,
                        )

                self.data_store.get_or_create_item(
                    model=ProcessSource,
                    source_id=source.source_id,
                    process_id=self.process.process_id,
                )

                source_list.append(source)

        return source_list

    def register_process_targets(
        self, targets=None, target_objects=None, target_object_attributes=None
    ):
        """
        Register target source(s) to a given process.
        :param targets: List of source name(s).  If target_objects is set, targets is ignored.
        :type targets: list
        :param target_objects: Finer grained list of target name(s) and their objects used in this process.
        :type target_objects: dict of lists
        :param target_object_attributes: Even finer grained list of target name(s), their objects, and their attributes used in this process.
        :type target_object_attributes: dict of lists
        :return: List of source or source object SQLAlchemy objects.
        """
        target_list = list()
        if target_object_attributes is not None:
            if isinstance(target_object_attributes, dict):
                for target, objects in target_object_attributes.items():
                    self.logger.debug("Working on source %s" % target)
                    source = self.data_store.get_or_create_item(
                        model=Source, source_name=target
                    )

                    for target_object, attributes in objects.items():
                        self.logger.debug("Working on object %s" % target_object)
                        source_object = self.data_store.get_or_create_item(
                            model=SourceObject,
                            source_id=source.source_id,
                            source_object_name=target_object,
                        )

                        for attribute in attributes:
                            self.logger.debug("Working on attribute %s" % attribute)
                            object_attribute = self.data_store.get_or_create_item(
                                model=SourceObjectAttribute,
                                source_object_id=source_object.source_object_id,
                                source_object_attribute_name=attribute,
                            )

                            self.logger.debug(
                                "Associating process %s with %s"
                                % (
                                    self.process.process_name,
                                    object_attribute.source_object_attribute_name,
                                )
                            )

                            self.data_store.get_or_create_item(
                                model=ProcessTargetObjectAttribute,
                                target_object_attribute_id=object_attribute.source_object_attribute_id,
                                process_id=self.process.process_id,
                            )

                            target_list.append(object_attribute)
            else:
                error_msg = "target_object_attributes is not a dictionary."
                self.logger.error(error_msg)
                raise Exception(error_msg)

        elif target_objects is not None:
            if isinstance(target_objects, dict):
                for target, objects in target_objects.items():

                    target = self.data_store.get_or_create_item(
                        model=Source, source_name=target
                    )

                    if self.dataset_types is not None:
                        for dataset_type in self.dataset_types:
                            self.data_store.get_or_create_item(
                                model=SourceDatasetType,
                                source_id=target.source_id,
                                dataset_type_id=dataset_type.dataset_type_id,
                            )

                    self.data_store.get_or_create_item(
                        model=ProcessTarget,
                        target_source_id=target.source_id,
                        process_id=self.process.process_id,
                    )

                    for item in objects:

                        target_object = self.data_store.get_or_create_item(
                            model=SourceObject,
                            source_id=target.source_id,
                            source_object_name=item,
                        )
                        if self.dataset_types is not None:
                            for dataset_type in self.dataset_types:
                                self.data_store.get_or_create_item(
                                    model=SourceObjectDatasetType,
                                    source_object_id=target_object.source_object_id,
                                    dataset_type_id=dataset_type.dataset_type_id,
                                )

                        self.data_store.get_or_create_item(
                            model=ProcessTargetObject,
                            process_id=self.process.process_id,
                            target_object_id=target_object.source_object_id,
                        )

                        target_list.append(target_object)
            else:
                self.logger.error("It appears target_objects is not a dictionary.")
                raise Exception("It appears target_objects is not a dictionary.")

        elif targets is not None:
            if isinstance(targets, str):
                targets = [targets]

            for target in targets:
                source = self.data_store.get_or_create_item(
                    model=Source, source_name=target
                )
                if self.dataset_types is not None:
                    for dataset_type in self.dataset_types:
                        self.data_store.get_or_create_item(
                            model=SourceDatasetType,
                            source_id=source.source_id,
                            dataset_type_id=dataset_type.dataset_type_id,
                        )

                self.data_store.get_or_create_item(
                    model=ProcessTarget,
                    target_source_id=source.source_id,
                    process_id=self.process.process_id,
                )

                target_list.append(source)
        return target_list

    def set_process_run_low_high_dates(self, low_date=None, high_date=None):
        """
        For the given process run, set the process_run_low_date_time and/or process_run_high_date_time.
        :param low_date: For the set of data being processed, the lowest datetime tracked.  If set multiple times within
         a run, will compare the new to old and adjust accordingly.
        :type low_date: datetime
        :param high_date: For the set of data being processed, the highest datetime tracked.
        :type high_date: datetime
        :return:
        """
        previous_low_date_time = self.process_tracking_run.process_run_low_date_time
        previous_high_date_time = self.process_tracking_run.process_run_low_date_time

        if utilities.determine_low_high_date(
            date=low_date, previous_date=previous_low_date_time, date_type="low"
        ):

            self.process_tracking_run.process_run_low_date_time = low_date

        if utilities.determine_low_high_date(
            date=high_date, previous_date=previous_high_date_time, date_type="high"
        ):

            self.process_tracking_run.process_run_high_date_time = high_date

        self.session.commit()

    def set_process_run_record_count(self, num_records):
        """
        For the given process run, set the process_run_record_count for the number of records processed.  Will also
        update the process' total_record_count - the total number of records ever processed by that process
        :param num_records:
        :return:
        """
        process_run_records = self.process.total_record_count

        if process_run_records == 0 or process_run_records is None:

            self.process.total_record_count = num_records
        else:
            self.process.total_record_count = self.process.total_record_count + (
                num_records - process_run_records
            )

        self.process_tracking_run.process_run_record_count = num_records
        self.session.commit()
