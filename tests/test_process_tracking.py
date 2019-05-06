# Tests for validating process_tracking works as expected.

import unittest

from process_tracker import data_store_type
from process_tracker.process_tracking import ProcessTracker


class TestProcessTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        process_tracker = ProcessTracker(process_name='Testing Process Tracking Initialization'
                                         , process_type='Extract'
                                         , actor_name='UnitTesting'
                                         , tool_name='Spark'
                                         , source_name='Unittests')

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
        given_result = self.process_tracker.actor
        expected_result = ''

        self.assertEqual(given_result, expected_result)