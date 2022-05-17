import unittest
import uuid
from datetime import datetime

from app.models.letter import Letter


class LetterUnitTest(unittest.TestCase):

    def test_getters(self):
        tracking_number = str(uuid.uuid4())
        status = str(uuid.uuid4())
        final = True
        updated = datetime.now()
        letter = Letter(tracking_number=tracking_number, status=status, final=final, updated=updated)
        self.assertEqual(letter.get_status_text(), status)
        self.assertTrue(letter.is_final())
        self.assertEqual(letter.get_last_update_timestamp(), updated)

    def test_make_final(self):
        letter = Letter()
        self.assertFalse(letter.is_final())
        letter.make_final()
        self.assertTrue(letter.is_final())


if __name__ == '__main__':
    unittest.main()
