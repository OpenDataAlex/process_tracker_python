# Settings manager and configuration, both for initialization and reading.

import configparser
import os
from pathlib import Path


class SettingsManager:
    def __init__(self, config_location=None):
        """
        Determine if config file exists, and if not create a basic file under the application directory.
        :param config_location: Location where configuration file can be found.
        :type config_location: str
        """

        self.config = configparser.ConfigParser(allow_no_value=True)

        if config_location is None:
            home = str(Path.home())
            self.config_path = os.path.join(home, ".process_tracker/")
            self.config_file = os.path.join(
                self.config_path, "process_tracker_config.ini"
            )

        else:
            self.config_path = config_location
            self.config_file = os.path.join(
                self.config_path, "process_tracker_config.ini"
            )

        exists = os.path.isfile(self.config_file)

        if exists:
            self.read_config_file()
        else:
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

        return self.config.read(self.config_file)
