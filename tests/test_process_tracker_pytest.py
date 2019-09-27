import pytest

from process_tracker.extract_tracker import ExtractTracker
from process_tracker.process_tracker import ProcessTracker
from process_tracker.utilities import utilities

from process_tracker.models.extract import Extract, ExtractDatasetType, ExtractProcess
from process_tracker.models.source import SourceDatasetType, SourceObjectDatasetType
from process_tracker.models.process import ErrorTracking, ErrorType, ProcessDatasetType


class TestProcessTracker:
    @pytest.fixture(scope="function")
    def create_example_process_run(self, setup_and_teardown):
        self.process_tracker = ProcessTracker(
            process_name="Testing Process Tracking Initialization",
            process_type="Extract",
            actor_name="UnitTesting",
            tool_name="Unittests",
            sources="Unittests",
            targets="Unittests",
            dataset_types="Category 1",
        )

        yield

        session.query(ExtractProcess).delete()
        session.query(ExtractDatasetType).delete()
        session.query(SourceDatasetType).delete()
        session.query(SourceObjectDatasetType).delete()
        session.query(ProcessDatasetType).delete()
        session.query(Extract).delete()
        session.query(ErrorType).delete()
        session.commit()

    def test_change_status_invalid_type(self, create_example_process_run):
        with pytest.raises(Exception) as context:
            self.process_tracker.change_run_status(new_status="blarg")

        assert "The provided status type blarg is invalid." in str(context.exception)
