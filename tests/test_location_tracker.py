import unittest

from process_tracker.data_store import DataStore
from process_tracker.location_tracker import LocationTracker


class TestLocationTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_store = DataStore()

    def test_derive_location_name_none(self):
        """
        Testing that if no location name is provided, and it's not a location path, the last directory is set as the
        location name.
        :return:
        """
        test_path = "/tmp/testing/test_dir"

        expected_result = "test_dir"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_name

        self.assertEqual(expected_result, given_result)

    def test_derive_location_name_s3(self):
        """
        Testing that if no location name is provided, and it's an s3 location path, the s3 prefix is added.
        :return:
        """
        test_path = "s3://tmp/testing/test_dir"

        expected_result = "s3 - test_dir"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_name

        self.assertEqual(expected_result, given_result)

    def test_derive_location_type_local(self):
        """
        Testing that if no other location type is found, set as local filesystem.
        :return:
        """
        test_path = "/tmp/testing/test_dir"

        expected_result = "local filesystem"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_type.location_type_name

        self.assertEqual(expected_result, given_result)

    def test_derive_location_type_s3(self):
        """
        Testing that if s3 is part of the location path, the type is set to s3.
        :return:
        """
        test_path = "s3://tmp/testing/test_dir"

        expected_result = "s3"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_type.location_type_name

        self.assertEqual(expected_result, given_result)
