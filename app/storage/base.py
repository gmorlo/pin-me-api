from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models.image import ReferenceImage


@dataclass
class ResolvedContent:
    data: bytes
    content_type: str


class ImageSource(Protocol):
    """Adapter for resolving (and optionally uploading) image binaries.

    Practice/board services depend on this protocol — not on S3 directly —
    so Pinterest/Drive adapters can land later without rewriting domain logic.
    """

    source_type: str

    def resolve(self, image: ReferenceImage) -> ResolvedContent:
        """Return display bytes for an image row."""

    def upload(
        self,
        *,
        board_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> str:
        """Store bootstrap bytes; return storage_key. Not all sources support upload."""

    def delete(self, storage_key: str) -> None:
        """Best-effort delete of a bootstrap object."""
