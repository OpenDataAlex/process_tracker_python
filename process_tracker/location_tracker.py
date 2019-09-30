# Location
# For processes dealing with Extract Locations.
import logging
from pathlib import PurePath

from process_tracker.utilities.aws_utilities import AwsUtilities
from process_tracker.utilities.logging import console
from process_tracker.utilities.settings import SettingsManager

from process_tracker.models.extract import Location, LocationType


class LocationTracker:
    def __init__(self, location_path, location_name=None, data_store=None):

        log_level = SettingsManager().determine_log_level()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        self.logger.addHandler(console)

        if data_store is None:
            self.logger.error("Data store is not set.")
            raise Exception("Data store is not set.")
        else:
            self.data_store = data_store
            self.session = self.data_store.session

        self.location_path = location_path.lower()
        self.location_name = location_name
        self.location_bucket_name = self.determine_location_bucket_name()

        if location_name is None:
            self.logger.info("Location name not provided.  Generating.")
            self.location_name = self.derive_location_name()

        self.location_type = self.derive_location_type()

        self.logger.info("Registering extract location.")

        self.location = self.data_store.get_or_create_item(
            model=Location,
            location_name=self.location_name,
            location_path=location_path,
            location_type_id=self.location_type.location_type_id,
            location_bucket_name=self.location_bucket_name,
        )

    def derive_location_name(self):
        """
        If location name is not provided, attempt to derive name from path.
        :return:
        """
        # Idea is to generalize things like grabbing the last directory name in the path,
        # what type of path is it (normal, s3, etc.)

        location_prefix = None

        current_name = (
            self.session.query(Location)
            .filter(Location.location_path == self.location_path)
            .first()
        )

        if current_name is not None:
            location_name = current_name.location_name
        else:
            location_name = ""

            if "s3" in self.location_path:
                # If the path is an S3 Bucket, prefix to name.
                self.logger.info("Location appears to be s3 related.  Setting prefix.")
                location_prefix = "s3 %s" % self.location_bucket_name
            else:
                location_prefix = "local"

            if location_prefix is not None:
                self.logger.info(
                    "Location prefix provided.  Appending to location name."
                )
                location_name = location_prefix + " - "

            if "." in str(PurePath(self.location_path).name):
                location_name += PurePath(self.location_path).parent.name
            else:
                location_name += PurePath(self.location_path).name

            name_count = (
                self.session.query(Location)
                .filter(Location.location_name.like(location_name + "%"))
                .count()
            )

            if name_count >= 1:
                self.logger.info(
                    "The location name already exists.  There are %s instances."
                    % name_count
                )

                location_name = "%s - %s" % (location_name, name_count)

                self.logger.info("Location name is now %s" % location_name)

        return location_name

    def derive_location_type(self):
        """
        Determine the type of location provided.
        :return:
        """

        if "s3" in self.location_path or "s3" in self.location_name:

            self.logger.info("Location appears to be s3 related.  Setting type to s3.")

            location_type = self.data_store.get_or_create_item(
                model=LocationType, location_type_name="s3"
            )

        else:

            self.logger.info(
                "Location did not match special types.  Assuming local directory path."
            )

            location_type = self.data_store.get_or_create_item(
                model=LocationType, location_type_name="local filesystem"
            )

        return location_type

    def register_file_count(self, file_count):
        """
        For the given file count, replace existing count with the new count.
        :param file_count:
        :return:
        """

        self.location.location_file_count = file_count
        self.session.commit()

    def determine_location_bucket_name(self):
        """
        If location is of type 's3', then find which bucket the location belongs to.
        :return:
        """
        self.logger.info("Determining if location is s3.")
        if "s3" in self.location_path or (
            self.location_name is not None and "s3" in self.location_name
        ):

            self.logger.info("Location is in s3.")
            location_bucket_name = AwsUtilities().determine_bucket_name(
                path=self.location_path
            )

        else:
            location_bucket_name = None

            self.session.commit()

        return location_bucket_name
