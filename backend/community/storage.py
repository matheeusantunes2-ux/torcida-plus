import os
from pathlib import Path

import cloudinary
import cloudinary.api
import cloudinary.uploader
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryImageStorage(Storage):
    resource_type = "image"

    def _configured(self):
        return bool(os.getenv("CLOUDINARY_URL") or (
            os.getenv("CLOUDINARY_CLOUD_NAME")
            and os.getenv("CLOUDINARY_API_KEY")
            and os.getenv("CLOUDINARY_API_SECRET")
        ))

    def _fallback(self):
        return FileSystemStorage()

    def _public_id(self, name):
        path = Path(name).as_posix().lstrip("/")
        return str(Path(path).with_suffix("")) if self.resource_type == "image" else path

    def _save(self, name, content):
        if not self._configured():
            return self._fallback().save(name, content)
        if hasattr(content, "seek"):
            content.seek(0)
        result = cloudinary.uploader.upload(
            content,
            public_id=self._public_id(name),
            resource_type=self.resource_type,
            overwrite=False,
            unique_filename=False,
            use_filename=False,
            invalidate=True,
        )
        public_id = result["public_id"]
        if self.resource_type == "image":
            extension = result.get("format") or Path(name).suffix.lstrip(".")
            return f"{public_id}.{extension}" if extension else public_id
        return public_id

    def _open(self, name, mode="rb"):
        if not self._configured():
            return self._fallback().open(name, mode)
        response = requests.get(self.url(name), timeout=30)
        response.raise_for_status()
        return ContentFile(response.content, name=Path(name).name)

    def delete(self, name):
        if not self._configured():
            return self._fallback().delete(name)
        cloudinary.uploader.destroy(self._public_id(name), resource_type=self.resource_type, invalidate=True)

    def exists(self, name):
        if not self._configured():
            return self._fallback().exists(name)
        try:
            cloudinary.api.resource(self._public_id(name), resource_type=self.resource_type)
            return True
        except Exception:
            return False

    def size(self, name):
        if not self._configured():
            return self._fallback().size(name)
        result = cloudinary.api.resource(self._public_id(name), resource_type=self.resource_type)
        return int(result.get("bytes", 0))

    def url(self, name):
        if not self._configured():
            return self._fallback().url(name)
        options = {"resource_type": self.resource_type, "secure": True}
        if self.resource_type == "image" and Path(name).suffix:
            options["format"] = Path(name).suffix.lstrip(".")
        return cloudinary.utils.cloudinary_url(self._public_id(name), **options)[0]


@deconstructible
class CloudinaryRawStorage(CloudinaryImageStorage):
    resource_type = "raw"
