# Process Tracking Framework
# Source class - methods to work with data integration sources within the process tracking framework


class Source:

    def __init__(self, name):
        """
        Initializing the process object with base elements
        """
        self.source_name = name

    def get_source_id(self):
        """
        Find the given Source's identifier.
        :return:
        """

        return True