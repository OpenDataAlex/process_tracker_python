
from datetime import datetime
import logging

from process_tracker import session
from process_tracker.data_store import DataStore
from models.actor import Actor
from models.process import Process, ProcessTracking, ProcessType, ProcessStatus
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

        self.actor = self.data_store.get_or_create(model=Actor, actor_name=actor_name)
        self.process_type = self.data_store.get_or_create(model=ProcessType, process_type_name=process_type)
        self.source = self.data_store.get_or_create(model=Source, source_name=source_name)
        self.tool = self.data_store.get_or_create(model=Tool, tool_name=tool_name)

        self.process = self.data_store.get_or_create(model=Process, process_name=process_name
                                                     , process_source_id=self.source.source_id
                                                     , process_type_id=self.process_type.process_type_id
                                                     , process_tool_id=self.tool.tool_id)

        self.process_status_running = session.query(ProcessStatus)\
            .filter(ProcessStatus.process_status_name == 'running').with_entities(ProcessStatus.process_status_id)
        self.process_status_complete = session.query(ProcessStatus)\
            .filter(ProcessStatus.process_status_name == 'complete').with_entities(ProcessStatus.process_status_id)
        self.process_status_failed = session.query(ProcessStatus)\
            .filter(ProcessStatus.process_status_name == 'failed').with_entities(ProcessStatus.process_status_id)

    def register_new_process_run(self):
        """
        When a new process instance is starting, register the run in process tracking.
        :return:
        """

        last_run = self.data_store.get_latest_tracking_record(process=self.process.process_id)

        new_run_flag = True
        new_run_id = 0

        if last_run:
            # Must validate that the process is not currently running.

            if last_run.process_status_id != self.process_status_running:
                new_run_flag = True
                new_run_id = last_run.process_run_id + 1
            else:
                new_run_flag = False

        if new_run_flag:
            new_run = ProcessTracking(process_id=self.process.process_id
                                      , process_status_id=self.process_status_running
                                      , process_run_id=new_run_id
                                      , process_run_start_date_time=datetime.now()
                                      , process_run_actor_id=self.actor.actor_id)

            session.add(new_run)
            session.commit()

            self.logging.info('Process tracking record added for %s' % new_run)