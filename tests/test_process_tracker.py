# Tests for validating process_tracking works as expected.

from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import boto3
import botocore
from moto import mock_s3
from sqlalchemy.orm import aliased, Session

from process_tracker.models.contact import Contact
from process_tracker.models.extract import (
    Extract,
    ExtractDatasetType,
    ExtractProcess,
    ExtractStatus,
    ExtractSource,
    Location,
)
from process_tracker.models.process import (
    ErrorType,
    ErrorTracking,
    Process,
    ProcessContact,
    ProcessDatasetType,
    ProcessDependency,
    ProcessFilter,
    ProcessSource,
    ProcessSourceObject,
    ProcessSourceObjectAttribute,
    ProcessTarget,
    ProcessTargetObject,
    ProcessTargetObjectAttribute,
    ProcessTracking,
)
from process_tracker.models.source import (
    DatasetType,
    FilterType,
    Source,
    SourceContact,
    SourceDatasetType,
    SourceLocation,
    SourceObject,
    SourceObjectAttribute,
    SourceObjectDatasetType,
    SourceObjectLocation,
)

from process_tracker.utilities.data_store import DataStore, ClusterProcess
from process_tracker.extract_tracker import ExtractTracker
from process_tracker.process_tracker import ProcessTracker
from process_tracker.utilities import utilities

test_bucket = "test_bucket"


# @mock_s3
class TestProcessTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.Logger(__name__)

        cls.data_store = DataStore()
        cls.session = cls.data_store.session
        cls.data_store_type = cls.data_store.data_store_type

        cls.blarg = cls.data_store.get_or_create_item(
            model=ExtractStatus, extract_status_name="blarg"
        )

    @classmethod
    def tearDownClass(cls):
        cls.session.query(ClusterProcess).delete()
        cls.session.query(ProcessContact).delete()
        cls.session.query(ProcessFilter).delete()
        cls.session.query(Location).delete()
        cls.session.query(DatasetType).delete()
        cls.session.query(ProcessSourceObjectAttribute).delete()
        cls.session.query(ProcessTargetObjectAttribute).delete()
        cls.session.query(ProcessSourceObject).delete()
        cls.session.query(ProcessTargetObject).delete()
        cls.session.query(ProcessSource).delete()
        cls.session.query(ProcessTarget).delete()
        cls.session.query(ProcessDependency).delete()
        cls.session.query(Process).delete()
        cls.session.delete(cls.blarg)
        cls.session.commit()
        cls.session.close()

    def setUp(self):
        """
        Creating an initial process tracking run record for testing.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Testing Process Tracking Initialization",
            process_run_name="Testing Process Tracking Initialization 01",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
            dataset_types="Category 1",
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
        self.session.query(ExtractSource).delete()
        self.session.query(ExtractDatasetType).delete()
        self.session.query(SourceDatasetType).delete()
        self.session.query(SourceObjectDatasetType).delete()
        self.session.query(SourceLocation).delete()
        self.session.query(SourceObjectLocation).delete()
        self.session.query(ProcessDatasetType).delete()
        self.session.query(ErrorTracking).delete()
        self.session.query(ProcessTracking).delete()
        self.session.query(Process)
        self.session.query(Extract).delete()
        self.session.query(ErrorType).delete()
        self.session.commit()

    def process_run_setup(self, process_name, status, num_runs):
        """
        Helper function to setup mutliple process tracking runs for a given process and set to a given status. Used to
        test the on_hold status logic.
        :param process_name: Name of the process that runs will be created of.
        :param status: Status the runs should be changed to
        :param num_runs: Number of runs that should be created
        :return:
        """
        i = 1
        while i <= num_runs:
            process_run = ProcessTracker(
                process_name=process_name,
                process_type="Extract",
                actor_name="UnitTesting",
                tool_name="Spark",
            )

            process_run.change_run_status(new_status=status)
            i += 1
            time.sleep(2)

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

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
        given_result = [record.full_filename for record in given_result]

        self.assertNotEqual(expected_result, given_result)

    def test_find_process_contacts(self):
        """
        Testing that when passed a process_id, a list of source and process contacts will be returned.
        :return:
        """
        source_contact = DataStore().get_or_create_item(
            model=Contact,
            contact_name="Test Contact",
            contact_email="testcontact@test.com",
        )

        process_contact = DataStore().get_or_create_item(
            model=Contact,
            contact_name="Process Contact",
            contact_email="processcontact@test.com",
        )

        source = DataStore().get_or_create_item(model=Source, source_name="Unittests")

        DataStore().get_or_create_item(
            model=SourceContact,
            source_id=source.source_id,
            contact_id=source_contact.contact_id,
        )

        DataStore().get_or_create_item(
            model=ProcessContact,
            process_id=self.process_id,
            contact_id=process_contact.contact_id,
        )

        given_result = self.process_tracker.find_process_contacts(
            process=self.process_id
        )

        expected_result = [
            {
                "contact_name": "Test Contact",
                "contact_email": "testcontact@test.com",
                "contact_type": "source",
            },
            {
                "contact_name": "Process Contact",
                "contact_email": "processcontact@test.com",
                "contact_type": "process",
            },
        ]

        self.assertEqual(expected_result, given_result)

    def test_initializing_process_tracking(self):
        """
        Testing that when ProcessTracking is initialized, the necessary objects are created.
        :return:
        """
        given_result = self.process_tracker.actor.actor_name
        expected_result = "UnitTesting"

        self.assertEqual(expected_result, given_result)

    @unittest.skip("Issue with hanging queries on database.")
    def test_process_on_hold_max_failures(self):
        """
        Testing that when number of failed processes matches the maximum_sequential_failures (default 5), process run
        goes on_hold.
        :return:
        """

        self.process_run_setup(
            process_name="On Hold Max Failures Test", status="failed", num_runs=5
        )

        with self.assertRaises(Exception) as context:
            ProcessTracker(
                process_name="On Hold Max Failures Test",
                process_type="Extract",
                actor_name="UnitTesting",
                tool_name="Spark",
            )

        self.assertTrue(
            "The process On Hold Max Failures Test is currently on hold."
            in str(context.exception)
        )

    @unittest.skip("Issue with hanging queries on database.")
    def test_process_on_hold_under_max_failures(self):
        """
        Testing that when number of failed processes is less than the maximum_sequential_failures (default 5), process run
        continues.
        :return:
        """
        process_name = "On Hold Under Max Failures Test"
        self.process_run_setup(process_name=process_name, status="failed", num_runs=3)

        process_run = ProcessTracker(
            process_name=process_name,
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
        )

        current_run_status = (
            self.session.query(ProcessTracking)
            .join(Process)
            .filter(Process.process_name == process_name)
            .filter(ProcessTracking.is_latest_run == True)
        )
        given_result = current_run_status[0].process_status_id

        expected_result = process_run.process_status_running

        self.assertEqual(expected_result, given_result)

    def test_process_on_hold_previous_run_on_hold(self):
        """
        If the previous run does not get moved from on_hold status, then the next run will not kick off and the process
        will remain on_hold.
        :return:
        """
        process_name = "On Hold Previous Run Test"

        process_run = ProcessTracker(
            process_name=process_name,
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
        )

        process_run.change_run_status(new_status="on hold")

        with self.assertRaises(Exception) as context:
            ProcessTracker(
                process_name=process_name,
                process_type="Extract",
                actor_name="UnitTesting",
                tool_name="Spark",
            )

        self.assertTrue(
            "The process On Hold Previous Run Test is currently on hold."
            in str(context.exception)
        )

    def test_register_extracts_by_location_local_file_count(self):
        """
        Testing that when the location is local, all the extracts are counted and registered in the location's file count.
        :return: 
        """
        with patch("os.listdir") as mocked_os_listdir:
            mocked_os_listdir.return_value = [
                "test_local_dir_1.csv",
                "test_local_dir_2.csv",
            ]

            self.process_tracker.register_extracts_by_location(
                location_path="/test/local/dir/"
            )

        given_result = self.session.query(Location.location_file_count).filter(
            Location.location_path == "/test/local/dir/"
        )
        expected_result = 2

        self.assertEqual(expected_result, given_result[0].location_file_count)

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

    @unittest.skipIf(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        "Skipping this test on Travis CI.",
    )
    @unittest.skip("Issue with hanging queries on database.")
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

            self.logger.debug("Filename %s" % file)
            self.logger.debug("File key %s" % key)
            self.logger.debug("Fixtures dir %s" % fixtures_dir)

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

        given_file_count = self.session.query(Location).filter(
            Location.location_path == "s3://test_bucket"
        )
        expected_file_count = 2

        self.assertEqual(expected_file_count, given_file_count[0].location_file_count)
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
            "The process Testing Process Tracking Initialization is currently running."
            in str(context.exception)
        )

    def test_register_new_process_run_with_previous_run(self):
        """
        Testing that a new run record is created if there is another instance of same process in 'completed' or 'failed'
        status.  Also flips the is_latest_run flag on previous run to False.
        :return:
        """

        self.process_tracker.change_run_status(new_status="completed")
        self.process_tracker.process_run_name = (
            "Testing Process Tracking Initialization 02"
        )
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
        )

        dependent_process.change_run_status(new_status="completed")
        self.process_tracker.change_run_status(new_status="completed")
        self.data_store.get_or_create_item(
            model=ProcessDependency,
            parent_process_id=dependent_process.process_tracking_run.process_id,
            child_process_id=self.process_id,
        )

        self.process_tracker.process_run_name = (
            "Testing Process Tracking Initialization 02"
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

    def test_register_process_dataset_types_one_type(self):
        """
        Testing that when a new process is registered, a dataset type is registered as well.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Single dataset types",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
            dataset_types="Category1",
        )

        given_result = (
            self.session.query(ProcessDatasetType)
            .join(Process)
            .filter(Process.process_name == "Single dataset types")
            .count()
        )

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_register_process_dataset_types_two_types(self):
        """
        Testing that when a new process is registered with multiple dataset types, those dataset types are registered as well.
        :return:
        """

        self.process_tracker = ProcessTracker(
            process_name="Multiple dataset types",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
            dataset_types=["Category1", "Category2"],
        )

        given_result = (
            self.session.query(ProcessDatasetType)
            .join(Process)
            .filter(Process.process_name == "Multiple dataset types")
            .count()
        )

        expected_result = 2

        self.assertEqual(expected_result, given_result)

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

    def test_register_process_source_objects_one_source_ignore_sources(self):
        """
        Testing that when a new process is registered with both sources and source_objects, sources is ignored.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Loading Source Objects",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
            source_objects={"source": ["source_table", "source_table2"]},
        )

        given_result = (
            self.session.query(ProcessSource)
            .join(Process)
            .join(Source)
            .filter(Process.process_name == "Loading Source Objects")
            .filter(Source.source_name == "Unittests")
            .count()
        )

        expected_result = 0

        self.assertEqual(expected_result, given_result)

    def test_register_process_source_objects_not_dict(self):
        """
        Testing that when a new process is registered with source_objects, and source_objects is not in dict format,
        throw an error.
        :return:
        """

        with self.assertRaises(Exception) as context:
            ProcessTracker(
                process_name="Loading Target Objects",
                process_type="Extract",
                actor_name="UnitTesting",
                tool_name="Spark",
                source_objects=["source.source_table", "source.source_table2"],
            )

        return self.assertTrue(
            "It appears source_objects is not a dictionary." in str(context.exception)
        )

    def test_register_process_source_objects_one_source(self):
        """
        Testing that when a new process is registered with source_objects, those source objects are registered as well.
        :return:
        """

        self.process_tracker = ProcessTracker(
            process_name="Loading Source Objects",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            targets="Unittests",
            source_objects={"source": ["source_table", "source_table2"]},
        )

        given_result = (
            self.session.query(ProcessSourceObject)
            .join(Process)
            .filter(Process.process_name == "Loading Source Objects")
            .count()
        )

        expected_result = 2

        self.assertEqual(expected_result, given_result)

    def test_register_process_source_objects_two_sources(self):
        """
        Testing that when a new process is registered with multiple source objects, those source objects are registered
        as well.
        :return:
        """

        self.process_tracker = ProcessTracker(
            process_name="Loading Source Objects",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            targets="Unittests",
            source_objects={
                "source": ["source_table", "source_table2"],
                "source2": ["source2_table"],
            },
        )

        given_result = (
            self.session.query(ProcessSourceObject)
            .join(Process)
            .filter(Process.process_name == "Loading Source Objects")
            .count()
        )

        expected_result = 3

        self.assertEqual(expected_result, given_result)

    def test_register_process_source_object_attributes(self):
        """Testing that when a new process is registered with source object attributes, those attributes are registered as well."""

        self.process_tracker = ProcessTracker(
            process_name="Loading Source Object Attributes",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            targets="Unittests",
            source_object_attributes={
                "source": {
                    "source_table": ["attr_1", "attr_2"],
                    "source_table2": ["attr_3", "attr_4"],
                }
            },
        )

        given_result = (
            self.session.query(ProcessSourceObjectAttribute)
            .join(Process)
            .filter(Process.process_name == "Loading Source Object Attributes")
            .count()
        )

        expected_result = 4

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

    def test_register_process_target_objects_not_dict(self):
        """
        Testing that when a new process is registered with target_objects, and target_objects is not in dict format,
        throw an error.
        :return: 
        """

        with self.assertRaises(Exception) as context:
            ProcessTracker(
                process_name="Loading Target Objects",
                process_type="Extract",
                actor_name="UnitTesting",
                tool_name="Spark",
                sources="Unittests",
                targets="Unittests",
                target_objects=["target.target_table", "target.target_table2"],
            )

        return self.assertTrue(
            "It appears target_objects is not a dictionary." in str(context.exception)
        )

    def test_register_process_target_objects_one_target_ignore_targets(self):
        """
        Testing that when a new process is registered with both targets and target_objects, targets is ignored.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Loading Target Objects",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
            target_objects={"target": ["target_table", "target_table2"]},
        )

        given_result = (
            self.session.query(ProcessTarget)
            .join(Process)
            .join(Source)
            .filter(Process.process_name == "Loading Target Objects")
            .filter(Source.source_name == "Unittests")
            .count()
        )

        expected_result = 0

        self.assertEqual(expected_result, given_result)

    def test_register_process_target_objects_one_target(self):
        """
         Testing that when a new process is registered with source_objects, those source objects are registered as well.
         :return:
         """

        self.process_tracker = ProcessTracker(
            process_name="Loading Target Objects",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            target_objects={"target": ["target_table", "target_table2"]},
        )

        given_result = (
            self.session.query(ProcessTargetObject)
            .join(Process)
            .filter(Process.process_name == "Loading Target Objects")
            .count()
        )

        expected_result = 2

        self.assertEqual(expected_result, given_result)

    def test_register_process_target_objects_two_targets(self):
        """
         Testing that when a new process is registered with multiple source objects, those source objects are
         registered as well.
         :return:
         """

        self.process_tracker = ProcessTracker(
            process_name="Loading Target Objects",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            target_objects={
                "target": ["target_table", "target_table2"],
                "target2": ["target_table3"],
            },
        )

        given_result = (
            self.session.query(ProcessTargetObject)
            .join(Process)
            .filter(Process.process_name == "Loading Target Objects")
            .count()
        )

        expected_result = 3

        self.assertEqual(expected_result, given_result)

    def test_register_process_target_object_attributes(self):
        """Testing that when a new process is registered with target object attributes, those attributes are registered as well."""

        self.process_tracker = ProcessTracker(
            process_name="Loading Target Object Attributes",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            targets="Unittests",
            target_object_attributes={
                "target": {
                    "target_table": ["attr_1", "attr_2"],
                    "target_table2": ["attr_3", "attr_4"],
                }
            },
        )

        given_result = (
            self.session.query(ProcessTargetObjectAttribute)
            .join(Process)
            .filter(Process.process_name == "Loading Target Object Attributes")
            .count()
        )

        expected_result = 4

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_complete(self):
        """
        Testing that when changing the run status from 'running' to 'complete' the run record updates successfully.
        Process record is also updated for last_completed_date_time.
        :return:
        """
        end_date = datetime.now()
        end_date = end_date.replace(microsecond=0)
        self.process_tracker.change_run_status(
            new_status="completed", end_date=end_date
        )

        run_record = (
            self.session.query(
                ProcessTracking.process_status_id, Process.last_completed_run_date_time
            )
            .join(Process)
            .filter(ProcessTracking.process_id == self.process_id)
        )

        given_result = [
            run_record[0].process_status_id,
            run_record[0].last_completed_run_date_time,
        ]
        expected_result = [self.process_tracker.process_status_complete, end_date]

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_failed(self):
        """
        Testing that when changing the run status from 'running' to 'failed' the run record updates successfully.
        Process record is also updated for last_failed_date_time.
        :return:
        """
        end_date = datetime.now()
        end_date = end_date.replace(microsecond=0)
        self.process_tracker.change_run_status(new_status="failed", end_date=end_date)

        run_record = (
            self.session.query(
                ProcessTracking.process_status_id, Process.last_failed_run_date_time
            )
            .join(Process)
            .filter(ProcessTracking.process_id == self.process_id)
        )

        given_result = [
            run_record[0].process_status_id,
            run_record[0].last_failed_run_date_time,
        ]
        expected_result = [self.process_tracker.process_status_failed, end_date]

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

    def test_register_source_dataset_type(self):
        """
        When both a source and dataset_type are provided, the source is registered to the dataset_type.
        :return:
        """
        given_result = (
            self.session.query(SourceDatasetType)
            .join(Source)
            .filter(Source.source_name == "Unittests")
            .count()
        )
        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_register_target_dataset_type(self):
        """
        When both a target and dataset type are provided, the target is registered to the dataset type.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Testing Process Tracking Initialization 2",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests Target",
            dataset_types="Category 1",
        )

        given_result = (
            self.session.query(SourceDatasetType)
            .join(Source)
            .filter(Source.source_name == "Unittests Target")
            .count()
        )
        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_register_source_object_dataset_type(self):
        """
        When both a source object and dataset type are provided, the source and source object are registered to the
        dataset type.
        :return:
        """
        self.process_tracker = ProcessTracker(
            process_name="Testing Register Source Object Dataset Type",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            source_objects={"Unittests": ["Table1"]},
            target_objects={"Unittests": ["Table1"]},
            dataset_types="Category 1",
        )

        source_given_result = (
            self.session.query(SourceDatasetType)
            .join(Source)
            .filter(Source.source_name == "Unittests")
            .count()
        )
        source_expected_result = 1

        object_given_result = (
            self.session.query(SourceObjectDatasetType)
            .join(SourceObject)
            .join(Source)
            .filter(Source.source_name == "Unittests")
            .filter(SourceObject.source_object_name == "Table1")
            .count()
        )
        object_expected_result = 1

        self.assertEqual(source_expected_result, source_given_result)
        self.assertEqual(object_expected_result, object_given_result)

    def test_register_target_object_dataset_type(self):
        """
        When both a source object and dataset type are provided, the target source and target source object are
        registered to the dataset type.
        :return:
        """

        self.process_tracker = ProcessTracker(
            process_name="Testing Register Target Object Dataset Type",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            source_objects={"Unittests": ["Table1"]},
            target_objects={"Unittest Target": ["Table1"]},
            dataset_types="Category 1",
        )

        source_given_result = (
            self.session.query(SourceDatasetType)
            .join(Source)
            .filter(Source.source_name == "Unittest Target")
            .count()
        )
        source_expected_result = 1

        object_given_result = (
            self.session.query(SourceObjectDatasetType)
            .join(SourceObject)
            .join(Source)
            .filter(Source.source_name == "Unittest Target")
            .filter(SourceObject.source_object_name == "Table1")
            .count()
        )
        object_expected_result = 1

        self.assertEqual(source_expected_result, source_given_result)
        self.assertEqual(object_expected_result, object_given_result)

    def test_find_process_by_schedule_frequency(self):
        """Testing that when querying based on a given frequency, the process id(s) associated with that frequency are returned."""

        process = ProcessTracker(
            process_name="Testing Schedule Frequency Hourly",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            source_objects={"Unittests": ["Table1"]},
            target_objects={"Unittest Target": ["Table1"]},
            dataset_types="Category 1",
            schedule_frequency="hourly",
        )

        given_result = process.find_process_by_schedule_frequency(frequency="hourly")

        expected_result = [process.process.process_id]

        self.assertEqual(expected_result, given_result)

    def test_find_process_filters(self):
        """
        Testing that when querying based on a given process, the process' filters are provided.
        :return:
        """

        process = ProcessTracker(
            process_name="Testing Process Filters",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            source_object_attributes={"source": {"source_table": ["attr_1", "attr_2"]}},
        )

        filter_type = process.data_store.get_or_create_item(
            model=FilterType, create=False, filter_type_code="eq"
        )
        source = process.data_store.get_or_create_item(
            model=Source, create=False, source_name="source"
        )
        source_object = process.data_store.get_or_create_item(
            model=SourceObject,
            create=False,
            source_id=source.source_id,
            source_object_name="source_table",
        )
        source_object_attribute = process.data_store.get_or_create_item(
            model=SourceObjectAttribute,
            create=False,
            source_object_id=source_object.source_object_id,
            source_object_attribute_name="attr_1",
        )

        process_filter = process.data_store.get_or_create_item(
            model=ProcessFilter,
            process_id=process.process.process_id,
            source_object_attribute_id=source_object_attribute.source_object_attribute_id,
            filter_type_id=filter_type.filter_type_id,
            filter_value_string="testing",
        )

        given_result = process.find_process_filters(process=process.process.process_id)

        expected_result = [
            {
                "source_name": "source",
                "source_object_name": "source_table",
                "source_object_attribute_name": "attr_1",
                "filter_type_code": "eq",
                "filter_value_numeric": None,
                "filter_value_string": "testing",
            }
        ]

        self.assertEqual(expected_result, given_result)

    def test_find_process_source_attributes(self):
        """Testing that when querying based on a given process, that process' source attributes are returned."""
        process = ProcessTracker(
            process_name="Testing Source Attributes",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            source_object_attributes={"source": {"source_table": ["attr_1", "attr_2"]}},
        )

        given_result = process.find_process_source_attributes(
            process=process.process.process_id
        )

        expected_result = [
            {
                "source_name": "source",
                "source_type": "Undefined",
                "source_object_name": "source_table",
                "source_object_attribute_name": "attr_1",
                "is_key": False,
                "is_filter": False,
                "is_partition": False,
            },
            {
                "source_name": "source",
                "source_type": "Undefined",
                "source_object_name": "source_table",
                "source_object_attribute_name": "attr_2",
                "is_key": False,
                "is_filter": False,
                "is_partition": False,
            },
        ]

        return self.assertListEqual(expected_result, given_result)

    def test_find_process_target_attributes(self):
        """Testing that when querying based on a given process, that process' target attributes are returned."""
        process = ProcessTracker(
            process_name="Testing Source Attributes",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            target_object_attributes={"target": {"target_table": ["attr_1", "attr_2"]}},
        )

        given_result = process.find_process_target_attributes(
            process=process.process.process_id
        )

        expected_result = [
            {
                "target_name": "target",
                "target_type": "Undefined",
                "target_object_name": "target_table",
                "target_object_attribute_name": "attr_1",
                "is_key": False,
                "is_filter": False,
                "is_partition": False,
            },
            {
                "target_name": "target",
                "target_type": "Undefined",
                "target_object_name": "target_table",
                "target_object_attribute_name": "attr_2",
                "is_key": False,
                "is_filter": False,
                "is_partition": False,
            },
        ]

        return self.assertListEqual(expected_result, given_result)

    def test_process_tracker_with_process_run_id(self):
        """
        Testing that when providing a process_id to ProcessTracker, the instance is returned instead of a new instance
        being created.
        :return:
        """
        process_run_id = self.process_tracker.process_tracking_run.process_tracking_id

        new_process_tracker = ProcessTracker(process_run_id=process_run_id)

        expected_process_name_result = self.process_tracker.process_name
        given_process_name_result = new_process_tracker.process_name

        expected_actor_result = self.process_tracker.actor.actor_name
        given_actor_result = new_process_tracker.actor.actor_name

        expected_process_type_result = (
            self.process_tracker.process_type.process_type_name
        )
        given_process_type_result = new_process_tracker.process_type.process_type_name

        expected_tool_result = self.process_tracker.tool.tool_name
        given_tool_result = new_process_tracker.tool.tool_name

        expected_schedule_frequency_result = (
            self.process_tracker.schedule_frequency.schedule_frequency_name
        )
        given_schedule_frequency_result = (
            new_process_tracker.schedule_frequency.schedule_frequency_name
        )

        expected_process_run_name = self.process_tracker.process_run_name
        given_process_run_name = new_process_tracker.process_run_name

        self.assertEqual(expected_process_name_result, given_process_name_result)
        self.assertEqual(expected_actor_result, given_actor_result)
        self.assertEqual(expected_process_type_result, given_process_type_result)
        self.assertEqual(expected_tool_result, given_tool_result)
        self.assertEqual(
            expected_schedule_frequency_result, given_schedule_frequency_result
        )
        self.assertEqual(expected_process_run_name, given_process_run_name)

    def test_determine_process_sources(self):
        """
        When provided an existing process run id, determine which level of source is needed and provide the details.
        Should return the lowest grain possible (i.e. attribute)
        :return:
        """
        process_run_id = self.process_tracker.process_tracking_run.process_tracking_id

        new_process_tracker = ProcessTracker(process_run_id=process_run_id)

        given_sources = new_process_tracker.sources
        expected_sources = self.process_tracker.sources

        return expected_sources == given_sources

    def test_determine_process_targets(self):
        """
        When provided an existing process run id, determine which level of source targets is needed and provide the details.
        Should return the lowest grain possible (i.e. attribute)
        :return:
        """
        process_run_id = self.process_tracker.process_tracking_run.process_tracking_id

        new_process_tracker = ProcessTracker(process_run_id=process_run_id)

        given_targets = new_process_tracker.targets
        expected_targets = self.process_tracker.targets

        return expected_targets == given_targets

    def test_ensure_nulls_caught_on_instantiation(self):
        """
        With the adding of the ability of have a process_tracking_id we have to allow for nulled values for process_name
        and process_type.  If ProcessTracker is instantiated with either (or both) being null, an exception should be
        raised.
        :return:
        """

        with self.assertRaises(Exception) as context:

            ProcessTracker()

        return self.assertTrue(
            "process_name and process_type must be set." in str(context.exception)
        )
