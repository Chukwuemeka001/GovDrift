import os
import tempfile
import unittest

import store

SAMPLE = {
    "name": "Test Patient A",
    "phone": "519-555-0101",
    "email": "patient.a@test.example",
    "service": "physio_initial",
    "preferred_date": "2030-01-15",
    "preferred_time": "morning",
    "reason": "Sore shoulder",
    "conditions": "None",
    "medications": "None",
    "consent": "yes",
}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")
        store.init(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_creates_empty_table(self):
        self.assertTrue(os.path.exists(self.db))
        self.assertEqual(store.list_requests(), [])

    def test_add_request_returns_id(self):
        new_id = store.add_request(SAMPLE)
        self.assertIsInstance(new_id, int)
        self.assertGreater(new_id, 0)

    def test_list_requests_oldest_first(self):
        first = store.add_request(SAMPLE)
        second = store.add_request(dict(SAMPLE, name="Test Patient B"))
        self.assertEqual([r["id"] for r in store.list_requests()], [first, second])

    def test_get_request(self):
        new_id = store.add_request(SAMPLE)
        row = store.get_request(new_id)
        self.assertEqual(row["name"], "Test Patient A")
        self.assertEqual(row["consent"], 1)
        self.assertIsNone(store.get_request(new_id + 100))


if __name__ == "__main__":
    unittest.main()
