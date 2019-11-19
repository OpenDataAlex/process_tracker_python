import configparser
import os
from pathlib import Path
import shutil
import unittest

import boto3
import botocore
from moto import mock_s3

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

    def test_config_location_set_no_file(self):
        """
        Testing that if config_location is set, but no config file is provided and the path does not end with
        a forward slash, it is added.
        :return:
        """
        expected_result = "/tmp/testing/process_tracker_config.ini"

        given_result = SettingsManager(config_location="/tmp/testing").config_file

        self.assertEqual(expected_result, given_result)

    def test_config_location_set_with_file(self):
        """
        Testing that if config_location is set, but a config file is provided.
        :return:
        """
        expected_result = "/tmp/testing/process_tracker_config.ini"

        given_result = SettingsManager(
            config_location="/tmp/testing/process_tracker_config.ini"
        ).config_file

        self.assertEqual(expected_result, given_result)

    def test_config_location_set_with_ini_file(self):
        """
        Testing that if an .ini file that is NOT named process_tracker_config.ini_in the config_location, it is accepted
        as the config file.
        :return:
        """

        expected_result = "/home/travis/.process_tracker/process_tracker_config_dev.ini"

        given_result = SettingsManager(
            config_location="/home/travis/.process_tracker/process_tracker_config_dev.ini"
        ).config_file

        self.assertEqual(expected_result, given_result)

    def test_config_location_s3(self):
        """
        Testing that if config_location is set and the path is an s3 file/location, use that instead of the home
        directory.
        :return:
        """

        expected_result = "s3://test_bucket/process_tracker_config.ini"

        given_result = SettingsManager(config_location="s3://test_bucket/").config_file

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

    # def test_determine_log_level_no_file(self):
    #     """
    #     If unable to get config option 'log_level', return value 'DEBUG'
    #     :return:
    #     """
    #     expected_result = "DEBUG"
    #     given_result = SettingsManager(
    #         config_location="/not/real"
    #     ).determine_log_level()
    #
    #     self.assertEqual(expected_result, given_result)

    @unittest.skipIf(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        "Skipping this test on Travis CI.",
    )
    @mock_s3
    def test_read_config_file_s3(self):
        """
        Testing that if config file is on s3 then the file is pulled down and read.
        :return:
        """
        expected_keys = ["process_tracker_config.ini"]
        test_bucket = "test_bucket"

        # path = (
        #    "s3://test_bucket/process_tracker_config/SANDBOX/process_tracker_config.ini"
        # )
        path = "s3://test_bucket/process_tracker_config.ini"

        client = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )

        try:
            s3 = boto3.resource(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="fake_access_key",
                aws_secret_access_key="fake_secret_key",
            )
            s3.meta.client.head_bucket(Bucket=test_bucket)

        except botocore.exceptions.ClientError:
            pass
        else:
            err = "%s should not exist" % test_bucket
            raise EnvironmentError(err)

        client.create_bucket(Bucket=test_bucket)

        current_dir = os.path.join(os.path.dirname(__file__), "..")
        fixtures_dir = os.path.join(current_dir, "fixtures")

        for file in expected_keys:
            key = file
            file = os.path.join(fixtures_dir, file)
            client.upload_file(Filename=file, Bucket=test_bucket, Key=key)

        settings = SettingsManager(config_location=path).config

        given_result = settings["DEFAULT"]["data_store_username"]

        expected_result = "pt_admin_test"

        self.assertEqual(expected_result, given_result)
