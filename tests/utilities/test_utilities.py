from datetime import datetime, timedelta
import unittest

from process_tracker.utilities.data_store import DataStore
from process_tracker.utilities import utilities


class TestUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data_store = DataStore()
        cls.data_store_type = data_store.data_store_type

    def test_determine_low_high_date_invalid_date_type(self):
        """
        Testing that determine_low_high_date() does not accept invalid date_types
        :return:
        """
        low_date = utilities.timestamp_converter(
            data_store_type=self.data_store_type, timestamp=datetime.now()
        )

        lower_low_date = low_date + timedelta(hours=1)

        with self.assertRaises(Exception) as context:
            utilities.determine_low_high_date(
                date=lower_low_date, previous_date=low_date, date_type="blarg"
            )

        return self.assertTrue(
            "blarg is not a valid date_type." in str(context.exception)
        )

    def test_timestamp_converter_mysql(self):
        """
        Testing that microseconds are removed off of timestamps if data_store_type = mysql.
        :return:
        """

        date = datetime.now()

        expected_result = date.replace(microsecond=0)

        given_result = utilities.timestamp_converter(
            data_store_type="mysql", timestamp=date
        )

        self.assertEqual(expected_result, given_result)

    def test_encrypt_password(self):
        """
        Given a password, it's hash will be returned.
        :return:
        """
        expected_result = "Encrypted wqfCvsKKwpzCrsOYw4rCvsKBwrHCrMOawr_DlcOZwro="
        given_result = utilities.encrypt_password("MySecretPassword")

        self.assertEqual(expected_result, given_result)

    def test_decrypt_password(self):
        """
        Given an encrypted password, return it's plaintext.
        :return:
        """
        expected_result = "MySecretPassword"
        given_result = utilities.decrypt_password(
            password="Encrypted wqfCvsKKwpzCrsOYw4rCvsKBwrHCrMOawr_DlcOZwro="
        )

        self.assertEqual(expected_result, given_result)
