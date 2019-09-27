import pytest


from process_tracker.models.extract import (
    Extract,
    ExtractDatasetType,
    ExtractProcess,
    ExtractStatus,
    Location,
)
from process_tracker.models.process import (
    ErrorType,
    ErrorTracking,
    Process,
    ProcessDatasetType,
    ProcessDependency,
    ProcessSource,
    ProcessSourceObject,
    ProcessTarget,
    ProcessTargetObject,
    ProcessTracking,
)
from process_tracker.models.source import (
    DatasetType,
    Source,
    SourceDatasetType,
    SourceObject,
    SourceObjectDatasetType,
)
from process_tracker.utilities.data_store import DataStore


@pytest.fixture(autouse=True, scope="module")
def setup_and_teardown():
    # This is purely for setup and teardown of the module

    data_store = DataStore()
    session = data_store.session

    yield

    session.query(Location).delete()
    session.query(ProcessDatasetType).delete()
    session.query(SourceDatasetType).delete()
    session.query(DatasetType).delete()
    session.query(ProcessSourceObject).delete()
    session.query(ProcessTargetObject).delete()
    session.query(ProcessSource).delete()
    session.query(ProcessTarget).delete()
    session.query(ProcessDependency).delete()
    session.query(ProcessTracking).delete()
    session.query(Process).delete()
    session.commit()
    session.close()
