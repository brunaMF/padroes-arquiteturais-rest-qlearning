from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.models.qlearning import QLearningState
from app.services.qlearning_agent import QLearningAgent
from app.config import settings


class StateDBStrategy:
    """
    Estratégia de gerenciamento de estado usando banco de dados PostgreSQL.
    Persiste a Q-table e hiperparâmetros do agente.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_agent(self, user_id: int) -> QLearningAgent:
        """
        Carrega ou cria um agente Q-learning para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Instância do QLearningAgent
        """
        # Busca estado existente no banco
        db_state = self.db.query(QLearningState).filter(
            QLearningState.user_id == user_id
        ).first()
        
        if db_state:
            # Carrega agente com estado existente
            agent = QLearningAgent(
                learning_rate=db_state.learning_rate,
                discount_factor=db_state.discount_factor,
                epsilon=db_state.epsilon
            )
            agent.set_q_table(db_state.get_q_table())
            agent.total_episodes = db_state.total_episodes
        else:
            # Cria novo agente
            agent = QLearningAgent()
            # Persiste estado inicial
            self._save_state(user_id, agent)
        
        return agent
    
    def save_agent(self, user_id: int, agent: QLearningAgent):
        """
        Salva o estado do agente no banco de dados.
        
        Args:
            user_id: ID do usuário
            agent: Instância do QLearningAgent
        """
        self._save_state(user_id, agent)
        self.db.commit()
    
    def _save_state(self, user_id: int, agent: QLearningAgent):
        """Método auxiliar para salvar estado"""
        db_state = self.db.query(QLearningState).filter(
            QLearningState.user_id == user_id
        ).first()
        
        if db_state:
            # Atualiza estado existente
            db_state.set_q_table(agent.get_q_table())
            db_state.learning_rate = agent.learning_rate
            db_state.discount_factor = agent.discount_factor
            db_state.epsilon = agent.epsilon
            db_state.total_episodes = agent.total_episodes
        else:
            # Cria novo estado
            db_state = QLearningState(
                user_id=user_id,
                state_key=f"user_{user_id}",
                learning_rate=agent.learning_rate,
                discount_factor=agent.discount_factor,
                epsilon=agent.epsilon,
                total_episodes=agent.total_episodes
            )
            db_state.set_q_table(agent.get_q_table())
            self.db.add(db_state)
        
        self.db.flush()
    
    def get_stats(self, user_id: int) -> Optional[Dict]:
        """
        Retorna estatísticas do agente do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com estatísticas ou None
        """
        db_state = self.db.query(QLearningState).filter(
            QLearningState.user_id == user_id
        ).first()
        
        if not db_state:
            return None
        
        return {
            "user_id": user_id,
            "total_episodes": db_state.total_episodes,
            "learning_rate": db_state.learning_rate,
            "discount_factor": db_state.discount_factor,
            "epsilon": db_state.epsilon,
            "q_table_size": len(db_state.get_q_table()) * len(db_state.get_q_table().get("baixo", {})),
            "last_updated": db_state.updated_at or db_state.created_at
        }
