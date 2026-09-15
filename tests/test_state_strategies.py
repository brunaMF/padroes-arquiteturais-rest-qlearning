import pytest
from sqlalchemy.orm import Session
from app.services.qlearning_agent import QLearningAgent
from app.services.state_db import StateDBStrategy
from app.services.state_cache import StateCacheStrategy
from app.models.user import User
from app.models.qlearning import QLearningState
from app.database import SessionLocal, Base, engine


@pytest.fixture
def db_session():
    """Cria sessão de banco de dados para testes"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session: Session):
    """Cria usuário de teste"""
    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestStateDBStrategy:
    """Testes para estratégia de estado com banco de dados"""
    
    def test_get_agent_new_user(self, db_session: Session, test_user: User):
        """Testa obtenção de agente para novo usuário"""
        strategy = StateDBStrategy(db_session)
        agent = strategy.get_agent(test_user.id)
        
        assert isinstance(agent, QLearningAgent)
        assert agent.total_episodes == 0
    
    def test_save_and_load_agent(self, db_session: Session, test_user: User):
        """Testa salvamento e carregamento de agente"""
        strategy = StateDBStrategy(db_session)
        
        # Cria e modifica agente
        agent = strategy.get_agent(test_user.id)
        agent.q_table["medio"]["basico"] = 0.5
        agent.total_episodes = 10
        
        # Salva
        strategy.save_agent(test_user.id, agent)
        db_session.commit()
        
        # Carrega novamente
        loaded_agent = strategy.get_agent(test_user.id)
        assert loaded_agent.q_table["medio"]["basico"] == 0.5
        assert loaded_agent.total_episodes == 10
    
    def test_get_stats(self, db_session: Session, test_user: User):
        """Testa obtenção de estatísticas"""
        strategy = StateDBStrategy(db_session)
        
        # Cria agente
        agent = strategy.get_agent(test_user.id)
        agent.total_episodes = 5
        strategy.save_agent(test_user.id, agent)
        db_session.commit()
        
        # Obtém estatísticas
        stats = strategy.get_stats(test_user.id)
        assert stats is not None
        assert stats["user_id"] == test_user.id
        assert stats["total_episodes"] == 5


class TestStateCacheStrategy:
    """Testes para estratégia de estado com cache"""
    
    def test_get_agent_new_user(self):
        """Testa obtenção de agente para novo usuário"""
        strategy = StateCacheStrategy()
        agent = strategy.get_agent(user_id=1)
        
        assert isinstance(agent, QLearningAgent)
        assert agent.total_episodes == 0
    
    def test_save_and_load_agent(self):
        """Testa salvamento e carregamento de agente"""
        strategy = StateCacheStrategy()
        
        # Cria e modifica agente
        agent = strategy.get_agent(user_id=1)
        agent.q_table["medio"]["basico"] = 0.5
        agent.total_episodes = 10
        
        # Salva
        strategy.save_agent(user_id=1, agent)
        
        # Carrega novamente
        loaded_agent = strategy.get_agent(user_id=1)
        assert loaded_agent.q_table["medio"]["basico"] == 0.5
        assert loaded_agent.total_episodes == 10
    
    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        strategy = StateCacheStrategy()
        
        # Cria agente
        agent = strategy.get_agent(user_id=1)
        agent.total_episodes = 5
        strategy.save_agent(user_id=1, agent)
        
        # Obtém estatísticas
        stats = strategy.get_stats(user_id=1)
        assert stats is not None
        assert stats["user_id"] == 1
        assert stats["total_episodes"] == 5
    
    def test_clear_cache(self):
        """Testa limpeza do cache"""
        strategy = StateCacheStrategy()
        
        # Cria agente
        agent = strategy.get_agent(user_id=1)
        
        # Limpa cache
        strategy.clear_cache()
        
        # Novo agente deve ser criado
        new_agent = strategy.get_agent(user_id=1)
        assert new_agent.total_episodes == 0
