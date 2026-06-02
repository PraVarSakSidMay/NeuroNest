"""DTOs for voice processing use case."""
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import UploadFile


class VoiceRequestDTO(BaseModel):
    """Validated request DTO for voice processing."""
    file: UploadFile
    audio_analysis: Optional[str] = None
    voice_name: str = Field(default="Rachel", min_length=1, max_length=50)
    
    @property
    def filename(self) -> str:
        return self.file.filename or "unnamed.webm"
    
    @property
    def content_type(self) -> Optional[str]:
        return self.file.content_type
    
    def validate_file(self) -> bool:
        if not self.file:
            return False
        if self.content_type and not any(
            ct in (self.content_type or "")
            for ct in ["audio/", "video/", "application/octet-stream"]
        ):
            return False
        return True