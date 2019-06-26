"""
Space for generalized helpers that can be utilized across the entire framework.
"""
import base64
import logging

from process_tracker.utilities.settings import SettingsManager

key = "ZE77KfeJ1P9gHfgVzsZIaafzoZXEuwKI7wDe4c1F8AY="

log_level = SettingsManager().determine_log_level()

logger = logging.getLogger(__name__)
logger.setLevel(log_level)


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


def encrypt_password(password):
    """
    Helper function for encrypting passwords (specifically for data store connections).
    :param password:
    :return:
    """
    encoded_chars = []

    for i in range(len(password)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(password[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)

    encoded_password = "".join(encoded_chars).encode()
    encrypted_password = base64.urlsafe_b64encode(encoded_password).decode()

    return "Encrypted %s" % encrypted_password


def decrypt_password(password):
    """
    Helper function for decrypting passwords (specifically for data store connections).
    :param password:
    :return:
    """

    password = password.replace("Encrypted ", "")

    decode = []
    encode = base64.urlsafe_b64decode(password).decode()
    for i in range(len(encode)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(encode[i]) - ord(key_c)) % 256)
        decode.append(dec_c)

    decrypted_password = "".join(decode)

    return decrypted_password
