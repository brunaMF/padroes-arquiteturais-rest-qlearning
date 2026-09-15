from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json
from app.database import Base


class QLearningState(Base):
    __tablename__ = "qlearning_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    state_key = Column(String, nullable=False, index=True)
    q_table_json = Column(Text, nullable=False)  # Q-table serializada como JSON
    learning_rate = Column(Float, default=0.1)
    discount_factor = Column(Float, default=0.9)
    epsilon = Column(Float, default=0.1)
    total_episodes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="qlearning_states")
    
    def get_q_table(self):
        """Deserializa a Q-table do JSON"""
        return json.loads(self.q_table_json)
    
    def set_q_table(self, q_table: dict):
        """Serializa a Q-table para JSON"""
        self.q_table_json = json.dumps(q_table)
