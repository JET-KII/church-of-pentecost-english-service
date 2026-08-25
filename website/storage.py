from io import BytesIO
from urllib.request import urlopen

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from vercel.blob import BlobClient


@deconstructible
class VercelBlobStorage(Storage):
    """Store user-uploaded media in the project's public Vercel Blob store."""

    def __init__(self):
        self.client = BlobClient()

    def _open(self, name, mode="rb"):
        if mode not in {"r", "rb"}:
            raise ValueError("Vercel Blob files can only be opened for reading")
        with urlopen(self.url(name), timeout=10) as response:
            return File(BytesIO(response.read()), name=name)

    def _save(self, name, content):
        content.open("rb")
        blob = self.client.put(
            name,
            content.read(),
            access="public",
            content_type=getattr(content, "content_type", None),
            add_random_suffix=True,
        )
        return blob.url

    def delete(self, name):
        self.client.delete(name)

    def exists(self, name):
        return False

    def url(self, name):
        if name.startswith(("https://", "http://")):
            return name
        return f"{settings.MEDIA_URL.rstrip('/')}/{name.lstrip('/')}"

