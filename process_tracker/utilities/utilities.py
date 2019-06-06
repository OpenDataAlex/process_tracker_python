"""
Space for generalized helpers that can be utilized across the entire framework.
"""
import logging

from process_tracker.utilities.settings import SettingsManager

config = SettingsManager().config

logger = logging.getLogger(__name__)
logger.setLevel(config["DEFAULT"]["log_level"])


def determine_low_high_date(date, previous_date, date_type):
    """
    For the given dates and date type, determine if the date replaces the previous date or not.
    :param date: The new datetime.
    :type date: Datetime/timestamp
    :param previous_date: The previous datetime that date is being compared to.
    :type previous_date: Datetime/timestamp
    :param date_type: Is the comparison for a low date or high date?  Valid values:  low, high
    :type date_type: str
    :return: Boolean if date replaces previous_date
    """

    if date_type == "low":

        if date is not None and (previous_date is None or date < previous_date):
            return True
        else:
            return False

    elif date_type == "high":

        if date is not None and (previous_date is None or previous_date > date):
            return True
        else:
            return False

    else:
        logger.error("%s is not a valid date_type." % date_type)
        raise Exception("%s is not a valid date_type." % date_type)


def timestamp_converter(data_store_type, timestamp):
    """
    Helper function for when testing with data stores that have funky formats for stock dates with SQLAlchemy.
    :param data_store_type: The type of data store
    :param timestamp: The timestamp to be created.
    :return:
    """

    if data_store_type == "mysql":
        timestamp = timestamp.replace(microsecond=0)
    else:
        timestamp = timestamp

    return timestamp
