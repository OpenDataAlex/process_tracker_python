# Process Tracking Framework
# Tool class - methods to work with various Data Integration tools within the process tracking framework


class Tool():

    def __init__(self, name):
        self.name = name

    def get_tool_id(self):
        """
        Get the identifier for Tool if it exists in the data source.
        Otherwise, register the new Tool and return the new identifier.
        :return:
        """

        return True