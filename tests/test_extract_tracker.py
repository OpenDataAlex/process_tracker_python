# Tests for validating extract_tracking
from datetime import datetime, timedelta
from pathlib import Path
import unittest

from process_tracker.models.capacity import ClusterProcess
from process_tracker.models.extract import Extract, ExtractProcess, Location
from process_tracker.models.process import (
    Process,
    ProcessDependency,
    ProcessSource,
    ProcessTarget,
    ProcessTracking,
)

from process_tracker.extract_tracker import ExtractDependency, ExtractTracker
from process_tracker.process_tracker import ErrorTracking, ProcessTracker
from process_tracker.utilities import utilities


class TestExtractTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process_tracker = ProcessTracker(
            process_name="Testing Extract Tracking",
            process_type="Load",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        cls.process_run = cls.process_tracker

        data_store = cls.process_tracker.data_store

        cls.session = data_store.session
        cls.data_store_type = data_store.data_store_type

    @classmethod
    def tearDownClass(cls):
        cls.session.query(ClusterProcess).delete()
        cls.session.query(ErrorTracking).delete()
        cls.session.query(ExtractProcess).delete()
        cls.session.query(ProcessTracking).delete()
        cls.session.query(ProcessSource).delete()
        cls.session.query(ProcessTarget).delete()
        cls.session.query(ProcessDependency).delete()
        cls.session.query(Process).delete()
        cls.session.commit()
        cls.session.close()

    def setUp(self):
        """
        Creating an initial extract tracking record for testing.
        :return:
        """

        self.extract = ExtractTracker(
            process_run=self.process_run,
            filename="test_extract_filename.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )

    def tearDown(self):
        """
        Need to clean up tables to return them to pristine state for other tests.
        :return:
        """
        self.session.query(ExtractDependency).delete()
        self.session.query(ExtractProcess).delete()
        self.session.query(Extract).delete()
        self.session.query(Location).delete()
        self.session.commit()

    def test_add_dependency_parent(self):
        """
        Testing that a parent extract dependency is created when adding dependency to extract.
        :return:
        """
        dependent_extract = ExtractTracker(
            process_run=self.process_run,
            filename="Dependent File.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )
        self.extract.add_dependency(
            dependency_type="parent", dependency=dependent_extract
        )

        given_result = (
            self.session.query(ExtractDependency)
            .filter(
                ExtractDependency.child_extract_id == self.extract.extract.extract_id
            )
            .count()
        )

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_add_dependency_child(self):
        """
        Testing that a child extract dependency is created when adding dependency to extract.
        :return:
        """
        dependent_extract = ExtractTracker(
            process_run=self.process_run,
            filename="Dependent File.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )
        self.extract.add_dependency(
            dependency_type="child", dependency=dependent_extract
        )

        given_result = (
            self.session.query(ExtractDependency)
            .filter(
                ExtractDependency.parent_extract_id == self.extract.extract.extract_id
            )
            .count()
        )

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_add_dependency_invalid_type(self):
        """
        Ensuring that when a dependency is added, only 'parent' and 'child' are accepted.
        :return:
        """

        with self.assertRaises(Exception) as context:
            self.extract.add_dependency(
                dependency_type="blarg", dependency=self.extract.extract
            )
        return self.assertTrue(
            "blarg is an invalid extract dependency type." in str(context.exception)
        )

    def test_initialization_no_location_no_location_path(self):
        """
        Testing that if no location or location path is set, an error is thrown.
        :return:
        """

        with self.assertRaises(Exception) as context:
            # Running registration a second time to mimic job being run twice
            ExtractTracker(
                process_run=self.process_run, filename="test_extract_filename.csv"
            )

        return self.assertTrue(
            "A location object or location_path must be provided."
            in str(context.exception)
        )

    def test_change_extract_status(self):
        """
        Testing that when changing the extract status, the extract record and extract process record updates
        successfully.
        :return:
        """
        extract_id = self.extract.extract.extract_id
        self.extract.change_extract_status("ready")

        extract_record = self.session.query(Extract).filter(
            Extract.extract_id == extract_id
        )
        extract_process_record = self.session.query(ExtractProcess).filter(
            ExtractProcess.extract_tracking_id == extract_id
        )

        given_result = [
            extract_record[0].extract_status_id,
            extract_process_record[0].extract_process_status_id,
        ]

        expected_result = [
            self.extract.extract_status_ready,
            self.extract.extract_status_ready,
        ]

        self.assertEqual(expected_result, given_result)

    def test_change_extract_status_invalid_type(self):
        """
        When trying to change a extract's status and the status is an invalid type, throw and error.
        :return:
        """

        with self.assertRaises(Exception) as context:
            # Running registration a second time to mimic job being run twice
            self.extract.change_extract_status(new_status="blarg")

        return self.assertTrue(
            "blarg is not a valid extract status type.  "
            "Please add the status to extract_status_lkup" in str(context.exception)
        )

    def test_change_extract_status_initialization(self):
        """
        Testing that when the extract is first being worked on by a process, the status is set to 'initializing'
        :return:
        """
        extract_id = self.extract.extract.extract_id
        self.extract.retrieve_extract_process()

        extract_process_record = self.session.query(ExtractProcess).filter(
            ExtractProcess.extract_tracking_id == extract_id
        )

        given_result = extract_process_record[0].extract_process_status_id
        expected_result = self.extract.extract_status_initializing

        self.assertEqual(expected_result, given_result)

    def test_derive_location_name_local_path(self):
        """
        Testing that if a location name is not provided, one is created from the local path provided.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_run,
            filename="test_extract_filename2.csv",
            location_path="/home/test/extract_dir2",
        )

        location = self.session.query(Location).filter(
            Location.location_id == extract.extract.extract_location_id
        )

        given_result = location[0].location_name
        expected_result = "extract_dir2"

        self.assertEqual(expected_result, given_result)

    def test_derive_location_name_s3(self):
        """
        Testing that if a location name is not provided, one is created from the s3 path provided.
        :return:
        """
        extract = ExtractTracker(
            process_run=self.process_run,
            filename="test_extract_filename2.csv",
            location_path="https://test-test.s3.amazonaws.com/test/extract_dir",
        )

        location = self.session.query(Location).filter(
            Location.location_id == extract.extract.extract_location_id
        )

        given_result = location[0].location_name
        expected_result = "s3 - extract_dir"

        self.assertEqual(expected_result, given_result)

    def test_extract_dependency_check(self):
        """
        Testing that if no dependencies are in a state that doesn't stop an extract from being loaded, then the extract
        is loaded.
        :return:
        """
        dependent_extract = ExtractTracker(
            process_run=self.process_run,
            filename="Dependent File.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )
        dependency = ExtractDependency(
            child_extract_id=dependent_extract.extract.extract_id,
            parent_extract_id=self.extract.extract.extract_id,
        )

        self.session.add(dependency)
        self.session.commit()
        self.extract.change_extract_status("loaded")

        given_result = dependent_extract.extract_dependency_check()

        expected_result = False

        self.assertEqual(expected_result, given_result)

    def test_extract_dependency_check_blocked(self):
        """
        Testing that if a dependency is in a state that stops an extract from being loaded, then the extract triggers an
        error blocking the file from being processed.
        :return:
        """
        dependent_extract = ExtractTracker(
            process_run=self.process_run,
            filename="Dependent File.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )
        dependency = ExtractDependency(
            child_extract_id=dependent_extract.extract.extract_id,
            parent_extract_id=self.extract.extract.extract_id,
        )

        self.session.add(dependency)
        self.session.commit()

        self.extract.change_extract_status("loading")

        with self.assertRaises(Exception) as context:
            dependent_extract.extract_dependency_check()

        clean_filename = str(Path("/home/test/extract_dir/Dependent File.csv"))

        return self.assertTrue(
            "Extract files that extract %s is dependent on have not been loaded,"
            " are being created, or are in the process of loading." % clean_filename
            in str(context.exception)
        )

    def test_extract_dependency_check_bulk(self):
        """
        Testing that if no dependencies are in a state that doesn't stop an extract from being loaded, then the extract
        is loaded.
        :return:
        """
        dependent_extract = ExtractTracker(
            process_run=self.process_run,
            filename="Dependent File.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )
        dependency = ExtractDependency(
            child_extract_id=dependent_extract.extract.extract_id,
            parent_extract_id=self.extract.extract.extract_id,
        )

        self.session.add(dependency)
        self.session.commit()
        self.extract.change_extract_status("loaded")

        extract_trackers = [dependent_extract, self.extract]

        given_result = dependent_extract.extract_dependency_check(
            extracts=extract_trackers
        )

        expected_result = False

        self.assertEqual(expected_result, given_result)

    def test_extract_dependency_check_bulk_in_list(self):
        """
        Testing that even if dependencies are in a state that stops an extract from being loaded, the extract status can
        still be changed because it is in the bulk extract list.
        :return:
        """
        dependent_extract = ExtractTracker(
            process_run=self.process_run,
            filename="Dependent File.csv",
            location_name="Test Location",
            location_path="/home/test/extract_dir",
        )
        dependency = ExtractDependency(
            child_extract_id=dependent_extract.extract.extract_id,
            parent_extract_id=self.extract.extract.extract_id,
        )

        self.session.add(dependency)
        self.session.commit()
        self.extract.change_extract_status("loading")

        extracts = [dependent_extract, self.extract]

        given_result = dependent_extract.extract_dependency_check(extracts=extracts)

        expected_result = False

        self.assertEqual(expected_result, given_result)

    def test_location_name_provided(self):
        """
        Testing that if a location name is provided (like with default extract), one is not created.
        :return:
        """
        location = self.session.query(Location).filter(
            Location.location_id == self.extract.extract.extract_location_id
        )

        given_result = location[0].location_name
        expected_result = "Test Location"

        self.assertEqual(expected_result, given_result)

    def test_set_extract_low_high_dates_write(self):
        """
        Testing that low and high dates are set for the write audit fields.
        :return:
        """
        low_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        ) - timedelta(hours=1)

        high_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        )

        self.extract.set_extract_low_high_dates(
            low_date=low_date, high_date=high_date, audit_type="write"
        )

        given_dates = self.session.query(
            Extract.extract_write_low_date_time, Extract.extract_write_high_date_time
        ).filter(Extract.extract_id == self.extract.extract.extract_id)

        expected_result = [low_date, high_date]
        given_result = [
            given_dates[0].extract_write_low_date_time,
            given_dates[0].extract_write_high_date_time,
        ]

        self.assertEqual(expected_result, given_result)

    def test_set_extract_low_high_dates_load(self):
        """
        Testing that low and high dates are set for the load audit fields.
        :return:
        """

        low_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        ) - timedelta(hours=1)

        high_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        )

        self.extract.set_extract_low_high_dates(
            low_date=low_date, high_date=high_date, audit_type="load"
        )

        given_dates = self.session.query(
            Extract.extract_load_low_date_time, Extract.extract_load_high_date_time
        ).filter(Extract.extract_id == self.extract.extract.extract_id)

        expected_result = [low_date, high_date]
        given_result = [
            given_dates[0].extract_load_low_date_time,
            given_dates[0].extract_load_high_date_time,
        ]

        self.assertEqual(expected_result, given_result)

    def test_set_extract_low_high_dates_invalid_type(self):
        """
        Testing that the set_extract_low_high_dates method does not allow invalid types.
        :return:
        """

        low_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        ) - timedelta(hours=1)

        high_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        )

        with self.assertRaises(Exception) as context:
            self.extract.set_extract_low_high_dates(
                low_date=low_date, high_date=high_date, audit_type="blarg"
            )

        return self.assertTrue(
            "blarg is not a valid audit_type." in str(context.exception)
        )

    def test_set_extract_record_count_write(self):
        """
        Testing that the record count is set for the write record count column.
        :return:
        """
        records = 10000

        self.extract.set_extract_record_count(num_records=records, audit_type="write")

        given_result = self.session.query(Extract.extract_write_record_count).filter(
            Extract.extract_id == self.extract.extract.extract_id
        )

        self.assertEqual(records, given_result[0].extract_write_record_count)

    def test_set_extract_record_count_load(self):
        """
        Testing that the record count is set for the load record count column.
        :return:
        """
        records = 10000

        self.extract.set_extract_record_count(num_records=records, audit_type="load")

        given_result = self.session.query(Extract.extract_load_record_count).filter(
            Extract.extract_id == self.extract.extract.extract_id
        )

        self.assertEqual(records, given_result[0].extract_load_record_count)

    def test_set_extract_record_count_invalid_type(self):
        """
        Testing that the set_extract_record_count method does not allow invalid types.
        :return:
        """

        with self.assertRaises(Exception) as context:
            self.extract.set_extract_record_count(
                num_records=100000, audit_type="blarg"
            )

        return self.assertTrue(
            "blarg is not a valid audit_type." in str(context.exception)
        )
