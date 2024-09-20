import unittest

from fastapi.testclient import TestClient
from init import app


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Run the TestClient context to initialize the lifespan
        with cls.client as client:
            pass

    def test_search(self):
        response = self.client.get("/search", params={"query": "Computer Vision"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print(data)
        self.assertTrue("results" in data)

    def test_embedding(self):
        response = self.client.get("/embedding", params={"query": "Computer Vision"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print(data)
        self.assertTrue("embedding" in data)


if __name__ == "__main__":
    unittest.main()
