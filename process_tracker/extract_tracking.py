# Extract Tracking
# Used in the creation and editing of extract records.  Used in conjunction with process tracking.

from models.extract import Extract, Location
from models.source import Source


class ExtractTracker:

    def __init__(self, source_name, filename, location, process_name):
        """
        ExtractTracker is the primary engine for tracking data extracts
        :param source_name: Name of the source where data extract is from.
        :type source_name: string
        :param filename: Name of the data extract file.
        :type filename:  string
        :param location: Location (filepath, s3 bucket, etc.) where the file is stored
        :type location: string
        :param process_name: Name of the process that produced the data extract.
        :type process_name: string
        """

