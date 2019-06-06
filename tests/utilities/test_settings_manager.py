import configparser
import shutil
import unittest

from process_tracker.utilities.settings import SettingsManager


class TestSettingsManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        cls.config = configparser.ConfigParser(allow_no_value=True)

    def test_config_location_set(self):
        """
        Testing that if config_location is set that the path is used instead of setting to home directory.
        :return:
        """

        expected_result = "/tmp/testing/process_tracker_config.ini"

        given_result = SettingsManager(config_location="/tmp/testing/").config_file

        shutil.rmtree("/tmp/testing/")

        self.assertEqual(expected_result, given_result)

    def test_create_config_file(self):
        """
        Testing that if the config file does not exist, it is created.
        :return:
        """

        settings = SettingsManager(config_location="/tmp/testing/").config
        given_result = settings["DEFAULT"]["data_store_type"]

        expected_result = "None"

        self.assertEqual(expected_result, given_result)
