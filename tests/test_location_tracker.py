import unittest

from process_tracker.models.extract import Location

from process_tracker.utilities.data_store import DataStore
from process_tracker.location_tracker import LocationTracker


class TestLocationTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_store = DataStore()
        cls.session = cls.data_store.session

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def tearDown(self):
        self.session.query(Location).delete()
        self.session.commit()

    def test_derive_location_name_no_trailing_slash_local(self):
        """
        Testing that if no location name is provided, and it's not a location already, the last directory is set as the
        location name even if a trailing slash is not provided.
        :return:
        """
        test_path = "/tmp/testing/test_dir"

        expected_result = "local - test_dir"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_name

        self.assertEqual(expected_result, given_result)

    def test_derive_location_name_no_trailing_slash_s3(self):
        """
        Testing that if no location name is provided, and it's not a location already, the last directory is set as the
        location name even if a trailing slash is not provided.
        :return:
        """
        test_path = "s3://tmp/testing/test_dir"

        expected_result = "s3 tmp - test_dir"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_name

        self.assertEqual(expected_result, given_result)

    def test_derive_location_name_none(self):
        """
        Testing that if no location name is provided, and it's not a location path, the last directory is set as the
        location name.
        :return:
        """
        test_path = "/tmp/testing/test_dir/"

        expected_result = "local - test_dir"
        given_result = LocationTracker(
            location_path=test_path, data_store=self.data_store
        ).location_name

        self.assertEqual(expected_result, given_result)

    def test_derive_location_name_s3(self):
        """
        Testing that if no location name is provided, and it's an s3 location path, the s3 prefix is added.
        :return:
        """
        test_path = "s3://tmp/testing/test_dir/"

        expected_result = "s3 tmp - test_dir"
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

    def test_location_tracker_no_data_store(self):
        """
        Testing that if location tracker is used but data store is not provided, throw error.
        :return:
        """

        with self.assertRaises(Exception) as context:
            LocationTracker(location_name="testing", location_path="fake path")

        self.assertTrue("Data store is not set." in str(context.exception))

    def test_register_file_count(self):
        """
        Testing that if a file count is set, it will be returned correctly.
        :return:
        """

        test_path = "/tmp/testing/test_dir"
        expected_result = 123

        location = LocationTracker(location_path=test_path, data_store=self.data_store)
        location.register_file_count(file_count=123)

        self.assertEqual(expected_result, location.location.location_file_count)

    def test_determine_location_bucket_name_s3(self):
        """
        Testing that if the location is related to s3, a bucket name will be set.
        :return:
        """
        expected_result = "test-bucket"

        location = LocationTracker(
            location_path="https://test-bucket.s3.amazonaws.com/this/is/a/test/dir/file.txt",
            data_store=self.data_store,
        )

        given_result = location.location.location_bucket_name

        self.assertEqual(expected_result, given_result)

    def test_determine_location_bucket_name_local(self):
        """
        Testing that if the location is not related to s3, a bucket name will not be set.
        :return:
        """
        expected_result = None

        location = LocationTracker(
            location_path="/local/dir/path/text.txt", data_store=self.data_store
        )

        given_result = location.location.location_bucket_name

        self.assertEqual(expected_result, given_result)

    def test_determine_location_name_duplicate_name_s3(self):
        """
        Testing that if two different s3 locations produce the same location name
        that the second location will append a number to ensure uniqueness.
        :return:
        """
        expected_result = "s3 duplicate-test - dir - 1"

        location = LocationTracker(
            location_path="https://duplicate-test.s3.amazonaws.com/this/is/a/test/dir/file.txt",
            data_store=self.data_store,
        )

        dupe_location = LocationTracker(
            location_path="https://duplicate-test.s3.amazonaws.com/this/is/another/test/dir/file.txt",
            data_store=self.data_store,
        )

        given_result = dupe_location.location.location_name

        self.assertEqual(expected_result, given_result)

    def test_determine_location_name_duplicate_name_local(self):
        """
        Testing that if two different s3 locations produce the same location name
        that the second location will append a number to ensure uniqueness.
        :return:
        """
        expected_result = "local - test_dir - 1"

        location = LocationTracker(
            location_path="/tmp/duplicate_testing/test_dir/file.txt",
            data_store=self.data_store,
        )

        dupe_location = LocationTracker(
            location_path="/tmp/duplicate_testing_another/test_dir/file.txt",
            data_store=self.data_store,
        )

        given_result = dupe_location.location.location_name

        self.assertEqual(expected_result, given_result)

    def test_determine_location_name_file_not_part_s3(self):
        """
        Testing that when a s3 path is provided with a filename at the end, the file is ignored.
        :return:
        """
        expected_result = "s3 test-bucket - dir"

        location = LocationTracker(
            location_path="https://test-bucket.s3.amazonaws.com/this/is/a/test/dir/file.txt",
            data_store=self.data_store,
        )

        given_result = location.location.location_name

        self.assertEqual(expected_result, given_result)

    def test_determine_location_name_file_not_part_local(self):
        """
        Testing that when a local path is provided with a filename at the end, the file is ignored.
        :return:
        """
        expected_result = "local - path"

        location = LocationTracker(
            location_path="/local/dir/path/text.txt", data_store=self.data_store
        )

        given_result = location.location.location_name

        self.assertEqual(expected_result, given_result)
