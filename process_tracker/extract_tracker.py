# Extract Tracking
# Used in the creation and editing of extract records.  Used in conjunction with process tracking.
from datetime import datetime
from os.path import basename, normpath

from process_tracker.data_store import DataStore

from process_tracker.models.extract import Extract, ExtractProcess, ExtractStatus, Location


class ExtractTracker:
# TODO:  Add filename/path variable
    def __init__(self, process_run, filename, location_path, location_name=None):
        """
        ExtractTracker is the primary engine for tracking data extracts
        :param process_run: The process object working with extracts (either creating or consuming)
        :type process_run: ProcessTracker object
        :param filename: Name of the data extract file.
        :type filename:  string
        :param location_path: Location (filepath, s3 bucket, etc.) where the file is stored
        :type location_path: string
        :param location_name: Optional parameter to provide a specific name for the location.  If not provided, will use
                              the last directory in the path as the location name.  If type of location can be
                              determined (i.e. S3 bucket), the location type will be prepended.
        :type location_name: string
        """
        self.data_store = DataStore()
        self.session = self.data_store.session
        self.process_run = process_run

        if location_name is None:
            location_name = self.derive_location_name(location_path=location_path)

        self.source = self.process_run.source
        self.filename = filename

        self.location = self.data_store.get_or_create(model=Location
                                                      , location_name=location_name
                                                      , location_path=location_path)

        self.extract = self.data_store.get_or_create(model=Extract
                                                     , extract_filename=filename
                                                     , extract_location_id=self.location.location_id
                                                     , extract_source_id=self.source.source_id)

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

        self.extract.extract_status_id = self.extract_status_initializing
        self.session.commit()

    def change_extract_status(self, new_status):
        """
        Change an extract record status.
        :return:
        """
        status_date = datetime.now()
        new_status = self.extract_status_types[new_status]

        if new_status:
            self.extract.extract_status_id = new_status

            self.extract_process.extract_process_status_id = new_status
            self.extract_process.extract_process_event_date_time = status_date

            self.session.commit()

        else:
            raise Exception('%s is not a valid extract status type.  '
                            'Please add the status to extract_status_lkup' % new_status)

    @staticmethod
    def derive_location_name(location_path):
        """
        If location name is not provided, attempt to derive name from path.
        :param location_path: The data extract file location path.
        :return:
        """
        # Idea is to generalize things like grabbing the last directory name in the path,
        # what type of path is it (normal, s3, etc.)

        location_prefix = None
        location_name = ""

        location_path = location_path.lower()  # Don't care about casing.

        if "s3" in location_path:
            # If the path is an S3 Bucket, prefix to name.

            location_prefix = "s3"

        if location_prefix is not None:

            location_name = location_prefix + " - "

        location_name += basename(normpath(location_path))

        return location_name

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

        extract_process = self.data_store.get_or_create(model=ExtractProcess
                                                        , extract_tracking_id=self.extract.extract_id
                                                        , process_tracking_id=self.process_run.process_tracking_run
                                                                                              .process_tracking_id)

        # Only need to set to 'initializing' when it's the first time a process run is trying to work with files.
        if extract_process.extract_process_status_id is None:

            extract_process.extract_process_status_id = self.extract_status_initializing
            self.session.commit()

        return extract_process
