from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from .storage import VercelBlobStorage


class VercelBlobStorageTests(SimpleTestCase):
    @patch("website.storage.BlobClient")
    def test_save_returns_public_blob_url(self, blob_client_class):
        client = blob_client_class.return_value
        client.put.return_value = SimpleNamespace(
            url="https://example.public.blob.vercel-storage.com/member/photo-abc.jpg"
        )
        storage = VercelBlobStorage()
        upload = SimpleUploadedFile("photo.jpg", b"image-bytes", content_type="image/jpeg")

        saved_name = storage.save("member/photo.jpg", upload)

        self.assertEqual(saved_name, client.put.return_value.url)
        client.put.assert_called_once_with(
            "member/photo.jpg",
            b"image-bytes",
            access="public",
            content_type="image/jpeg",
            add_random_suffix=True,
        )
        self.assertEqual(storage.url(saved_name), saved_name)

    @patch("website.storage.BlobClient")
    def test_delete_uses_saved_blob_url(self, blob_client_class):
        client = blob_client_class.return_value
        storage = VercelBlobStorage()
        blob_url = "https://example.public.blob.vercel-storage.com/member/photo-abc.jpg"

        storage.delete(blob_url)

        client.delete.assert_called_once_with(blob_url)

