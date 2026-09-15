from typing import Optional, Dict
from app.services.qlearning_agent import QLearningAgent
import threading
import time


class StateCacheStrategy:
    """
    Estratégia de gerenciamento de estado usando cache em memória.
    Mantém os agentes em um dicionário em memória para baixa latência.
    """
    
    def __init__(self):
        # Cache: user_id -> (agent, last_access_time)
        self._cache: Dict[int, tuple] = {}
        self._lock = threading.Lock()
        self._max_idle_time = 3600  # 1 hora em segundos
    
    def get_agent(self, user_id: int) -> QLearningAgent:
        """
        Carrega ou cria um agente Q-learning para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Instância do QLearningAgent
        """
        with self._lock:
            if user_id in self._cache:
                agent, _ = self._cache[user_id]
                # Atualiza tempo de acesso
                self._cache[user_id] = (agent, time.time())
                return agent
            else:
                # Cria novo agente
                agent = QLearningAgent()
                self._cache[user_id] = (agent, time.time())
                return agent
    
    def save_agent(self, user_id: int, agent: QLearningAgent):
        """
        Salva o estado do agente no cache.
        
        Args:
            user_id: ID do usuário
            agent: Instância do QLearningAgent
        """
        with self._lock:
            self._cache[user_id] = (agent, time.time())
    
    def _cleanup_idle_agents(self):
        """Remove agentes inativos do cache"""
        current_time = time.time()
        with self._lock:
            idle_users = [
                user_id for user_id, (_, last_access) in self._cache.items()
                if current_time - last_access > self._max_idle_time
            ]
            for user_id in idle_users:
                del self._cache[user_id]
    
    def get_stats(self, user_id: int) -> Optional[Dict]:
        """
        Retorna estatísticas do agente do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com estatísticas ou None
        """
        with self._lock:
            if user_id not in self._cache:
                return None
            
            agent, last_access = self._cache[user_id]
            stats = agent.get_stats()
            stats["user_id"] = user_id
            stats["last_updated"] = time.time()
            return stats
    
    def clear_cache(self):
        """Limpa todo o cache (útil para testes)"""
        with self._lock:
            self._cache.clear()
