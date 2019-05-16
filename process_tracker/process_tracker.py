# Process Tracking
# Used in the creation and editing of process tracking records.

from datetime import datetime
import logging
from os.path import join

from process_tracker.data_store import DataStore

from process_tracker.models.actor import Actor
from process_tracker.models.extract import Extract, ExtractProcess, ExtractStatus, Location
from process_tracker.models.process import ErrorTracking, ErrorType, Process, ProcessTracking, ProcessStatus, ProcessType
from process_tracker.models.source import Source
from process_tracker.models.tool import Tool


class ProcessTracker:

    def __init__(self, process_name, process_type, actor_name, tool_name, source_name):
        """
        ProcessTracker is the primary engine for tracking data integration processes.
        :param process_name: Name of the process being tracked.
        :param actor_name: Name of the person or environment runnning the process.
        :param tool_name: Name of the tool used to run the process.
        :param source_name: Name of the source that the data is coming from.
        """

        self.logger = logging.getLogger(__name__)

        self.data_store = DataStore()
        self.session = self.data_store.session

        self.actor = self.data_store.get_or_create(model=Actor, actor_name=actor_name)
        self.process_type = self.data_store.get_or_create(model=ProcessType, process_type_name=process_type)
        self.source = self.data_store.get_or_create(model=Source, source_name=source_name)
        self.tool = self.data_store.get_or_create(model=Tool, tool_name=tool_name)

        self.process = self.data_store.get_or_create(model=Process, process_name=process_name
                                                     , process_source_id=self.source.source_id
                                                     , process_type_id=self.process_type.process_type_id
                                                     , process_tool_id=self.tool.tool_id)

        self.process_name = process_name

        # Getting all status types in the event there are custom status types added later.
        self.process_status_types = self.get_process_status_types()

        # For specific status types, need to retrieve their ids to be used for those status types' logic.
        self.process_status_running = self.process_status_types['running']
        self.process_status_complete = self.process_status_types['completed']
        self.process_status_failed = self.process_status_types['failed']

        self.process_tracking_run = self.register_new_process_run()

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

        if self.process_status_types[new_status]:

            self.process_tracking_run.process_status_id = self.process_status_types[new_status]

            if (self.process_status_types[new_status] == self.process_status_complete) \
                    or (self.process_status_types[new_status] == self.process_status_failed):

                self.logger.info("Process status changing to failed or completed.")

                self.process_tracking_run.process_run_end_date_time = end_date

                if self.process_status_types[new_status] == self.process_status_failed:
                    self.logger.info("Process recording as failed.  Setting process last_failed_run_date_time.")

                    self.process.last_failed_run_date_time = end_date

            self.session.commit()

        else:
            raise Exception('%s is not a valid process status type.  '
                            'Please add the status to process_status_type_lkup' % new_status)

    def find_ready_extracts_by_filename(self, filename):
        """
        For the given filename, or filename part, find all matching extracts that are ready for processing.

        :param filename:
        :return:
        """
        extract_files = []

        process_files = self.session.query(Extract.extract_filename, Location.location_path)\
                                           .join(Location)\
                                           .join(ExtractStatus)\
                                           .filter(Extract.extract_filename.like("%" + filename + "%"))\
                                           .filter(ExtractStatus.extract_status_name == 'ready') \
                                           .order_by(Extract.extract_registration_date_time)

        for record in process_files:
            extract_files.append(join(record.location_path, record.extract_filename))

        return extract_files

    def find_ready_extracts_by_location(self, location):
        """
        For the given location name, find all matching extracts that are ready for processing
        :param location:
        :return:
        """
        extract_files = []

        process_files = self.session.query(Extract.extract_filename, Location.location_path)\
                               .join(Location)\
                               .join(ExtractStatus)\
                               .filter(ExtractStatus.extract_status_name == 'ready')\
                               .filter(Location.location_name == location) \
                               .order_by(Extract.extract_registration_date_time)

        for record in process_files:
            extract_files.append(join(record.location_path, record.extract_filename))

        return extract_files

    def find_ready_extracts_by_process(self, extract_process_name):
        """
        For the given named process, find the extracts that are ready for processing.
        :return: List of OS specific filepaths with filenames.
        """
        extract_files = []

        process_files = self.session.query(Extract.extract_filename, Location.location_path) \
            .join(ExtractStatus, Extract.extract_status_id == ExtractStatus.extract_status_id) \
            .join(Location, Extract.extract_location_id == Location.location_id) \
            .join(ExtractProcess, Extract.extract_id == ExtractProcess.extract_tracking_id) \
            .join(ProcessTracking) \
            .join(Process) \
            .filter(Process.process_name == extract_process_name
                    , ExtractStatus.extract_status_name == 'ready') \
            .order_by(Extract.extract_registration_date_time)

        for record in process_files:
            extract_files.append(join(record.location_path, record.extract_filename))

        return extract_files

    def get_latest_tracking_record(self, process):
        """
        For the given process, find the latest tracking record.
        :param process: The process' process_id.
        :type process: integer
        :return:
        """

        instance = self.session.query(ProcessTracking)\
            .filter(ProcessTracking.process_id == process.process_id)\
            .order_by(ProcessTracking.process_run_id.desc())\
            .first()

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

    def raise_run_error(self, error_type_name, error_description=None, fail_run=False, end_date=None):
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
            end_date = datetime.now()  # Need the date to match across all parts of the event in case the run is failed.

        if error_description is None:
            error_description = 'Unspecified error.'

        error_type = self.data_store.get_or_create(model=ErrorType, create=False, error_type_name=error_type_name)

        run_error = ErrorTracking(error_type_id=error_type.error_type_id
                                  , error_description=error_description
                                  , process_tracking_id=self.process_tracking_run.process_tracking_id
                                  , error_occurrence_date_time=end_date)

        self.logger.error('%s - %s - %s' % (self.process_name, error_type_name, error_description))
        self.session.add(run_error)
        self.session.commit()

        if fail_run:
            self.change_run_status(new_status='failed', end_date=end_date)
            self.session.commit()
            raise Exception('Process halting.  An error triggered the process to fail.')

    def register_new_process_run(self):
        """
        When a new process instance is starting, register the run in process tracking.
        :return:
        """

        last_run = self.get_latest_tracking_record(process=self.process)

        new_run_flag = True
        new_run_id = 1

        if last_run:
            # Must validate that the process is not currently running.

            if last_run.process_status_id != self.process_status_running:
                last_run.is_latest_run = False
                new_run_flag = True
                new_run_id = last_run.process_run_id + 1
            else:
                new_run_flag = False

        if new_run_flag:
            new_run = ProcessTracking(process_id=self.process.process_id
                                      , process_status_id=self.process_status_running
                                      , process_run_id=new_run_id
                                      , process_run_start_date_time=datetime.now()
                                      , process_run_actor_id=self.actor.actor_id
                                      , is_latest_run=True)

            self.session.add(new_run)
            self.session.commit()

            return new_run

            self.logger.info('Process tracking record added for %s' % self.process_name)

        else:
            raise Exception('The process %s is currently running.' % self.process_name)
            exit()
