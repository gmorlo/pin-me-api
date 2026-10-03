from __future__ import annotations

import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import Settings
from app.models.image import ReferenceImage, SourceType
from app.storage.base import ResolvedContent


class LocalUploadSource:
    """S3-compatible bootstrap storage for LOCAL_UPLOAD images."""

    source_type = SourceType.LOCAL_UPLOAD.value

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def upload(
        self,
        *,
        board_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_") or "upload.bin"
        key = f"boards/{board_id}/{uuid.uuid4().hex}_{safe_name}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def resolve(self, image: ReferenceImage) -> ResolvedContent:
        if not image.storage_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image has no storage_key",
            )
        try:
            response = self._client.get_object(
                Bucket=self._bucket, Key=image.storage_key
            )
        except ClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image object not found in storage",
            ) from exc
        data = response["Body"].read()
        content_type = (
            image.content_type
            or response.get("ContentType")
            or "application/octet-stream"
        )
        return ResolvedContent(data=data, content_type=content_type)

    def delete(self, storage_key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=storage_key)
        except ClientError:
            # Best-effort: DB row removal should still proceed.
            pass
