# Tests for validating process_tracking works as expected.

from datetime import datetime
import unittest

from sqlalchemy.orm import Session

from process_tracker.models.extract import Extract, ExtractProcess
from process_tracker.models.process import ErrorType, ErrorTracking, Process, ProcessTracking

from process_tracker.data_store import DataStore
from process_tracker.extract_tracker import ExtractTracker
from process_tracker.process_tracker import ProcessTracker


class TestProcessTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        data_store = DataStore()
        cls.session = data_store.session
        cls.data_store_type = data_store.data_store_type

    @classmethod
    def tearDownClass(cls):
        cls.session.query(Process).delete()
        cls.session.commit()

    def setUp(self):
        """
        Creating an initial process tracking run record for testing.
        :return:
        """
        self.process_tracker = ProcessTracker(process_name='Testing Process Tracking Initialization'
                                             , process_type='Extract'
                                             , actor_name='UnitTesting'
                                             , tool_name='Spark'
                                             , source_name='Unittests')

        self.process_id = self.process_tracker.process.process_id
        self.provided_end_date = datetime.now()

    def tearDown(self):
        """
        Need to clean up tables to return them to pristine state for other tests.
        :return:
        """
        self.session.query(ExtractProcess).delete()
        self.session.query(ProcessTracking).delete()
        self.session.query(Extract).delete()
        self.session.query(ErrorTracking).delete()
        self.session.query(ErrorType).delete()
        self.session.commit()

    def test_verify_session_variables_postgresql(self):
        """
        Testing that variables for creating postgresql sqlalchemy session.
        :return:
        """

        given_result = self.data_store_type
        expected_result = 'postgresql'

        self.assertEqual(expected_result, given_result)

    def test_find_ready_extracts_by_filename_full(self):
        """
        Testing that for the given full filename, find the extract, provided it's in 'ready' state.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename2.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename2.csv']

        given_result = self.process_tracker.find_ready_extracts_by_filename('test_extract_filename2.csv')

        self.assertEqual(expected_result, given_result)

    def test_find_ready_extracts_by_filename_partial(self):
        """
        Testing that for the given partial filename, find the extracts, provided they are in 'ready' state.  Should return
        them in ascending order by registration datetime.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename3-1.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        extract2 = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename3-2.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename3-1.csv'
                           , '/home/test/extract_dir/test_extract_filename3-2.csv']

        given_result = self.process_tracker.find_ready_extracts_by_filename('test_extract_filename')

        self.assertEqual(expected_result, given_result)

    def test_find_ready_extracts_by_filename_partial_not_descending(self):
        """
        Testing that for the given partial filename, find the extracts, provided they are in 'ready' state.  Verifying
        that records are NOT returned in descending order.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename3-1.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        extract2 = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename3-2.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename3-2.csv'
                           , '/home/test/extract_dir/test_extract_filename3-1.csv']

        given_result = self.process_tracker.find_ready_extracts_by_filename('test_extract_filename')

        self.assertNotEqual(expected_result, given_result)

    def test_find_ready_extracts_by_location(self):
        """
        Testing that for the given location name, find the extracts, provided they are in 'ready' state.  Should return
        them in ascending order by registration datettime.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename4-1.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        extract2 = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename4-2.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename4-1.csv'
                           , '/home/test/extract_dir/test_extract_filename4-2.csv']

        given_result = self.process_tracker.find_ready_extracts_by_location('Test Location')

        self.assertEqual(expected_result, given_result)

    def test_find_ready_extracts_by_location_not_descending(self):
        """
        Testing that for the given location name, find the extracts, provided they are in 'ready' state.  Verifying that
        records NOT returned in descending order.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename4-1.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        extract2 = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename4-2.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename4-2.csv'
                           , '/home/test/extract_dir/test_extract_filename4-1.csv']

        given_result = self.process_tracker.find_ready_extracts_by_location('Test Location')

        self.assertNotEqual(expected_result, given_result)

    def test_find_ready_extracts_by_process(self):
        """
        Testing that for the given process name, find the extracts, provided they are in 'ready' state.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename5-1.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        extract2 = ExtractTracker(process_run=self.process_tracker
                       , filename='test_extract_filename5-2.csv'
                       , location_name='Test Location'
                       , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename5-1.csv'
                           , '/home/test/extract_dir/test_extract_filename5-2.csv']

        given_result = self.process_tracker.find_ready_extracts_by_process('Testing Process Tracking Initialization')

        self.assertEqual(expected_result, given_result)

    def test_find_ready_extracts_by_process_not_descending(self):
        """
        Testing that for the given process name, find the extracts, provided they are in 'ready' state.  Verifying that
        records are NOT returned in Descending order.
        :return:
        """
        extract = ExtractTracker(process_run=self.process_tracker
                                 , filename='test_extract_filename5-1.csv'
                                 , location_name='Test Location'
                                 , location_path='/home/test/extract_dir')

        extract2 = ExtractTracker(process_run=self.process_tracker
                                  , filename='test_extract_filename5-2.csv'
                                  , location_name='Test Location'
                                  , location_path='/home/test/extract_dir')

        # Need to manually change the status, because this would normally be done while the process was processing data
        extract.extract.extract_status_id = extract.extract_status_ready
        session = Session.object_session(extract.extract)
        session.commit()

        extract2.extract.extract_status_id = extract2.extract_status_ready
        session = Session.object_session(extract2.extract)
        session.commit()

        expected_result = ['/home/test/extract_dir/test_extract_filename5-2.csv'
            , '/home/test/extract_dir/test_extract_filename5-1.csv']

        given_result = self.process_tracker.find_ready_extracts_by_process('Testing Process Tracking Initialization')

        self.assertNotEqual(expected_result, given_result)

    def test_initializing_process_tracking(self):
        """
        Testing that when ProcessTracking is initialized, the necessary objects are created.
        :return:
        """
        given_result = self.process_tracker.actor.actor_name
        expected_result = 'UnitTesting'

        self.assertEqual(expected_result, given_result)

    def test_register_new_process_run(self):
        """
        Testing that a new run record is created if there is no other instance of the same
        process currently in 'running' status.
        :return:
        """

        given_result = self.session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id).count()
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

        return self.assertTrue('The process Testing Process Tracking Initialization '
                               'is currently running.' in str(context.exception))

    def test_register_new_process_run_with_previous_run(self):
        """
        Testing that a new run record is created if there is another instance of same process in 'completed' or 'failed'
        status.  Also flips the is_latest_run flag on previous run to False.
        :return:
        """

        self.process_tracker.change_run_status(new_status='completed')
        self.process_tracker.register_new_process_run()

        process_runs = self.session.query(ProcessTracking)\
                              .filter(ProcessTracking.process_id == self.process_id)\
                              .order_by(ProcessTracking.process_tracking_id)

        given_result = process_runs[0].is_latest_run
        expected_result = False

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_complete(self):
        """
        Testing that when changing the run status from 'running' to 'complete' the run record updates successfully.
        :return:
        """
        self.process_tracker.change_run_status(new_status='completed')

        run_record = self.session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id)

        given_result = run_record[0].process_status_id
        expected_result = self.process_tracker.process_status_complete

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_failed(self):
        """
        Testing that when changing the run status from 'running' to 'failed' the run record updates successfully.
        :return:
        """
        self.process_tracker.change_run_status(new_status='failed')

        run_record = self.session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id)

        given_result = run_record[0].process_status_id
        expected_result = self.process_tracker.process_status_failed

        self.assertEqual(expected_result, given_result)

    def test_change_run_status_with_end_date(self):
        """
        Testing that if end date is provided, the end date will be set on status change to 'completed'.
        :return:
        """

        self.process_tracker.change_run_status(new_status='completed', end_date=self.provided_end_date)

        run_record = self.session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id)

        given_result = run_record[0].process_run_end_date_time
        expected_result = self.provided_end_date

        self.assertEqual(expected_result, given_result)

    def test_raise_run_error_type_exists_no_fail(self):
        """
        Testing that if an error is triggered, it gets recorded in the data store, provided that the error type exists.
        :return:
        """
        error_type = ErrorType(error_type_name='Does Exist')
        self.session.add(error_type)
        self.session.commit()

        self.process_tracker.raise_run_error(error_type_name='Does Exist')

        given_result = self.session.query(ErrorTracking)\
                              .filter(ErrorTracking.error_type_id == error_type.error_type_id)\
                              .count()

        expected_result = 1

        self.assertEqual(expected_result, given_result)

    def test_raise_run_error_type_not_exists(self):
        """
        Testing that exception raised if the error type does not exist.
        :return:
        """

        with self.assertRaises(Exception) as context:

            self.process_tracker.raise_run_error(error_type_name='Does Not Exist')

        return self.assertTrue('There is no record match in error_type_lkup .' in str(context.exception))

    def test_raise_run_error_with_fail(self):
        """
        Testing that if fail flag set, the process_tracking record status is changed to 'failed' and last_failure date
        for process is set.
        :return:
        """
        error_type = ErrorType(error_type_name='Fail Check')
        self.session.add(error_type)
        self.session.commit()

        with self.assertRaises(Exception) as context:

            self.process_tracker.raise_run_error(error_type_name='Fail Check'
                                                 , fail_run=True
                                                 , end_date=self.provided_end_date)

        run_error = self.session.query(ErrorTracking)\
                           .filter(ErrorTracking.error_type_id == error_type.error_type_id)

        process_tracking_run = self.session.query(ProcessTracking)\
                                      .filter(ProcessTracking.process_tracking_id == run_error[0].process_tracking_id)

        process = self.session.query(Process).filter(Process.process_id == process_tracking_run[0].process_id)

        given_result = [process_tracking_run[0].process_status_id
                        , process_tracking_run[0].process_run_end_date_time
                        , process[0].last_failed_run_date_time]

        expected_result = [self.process_tracker.process_status_failed
                           , self.provided_end_date
                           , self.provided_end_date]

        with self.subTest():
            self.assertEqual(expected_result, given_result)
        with self.subTest():
            self.assertTrue('Process halting.  An error triggered the process to fail.' in str(context.exception))

