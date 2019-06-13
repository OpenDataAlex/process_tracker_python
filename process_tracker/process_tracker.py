# Process Tracking
# Used in the creation and editing of process tracking records.

from datetime import datetime
import logging
import os

import boto3
from sqlalchemy.orm import aliased

from process_tracker.data_store import DataStore
from process_tracker.extract_tracker import ExtractTracker
from process_tracker.location_tracker import LocationTracker
from process_tracker.utilities.logging import console
from process_tracker.utilities.settings import SettingsManager
from process_tracker.utilities import utilities

from process_tracker.models.actor import Actor
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
    ProcessDependency,
    ProcessTracking,
    ProcessStatus,
    ProcessSource,
    ProcessTarget,
    ProcessType,
)
from process_tracker.models.source import Source
from process_tracker.models.tool import Tool


class ProcessTracker:
    def __init__(
        self,
        process_name,
        process_type,
        actor_name,
        tool_name,
        sources,
        targets,
        config_location=None,
    ):
        """
        ProcessTracker is the primary engine for tracking data integration processes.
        :param process_name: Name of the process being tracked.
        :param actor_name: Name of the person or environment runnning the process.
        :param tool_name: Name of the tool used to run the process.
        :param sources: A single source name or list of source names for the given process.
        :type sources: list
        :param targets: A single target name or list of target names for the given process.
        :type targets: list
        :param config_location: Location where Process Tracker configuration file is.
        :type config_location: file path
        """
        config = SettingsManager().config

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config["DEFAULT"]["log_level"])
        self.logger.addHandler(console)

        self.data_store = DataStore(config_location=config_location)
        self.session = self.data_store.session

        self.actor = self.data_store.get_or_create_item(
            model=Actor, actor_name=actor_name
        )
        self.process_type = self.data_store.get_or_create_item(
            model=ProcessType, process_type_name=process_type
        )
        self.tool = self.data_store.get_or_create_item(model=Tool, tool_name=tool_name)

        self.process = self.data_store.get_or_create_item(
            model=Process,
            process_name=process_name,
            process_type_id=self.process_type.process_type_id,
            process_tool_id=self.tool.tool_id,
        )

        self.sources = self.register_process_sources(sources=sources)
        self.targets = self.register_process_targets(targets=targets)

        self.process_name = process_name

        # Getting all status types in the event there are custom status types added later.
        self.process_status_types = self.get_process_status_types()

        # For specific status types, need to retrieve their ids to be used for those status types' logic.
        self.process_status_running = self.process_status_types["running"]
        self.process_status_complete = self.process_status_types["completed"]
        self.process_status_failed = self.process_status_types["failed"]

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

            if (
                self.process_status_types[new_status] == self.process_status_complete
            ) or (self.process_status_types[new_status] == self.process_status_failed):

                self.logger.info("Process status changing to failed or completed.")

                self.process_tracking_run.process_run_end_date_time = end_date

                if self.process_status_types[new_status] == self.process_status_failed:
                    self.logger.info(
                        "Process recording as failed.  Setting process last_failed_run_date_time."
                    )

                    self.process.last_failed_run_date_time = end_date

            self.session.commit()

            if (
                self.process_status_types[new_status] == self.process_status_complete
            ) or (self.process_status_types[new_status] == self.process_status_failed):
                self.session.close()

        else:
            raise Exception("The provided status type %s is invalid." % new_status)

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

        self.logger.info("Returning extract files by process.")

        return process_files

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

        if instance is None:
            return False

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

        if location.location_type.location_type_name == "s3":
            s3 = boto3.resource("s3")

            path = location.location_path

            path = path[path.startswith("s3://") and len("s3://") :]

            self.logger.debug("Path is now %s" % path)

            bucket = s3.Bucket(path)

            for file in bucket.objects.all():
                ExtractTracker(
                    process_run=self,
                    filename=file.key,
                    location=location,
                    status="ready",
                )
        else:
            for file in os.listdir(location_path):
                ExtractTracker(
                    process_run=self, filename=file, location=location, status="ready"
                )

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

        if last_run:
            # Must validate that the process is not currently running.

            if last_run.process_status_id != self.process_status_running:
                last_run.is_latest_run = False
                new_run_flag = True
                new_run_id = last_run.process_run_id + 1
            else:
                new_run_flag = False

        if new_run_flag:
            new_run = ProcessTracking(
                process_id=self.process.process_id,
                process_status_id=self.process_status_running,
                process_run_id=new_run_id,
                process_run_start_date_time=datetime.now(),
                process_run_actor_id=self.actor.actor_id,
                is_latest_run=True,
            )

            self.session.add(new_run)
            self.session.commit()

            return new_run

            self.logger.info("Process tracking record added for %s" % self.process_name)

        else:
            raise Exception("The process %s is currently running." % self.process_name)

    def register_process_sources(self, sources):
        """
        Register source(s) to a given process.
        :param sources: List of source name(s)
        :return: List of source objects.
        """
        if isinstance(sources, str):
            sources = [sources]
        source_list = []

        for source in sources:
            source = self.data_store.get_or_create_item(
                model=Source, source_name=source
            )

            self.data_store.get_or_create_item(
                model=ProcessSource,
                source_id=source.source_id,
                process_id=self.process.process_id,
            )

            source_list.append(source)
        return source_list

    def register_process_targets(self, targets):
        """
        Register target source(s) to a given process.
        :param targets: List of source name(s)
        :return: List of source objects.
        """
        if isinstance(targets, str):
            targets = [targets]
        target_list = []

        for target in targets:
            source = self.data_store.get_or_create_item(
                model=Source, source_name=target
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

        if process_run_records == 0:

            self.process.total_record_count += num_records
        else:
            self.process.total_record_count = self.process.total_record_count + (
                num_records - process_run_records
            )

        self.process_tracking_run.process_run_record_count = num_records
        self.session.commit()
