import numpy as np
from typing import Dict, Tuple, Optional
import random


class QLearningAgent:
    """
    Agente Q-learning para personalização educacional.
    
    CONTEXTO EDUCACIONAL:
    Este agente implementa aprendizado por reforço para personalizar a experiência
    de aprendizado de cada aluno em uma plataforma educacional.
    
    Estados (Níveis de Desempenho do Aluno):
    - "baixo": Aluno com desempenho < 40% (precisa de conteúdo básico)
    - "medio": Aluno com desempenho entre 40% e 70% (em desenvolvimento)
    - "alto": Aluno com desempenho >= 70% (pronto para desafios avançados)
    
    Ações (Tipos de Conteúdo Educacional):
    - "basico": Conteúdo introdutório para alunos iniciantes
    - "intermediario": Conteúdo para alunos em desenvolvimento
    - "avancado": Conteúdo desafiador para alunos proficientes
    - "revisao": Material de reforço para consolidar aprendizado
    
    Recompensas (Feedback do Aluno):
    - 0.0 a 1.0: Representa quão efetivo foi o conteúdo para o aluno
    - Alto valor: Conteúdo foi adequado e efetivo
    - Baixo valor: Conteúdo não foi adequado ao nível do aluno
    
    O agente aprende qual tipo de conteúdo funciona melhor para cada perfil
    de aluno através de tentativa e erro, melhorando as recomendações ao longo do tempo.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Estados: níveis de desempenho educacional do aluno
        self.states = ["baixo", "medio", "alto"]
        
        # Ações: tipos de conteúdo educacional disponíveis
        self.actions = ["basico", "intermediario", "avancado", "revisao"]
        
        # Q-table: estado -> ação -> valor Q
        self.q_table: Dict[str, Dict[str, float]] = self._init_q_table()
        
        # Contador de episódios
        self.total_episodes = 0
    
    def _init_q_table(self) -> Dict[str, Dict[str, float]]:
        """Inicializa a Q-table com valores zero"""
        q_table = {}
        for state in self.states:
            q_table[state] = {action: 0.0 for action in self.actions}
        return q_table
    
    def get_state(self, user_performance: float) -> str:
        """
        Determina o estado baseado no desempenho do usuário.
        
        Args:
            user_performance: Valor entre 0.0 e 1.0 representando desempenho
            
        Returns:
            Estado: "baixo", "medio" ou "alto"
        """
        if user_performance < 0.4:
            return "baixo"
        elif user_performance < 0.7:
            return "medio"
        else:
            return "alto"
    
    def choose_action(self, state: str, exploration: bool = True) -> str:
        """
        Escolhe uma ação usando política ε-greedy.
        
        Args:
            state: Estado atual
            exploration: Se True, permite exploração (ε-greedy)
            
        Returns:
            Ação escolhida
        """
        if exploration and random.random() < self.epsilon:
            # Exploração: escolhe ação aleatória
            return random.choice(self.actions)
        else:
            # Exploração: escolhe melhor ação conhecida
            q_values = self.q_table[state]
            max_q = max(q_values.values())
            # Se houver empate, escolhe aleatoriamente entre as melhores
            best_actions = [a for a, q in q_values.items() if q == max_q]
            return random.choice(best_actions)
    
    def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: Optional[str] = None
    ):
        """
        Atualiza o valor Q usando a equação de Bellman.
        
        Q(s,a) = Q(s,a) + α[r + γ * max(Q(s',a')) - Q(s,a)]
        
        Args:
            state: Estado atual
            action: Ação tomada
            reward: Recompensa recebida
            next_state: Próximo estado (opcional)
        """
        current_q = self.q_table[state][action]
        
        if next_state:
            max_next_q = max(self.q_table[next_state].values())
        else:
            max_next_q = 0.0
        
        # Equação de Bellman
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
        
        # Decaimento do epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def get_best_action(self, state: str) -> Tuple[str, float]:
        """
        Retorna a melhor ação para um estado e seu valor Q.
        
        Args:
            state: Estado atual
            
        Returns:
            Tupla (ação, valor_q)
        """
        q_values = self.q_table[state]
        best_action = max(q_values, key=q_values.get)
        best_value = q_values[best_action]
        return best_action, best_value
    
    def get_q_table(self) -> Dict[str, Dict[str, float]]:
        """Retorna a Q-table completa"""
        return self.q_table.copy()
    
    def set_q_table(self, q_table: Dict[str, Dict[str, float]]):
        """Define a Q-table (útil para carregar estado persistido)"""
        self.q_table = q_table
    
    def increment_episodes(self):
        """Incrementa o contador de episódios"""
        self.total_episodes += 1
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do agente"""
        return {
            "total_episodes": self.total_episodes,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "q_table_size": sum(len(actions) for actions in self.q_table.values())
        }
