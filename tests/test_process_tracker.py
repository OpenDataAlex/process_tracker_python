# Tests for validating process_tracking works as expected.

from datetime import datetime, timedelta
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import boto3
import botocore
from moto import mock_s3
from sqlalchemy.orm import aliased, Session

from process_tracker.models.extract import (
    Extract,
    ExtractProcess,
    ExtractStatus,
    Location,
)
from process_tracker.models.process import (
    ErrorType,
    ErrorTracking,
    Process,
    ProcessDependency,
    ProcessSource,
    ProcessTarget,
    ProcessTracking,
)

from process_tracker.data_store import DataStore
from process_tracker.extract_tracker import ExtractTracker
from process_tracker.process_tracker import ProcessTracker
from process_tracker.utilities import utilities

test_bucket = "test_bucket"


# @mock_s3
class TestProcessTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_store = DataStore()
        cls.session = cls.data_store.session
        cls.data_store_type = cls.data_store.data_store_type

        cls.blarg = ExtractStatus(extract_status_name="blarg")
        cls.session.add(cls.blarg)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.session.query(Location).delete()
        cls.session.query(ProcessSource).delete()
        cls.session.query(ProcessTarget).delete()
        cls.session.query(ProcessDependency).delete()
        cls.session.query(Process).delete()
        cls.session.delete(cls.blarg)
        cls.session.commit()
        cls.session.close()

        # bucket = cls.s3.Bucket(test_bucket)
        # for key in bucket.objects.all():
        #     key.delete()
        # bucket.delete()

    def setUp(self):
        """
        Creating an initial process tracking run record for testing.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Testing Process Tracking Initialization",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        self.process_id = self.process_tracker.process.process_id

        if self.data_store_type == "mysql":
            self.provided_end_date = datetime.now().replace(microsecond=0)
        else:
            self.provided_end_date = datetime.now()

    def tearDown(self):
        """
        Need to clean up tables to return them to pristine state for other tests.
        :return:
        """
        self.session.query(ExtractProcess).delete()
        self.session.query(ErrorTracking).delete()
        self.session.query(ProcessTracking).delete()
        self.session.query(Extract).delete()
        self.session.query(ErrorType).delete()
        self.session.commit()

    def test_bulk_change_extract_status(self):
        """
        Testing that bulk change occurs when extracts provided.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename3.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract_trackers = [extract, extract2]

        self.process_tracker.bulk_change_extract_status(
            extracts=extract_trackers, extract_status="loading"
        )

        given_result = (
            self.session.query(ExtractProcess)
            .join(ExtractStatus)
            .filter(
                ExtractProcess.process_tracking_id
                == self.process_tracker.process_tracking_run.process_tracking_id
            )
            .filter(ExtractStatus.extract_status_name == "loading")
            .count()
        )

        expected_result = 2

        self.assertEqual(expected_result, given_result)

    def test_change_status_invalid_type(self):
        """
        Testing that if an invalid process status type is passed, it will trigger an exception.
        :return:
        """
        with self.assertRaises(Exception) as context:
            self.process_tracker.change_run_status(new_status="blarg")
        return self.assertTrue(
            "The provided status type blarg is invalid." in str(context.exception)
        )

    def test_find_extracts_by_filename_custom_status(self):
        """
        Testing that for the given full filename and a custom status, find the extract.
        :return:
        """

        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.change_extract_status("blarg")

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename2.csv"))
        ]

        given_result = self.process_tracker.find_extracts_by_filename(
            "test_extract_filename2.csv", status="blarg"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_filename_full(self):
        """
        Testing that for the given full filename, find the extract, provided it's in 'ready' state.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename2.csv"))
        ]

        given_result = self.process_tracker.find_extracts_by_filename(
            "test_extract_filename2.csv"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_filename_partial(self):
        """
        Testing that for the given partial filename, find the extracts, provided they are in 'ready' state. Should return in
        Ascending order.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename3-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename3-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename3-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename3-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_filename(
            "test_extract_filename"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_filename_partial_not_descending(self):
        """
        Testing that for the given partial filename, find the extracts, provided they are in 'ready' state.  Verifying
        that records are NOT returned in descending order.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename3-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename3-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename3-2.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename3-1.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_filename(
            "test_extract_filename"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertNotEqual(expected_result, given_result)

    def test_find_extracts_by_location_name_custom_status(self):
        """
         Testing that for the given location name and custom status, find the extracts.  Should return
         them in ascending order by registration datettime.
         :return:
         """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.change_extract_status("blarg")
        extract2.change_extract_status("blarg")

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename4-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename4-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_location(
            location_name="Test Location", status="blarg"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_location_name(self):
        """
        Testing that for the given location name, find the extracts, provided they are in 'ready' state.  Should return
        them in ascending order by registration datettime.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename4-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename4-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_location(
            location_name="Test Location"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_location_not_descending(self):
        """
        Testing that for the given location name, find the extracts, provided they are in 'ready' state.  Verifying that
        records NOT returned in descending order.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename4-2.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename4-1.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_location(
            location_name="Test Location"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertNotEqual(expected_result, given_result)

    def test_find_extracts_by_location_path_custom_status(self):
        """
                Testing that for the given location path and custom status, find the extracts.  Should return
                them in ascending order by registration datettime.
                :return:
                """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.change_extract_status("blarg")

        extract2.change_extract_status("blarg")

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename4-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename4-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_location(
            location_path="/home/test/extract_dir", status="blarg"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_location_path(self):
        """
        Testing that for the given location path, find the extracts, provided they are in 'ready' state.  Should return
        them in ascending order by registration datettime.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename4-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename4-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename4-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_location(
            location_path="/home/test/extract_dir"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_location_unset(self):
        """
        Testing that if both the location path and location name are not set, find_ready_extracts_by_location
        will throw an exception.
        :return:
        """
        with self.assertRaises(Exception) as context:
            self.process_tracker.find_extracts_by_location()

        return self.assertTrue(
            "A location name or path must be provided.  Please try again."
            in str(context.exception)
        )

    def test_find_extracts_by_process_custom_status(self):
        """
        Testing that for the given process name and custom status, find the extracts.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename5-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename5-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.change_extract_status("blarg")

        extract2.change_extract_status("blarg")

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename5-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename5-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_process(
            "Testing Process Tracking Initialization", status="blarg"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_process(self):
        """
        Testing that for the given process name, find the extracts, provided they are in 'ready' state.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename5-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename5-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename5-1.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename5-2.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_process(
            "Testing Process Tracking Initialization"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertCountEqual(expected_result, given_result)

    def test_find_extracts_by_process_not_descending(self):
        """
        Testing that for the given process name, find the extracts, provided they are in 'ready' state.  Verifying that
        records are NOT returned in Descending order.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename5-1.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        time.sleep(3)

        extract2 = ExtractTracker(
            process_run=self.process_tracker,
            filename="test_extract_filename5-2.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        extract2.extract.extract_registration_date_time = (
            datetime.now()
        )  # Records were being committed too close together.
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = [
            str(Path("/home/test/extract_dir/test_extract_filename5-2.csv")),
            str(Path("/home/test/extract_dir/test_extract_filename5-1.csv")),
        ]

        given_result = self.process_tracker.find_extracts_by_process(
            "Testing Process Tracking Initialization"
        )
        given_result = [record.full_filepath() for record in given_result]

        self.assertNotEqual(expected_result, given_result)

    def test_initializing_process_tracking(self):
        """
        Testing that when ProcessTracking is initialized, the necessary objects are created.
        :return:
        """
        given_result = self.process_tracker.actor.actor_name
        expected_result = "UnitTesting"

        self.assertEqual(expected_result, given_result)

    def test_register_extracts_by_location_local(self):
        """
        Testing that when the location is local, all the extracts are registered and set to 'ready' status.
        The process/extract relationship should also be set to 'ready' since that is the last status the process set
        the extracts to.
        :return:
        """
        process_status = aliased(ExtractStatus)
        extract_status = aliased(ExtractStatus)

        with patch("os.listdir") as mocked_os_listdir:
            mocked_os_listdir.return_value = [
                "test_local_dir_1.csv",
                "test_local_dir_2.csv",
            ]

            self.process_tracker.register_extracts_by_location(
                location_path="/test/local/dir/"
            )

        extracts = (
            self.session.query(
                Extract.extract_filename,
                extract_status.extract_status_name,
                process_status.extract_status_name,
            )
            .join(
                ExtractProcess, Extract.extract_id == ExtractProcess.extract_tracking_id
            )
            .join(
                extract_status,
                Extract.extract_status_id == extract_status.extract_status_id,
            )
            .join(
                process_status,
                ExtractProcess.extract_process_status_id
                == process_status.extract_status_id,
            )
            .filter(
                ExtractProcess.process_tracking_id
                == self.process_tracker.process_tracking_run.process_tracking_id
            )
        )

        given_result = [
            [
                extracts[0].extract_filename,
                extracts[0].extract_status_name,
                extracts[0].extract_status_name,
            ],
            [
                extracts[1].extract_filename,
                extracts[1].extract_status_name,
                extracts[1].extract_status_name,
            ],
        ]

        expected_result = [
            ["test_local_dir_1.csv", "ready", "ready"],
            ["test_local_dir_2.csv", "ready", "ready"],
        ]

        self.assertCountEqual(expected_result, given_result)

    @mock_s3
    def test_register_extracts_by_location_s3(self):
        """
        Testing that when the location is s3, all the extracts are registered and set to 'ready' status.
        The process/extract relationship should also be set to 'ready' since that is the last status the process set
        the extracts to.
        :return:
        """
        process_status = aliased(ExtractStatus)
        extract_status = aliased(ExtractStatus)
        test_bucket = "test_bucket"

        expected_keys = ["test_local_dir_1.csv", "test_local_dir_2.csv"]

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

        current_dir = os.path.dirname(__file__)
        fixtures_dir = os.path.join(current_dir, "fixtures")

        for file in expected_keys:

            key = os.path.join(test_bucket, file)

            print(file)
            print(key)
            print(fixtures_dir)

            file = os.path.join(fixtures_dir, file)
            client.upload_file(Filename=file, Bucket=test_bucket, Key=key)

        self.process_tracker.register_extracts_by_location(
            location_path="s3://test_bucket"
        )

        extracts = (
            self.session.query(
                Extract.extract_filename,
                extract_status.extract_status_name,
                process_status.extract_status_name,
            )
            .join(
                ExtractProcess, Extract.extract_id == ExtractProcess.extract_tracking_id
            )
            .join(
                extract_status,
                Extract.extract_status_id == extract_status.extract_status_id,
            )
            .join(
                process_status,
                ExtractProcess.extract_process_status_id
                == process_status.extract_status_id,
            )
            .filter(
                ExtractProcess.process_tracking_id
                == self.process_tracker.process_tracking_run.process_tracking_id
            )
        )

        given_result = list()

        for extract in extracts:
            given_result.append(
                [
                    extract.extract_filename,
                    extract.extract_status_name,
                    extract.extract_status_name,
                ]
            )

        expected_result = [
            ["test_bucket/test_local_dir_1.csv", "ready", "ready"],
            ["test_bucket/test_local_dir_2.csv", "ready", "ready"],
        ]

        self.assertCountEqual(expected_result, given_result)

    def test_register_new_process_run(self):
        """
        Testing that a new run record is created if there is no other instance of the same
        process currently in 'running' status.
        :return:
        """

        given_result = (
            self.session.query(ProcessTracking)
            .filter(ProcessTracking.process_id == self.process_id)
            .count()
        )
        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_register_new_process_run_exception(self):
        """
        Testing that a new run record is not created if a run record is currently in 'running' status.  An exception
        should be triggered.
        :return:
        """

        with self.assertRaises(Exception) as context:
            # Running registration a second time to mimic job being run twice
            self.process_tracker.register_new_process_run()

        return self.assertTrue(
            "The process Testing Process Tracking Initialization "
            "is currently running." in str(context.exception)
        )

    def test_register_new_process_run_with_previous_run(self):
        """
        Testing that a new run record is created if there is another instance of same process in 'completed' or 'failed'
        status.  Also flips the is_latest_run flag on previous run to False.
        :return:
        """

        self.process_tracker.change_run_status(new_status="completed")
        self.process_tracker.register_new_process_run()

        process_runs = (
            self.session.query(ProcessTracking)
            .filter(ProcessTracking.process_id == self.process_id)
            .order_by(ProcessTracking.process_tracking_id)
        )

        given_result = process_runs[0].is_latest_run
        expected_result = False

        self.assertEqual(expected_result, given_result)

    def test_register_new_process_run_dependencies_completed(self):
        """
        Testing that for a given process, if there are completed dependencies, then the process run is created.
        :return:
        """
        dependent_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        dependent_process.change_run_status(new_status="completed")
        self.process_tracker.change_run_status(new_status="completed")
        self.data_store.get_or_create_item(
            model=ProcessDependency,
            parent_process_id=dependent_process.process_tracking_run.process_id,
            child_process_id=self.process_id,
        )

        self.process_tracker.register_new_process_run()

        given_count = (
            self.session.query(ProcessTracking)
            .filter(ProcessTracking.process_id == self.process_id)
            .count()
        )

        expected_count = 2

        self.assertEqual(expected_count, given_count)

    def test_register_new_process_run_dependencies_running(self):
        """
        Testing that for a given process, if there are running dependencies, then the process run is prevented from starting.
        :return:
        """
        dependent_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency Running",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        dependent_process.change_run_status(new_status="running")
        self.process_tracker.change_run_status(new_status="completed")
        self.data_store.get_or_create_item(
            model=ProcessDependency,
            parent_process_id=dependent_process.process_tracking_run.process_id,
            child_process_id=self.process_id,
        )

        with self.assertRaises(Exception) as context:
            self.process_tracker.register_new_process_run()

        return self.assertTrue(
            "Processes that this process is dependent on are running or failed."
            in str(context.exception)
        )

    def test_register_new_process_run_dependencies_failed(self):
        """
        Testing that for a given process, if there are failed dependencies, then the process run is prevented from starting.
        :return:
        """
        dependent_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency Failed",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        dependent_process.change_run_status(new_status="failed")
        self.process_tracker.change_run_status(new_status="completed")
        self.data_store.get_or_create_item(
            model=ProcessDependency,
            parent_process_id=dependent_process.process_tracking_run.process_id,
            child_process_id=self.process_id,
        )

        with self.assertRaises(Exception) as context:
            self.process_tracker.register_new_process_run()

        return self.assertTrue(
            "Processes that this process is dependent on are running or failed."
            in str(context.exception)
        )

    def test_register_process_sources_one_source(self):
        """
        Testing that when a new process is registered, a source registered as well.
        :return:
        """
        given_result = (
            self.session.query(ProcessSource)
            .join(Process)
            .filter(Process.process_name == "Testing Process Tracking Initialization")
            .count()
        )

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_register_process_sources_two_sources(self):
        """
        Testing that when a new process is registered, multiple sources can be registered as well.
        :return:
        """
        ProcessTracker(
            process_name="Multiple Source, Target Test",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources=["Unittests", "Unittests2"],
            targets=["Unittests", "Unittests2"],
        )

        given_result = (
            self.session.query(ProcessSource)
            .join(Process)
            .filter(Process.process_name == "Multiple Source, Target Test")
            .count()
        )

        expected_result = 2

        self.assertEqual(expected_result, given_result)

    def test_register_process_targets_one_target(self):
        """
        Testing that when a new process is registered, a target registered as well.
        :return:
        """
        given_result = (
            self.session.query(ProcessTarget)
            .join(Process)
            .filter(Process.process_name == "Testing Process Tracking Initialization")
            .count()
        )

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_register_process_targets_two_targets(self):
        """
        Testing that when a new process is registered, multiple targets can be registered as well.
        :return:
        """
        ProcessTracker(
            process_name="Multiple Source, Target Test",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources=["Unittests", "Unittests2"],
            targets=["Unittests", "Unittests2"],
        )

        given_result = (
            self.session.query(ProcessTarget)
            .join(Process)
            .filter(Process.process_name == "Multiple Source, Target Test")
            .count()
        )

        expected_result = 2

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_complete(self):
        """
        Testing that when changing the run status from 'running' to 'complete' the run record updates successfully.
        :return:
        """
        self.process_tracker.change_run_status(new_status="completed")

        run_record = self.session.query(ProcessTracking).filter(
            ProcessTracking.process_id == self.process_id
        )

        given_result = run_record[0].process_status_id
        expected_result = self.process_tracker.process_status_complete

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_failed(self):
        """
        Testing that when changing the run status from 'running' to 'failed' the run record updates successfully.
        :return:
        """
        self.process_tracker.change_run_status(new_status="failed")

        run_record = self.session.query(ProcessTracking).filter(
            ProcessTracking.process_id == self.process_id
        )

        given_result = run_record[0].process_status_id
        expected_result = self.process_tracker.process_status_failed

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_with_end_date(self):
        """
        Testing that if end date is provided, the end date will be set on status change to 'completed'.
        :return:
        """

        self.process_tracker.change_run_status(
            new_status="completed", end_date=self.provided_end_date
        )

        run_record = self.session.query(ProcessTracking).filter(
            ProcessTracking.process_id == self.process_id
        )

        given_result = run_record[0].process_run_end_date_time
        expected_result = self.provided_end_date

        self.assertEqual(expected_result, given_result)

    def test_raise_run_error_type_exists_no_fail(self):
        """
        Testing that if an error is triggered, it gets recorded in the data store, provided that the error type exists.
        :return:
        """
        error_type = ErrorType(error_type_name="Does Exist")
        self.session.add(error_type)
        self.session.commit()

        self.process_tracker.raise_run_error(error_type_name="Does Exist")

        given_result = (
            self.session.query(ErrorTracking)
            .filter(ErrorTracking.error_type_id == error_type.error_type_id)
            .count()
        )

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_raise_run_error_type_not_exists(self):
        """
        Testing that exception raised if the error type does not exist.
        :return:
        """

        with self.assertRaises(Exception) as context:

            self.process_tracker.raise_run_error(error_type_name="Does Not Exist")

        return self.assertTrue(
            "There is no record match in error_type_lkup ." in str(context.exception)
        )

    def test_raise_run_error_with_fail(self):
        """
        Testing that if fail flag set, the process_tracking record status is changed to 'failed' and last_failure date
        for process is set.
        :return:
        """
        error_type = ErrorType(error_type_name="Fail Check")
        self.session.add(error_type)
        self.session.commit()

        with self.assertRaises(Exception) as context:

            self.process_tracker.raise_run_error(
                error_type_name="Fail Check",
                fail_run=True,
                end_date=self.provided_end_date,
            )

        run_error = self.session.query(ErrorTracking).filter(
            ErrorTracking.error_type_id == error_type.error_type_id
        )

        process_tracking_run = self.session.query(ProcessTracking).filter(
            ProcessTracking.process_tracking_id == run_error[0].process_tracking_id
        )

        process = self.session.query(Process).filter(
            Process.process_id == process_tracking_run[0].process_id
        )

        fail_date = process[0].last_failed_run_date_time
        fail_date = fail_date.replace(tzinfo=None)

        given_result = [
            process_tracking_run[0].process_status_id,
            process_tracking_run[0].process_run_end_date_time,
            fail_date,
        ]

        print(self.provided_end_date)
        print(process[0].last_failed_run_date_time)

        expected_result = [
            self.process_tracker.process_status_failed,
            self.provided_end_date,
            self.provided_end_date,
        ]

        with self.subTest():
            self.assertEqual(expected_result, given_result)
        with self.subTest():
            self.assertTrue(
                "Process halting.  An error triggered the process to fail."
                in str(context.exception)
            )

    def test_set_run_low_high_dates(self):
        """
        Testing that if low and high date are not set, the process_tracking_record low/high dates are set.
        :return:
        """
        low_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        ) - timedelta(hours=1)

        high_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        )

        self.process_tracker.set_process_run_low_high_dates(
            low_date=low_date, high_date=high_date
        )

        given_dates = self.session.query(
            ProcessTracking.process_run_low_date_time,
            ProcessTracking.process_run_high_date_time,
        ).filter(
            ProcessTracking.process_tracking_id
            == self.process_tracker.process_tracking_run.process_tracking_id
        )

        expected_result = [low_date, high_date]
        given_result = [
            given_dates[0].process_run_low_date_time,
            given_dates[0].process_run_high_date_time,
        ]

        self.assertEqual(expected_result, given_result)

    def test_set_run_low_high_dates_lower_low_date(self):
        """
        Testing that if a new low date comes in for a given process_run, set the process_run_low_date_time to the new
        low date.
        :return:
        """
        low_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        ) - timedelta(hours=1)
        lower_low_date = low_date - timedelta(hours=1)

        self.process_tracker.set_process_run_low_high_dates(low_date=low_date)

        self.process_tracker.set_process_run_low_high_dates(low_date=lower_low_date)

        given_dates = self.session.query(
            ProcessTracking.process_run_low_date_time
        ).filter(
            ProcessTracking.process_tracking_id
            == self.process_tracker.process_tracking_run.process_tracking_id
        )

        expected_result = lower_low_date
        given_result = given_dates[0].process_run_low_date_time

        self.assertEqual(expected_result, given_result)

    def test_set_run_low_high_dates_higher_high_date(self):
        """
        Testing that if a new low date comes in for a given process_run, set the process_run_low_date_time to the new
        low date.
        :return:
        """
        high_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        )

        higher_high_date = high_date + timedelta(hours=1)

        self.process_tracker.set_process_run_low_high_dates(high_date=high_date)

        self.process_tracker.set_process_run_low_high_dates(high_date=higher_high_date)

        given_dates = self.session.query(
            ProcessTracking.process_run_high_date_time
        ).filter(
            ProcessTracking.process_tracking_id
            == self.process_tracker.process_tracking_run.process_tracking_id
        )

        expected_result = higher_high_date
        given_result = given_dates[0].process_run_high_date_time

        self.assertEqual(expected_result, given_result)

    def test_set_process_run_record_count(self):
        """
        Testing that if record counts are provided for a given process_run, set the process_run_record_count and process'
        total_record_counts correctly.
        :return:
        """
        initial_record_count = 1000

        self.process_tracker.set_process_run_record_count(
            num_records=initial_record_count
        )

        given_counts = (
            self.session.query(
                ProcessTracking.process_run_record_count, Process.total_record_count
            )
            .join(Process)
            .filter(
                ProcessTracking.process_tracking_id
                == self.process_tracker.process_tracking_run.process_tracking_id
            )
        )

        expected_result = [initial_record_count, initial_record_count]
        given_result = [
            given_counts[0].process_run_record_count,
            given_counts[0].total_record_count,
        ]

        self.assertEqual(expected_result, given_result)

    def test_set_process_run_record_count_twice(self):
        """
        Testing that if record counts get set multiple times, then the process total record count will be set correctly.
        :return:
        """
        initial_record_count = 1000
        modified_record_count = 1500

        self.process_tracker.set_process_run_record_count(
            num_records=initial_record_count
        )
        self.process_tracker.set_process_run_record_count(
            num_records=modified_record_count
        )

        given_counts = (
            self.session.query(
                ProcessTracking.process_run_record_count, Process.total_record_count
            )
            .join(Process)
            .filter(
                ProcessTracking.process_tracking_id
                == self.process_tracker.process_tracking_run.process_tracking_id
            )
        )

        expected_result = [modified_record_count, modified_record_count]
        given_result = [
            given_counts[0].process_run_record_count,
            given_counts[0].total_record_count,
        ]

        self.assertEqual(expected_result, given_result)
