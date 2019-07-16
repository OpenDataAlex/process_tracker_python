# AWS Utilities
# Utilities for working with AWS services

import logging
import re

import boto3
from botocore.errorfactory import ClientError


class AwsUtilities:
    def __init__(self):
        self.log_level = "INFO"

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.log_level)

        self.s3 = boto3.resource("s3")

        self.url_match = re.compile(
            "s3.([a-z]{2}-[a-z]{3,9}(-[a-z]{3,9}){0,1}-[1,2,3,4]{1}.){0,1}amazonaws.com\/"
        )

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

                if self.url_match.search(path):
                    # For URL format where bucket is the first item past the .com portion of the URL.
                    self.logger.debug("Path matched url_match")
                    path = re.sub(self.url_match, "", path)

                    self.logger.debug("Path is now %s" % path)

                    if "/" in path:

                        bucket_name = path.split("/")[0]

                        if "." in bucket_name:
                            bucket_name = bucket_name.split(".")[0]
                    else:
                        # For URL format where bucket is the first item past http(s)://
                        bucket_name = path.split(".")[0]

                self.logger.debug("Bucket name is %s" % bucket_name)

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

            groups = path.split("/", 4)

            if self.url_match.search(path):
                self.logger.debug("File matches url pattern.")
                path = re.sub(self.url_match, "", path)
                groups = path.split("/", 3)
                size = len(groups) - 1
                key = groups[size]

                # For files where the bucket is provided after the https://
                if key.count(".") >= 2:
                    groups = key.split(".", 1)
                    key = groups[1]

            else:
                error_msg = "It appears the URL is not a valid s3 path. %s" % path

                self.logger.error(error_msg)
                raise Exception(error_msg)

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
            self.logger.info("Path is not to s3.")
            return False

    def get_s3_bucket(self, path):
        """
        For the given path, find the bucket and return the bucket object.
        :param path:
        :return:
        """
        bucket_name = self.determine_bucket_name(path=path)

        return self.s3.Bucket(bucket_name)
