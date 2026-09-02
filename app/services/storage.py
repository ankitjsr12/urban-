from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4
from app.core.config import settings

class StorageProvider(ABC):
    @abstractmethod
    async def put(self, data: bytes, content_type: str, filename: str) -> str: ...

class LocalStorage(StorageProvider):
    def __init__(self): self.root=Path('/tmp/urbansense-evidence'); self.root.mkdir(parents=True, exist_ok=True)
    async def put(self, data: bytes, content_type: str, filename: str) -> str:
        key=f'{uuid4()}-{Path(filename).name}'; (self.root/key).write_bytes(data); return f'file://{self.root/key}'

def get_storage() -> StorageProvider:
    # MinIO/S3 and Cloudinary adapters can be substituted here by STORAGE_PROVIDER.
    return LocalStorage()
