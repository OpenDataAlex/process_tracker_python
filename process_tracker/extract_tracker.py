# Extract Tracking
# Used in the creation and editing of extract records.  Used in conjunction with process tracking.
from datetime import datetime
import logging
import os
from os.path import join


from process_tracker.data_store import DataStore
from process_tracker.location_tracker import LocationTracker
from process_tracker.utilities.settings import SettingsManager
from process_tracker.models.extract import Extract, ExtractProcess, ExtractStatus, Location


class ExtractTracker:

    def __init__(self, process_run, filename, location=None, location_name=None, location_path=None, status=None):
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
        """
        config = SettingsManager().config

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config['DEFAULT']['log_level'])

        self.data_store = DataStore()
        self.session = self.data_store.session
        self.process_run = process_run

        self.filename = filename

        if location is not None:
            self.location = location
        elif location_path is not None:
            self.location = LocationTracker(location_name=location_name, location_path=location_path)
        else:
            raise Exception('A location object or location_path must be provided.')

        self.extract = self.data_store.get_or_create_item(model=Extract
                                                          , extract_filename=filename
                                                          , extract_location_id=self.location.location.location_id)

        if location_path is not None:
            self.full_filename = join(location_path, filename)
        else:
            self.full_filename = join(self.location.location_path, self.extract.extract_filename)

        # Getting all status types in the event there are custom status types added later.
        self.extract_status_types = self.get_extract_status_types()

        # For specific status types, need to retrieve their ids to be used for those status types' logic.

        self.extract_status_initializing = self.extract_status_types['initializing']
        self.extract_status_ready = self.extract_status_types['ready']
        self.extract_status_loading = self.extract_status_types['loading']
        self.extract_status_loaded = self.extract_status_types['loaded']
        self.extract_status_archived = self.extract_status_types['archived']
        self.extract_status_deleted = self.extract_status_types['deleted']
        self.extract_status_error = self.extract_status_types['error']

        self.extract_process = self.retrieve_extract_process()

        if status is not None:
            self.change_extract_status(new_status=status)
        else:
            self.extract.extract_status_id = self.extract_status_initializing

        self.session.commit()

    def change_extract_status(self, new_status):
        """
        Change an extract record status.
        :return:
        """

        status_date = datetime.now()
        if new_status in self.extract_status_types:
            self.logger.info('Setting extract status to %s' % new_status)

            new_status = self.extract_status_types[new_status]

            self.extract.extract_status_id = new_status

            self.extract_process.extract_process_status_id = new_status
            self.extract_process.extract_process_event_date_time = status_date

            self.session.commit()

        else:
            raise Exception('%s is not a valid extract status type.  '
                            'Please add the status to extract_status_lkup' % new_status)

    def get_extract_status_types(self):
        """
        Get list of process status types and return dictionary.
        :return:
        """
        status_types = {}

        for record in self.session.query(ExtractStatus):
            status_types[record.extract_status_name] = record.extract_status_id

        return status_types

    def retrieve_extract_process(self):
        """
        Create and initialize or retrieve the process/extract relationship.
        :return:
        """

        extract_process = self.data_store.get_or_create_item(model=ExtractProcess
                                                             , extract_tracking_id=self.extract.extract_id
                                                             , process_tracking_id=self.process_run.process_tracking_run
                                                             .process_tracking_id)

        # Only need to set to 'initializing' when it's the first time a process run is trying to work with files.
        if extract_process.extract_process_status_id is None:

            extract_process.extract_process_status_id = self.extract_status_initializing
            self.session.commit()

        return extract_process
