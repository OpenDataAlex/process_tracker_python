# AWS Utilities
# Utilities for working with AWS services

import logging

import boto3
from botocore.errorfactory import ClientError


class AwsUtilities:
    def __init__(self):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel("DEBUG")

        self.s3 = boto3.resource("s3")

    def determine_bucket_name(self, path):
        """
        For the given path, return the bucket name, if path is a valid s3 URL.
        :param path: Valid s3 URL.
        :return:
        """
        if self.determine_valid_s3_path(path=path):
            self.logger.debug("Parsing %s" % path)

            if "s3://" in path:
                path = path[path.startswith("s3://") and len("s3://") :]

                self.logger.debug("Path is now %s" % path)

                bucket_name = path.split("/")[0]

                self.logger.debug("Bucket name is %s" % bucket_name)

            elif "s3" in path and ".amazonaws.com" in path:
                if path.startswith("http://"):

                    path = path[len("http://") :]

                    self.logger.debug("Path is now %s" % path)

                elif path.startswith("https://"):

                    path = path[len("https://") :]
                    self.logger.debug("Path is now %s" % path)

                else:
                    error_msg = "It appears the URL is not valid. %s" % path

                    self.logger.error(error_msg)
                    raise Exception(error_msg)

                bucket_name = path.split(".")[0]
        else:
            error_msg = "It appears the URL is not a valid s3 path. %s" % path

            self.logger.error(error_msg)
            raise Exception(error_msg)

        return bucket_name

    def determine_file_key(self, path):
        """
        Determine the key of the s3 file based on the filepath provided.
        :param path: Full s3 filepath.  Can be in s3:// or http(s):// format.
        :type path: str
        :return:
        """

        if "s3://" in path:
            groups = path.split("/", 3)

            key = groups[3]

        elif "s3" in path and ".amazonaws.com" in path:
            groups = path.split(".amazonaws.com/")

            key = groups[1]

        else:
            error_msg = "It appears the URL is not valid. %s" % path

            self.logger.error(error_msg)
            raise Exception(error_msg)

        return key

    def determine_s3_file_exists(self, path):
        """
        Determine if a file exists on s3 based on given path.
        :param path: Full s3 filepath.  Can be in s3:// or http(s):// format.
        :type path: str
        :return:
        """
        self.logger.info("Determining if %s exists." % path)

        bucket_name = self.determine_bucket_name(path=path)

        key = self.determine_file_key(path=path)

        try:
            self.s3.Object(bucket_name, key).load()

            return True

        except ClientError:
            error_msg = "File %s does not exist in s3." % path
            self.logger.error(error_msg)

            return False

    def determine_valid_s3_path(self, path):
        """
        Take the provided path and determine if valid s3 URL.
        :param path: Full s3 filepath.  Can be in s3:// or http(s):// format.
        :type path: str
        :return:
        """
        self.logger.debug("Validating %s" % path)
        if "s3://" in path:
            self.logger.debug("s3:// in path.")
            return True
        elif "s3" in path and ".amazonaws.com" in path:
            self.logger.debug("s3 and .amazonaws.com in path")
            return True
        else:
            self.logger.error("Path is invalid.")
            return False

    def get_s3_bucket(self, bucket_name):

        return self.s3.Bucket(bucket_name)

    def read_from_s3(self, bucket_name, filename):
        """
        With a given bucket and filename, read from s3.
        :param bucket:
        :param file:
        :return:
        """

        bucket = self.get_s3_bucket(bucket_name=bucket_name)
