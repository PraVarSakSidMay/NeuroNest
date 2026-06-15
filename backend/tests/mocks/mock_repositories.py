"""Mock repositories for testing without database."""
from typing import Optional, List
from uuid import uuid4
from domain.entities import Interaction, Session, User
from domain.value_objects import Emotion, AudioFeatures


class MockInteractionRepository:
    """In-memory mock interaction repository."""
    
    def __init__(self):
        self._interactions: dict[str, Interaction] = {}
    
    async def create(self, interaction: Interaction) -> Optional[str]:
        interaction_id = str(uuid4())
        interaction.id = interaction_id
        self._interactions[interaction_id] = interaction
        return interaction_id
    
    async def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        return self._interactions.get(interaction_id)
    
    async def get_by_session(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[Interaction]:
        results = [
            i for i in self._interactions.values()
            if i.session_id == session_id
        ]
        return results[offset:offset + limit]
    
    async def update_emotion(self, interaction_id: str, emotion: Emotion) -> bool:
        if interaction_id in self._interactions:
            self._interactions[interaction_id].emotion_data = emotion
            return True
        return False
    
    async def update_embedding(self, interaction_id: str, embedding: List[float]) -> bool:
        if interaction_id in self._interactions:
            return True
        return False
    
    async def upload_file(self, bucket: str, path: str, file_data: bytes) -> Optional[str]:
        return f"https://mock.storage/{bucket}/{path}"

    async def get_successful_interactions(self, limit: int = 5) -> List[Interaction]:
        return []


class MockSessionRepository:
    """In-memory mock session repository."""
    
    def __init__(self):
        self._sessions: dict[str, Session] = {}
    
    async def create(self, user_id: str) -> Optional[Session]:
        session = Session.create(user_id=user_id)
        self._sessions[session.id] = session
        return session
    
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)
    
    async def get_last_by_user(self, user_id: str) -> Optional[Session]:
        sessions = [s for s in self._sessions.values() if s.user_id == user_id]
        return sessions[-1] if sessions else None
    
    async def end(self, session_id: str) -> bool:
        if session_id in self._sessions:
            self._sessions[session_id].ended_at = "now"
            return True
        return False


class MockUserRepository:
    """In-memory mock user repository."""
    
    def __init__(self):
        self._default_user_id = "test-user-id"
    
    async def create(self, full_name: Optional[str] = None) -> str:
        return self._default_user_id
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        return User.create(user_id=user_id, full_name="Test User")
    
    async def get_default_user(self) -> str:
        return self._default_user_id


class MockEmbeddingRepository:
    """In-memory mock embedding repository."""
    
    async def find_similar(
        self,
        user_id: str,
        query_embedding: List[float],
        k: int = 5,
        exclude_session: Optional[str] = None,
    ) -> List[dict]:
        return [
            {
                "transcript": "test memory",
                "emotion": "happy",
                "stress_level": 30,
                "tone": "calm",
                "hidden_emotion": "",
                "response_text": "test response",
                "created_at": "2024-01-01T00:00:00Z",
                "similarity": 0.8,
            }
        ]
    
    async def store(self, interaction_id: str, embedding: List[float]) -> bool:
        return True