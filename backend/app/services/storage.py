import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4
import hashlib
from app.core.config import settings


class StorageProvider(ABC):
    @abstractmethod
    async def put(self, data: bytes, content_type: str, filename: str) -> tuple[str, str | None]:
        """Uploads data and returns (public_or_endpoint_url, object_key)."""
        ...

    @abstractmethod
    async def get(self, object_key: str) -> bytes | None:
        """Retrieves object data given the storage object key."""
        ...


class LocalStorage(StorageProvider):
    def __init__(self, base_dir: str = '/tmp/urbansense-evidence'):
        self.root = Path(base_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    async def put(self, data: bytes, content_type: str, filename: str) -> tuple[str, str | None]:
        safe_filename = Path(filename).name if filename else 'evidence.bin'
        key = f'{uuid4()}-{safe_filename}'
        file_path = self.root / key
        file_path.write_bytes(data)
        return f'file://{file_path.resolve()}', key

    async def get(self, object_key: str) -> bytes | None:
        file_path = self.root / object_key
        if file_path.is_file():
            return file_path.read_bytes()
        return None


class S3Storage(StorageProvider):
    def __init__(self):
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except Exception:
                pass

    async def put(self, data: bytes, content_type: str, filename: str) -> tuple[str, str | None]:
        safe_filename = Path(filename).name if filename else 'evidence.bin'
        key = f'evidence/{uuid4()}/{safe_filename}'
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        endpoint = settings.s3_endpoint.rstrip('/')
        url = f'{endpoint}/{self.bucket}/{key}'
        return url, key

    async def get(self, object_key: str) -> bytes | None:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response['Body'].read()
        except ClientError:
            return None


def get_storage() -> StorageProvider:
    if settings.storage_provider in ('minio', 's3', 'aws_s3'):
        try:
            return S3Storage()
        except Exception:
            return LocalStorage()
    return LocalStorage()
