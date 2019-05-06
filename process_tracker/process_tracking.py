
from datetime import datetime
import logging

from process_tracker import session
from process_tracker.data_store import DataStore
from models.actor import Actor
from models.process import Process, ProcessTracking, ProcessType
from models.source import Source
from models.tool import Tool


class ProcessTracker:

    def __init__(self, process_name, process_type, actor_name, tool_name, source_name):
        """
        ProcessTracker is the primary enginer for tracking data integration processes.
        :param process_name: Name of the process being tracked.
        :param actor_name: Name of the person or environment runnning the process.
        :param tool_name: Name of the tool used to run the process.
        :param source_name: Name of the source that the data is coming from.
        """

        self.logging = logging.getLogger(__name__)

        self.data_store = DataStore()

        actor_uuid = self.data_store.generate_universally_unique_identifier(actor_name=actor_name)
        print("Actor UUID is: %s" % actor_uuid)

        self.actor = self.data_store.get_or_create(model=Actor, actor_uuid=actor_uuid, actor_name=actor_name)
        self.process_type = self.data_store.get_or_create(model=ProcessType, process_type_name=process_type)
        self.source = self.data_store.get_or_create(model=Source, source_name=source_name)
        self.tool = self.data_store.get_or_create(model=Tool, tool_name=tool_name)

        self.process = self.data_store.get_or_create(model=Process, process_name=process_name
                                                     , process_source_id=self.source
                                                     , process_type_id=self.process_type
                                                     , process_tool_id=self.tool)

        self.process_status_running = 1
        self.process_status_complete = 2
        self.process_status_failed = 3

    def register_new_process_run(self):
        """
        When a new process instance is starting, register the run in process tracking.
        :return:
        """

        last_run = self.data_store.get_latest_tracking_record(model=ProcessTracking, process=self.process)

        # Must validate that the process is not currently running.

        if last_run.process_status != self.process_status_running:

            ProcessTracking(process_uuid=self.process
                            , process_status=self.process_status_running
                            , process_run_id=last_run.process_run_id + 1
                            , process_run_start_date_time=datetime.now()
                            , process_run_actor_uuid=self.actor)

            session.add(ProcessTracking)
            session.commit()

            self.logging.info('Process tracking record added for %s' % ProcessTracking)

