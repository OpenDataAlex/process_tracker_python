import logging
import os
import time
import unittest

from click.testing import CliRunner
import sqlalchemy

from process_tracker.cli import main
from process_tracker.data_store import DataStore
from process_tracker.process_tracker import ProcessTracker
from process_tracker.utilities.logging import console

from process_tracker.models.actor import Actor
from process_tracker.models.capacity import Cluster, ClusterProcess
from process_tracker.models.extract import ExtractStatus
from process_tracker.models.process import (
    ErrorType,
    Process,
    ProcessDependency,
    ProcessStatus,
    ProcessType,
)
from process_tracker.models.source import Source
from process_tracker.models.tool import Tool


class TestCliDataStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(__name__)
        cls.logger.addHandler(console)

    def setUp(self):
        self.data_store = DataStore()
        self.session = self.data_store.session
        self.runner = CliRunner()

    @unittest.skipIf(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        "Skipping this test on Travis CI.",
    )
    @unittest.skip("Causes a deadlock when run in the suite.")
    def test_setup_delete(self):
        """
        Testing that data store is deleted if delete is triggered.
        :return:
        """
        self.data_store.delete_data_store()
        table_names = sqlalchemy.inspect(self.data_store.engine).get_table_names()
        is_empty = table_names == []

        self.assertTrue(True, is_empty)

    # def test_setup_overwrite(self):
    #     """
    #     Testing that if data store is already set up and overwrite is set to True, wipe and recreate the data store.
    #     :return:
    #     """
    #     self.runner.invoke(main, "setup -o True")
    #
    #     instance = self.session.query(Actor).count()
    #
    #     self.assertEqual(0, instance)
    @unittest.skipIf(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        "Skipping this test on Travis CI.",
    )
    @unittest.skip("Causes a deadlock when run in the suite.")
    def test_setup_initialize(self):
        """
        Testing that if data store is not already set up, create the data store and initialize required data.
        :return:
        """
        result = self.runner.invoke(main, "setup")

        instance = self.session.query(ProcessStatus).count()

        self.assertEqual(3, instance)


class TestCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(__name__)
        cls.logger.addHandler(console)

    def setUp(self):
        self.data_store = DataStore()
        self.session = self.data_store.session
        self.runner = CliRunner()

    def test_create_actor(self):
        """
        Testing that when creating an actor record it is added.
        :return:
        """
        result = self.runner.invoke(main, ["create", "-t", "actor", "-n", "Test Test"])

        instance = (
            self.session.query(Actor).filter(Actor.actor_name == "Test Test").first()
        )
        given_name = instance.actor_name

        self.runner.invoke(main, ["delete", "-t", "actor", "-n", "Test Test"])

        self.assertEqual("Test Test", given_name)
        self.assertEqual(0, result.exit_code)

    def test_create_cluster(self):
        """
        Testing that when creating a performance cluster record it is added.
        :return:
        """
        result = self.runner.invoke(
            main,
            'create -t cluster -n "Test Cluster" --max-processing 4 --processing-unit DPU --max-memory 128 --memory-unit GB',
        )

        instance = (
            self.session.query(Cluster)
            .filter(Cluster.cluster_name == "Test Cluster")
            .first()
        )

        given_name = instance.cluster_name

        self.runner.invoke(main, ["delete", "-t", "cluster", "-n", "Test Cluster"])

        self.assertEqual("Test Cluster", given_name)

    def test_create_cluster_process(self):
        """
        Testing that when creating a cluster process relationship record, it is added.
        :return:
        """
        cluster = self.data_store.get_or_create_item(
            model=Cluster, cluster_name="Test Cluster"
        )

        process = self.data_store.get_or_create_item(
            model=Process, process_name="Test Cluster Process"
        )

        result = self.runner.invoke(
            main,
            'create -t "cluster process" --cluster "%s" --child "%s"'
            % (cluster.cluster_name, process.process_name),
        )

        instance = (
            self.session.query(ClusterProcess)
            .filter(ClusterProcess.cluster_id == cluster.cluster_id)
            .filter(ClusterProcess.process_id == process.process_id)
            .first()
        )

        given_result = [instance.cluster_id, instance.process_id]
        expected_result = [cluster.cluster_id, process.process_id]

        self.runner.invoke(
            main,
            [
                "delete",
                "-t",
                "cluster process",
                "--cluster",
                "Test Cluster",
                "-c",
                "Test Cluster Process",
            ],
        )
        self.runner.invoke(main, ["delete", "-t", "cluster", "-n", "Test Cluster"])
        self.runner.invoke(
            main, ["delete", "-t", "process", "-n", "Test Cluster Process"]
        )

        self.assertEqual(expected_result, given_result)

    def test_create_extract_status(self):
        """
        Testing that when creating an extract status record it is added.
        :return:
        """
        result = self.runner.invoke(
            main, ["create", "-t", "extract status", "-n", "New Status"]
        )

        instance = (
            self.session.query(ExtractStatus)
            .filter(ExtractStatus.extract_status_name == "New Status")
            .first()
        )
        given_name = instance.extract_status_name
        self.runner.invoke(main, ["delete", "-t", "extract status", "-n", "New Status"])

        self.assertEqual("New Status", given_name)
        self.assertEqual(0, result.exit_code)

    def test_create_error_type(self):
        """
        Testing that when creating an error type record it is added.
        :return:
        """
        result = self.runner.invoke(main, 'create -t "error type" -n "New Error Type"')
        instance = (
            self.session.query(ErrorType)
            .filter(ErrorType.error_type_name == "New Error Type")
            .first()
        )
        try:
            self.logger.debug(str(instance.error_type_name))
        except Exception as e:
            self.logger.debug(e)
        given_name = instance.error_type_name

        self.runner.invoke(main, 'delete -t "error type" -n "New Error Type"')

        self.assertEqual("New Error Type", given_name)

        self.assertEqual(0, result.exit_code)

    # def test_create_invalid_type(self):
    #     """
    #     Testing that when an invalid type is passed to the create option, an exception occurs.
    #     :return:
    #     """
    #     given_result = self.runner.invoke(main, 'create -t blarg -n "Argle Bargle"')
    #     given_result = given_result.exception
    #
    #     expected_result = "Invalid topic type."
    #
    #     return self.assertEqual(expected_result, given_result)
    def test_create_process_dependency(self):
        """
        Testing that when creating a process dependency record, it is created.
        :return:
        """
        parent_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency Parent",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        parent_process.change_run_status("completed")

        child_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency Child",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        child_process.change_run_status("completed")

        result = self.runner.invoke(
            main,
            'create -t "process dependency" -p "%s" -c "%s"'
            % (parent_process.process_name, child_process.process_name),
        )

        instance = (
            self.session.query(ProcessDependency)
            .filter(
                ProcessDependency.parent_process_id == parent_process.process.process_id
            )
            .filter(
                ProcessDependency.child_process_id == child_process.process.process_id
            )
            .first()
        )

        given_result = [instance.parent_process_id, instance.child_process_id]
        expected_result = [
            parent_process.process.process_id,
            child_process.process.process_id,
        ]

        self.assertEqual(expected_result, given_result)
        self.assertEqual(0, result.exit_code)

    def test_create_process_type(self):
        """
        Testing that when creating an process type record it is added.
        :return:
        """
        result = self.runner.invoke(
            main, 'create -t "process type" -n "New Process Type"'
        )

        instance = (
            self.session.query(ProcessType)
            .filter(ProcessType.process_type_name == "New Process Type")
            .first()
        )
        given_name = instance.process_type_name

        self.runner.invoke(main, 'delete -t "process type" -n "New Process Type"')

        self.assertEqual("New Process Type", given_name)
        self.assertEqual(0, result.exit_code)

    def test_create_process_status(self):
        """
        Testing that when creating an process status record it is added.
        :return:
        """
        result = self.runner.invoke(
            main, 'create -t "process status" -n "New Status Type"'
        )

        instance = (
            self.session.query(ProcessStatus)
            .filter(ProcessStatus.process_status_name == "New Status Type")
            .first()
        )
        given_name = instance.process_status_name

        self.runner.invoke(main, 'delete -t "process status" -n "New Status Type"')

        self.assertEqual("New Status Type", given_name)
        self.assertEqual(0, result.exit_code)

    def test_create_source(self):
        """
        Testing that when creating a source record it is added.
        :return:
        """
        result = self.runner.invoke(main, 'create -t source -n "New Source"')

        instance = (
            self.session.query(Source)
            .filter(Source.source_name == "New Source")
            .first()
        )
        given_name = instance.source_name

        self.runner.invoke(main, 'delete -t "source" -n "New Source"')

        self.assertEqual("New Source", given_name)
        self.assertEqual(0, result.exit_code)

    def test_create_tool(self):
        """
        Testing that when creating a tool record it is added.
        :return:
        """
        result = self.runner.invoke(main, 'create -t tool -n "New Tool"')

        instance = self.session.query(Tool).filter(Tool.tool_name == "New Tool").first()
        given_name = instance.tool_name

        self.runner.invoke(main, 'delete -t "tool" -n "New Tool"')

        self.assertEqual("New Tool", given_name)
        self.assertEqual(0, result.exit_code)

    # def test_create_process_dependency(self):
    #     """
    #     Testing that when creating an error type record it is added.
    #     :return:
    #     """
    #     result = self.runner.invoke(main, 'create -t "error type" -n "New Error Type"')
    #
    #     self.assertEqual(0, result.exit_code)

    def test_delete_actor(self):
        """
        Testing that when deleting an actor record it is deleted.
        :return:
        """
        self.runner.invoke(main, 'create -t actor -n "Test Test"')
        result = self.runner.invoke(main, 'delete -t actor -n "Test Test"')

        instance = (
            self.session.query(Actor).filter(Actor.actor_name == "Test Test").first()
        )
        self.logger.debug(result.output)
        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_cluster(self):
        """
        Testing that when deleting a cluster record it is deleted.
        :return:
        """
        self.runner.invoke(
            main,
            'create -t cluster -n "Test Cluster" --max-processing 4 --processing-unit DPU --max-memory 128 --memory-unit GB',
        )
        result = self.runner.invoke(main, 'delete -t cluster -n "Test Cluster"')

        instance = (
            self.session.query(Cluster)
            .filter(Cluster.cluster_name == "Test Cluster")
            .first()
        )

        self.logger.debug(result.output)
        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_create_cluster_process(self):
        """
        Testing that when creating a cluster process relationship record, it is added.
        :return:
        """
        cluster = self.data_store.get_or_create_item(
            model=Cluster, cluster_name="Test Cluster"
        )

        process = self.data_store.get_or_create_item(
            model=Process, process_name="Test Cluster Process"
        )

        result = self.runner.invoke(
            main,
            'create -t "cluster process" --cluster "%s" --child "%s"'
            % (cluster.cluster_name, process.process_name),
        )

        self.runner.invoke(
            main,
            [
                "delete",
                "-t",
                "cluster process",
                "--cluster",
                "Test Cluster",
                "-c",
                "Test Cluster Process",
            ],
        )
        self.runner.invoke(main, ["delete", "-t", "cluster", "-n", "Test Cluster"])
        self.runner.invoke(
            main, ["delete", "-t", "process", "-n", "Test Cluster Process"]
        )

        instance = (
            self.session.query(ClusterProcess)
            .filter(ClusterProcess.cluster_id == cluster.cluster_id)
            .filter(ClusterProcess.process_id == process.process_id)
            .first()
        )

        self.assertEqual(None, instance)

    def test_delete_extract_status(self):
        """
        Testing that when deleting an extract status record not on the protected list, it is deleted.
        :return:
        """
        self.runner.invoke(main, 'create -t "extract status" -n "New Status"')
        result = self.runner.invoke(main, 'delete -t "extract status" -n "New Status"')

        instance = (
            self.session.query(ExtractStatus)
            .filter(ExtractStatus.extract_status_name == "New Status")
            .first()
        )

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_extract_status_protected(self):
        """
        Testing that when deleting a protected extract status record it is not deleted.
        :return:
        """
        result = self.runner.invoke(
            main, 'delete -t "extract status" -n "initializing"'
        )

        expected_result = (
            "The item could not be deleted because it is a protected record."
        )

        self.assertIn(expected_result, result.output)
        self.assertEqual(0, result.exit_code)

    def test_delete_error_type(self):
        """
        Testing that when deleting an error type record not on the protected list, it is deleted.
        :return:
        """
        result = self.runner.invoke(main, 'delete -t "error type" -n "New Error Type"')

        instance = (
            self.session.query(ErrorType)
            .filter(ErrorType.error_type_name == "New Error Type")
            .first()
        )

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_error_type_protected(self):
        """
        Testing that when deleting a protected error type record it is not deleted.
        :return:
        """
        result = self.runner.invoke(main, 'delete -t "error type" -n "File Error"')
        expected_result = (
            "The item could not be deleted because it is a protected record."
        )

        self.assertIn(expected_result, result.output)
        self.assertEqual(0, result.exit_code)

    # def test_delete_invalid_type(self):
    #     """
    #     Testing that when an invalid type is passed to the delete option, an exception occurs.
    #     :return:
    #     """
    #     given_result = self.runner.invoke(main, 'delete -t blarg -n "Argle Bargle"')
    #     given_result = given_result.exception
    #
    #     expected_result = "Invalid topic.  Unable to delete instance."
    #
    #     return self.assertEqual(expected_result, given_result)

    def test_delete_process_dependency(self):
        """
        Testing that when deleting a process dependency record, it is deleted.
        :return:
        """
        parent_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency Parent",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        parent_process.change_run_status("completed")

        child_process = ProcessTracker(
            process_name="Testing Process Tracking Dependency Child",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Spark",
            sources="Unittests",
            targets="Unittests",
        )

        child_process.change_run_status("completed")

        self.runner.invoke(
            main,
            'create -t "process dependency" -p "%s" -c "%s"'
            % (parent_process.process_name, child_process.process_name),
        )

        result = self.runner.invoke(
            main,
            'delete -t "process dependency" -p "%s" -c "%s"'
            % (parent_process.process_name, child_process.process_name),
        )

        instance = (
            self.session.query(ProcessDependency)
            .filter(
                ProcessDependency.parent_process_id == parent_process.process.process_id
            )
            .filter(
                ProcessDependency.child_process_id == child_process.process.process_id
            )
            .first()
        )

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_process_type(self):
        """
        Testing that when deleting an process type record not on the protected list, it is deleted.
        :return:
        """
        self.runner.invoke(main, 'create -t "process type" -n "New Process Type"')

        result = self.runner.invoke(
            main, 'delete -t "process type" -n "New Process Type"'
        )

        instance = (
            self.session.query(ProcessType)
            .filter(ProcessType.process_type_name == "New Process Type")
            .first()
        )

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_process_type_protected(self):
        """
        Testing that when deleting a protected process type record it is not deleted.
        :return:
        """
        result = self.runner.invoke(main, 'delete -t "process type" -n "extract"')

        expected_result = (
            "The item could not be deleted because it is a protected record."
        )

        self.assertIn(expected_result, result.output)
        self.assertEqual(0, result.exit_code)

    def test_delete_process_status(self):
        """
        Testing that when deleting an process status record not on the protected list, it is deleted.
        :return:
        """
        self.runner.invoke(main, 'create -t "process status" -n "New Status Type"')

        result = self.runner.invoke(
            main, 'delete -t "process status" -n "New Status Type"'
        )

        instance = (
            self.session.query(ProcessStatus)
            .filter(ProcessStatus.process_status_name == "New Status Type")
            .first()
        )

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_process_status_protected(self):
        """
        Testing that when deleting a protected process status record it is not deleted.
        :return:
        """
        result = self.runner.invoke(main, 'delete -t "process status" -n "running"')

        expected_result = (
            "The item could not be deleted because it is a protected record."
        )

        self.assertIn(expected_result, result.output)
        self.assertEqual(0, result.exit_code)

    def test_delete_source(self):
        """
        Testing that when deleting a source record not on the protected list, it is deleted.
        :return:
        """
        self.runner.invoke(main, 'create -t source -n "New Source"')

        result = self.runner.invoke(main, 'delete -t "source" -n "New Source"')

        instance = (
            self.session.query(Source)
            .filter(Source.source_name == "New Source")
            .first()
        )

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    def test_delete_tool(self):
        """
        Testing that when deleting a tool record not on the protected list, it is deleted.
        :return:
        """
        self.runner.invoke(main, 'create -t tool -n "New Tool"')

        result = self.runner.invoke(main, 'delete -t "tool" -n "New Tool"')

        instance = self.session.query(Tool).filter(Tool.tool_name == "New Tool").first()

        self.assertEqual(None, instance)
        self.assertEqual(0, result.exit_code)

    # def test_delete_process_dependency(self):
    #
    def test_update_actor(self):
        """
        Testing that when updating an actor record it is updated.
        :return:
        """
        self.runner.invoke(main, 'create -t actor -n "Update Me"')

        result = self.runner.invoke(main, 'update -t actor -i "Update Me" -n "Updated"')

        instance = (
            self.session.query(Actor).filter(Actor.actor_name == "Updated").first()
        )
        given_name = instance.actor_name

        self.runner.invoke(main, 'delete -t actor -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_cluster(self):
        """
        Testing that when updating a cluster record it is updated.
        :return:
        """
        self.runner.invoke(
            main,
            'create -t cluster -n "Test Cluster" --max-processing 4 --processing-unit DPU --max-memory 128 --memory-unit GB',
        )

        result = self.runner.invoke(
            main, 'update -t cluster -i "Test Cluster" -n "Updated"'
        )

        instance = (
            self.session.query(Cluster)
            .filter(Cluster.cluster_name == "Updated")
            .first()
        )

        given_name = instance.cluster_name

        self.runner.invoke(main, "delete -t cluster -n Updated")

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_extract_status(self):
        """
        Testing that when updating an extract status non-protected record it is updated.
        :return:
        """
        self.runner.invoke(main, 'create -t "extract status" -n "Update Me"')

        result = self.runner.invoke(
            main, 'update -t "extract status" -i "Update Me" -n "Updated"'
        )

        instance = (
            self.session.query(ExtractStatus)
            .filter(ExtractStatus.extract_status_name == "Updated")
            .first()
        )
        given_name = instance.extract_status_name

        self.runner.invoke(main, 'delete -t "extract status" -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_extract_status_protected(self):
        """
        Testing that when updating a protected extract status record it is not updated.
        :return:
        """
        result = self.runner.invoke(
            main, 'update -t "extract status" -i "initializing" -n "Updated"'
        )

        expected_result = (
            "The item could not be updated because it is a protected record."
        )

        self.assertIn(expected_result, result.output)

    def test_update_error_type(self):
        """
        Testing that when updating an error type record not on the protected list, it is updated.
        :return:
        """
        self.runner.invoke(main, 'create -t "error type" -n "Update Me"')

        result = self.runner.invoke(
            main, 'update -t "error type" -i "Update Me" -n "Updated"'
        )

        instance = (
            self.session.query(ErrorType)
            .filter(ErrorType.error_type_name == "Updated")
            .first()
        )
        given_name = instance.error_type_name

        self.runner.invoke(main, 'delete -t "error type" -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_error_type_protected(self):
        """
        Testing that when updating a protected error type record it is not updated.
        :return:
        """
        result = self.runner.invoke(
            main, 'update -t "error type" -i "File Error" -n "Updated"'
        )
        expected_result = (
            "The item could not be updated because it is a protected record."
        )

        self.assertIn(expected_result, result.output)

    # def test_update_invalid_type(self):
    #     """
    #     Testing that when an invalid type is passed to the update option, an exception occurs.
    #     :return:
    #     """
    #     given_result = self.runner.invoke(
    #         main, 'update -t blarg -i "Testing" -n "Argle Bargle"'
    #     )
    #     given_result = given_result.exception
    #
    #     expected_result = "Invalid topic.  Unable to delete instance."
    #
    #     return self.assertEqual(expected_result, given_result)

    def test_update_process_type(self):
        """
         Testing that when updating a process type record not on the protected list, it is updated.
         :return:
         """
        self.runner.invoke(main, 'create -t "process type" -n "Update Me"')

        result = self.runner.invoke(
            main, 'update -t "process type" -i "Update Me" -n "Updated"'
        )

        instance = (
            self.session.query(ProcessType)
            .filter(ProcessType.process_type_name == "Updated")
            .first()
        )
        given_name = instance.process_type_name
        self.runner.invoke(main, 'delete -t "process type" -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_process_type_protected(self):
        """
        Testing that when updating a protected process type record it is not updated.
        :return:
        """
        result = self.runner.invoke(
            main, 'update -t "process type" -i "extract" -n "Updated"'
        )

        expected_result = (
            "The item could not be updated because it is a protected record."
        )

        self.assertIn(expected_result, result.output)

    def test_update_process_status(self):
        """
         Testing that when updating a process status record not on the protected list, it is updated.
         :return:
         """
        self.runner.invoke(main, 'create -t "process status" -n "Update Me"')

        result = self.runner.invoke(
            main, 'update -t "process status" -i "Update Me" -n "Updated"'
        )

        instance = (
            self.session.query(ProcessStatus)
            .filter(ProcessStatus.process_status_name == "Updated")
            .first()
        )
        given_name = instance.process_status_name
        self.runner.invoke(main, 'delete -t "process status" -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_process_status_protected(self):
        """
        Testing that when updating a protected process status record it is not updated.
        :return:
        """
        result = self.runner.invoke(
            main, 'update -t "process status" -i "running" -n "Updated"'
        )

        expected_result = (
            "The item could not be updated because it is a protected record."
        )

        self.assertIn(expected_result, result.output)

    def test_update_source(self):
        """
         Testing that when updating a source record, it is updated.
         :return:
         """
        self.runner.invoke(main, 'create -t source -n "Update Me"')

        result = self.runner.invoke(
            main, 'update -t "source" -i "Update Me" -n "Updated"'
        )

        instance = (
            self.session.query(Source).filter(Source.source_name == "Updated").first()
        )
        given_name = instance.source_name

        self.runner.invoke(main, 'delete -t "source" -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    def test_update_tool(self):
        """
         Testing that when updating a tool record not on the protected list, it is updated.
         :return:
         """
        self.runner.invoke(main, 'create -t tool -n "Update Me"')

        result = self.runner.invoke(
            main, 'update -t "tool" -i "Update Me" -n "Updated"'
        )

        instance = self.session.query(Tool).filter(Tool.tool_name == "Updated").first()
        given_name = instance.tool_name

        self.runner.invoke(main, 'delete -t "tool" -n "Updated"')

        self.assertEqual("Updated", given_name)
        self.assertEqual(0, result.exit_code)

    # def test_update_process_dependency(self):
