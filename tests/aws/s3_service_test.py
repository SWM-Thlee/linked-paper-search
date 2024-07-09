import os
import sys
import unittest

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from services.storage.s3_service import S3Service


class TestS3Service(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "paper-feed"
        self.s3_service = S3Service(bucket_name=self.bucket_name)
        # Ensure the test.txt and example.txt files exist for the test.
        self.s3_service.put_object("test.txt", "This is a test file.")

    def test_get_object(self):
        # Verify uploading an object to S3 by fetching what was just uploaded.
        content = self.s3_service.get_object("test.txt")
        self.assertEqual(content, "This is a test file.")


if __name__ == "__main__":
    unittest.main()
