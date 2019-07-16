import logging
import unittest

import boto3
import botocore
from moto import mock_s3
import os

from process_tracker.utilities.aws_utilities import AwsUtilities


class TestAwsUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.Logger(__name__)

        cls.aws_util = AwsUtilities()

    def test_determine_bucket_name_valid_path_s3(self):
        """
        If path provided is an AWS CLI url, parse and return the bucket name.
        :return:
        """
        path = "s3://test_bucket/bucket_file.csv"

        expected_result = "test_bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_valid_path_url_https_bucket_front_long_filepath(
        self
    ):
        """
        Ensuring that bucket name is correctly found, event with long urls
        :return:
        """

        path = "https://test-bucket.s3.amazonaws.com/this/is/a/test/dir/file.txt"

        expected_result = "test-bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_valid_path_url_http_bucket_front(self):
        """
        If path provided is an AWS http URL, parse and return the bucket name.
        :return:
        """
        path = "http://test_bucket.s3.amazonaws.com/bucket_file.csv"

        expected_result = "test_bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_valid_path_url_https_bucket_front(self):
        """
        If path provided is an AWS https URL, parse and return the bucket name
        :return:
        """
        path = "https://test_bucket.s3.amazonaws.com/bucket_file.csv"

        expected_result = "test_bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_valid_path_url_http_bucket_back(self):
        """
        If path provided is an AWS http URL, parse and return the bucket name.
        :return:
        """
        path = "http://s3.amazonaws.com/test_bucket/bucket_file.csv"

        expected_result = "test_bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_valid_path_url_http_bucket_back_long_key(self):
        """
        If path provided is an AWS http URL, parse and return the bucket name.
        :return:
        """
        path = (
            "http://s3.amazonaws.com/test_bucket/with/subdirs/aplenty/bucket_file.csv"
        )

        expected_result = "test_bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_valid_path_url_https_bucket_back(self):
        """
        If path provided is an AWS https URL, parse and return the bucket name
        :return:
        """
        path = "https://s3.amazonaws.com/test_bucket/bucket_file.csv"

        expected_result = "test_bucket"

        given_result = self.aws_util.determine_bucket_name(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_bucket_name_invalid_path(self):
        """
        If path provided is an invalid s3 path, throw exception.
        :return:
        """
        path = "invalid.path/test_bucket/bucket_file.csv"

        with self.assertRaises(Exception) as context:

            self.aws_util.determine_bucket_name(path=path)

        return self.assertTrue(
            "It appears the URL is not a valid s3 path. invalid.path/test_bucket/bucket_file.csv"
            in str(context.exception)
        )

    def test_determine_bucket_name_invalid_path_url(self):
        """
        If path provided is an invalid s3 path, throw exception.
        :return:
        """
        path = "httpz://s3.amazonaws.com/test_bucket/bucket_file.csv"

        with self.assertRaises(Exception) as context:

            self.aws_util.determine_bucket_name(path=path)

        return self.assertTrue(
            "It appears the URL is not valid. httpz://s3.amazonaws.com/test_bucket/bucket_file.csv"
            in str(context.exception)
        )

    def test_determine_file_key_valid_path_s3(self):
        """
        If path provided is an AWS CLI url, parse and return the object key.
        :return:
        """
        path = "s3://test_bucket/folder/bucket_file.csv"

        expected_result = "folder/bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_http_bucket_front(self):
        """
        If path provided is an AWS http URL, parse and return the object key.
        :return:
        """

        path = "http://test_bucket.s3.amazonaws.com/bucket_file.csv"

        expected_result = "bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_https_bucket_front(self):
        """
        If path provided is an AWS https URL, parse and return the object key.
        :return:
        """

        path = "https://test_bucket.s3.amazonaws.com/bucket_file.csv"

        expected_result = "bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_http_bucket_back(self):
        """
        If path provided is an AWS http URL, parse and return the object key.
        :return:
        """

        path = "http://s3.amazonaws.com/test_bucket/bucket_file.csv"

        expected_result = "bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_http_bucket_back_long_key(self):
        """
        If path provided is an AWS http URL, parse and return the object key.
        :return:
        """

        path = "http://s3.amazonaws.com/test_bucket/with/afew/subdir/bucket_file.csv"

        expected_result = "with/afew/subdir/bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_https_bucket_back(self):
        """
        If path provided is an AWS https URL, parse and return the object key.
        :return:
        """

        path = "https://s3.amazonaws.com/test_bucket/bucket_file.csv"

        expected_result = "bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_http_bucket_back_with_region(self):
        """
        If path provided is an AWS http URL, parse and return the object key.
        :return:
        """

        path = "http://s3.us-east-1.amazonaws.com/test_bucket/bucket_file.csv"

        expected_result = "bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_valid_path_https_bucket_back_with_region(self):
        """
        If path provided is an AWS https URL, parse and return the object key.
        :return:
        """

        path = "https://s3.us-east-1.amazonaws.com/test_bucket/bucket_file.csv"

        expected_result = "bucket_file.csv"

        given_result = self.aws_util.determine_file_key(path=path)

        self.assertEqual(expected_result, given_result)

    def test_determine_file_key_invalid_path(self):
        """
        If path provided is an invalid URL, throw an exception.
        :return:
        """

        path = "invalid.path/test_bucket/bucket_file.csv"

        with self.assertRaises(Exception) as context:

            self.aws_util.determine_file_key(path=path)

        return self.assertTrue(
            "It appears the URL is not valid. invalid.path/test_bucket/bucket_file.csv"
            in str(context.exception)
        )

    def test_determine_file_key_invalid_path_url(self):
        """
        If path provided is an invalid URL, throw an exception.
        :return:
        """

        path = "https://s3.argle-barglenarf.amazonaws.com/test_bucket/test_file.csv"

        with self.assertRaises(Exception) as context:

            self.aws_util.determine_file_key(path=path)

        return self.assertTrue(
            "It appears the URL is not a valid s3 path. https://s3.argle-barglenarf.amazonaws.com/test_bucket/test_file.csv"
            in str(context.exception)
        )

    @unittest.skipIf(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        "Skipping this test on Travis CI.",
    )
    @mock_s3
    def test_determine_s3_file_exists_valid_file(self):
        """
        If path provided is valid, determine if file exists or not.
        :return:
        """
        expected_keys = ["test_local_dir_1.csv"]
        test_bucket = "test_bucket"

        path = "s3://test_bucket/test_local_dir_1.csv"

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
            self.logger.debug("Filename %s" % file)
            self.logger.debug("Fixtures dir %s" % fixtures_dir)

            file = os.path.join(fixtures_dir, file)
            client.upload_file(Filename=file, Bucket=test_bucket, Key=key)

        given_result = self.aws_util.determine_s3_file_exists(path=path)
        expected_result = True

        self.assertEqual(expected_result, given_result)

    @mock_s3
    def test_determine_s3_file_exists_invalid_file(self):
        """
        If path provided, but file does not exist is s3, throw ClientError.
        :return:
        """

        path = "s3://test_bucket/test_local_dir_1.csv"

        given_result = self.aws_util.determine_s3_file_exists(path=path)
        expected_result = False

        return self.assertEqual(expected_result, given_result)

    def test_determine_valid_s3_path_valid_path_s3(self):
        """
        Testing that if path is an AWS CLI URL, that the path is validated.
        :return:
        """
        path = "s3://test_bucket/folder/bucket_file.csv"

        given_result = self.aws_util.determine_valid_s3_path(path=path)

        self.assertTrue(given_result)

    def test_determine_valid_s3_path_valid_path_http(self):
        """
        Testing that if a path is a valid http AWS S3 URL, that the path is validated.
        :return:
        """
        path = "http://test_bucket.s3.amazonaws.com/bucket_file.csv"

        given_result = self.aws_util.determine_valid_s3_path(path=path)

        self.assertTrue(given_result)

    def test_determine_valid_s3_path_valid_path_https(self):
        """
        Testing that if a path is a valid https AWS S3 URL, that the path is validated.
        :return:
        """
        path = "https://test_bucket.s3.amazonaws.com/bucket_file.csv"

        given_result = self.aws_util.determine_valid_s3_path(path=path)

        self.assertTrue(given_result)

    def test_determine_valid_s3_path_invalid_path(self):
        """
        Testing that if a path is not a valid URL, that the path is not validated.
        :return:
        """
        path = "argle.bargle/test_bucket/bucket_file.csv"

        given_result = self.aws_util.determine_valid_s3_path(path=path)

        self.assertFalse(given_result)
