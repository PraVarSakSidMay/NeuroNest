
from typing import Optional, List
from datetime import datetime, timezone
from domain.entities import UserState
from domain.value_objects import Emotion, Goal, Project, InteractionStyle, EmotionEnum
from infrastructure.repositories import IUserStateRepository
from core.logger import logger

class UserStateService:
    """
    Application service for managing persistent user state.
    Coordinates state updates, emotional signal merging, and goal tracking.
    """
    
    def __init__(self, user_state_repo: IUserStateRepository):
        self.user_state_repo = user_state_repo

    async def get_state(self, user_id: str) -> UserState:
        """Retrieve the current state for a user, creating a default one if none exists."""
        state = await self.user_state_repo.get_by_user_id(user_id)
        if not state:
            logger.info(f"Initializing new user state for {user_id}")
            state = UserState.create(user_id)
            await self.user_state_repo.update(user_id, state)
        return state

    async def update_state(self, user_id: str, emotion_data: Emotion, transcript: str) -> UserState:
        """
        Update the user state based on the latest interaction.
        Merges emotional signals and updates recent topics.
        """
        state = await self.get_state(user_id)
        
        # 1. Update emotional metrics
        state = self.merge_emotional_signals(state, emotion_data)
        
        # 2. Update recent topics (simple extraction for now)
        # In a real production app, this would use an LLM or NLP service
        words = transcript.lower().split()
        important_words = [w for w in words if len(w) > 4][:5]
        for word in important_words:
            if word not in state.recent_topics:
                state.recent_topics.insert(0, word)
        state.recent_topics = state.recent_topics[:10]  # Keep last 10
        
        state.last_updated = datetime.now(timezone.utc)
        await self.user_state_repo.update(user_id, state)
        return state

    def merge_emotional_signals(self, state: UserState, emotion_data: Emotion) -> UserState:
        """
        Merges new emotional data into the persistent state.
        Uses a decaying average for levels and a frequency-based approach for dominant emotion.
        """
        # Update current emotion
        state.current_emotion = emotion_data.emotion
        
        # Decaying average for stress level (weighted towards new data)
        alpha = 0.3
        state.stress_level = int((1 - alpha) * state.stress_level + alpha * emotion_data.stress_level)
        
        # Update confidence and engagement (simulated logic based on gaze and tone)
        if emotion_data.eye_contact_ratio is not None:
            state.engagement_level = int(emotion_data.eye_contact_ratio * 100)
        
        # If user is frustrated or angry, confidence might be lower
        if emotion_data.emotion in [EmotionEnum.ANGRY, EmotionEnum.FRUSTRATED]:
            state.confidence_level = max(0, state.confidence_level - 10)
        elif emotion_data.emotion == EmotionEnum.EXCITED:
            state.confidence_level = min(100, state.confidence_level + 5)
            
        # Update dominant emotion (simple heuristic: if current persists, it becomes dominant)
        # In production, this would track emotion frequency over a window
        if state.current_emotion == state.dominant_emotion:
            pass # Already dominant
        else:
            # For now, just set it directly if stress is high
            if state.stress_level > 70:
                state.dominant_emotion = state.current_emotion
                
        return state

    async def update_goal_progress(self, user_id: str, goal_id: str, progress_increment: int) -> UserState:
        """Update progress for a specific user goal."""
        state = await self.get_state(user_id)
        for goal in state.current_goals:
            if goal.id == goal_id:
                goal.progress = min(100, goal.progress + progress_increment)
                if goal.progress >= 100:
                    goal.is_completed = True
                break
        
        state.last_updated = datetime.now(timezone.utc)
        await self.user_state_repo.update(user_id, state)
        return state

    async def add_goal(self, user_id: str, description: str) -> UserState:
        """Add a new goal to the user's state."""
        state = await self.get_state(user_id)
        new_goal = Goal(description=description)
        state.current_goals.append(new_goal)
        await self.user_state_repo.update(user_id, state)
        return state

    async def add_project(self, user_id: str, name: str) -> UserState:
        """Add a new active project to the user's state."""
        state = await self.get_state(user_id)
        new_project = Project(name=name)
        state.active_projects.append(new_project)
        await self.user_state_repo.update(user_id, state)
        return state

    async def set_interaction_style(self, user_id: str, style: InteractionStyle) -> UserState:
        """Explicitly update the user's preferred interaction style."""
        state = await self.get_state(user_id)
        state.preferred_interaction_style = style
        await self.user_state_repo.update(user_id, state)
        return state
