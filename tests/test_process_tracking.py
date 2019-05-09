# Tests for validating process_tracking works as expected.

from datetime import datetime
import unittest

from models.process import ErrorType, ErrorTracking, Process, ProcessTracking

from process_tracker import data_store_type
from process_tracker import session
from process_tracker.process_tracking import ProcessTracker


class TestProcessTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.process_tracker = ProcessTracker(process_name='Testing Process Tracking Initialization'
                                         , process_type='Extract'
                                         , actor_name='UnitTesting'
                                         , tool_name='Spark'
                                         , source_name='Unittests')

    @classmethod
    def tearDownClass(cls):
        session.query(Process).delete()
        session.commit()

    def setUp(self):
        """
        Creating an initial process tracking run record for testing.
        :return:
        """

        self.process_tracker.register_new_process_run()

        self.process_id = self.process_tracker.process.process_id
        self.provided_end_date = datetime.now()

    def tearDown(self):
        """
        Need to clean up tables to return them to pristine state for other tests.
        :return:
        """
        session.query(ProcessTracking).delete()
        session.query(ErrorTracking).delete()
        session.query(ErrorType).delete()
        session.commit()

    def test_verify_session_variables_postgresql(self):
        """
        Testing that variables for creating postgresql sqlalchemy session.
        :return:
        """

        given_result = data_store_type
        expected_result = 'postgresql'

        self.assertEqual(given_result, expected_result)

    def test_initializing_process_tracking(self):
        """
        Testing that when ProcessTracking is initialized, the necessary objects are created.
        :return:
        """
        given_result = self.process_tracker.actor.actor_name
        expected_result = 'UnitTesting'

        self.assertEqual(given_result, expected_result)

    def test_register_new_process_run(self):
        """
        Testing that a new run record is created if there is no other instance of the same
        process currently in 'running' status.
        :return:
        """

        given_result = session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id).count()
        expected_result = 1

        self.assertEqual(given_result, expected_result)

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

    def test_change_run_status_complete(self):
        """
        Testing that when changing the run status from 'running' to 'complete' the run record updates successfully.
        :return:
        """
        self.process_tracker.change_run_status(new_status='completed')

        run_record = session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id)

        given_result = run_record[0].process_status_id
        expected_result = self.process_tracker.process_status_complete

        self.assertEqual(given_result, expected_result)

    def test_change_run_status_failed(self):
        """
        Testing that when changing the run status from 'running' to 'failed' the run record updates successfully.
        :return:
        """
        self.process_tracker.change_run_status(new_status='failed')

        run_record = session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id)

        given_result = run_record[0].process_status_id
        expected_result = self.process_tracker.process_status_failed

        self.assertEqual(given_result, expected_result)

    def test_change_run_status_with_end_date(self):
        """
        Testing that if end date is provided, the end date will be set on status change to 'completed'.
        :return:
        """

        self.process_tracker.change_run_status(new_status='completed', end_date=self.provided_end_date)

        run_record = session.query(ProcessTracking).filter(ProcessTracking.process_id == self.process_id)

        given_result = run_record[0].process_run_end_date_time
        expected_result = self.provided_end_date

        self.assertEqual(given_result, expected_result)

    def test_raise_run_error_type_exists_no_fail(self):
        """
        Testing that if an error is triggered, it gets recorded in the data store, provided that the error type exists.
        :return:
        """
        error_type = ErrorType(error_type_name='Does Exist')
        session.add(error_type)
        session.commit()

        self.process_tracker.raise_run_error(error_type_name='Does Exist')

        given_result = session.query(ErrorTracking)\
                              .filter(ErrorTracking.error_type_id == error_type.error_type_id)\
                              .count()

        expected_result = 1

        self.assertEqual(given_result, expected_result)

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
        session.add(error_type)
        session.commit()

        with self.assertRaises(Exception) as context:

            self.process_tracker.raise_run_error(error_type_name='Fail Check'
                                                 , fail_run=True
                                                 , end_date=self.provided_end_date)

        run_error = session.query(ErrorTracking)\
                           .filter(ErrorTracking.error_type_id == error_type.error_type_id)

        process_tracking_run = session.query(ProcessTracking)\
                                      .filter(ProcessTracking.process_tracking_id == run_error[0].process_tracking_id)

        process = session.query(Process).filter(Process.process_id == process_tracking_run[0].process_id)

        given_result = [process_tracking_run[0].process_status_id
                        , process_tracking_run[0].process_run_end_date_time
                        , process[0].last_failed_run_date_time]

        expected_result = [self.process_tracker.process_status_failed
                           , self.provided_end_date
                           , self.provided_end_date]

        with self.subTest():
            self.assertEqual(given_result, expected_result)
        with self.subTest():
            self.assertTrue('Process halting.  An error triggered the process to fail.' in str(context.exception))

