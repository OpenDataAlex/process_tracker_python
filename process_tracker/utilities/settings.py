# Settings manager and configuration, both for initialization and reading.

import configparser
import logging
import os
from pathlib import Path
import tempfile

from process_tracker.utilities.aws_utilities import AwsUtilities


class SettingsManager:
    def __init__(self, config_location=None):
        """
        Determine if config file exists, and if not create a basic file under the application directory.
        :param config_location: Location where configuration file can be found.
        :type config_location: str
        """

        self.config = configparser.ConfigParser(allow_no_value=True)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel("DEBUG")

        self.aws_utils = AwsUtilities()

        exists = False

        if config_location is None:
            home = Path.home()

            self.config_path = str(home.joinpath(".process_tracker/"))
            self.config_file = str(
                Path(self.config_path).joinpath("process_tracker_config.ini")
            )

            exists = os.path.isfile(self.config_file)

        else:
            self.config_path = config_location

            if "process_tracker_config.ini" not in self.config_path:
                self.logger.debug(
                    "process_tracker_config.ini not present.  Appending to %s"
                    % self.config_path
                )

                self.config_file = self.config_path

                if not self.config_file.endswith("/"):
                    self.config_file += "/"

                self.config_file += "process_tracker_config.ini"

                self.logger.debug("Config file is now %s" % self.config_file)
            else:
                self.logger.debug(
                    "process_tracker_config.ini present.  Setting config_path to config_file."
                )
                self.config_file = self.config_path

            if self.aws_utils.determine_valid_s3_path(
                path=self.config_path
            ) and self.aws_utils.determine_s3_file_exists(path=self.config_file):

                exists = True

        if exists:
            self.read_config_file()
        else:
            # How to handle if exists is false and it's s3?

            self.create_config_file()

    def create_config_file(self):
        """
        When config file does not exist, setup a stock config file.
        :return:
        """

        self.config["DEFAULT"] = {"log_level": "ERROR"}

        self.config["DEFAULT"]["data_store_type"] = "None"
        self.config["DEFAULT"]["data_store_username"] = "None"
        self.config["DEFAULT"]["data_store_password"] = "None"
        self.config["DEFAULT"]["data_store_host"] = "None"
        self.config["DEFAULT"]["data_store_port"] = "None"
        self.config["DEFAULT"]["data_store_name"] = "None"

        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)

        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)

    def read_config_file(self):
        """
        Read and parse the config file for use.
        :return:
        """

        if self.aws_utils.determine_valid_s3_path(
            path=self.config_path
        ) and self.aws_utils.determine_s3_file_exists(path=self.config_file):

            temp_file = tempfile.NamedTemporaryFile()
            bucket_name = self.aws_utils.determine_bucket_name(path=self.config_path)

            bucket = self.aws_utils.get_s3_bucket(bucket_name=bucket_name)
            key = self.aws_utils.determine_file_key(path=self.config_file)

            bucket.download_file(key, temp_file.name)

            with open(temp_file.name, "r") as f:
                self.config.readfp(f)
            temp_file.close()

        else:

            return self.config.read(self.config_file)
