
from actor import Actor
from process import Process
from source import Source
from tool import Tool


class ProcessTracker:

    def __init__(self, process_name, actor_name, tool_name, source_name):

        self.actor = Actor(name=actor_name).get_actor_id()
        self.process = Process(name=process_name).get_process_id()
        self.source = Source(name=source_name).get_source_id()
        self.tool = Tool(name=tool_name).get_tool_id()

    def register_new_process_run(self):
        """

        :return:
        """