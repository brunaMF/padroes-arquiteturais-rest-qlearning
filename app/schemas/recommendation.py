from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RecommendationRequest(BaseModel):
    user_id: int


class RecommendationResponse(BaseModel):
    user_id: int
    recommended_content: str
    content_id: str
    confidence: float
    state: str
    action: str
    timestamp: datetime


class FeedbackRequest(BaseModel):
    user_id: int
    content_id: str
    reward: float  # 0.0 a 1.0
    interaction_type: Optional[str] = "view"  # view, complete, like, etc.


class FeedbackResponse(BaseModel):
    user_id: int
    content_id: str
    reward: float
    updated: bool
    message: str
    timestamp: datetime


class AgentStats(BaseModel):
    user_id: int
    total_episodes: int
    learning_rate: float
    discount_factor: float
    epsilon: float
    q_table_size: int
    last_updated: datetime
