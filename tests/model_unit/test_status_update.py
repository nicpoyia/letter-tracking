import unittest
import uuid
from datetime import datetime

from app.models.status_update import StatusUpdate


class StatusUpdateUnitTest(unittest.TestCase):

    def test_getters(self):
        letter_id = str(uuid.uuid4())
        status = str(uuid.uuid4())
        timestamp_tracked = datetime.now()
        status_update = StatusUpdate(letter_id=letter_id, status=status, timestamp_tracked=timestamp_tracked)
        self.assertTrue(status_update.get_letter_id(), letter_id)
        self.assertEqual(status_update.get_status_text(), status)
        self.assertEqual(status_update.get_tracking_timestamp(), timestamp_tracked)


if __name__ == '__main__':
    unittest.main()
