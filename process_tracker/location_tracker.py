# Location
# For processes dealing with Extract Locations.
import logging
from os.path import basename, normpath

from process_tracker.data_store import DataStore
from process_tracker.utilities.logging import console
from process_tracker.utilities.settings import SettingsManager

from process_tracker.models.extract import Location, LocationType


class LocationTracker:

    def __init__(self, location_path, location_name=None):
        config = SettingsManager().config

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config['DEFAULT']['log_level'])
        self.logger.addHandler(console)

        self.data_store = DataStore()

        self.location_path = location_path.lower()

        if location_name is None:
            self.location_name = self.derive_location_name()
        else:
            self.location_name = location_name

        self.location_type = self.derive_location_type()
        self.location = self.data_store.get_or_create_item(model=Location
                                                           , location_name=self.location_name
                                                           , location_path=location_path
                                                           , location_type=self.location_type.location_type_id)

    def derive_location_name(self):
        """
        If location name is not provided, attempt to derive name from path.
        :return:
        """
        # Idea is to generalize things like grabbing the last directory name in the path,
        # what type of path is it (normal, s3, etc.)

        location_prefix = None

        location_name = ""

        if "s3" in self.location_path:
            # If the path is an S3 Bucket, prefix to name.

            location_prefix = "s3"

        if location_prefix is not None:
            location_name = location_prefix + " - "

        location_name += basename(normpath(self.location_path))

        return location_name

    def derive_location_type(self):
        """
        Determine the type of location provided.
        :return:
        """

        if "s3" in self.location_path or "s3" in self.location_name:

            location_type = self.data_store.get_or_create_item(model=LocationType
                                                               , location_type_name="s3")

        else:
            location_type = self.data_store.get_or_create_item(model=LocationType
                                                               , location_type_name="local directory")

        return location_type
