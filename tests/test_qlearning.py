import pytest
from app.services.qlearning_agent import QLearningAgent


class TestQLearningAgent:
    """Testes para o agente Q-learning"""
    
    def test_agent_initialization(self):
        """Testa inicialização do agente"""
        agent = QLearningAgent()
        assert agent.learning_rate == 0.1
        assert agent.discount_factor == 0.9
        assert agent.epsilon == 0.1
        assert len(agent.states) == 3
        assert len(agent.actions) == 4
    
    def test_get_state(self):
        """Testa determinação de estado baseado em desempenho"""
        agent = QLearningAgent()
        
        assert agent.get_state(0.3) == "baixo"
        assert agent.get_state(0.5) == "medio"
        assert agent.get_state(0.8) == "alto"
    
    def test_choose_action(self):
        """Testa escolha de ação"""
        agent = QLearningAgent()
        state = "medio"
        
        # Com exploração, deve retornar uma ação válida
        action = agent.choose_action(state, exploration=True)
        assert action in agent.actions
        
        # Sem exploração, deve retornar melhor ação
        action = agent.choose_action(state, exploration=False)
        assert action in agent.actions
    
    def test_update_q_value(self):
        """Testa atualização de valor Q"""
        agent = QLearningAgent()
        state = "medio"
        action = "basico"
        initial_q = agent.q_table[state][action]
        
        # Atualiza com recompensa positiva
        agent.update_q_value(state, action, reward=1.0, next_state="alto")
        
        # Valor Q deve ter aumentado
        new_q = agent.q_table[state][action]
        assert new_q > initial_q
    
    def test_get_best_action(self):
        """Testa obtenção da melhor ação"""
        agent = QLearningAgent()
        state = "medio"
        
        # Define valores Q manualmente
        agent.q_table[state]["basico"] = 0.5
        agent.q_table[state]["intermediario"] = 0.8
        agent.q_table[state]["avancado"] = 0.3
        agent.q_table[state]["revisao"] = 0.6
        
        best_action, best_value = agent.get_best_action(state)
        assert best_action == "intermediario"
        assert best_value == 0.8
    
    def test_q_table_persistence(self):
        """Testa persistência da Q-table"""
        agent = QLearningAgent()
        
        # Modifica Q-table
        agent.q_table["medio"]["basico"] = 0.5
        
        # Obtém Q-table
        q_table = agent.get_q_table()
        assert q_table["medio"]["basico"] == 0.5
        
        # Define nova Q-table
        new_q_table = {"baixo": {"basico": 1.0}}
        agent.set_q_table(new_q_table)
        assert agent.q_table["baixo"]["basico"] == 1.0
    
    def test_increment_episodes(self):
        """Testa incremento de episódios"""
        agent = QLearningAgent()
        assert agent.total_episodes == 0
        
        agent.increment_episodes()
        assert agent.total_episodes == 1
        
        agent.increment_episodes()
        assert agent.total_episodes == 2
    
    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        agent = QLearningAgent()
        stats = agent.get_stats()
        
        assert "total_episodes" in stats
        assert "learning_rate" in stats
        assert "discount_factor" in stats
        assert "epsilon" in stats
        assert "q_table_size" in stats
