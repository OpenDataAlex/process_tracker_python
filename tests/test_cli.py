from click.testing import CliRunner
import unittest

import process_tracker.cli
from process_tracker.data_store import DataStore

from process_tracker.models.actor import Actor
from process_tracker.models.extract import ExtractStatus
from process_tracker.models.process import ErrorType, ProcessStatus, ProcessType
from process_tracker.models.source import Source
from process_tracker.models.tool import Tool


class TestCli(unittest.TestCase):

    def setUp(self):

        self.runner = CliRunner()
        self.session = DataStore().session

    # def test_setup(self):
    #
    # def test_setup_overwrite(self):
    #
    # def test_setup_already_exists(self):

    def test_create_actor(self):
        """
        Testing that when creating an actor record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t actor -n "Test Test"')

        instance = self.session.query(Actor).filter(Actor.actor_name == 'Test Test')

        self.assertEqual('Test Test', instance[0].actor_name)
        self.assertEqual(0, result.exit_code)

    def test_create_extract_status(self):
        """
        Testing that when creating an extract status record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t "extract status" -n "New Status"')

        instance = self.session.query(ExtractStatus).filter(ExtractStatus.extract_status_name == 'New Status')


        self.assertEqual('New Status', instance[0].extract_status_name)
        self.assertEqual(0, result.exit_code)

    def test_create_error_type(self):
        """
        Testing that when creating an error type record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t "error type" -n "New Error Type"')

        instance = self.session.query(ErrorType).filter(ErrorType.error_type_name == 'New Error Type')

        self.assertEqual('New Error Type', instance[0].error_type_name)
        self.assertEqual(0, result.exit_code)

    def test_create_process_type(self):
        """
        Testing that when creating an process type record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t "process type" -n "New Process Type"')

        instance = self.session.query(ProcessType).filter(ProcessType.process_type_name == 'New Process Type')

        self.assertEqual('New Process Type', instance[0].process_type_name)
        self.assertEqual(0, result.exit_code)

    def test_create_process_status(self):
        """
        Testing that when creating an process status record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t "process status" -n "New Status Type"')

        instance = self.session.query(ProcessStatus).filter(ProcessStatus.process_status_name == 'New Status Type')

        self.assertEqual('New Status Type', instance[0].process_status_name)
        self.assertEqual(0, result.exit_code)

    def test_create_source(self):
        """
        Testing that when creating a source record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t source -n "New Source"')

        instance = self.session.query(Source).filter(Source.source_name == 'New Source')

        self.assertEqual('New Source', instance[0].source_name)
        self.assertEqual(0, result.exit_code)

    def test_create_tool(self):
        """
        Testing that when creating a tool record it is added.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'create -t tool -n "New Tool"')

        instance = self.session.query(Tool).filter(Tool.tool_name == 'New Tool')

        self.assertEqual('New Tool', instance[0].tool_name)
        self.assertEqual(0, result.exit_code)

    # def test_create_process_dependency(self):
    #     """
    #     Testing that when creating an error type record it is added.
    #     :return:
    #     """
    #     result = self.runner.invoke(process_tracker.cli.main, 'create -t "error type" -n "New Error Type"')
    #
    #     self.assertEqual(0, result.exit_code)

    def test_delete_actor(self):
        """
        Testing that when deleting an actor record it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t actor -n "Test Test"')

        instance = self.session.query(Actor).filter(Actor.actor_name == 'Test Test').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_extract_status(self):
        """
        Testing that when deleting an extract status record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "extract status" -n "New Status"')

        instance = self.session.query(ExtractStatus).filter(ExtractStatus.extract_status_name == 'New Status').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_extract_status_protected(self):
        """
        Testing that when deleting a protected extract status record it is not deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "extract status" -n "initializing"')

        expected_result = 'The item could not be deleted because it is a protected record.'

        self.assertIn(expected_result, result.output)

    def test_delete_error_type(self):
        """
        Testing that when deleting an error type record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "error type" -n "New Error Type"')

        instance = self.session.query(ErrorType).filter(ErrorType.error_type_name == 'New Error Type').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_error_type_protected(self):
        """
        Testing that when deleting a protected error type record it is not deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "error type" -n "File Error"')
        expected_result = 'The item could not be deleted because it is a protected record.'

        self.assertIn(expected_result, result.output)

    def test_delete_process_type(self):
        """
        Testing that when deleting an process type record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "process type" -n "New Process Type"')

        instance = self.session.query(ProcessType).filter(ProcessType.process_type_name == 'New Process Type').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_process_type_protected(self):
        """
        Testing that when deleting a protected process type record it is not deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "process type" -n "extract"')

        expected_result = 'The item could not be deleted because it is a protected record.'

        self.assertIn(expected_result, result.output)

    def test_delete_process_status(self):
        """
        Testing that when deleting an process status record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "process status" -n "New Status Type"')

        instance = self.session.query(ProcessStatus).filter(ProcessStatus.process_status_name == 'New Status Type').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_process_status_protected(self):
        """
        Testing that when deleting a protected process status record it is not deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "process status" -n "running"')

        expected_result = 'The item could not be deleted because it is a protected record.'

        self.assertIn(expected_result, result.output)

    def test_delete_source(self):
        """
        Testing that when deleting a source record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "source" -n "New Source"')

        instance = self.session.query(Source).filter(Source.source_name == 'New Source').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_tool(self):
        """
        Testing that when deleting a tool record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(process_tracker.cli.main, 'delete -t "tool" -n "New Tool"')

        instance = self.session.query(Tool).filter(Tool.tool_name == 'New Tool').first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    # def test_delete_process_dependency(self):
    #
    def test_update_actor(self):

    def test_update_extract_status(self):

    def test_update_extract_status_protected(self):

    def test_update_error_type(self):

    def test_update_error_type_protected(self):

    def test_update_process_type(self):

    def test_update_process_type_protected(self):

    def test_update_process_status(self):

    def test_update_process_status_protected(self):

    def test_update_source(self):

    def test_update_tool(self):

    # def test_update_process_dependency(self):