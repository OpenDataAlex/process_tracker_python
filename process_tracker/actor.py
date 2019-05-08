# Process Tracking Framework
# Actor class - methods to work with data integration actors within the process tracking framework


class Actor:

    def __init__(self, name):
        """
        Initializing the process object with base elements
        """
        self.actor_name = name

    def get_actor_id(self):
        """
        Find the given Actor's identifier.
        :return:
        """

        return True