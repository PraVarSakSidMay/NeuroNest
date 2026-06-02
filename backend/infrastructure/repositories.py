"""Repository interface protocols for persistence abstraction."""
from typing import Protocol, Optional, List
from datetime import datetime
from domain.entities import Interaction, Session, User
from domain.value_objects import Emotion, AudioFeatures


class IInteractionRepository(Protocol):
    """Repository for interaction persistence."""
    
    async def create(self, interaction: Interaction) -> Optional[str]:
        """Create an interaction and return its ID."""
        ...
    
    async def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Retrieve an interaction by ID."""
        ...
    
    async def get_by_session(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[Interaction]:
        """Get interactions for a session with pagination."""
        ...
    
    async def update_emotion(self, interaction_id: str, emotion: Emotion) -> bool:
        """Update emotion data for an interaction."""
        ...
    
    async def update_embedding(self, interaction_id: str, embedding: List[float]) -> bool:
        """Store embedding vector for an interaction."""
        ...
    
    async def submit_feedback(
        self, interaction_id: str, score: float, text: Optional[str] = None
    ) -> bool:
        """Submit feedback for an interaction (Reward Signal for RL)."""
        ...

    async def get_persona_performance(self) -> dict:
        """Get performance statistics for different personas."""
        ...
    
    async def get_successful_interactions(self, limit: int = 5) -> List[Interaction]:
        """Fetch highly-rated interactions for training context."""
        ...
    
    async def upload_file(self, bucket: str, path: str, file_data: bytes) -> Optional[str]:
        """Upload file to storage and return URL."""
        ...


class ISessionRepository(Protocol):
    """Repository for session management."""
    
    async def create(self, user_id: str) -> Optional[Session]:
        """Create a new session for a user."""
        ...
    
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        ...
    
    async def get_last_by_user(self, user_id: str) -> Optional[Session]:
        """Get the most recent session for a user."""
        ...
    
    async def end(self, session_id: str) -> bool:
        """Mark a session as ended."""
        ...


class IUserRepository(Protocol):
    """Repository for user management."""
    
    async def create(self, full_name: Optional[str] = None) -> str:
        """Create a user and return the ID."""
        ...
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        ...
    
    async def get_default_user(self) -> str:
        """Get the default system user ID."""
        ...


class IEmbeddingRepository(Protocol):
    """Repository for embedding operations."""
    
    async def find_similar(
        self,
        user_id: str,
        query_embedding: List[float],
        k: int = 5,
        exclude_session: Optional[str] = None,
    ) -> List[dict]:
        """Find similar interactions by embedding vector."""
        ...
    
    async def store(self, interaction_id: str, embedding: List[float]) -> bool:
        """Store an embedding for an interaction."""
        ...