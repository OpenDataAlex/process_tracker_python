# Tests for validating extract_tracking

from datetime import datetime
import unittest

from models.extract import Extract, ExtractProcess, ExtractStatus
from models.process import Process, ProcessTracking

from process_tracker import session
from process_tracker.extract_tracking import ExtractTracker
from process_tracker.process_tracking import ProcessTracker


class TestExtractTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.process_tracker = ProcessTracker(process_name='Testing Extract Tracking'
                                             , process_type='Load'
                                             , actor_name='UnitTesting'
                                             , tool_name='Spark'
                                             , source_name='Unittests')

        cls.process_tracker.register_new_process_run()

        cls.process_run = cls.process_tracker.process_tracking_run

    @classmethod
    def tearDownClass(cls):
        session.query(Process).delete()
        session.commit()

    def setUp(self):
        """
        Creating an initial extract tracking record for testing.
        :return:
        """

        self.extract = ExtractTracker(process_run=self.process_run
                                      , filename='test_extract_filename.csv'
                                      , location_name='Test Location'
                                      , location_path='/home/test/extract_dir')

    def tearDown(self):
        """
        Need to clean up tables to return them to pristine state for other tests.
        :return:
        """
        session.query(ProcessTracking).delete()
        session.query(ExtractProcess).delete()
        session.query(Extract).delete()
        session.commit()

    def test_change_extract_status(self):
        """
        Testing that when changing the extract status, the extract record and extract process record updates
        successfully.
        :return:
        """
        extract_id = self.extract.extract.extract_id
        self.extract.change_extract_status('ready')

        extract_record = session.query(Extract).filter(Extract.extract_id == extract_id)
        extract_process_record = session.query(ExtractProcess).filter(ExtractProcess.extract_tracking_id == extract_id)

        given_result = [extract_record[0].extract_status_id
                        , extract_process_record[0].extract_process_status_id]

        expected_result = [self.extract.extract_status_ready
                           , self.extract.extract_status_ready]

        self.assertEqual(given_result, expected_result)