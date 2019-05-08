# Tests for validating process_tracking works as expected.

import unittest

from models.process import ProcessTracking

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

    def tearDown(self):
        """
        Need to clean up tables to return them to pristine state for other tests.
        :return:
        """
        session.query(ProcessTracking).delete()

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
        Testing that a new run record is created if there are no runs currently running
        :return:
        """
        process_id = self.process_tracker.process.process_id

        self.process_tracker.register_new_process_run()

        # Running registration a second time to mimic job being run twice
        self.process_tracker.register_new_process_run()

        given_result = session.query(ProcessTracking).filter(ProcessTracking.process_id == process_id).count()
        expected_result = 1

        self.assertEqual(given_result, expected_result)