from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    FeedbackRequest,
    FeedbackResponse,
    AgentStats
)
from app.services.qlearning_agent import QLearningAgent
from app.services.state_db import StateDBStrategy
from app.services.state_cache import StateCacheStrategy
from app.config import settings
import random

router = APIRouter()

# Instância global da estratégia de cache (se aplicável)
_cache_strategy: Optional[StateCacheStrategy] = None


def get_state_strategy(db: Session = Depends(get_db)):
    """
    Factory que retorna a estratégia de estado configurada.
    """
    global _cache_strategy
    
    if settings.STATE_STRATEGY == "cache":
        if _cache_strategy is None:
            _cache_strategy = StateCacheStrategy()
        return _cache_strategy
    else:
        return StateDBStrategy(db)


def get_user_performance(user_id: int, db: Session = None) -> float:
    """
    Calcula o desempenho educacional do aluno baseado em histórico.
    
    CONTEXTO EDUCACIONAL:
    Esta função representa a avaliação do desempenho do aluno em uma plataforma
    educacional. Em produção, calcularia baseado em:
    - Notas médias em exercícios e avaliações
    - Taxa de conclusão de conteúdos
    - Tempo médio de resposta em questões
    - Taxa de acerto em diferentes níveis de dificuldade
    - Histórico de feedback sobre conteúdos
    
    Args:
        user_id: ID do aluno
        db: Sessão do banco de dados (opcional, para consultar histórico real)
        
    Returns:
        Valor de desempenho entre 0.0 (0%) e 1.0 (100%)
        - 0.0-0.4: Desempenho baixo (aluno com dificuldades)
        - 0.4-0.7: Desempenho médio (aluno em desenvolvimento)
        - 0.7-1.0: Desempenho alto (aluno proficiente)
    """
    # TODO: Em produção, implementar cálculo real baseado em:
    # - Média de notas em exercícios
    # - Taxa de conclusão de módulos
    # - Análise de padrões de aprendizado
    # - Feedback histórico do aluno
    
    # Simulação para MVP: retorna valor aleatório
    # Em produção, consultaria tabelas como:
    # - user_exercises (notas, tentativas)
    # - user_content_interactions (tempo, conclusão)
    # - user_feedback (avaliações, dificuldade percebida)
    return random.uniform(0.2, 0.9)


@router.get("/{user_id}", response_model=RecommendationResponse)
def get_recommendation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtém recomendação personalizada de conteúdo educacional para o aluno.
    
    PERSONALIZAÇÃO EDUCACIONAL:
    Este endpoint implementa a personalização através de:
    1. Avaliação do desempenho atual do aluno
    2. Classificação do aluno em um estado (baixo/médio/alto desempenho)
    3. Uso do Q-learning para escolher o tipo de conteúdo mais adequado
    4. Recomendação de conteúdo educacional personalizado
    
    O agente Q-learning aprende continuamente qual tipo de conteúdo funciona
    melhor para cada perfil de aluno, melhorando as recomendações ao longo do tempo.
    """
    # Verifica se o usuário tem permissão
    if current_user.id != user_id and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Obtém estratégia de estado
    state_strategy = get_state_strategy(db)
    
    # Carrega ou cria agente
    agent = state_strategy.get_agent(user_id)
    
    # Obtém desempenho do usuário
    user_performance = get_user_performance(user_id, db)
    
    # Determina estado atual
    state = agent.get_state(user_performance)
    
    # Escolhe ação (recomendação)
    action = agent.choose_action(state, exploration=True)
    
    # Mapeia ação do Q-learning para conteúdo educacional personalizado
    # CONTEXTO EDUCACIONAL: Cada tipo de conteúdo é adequado para diferentes
    # níveis de desempenho do aluno, permitindo personalização da experiência
    content_map = {
        "basico": "Conteúdo Básico de Introdução - Ideal para alunos iniciantes",
        "intermediario": "Conteúdo Intermediário - Para alunos em desenvolvimento",
        "avancado": "Conteúdo Avançado - Desafios para alunos proficientes",
        "revisao": "Material de Revisão - Reforço e consolidação de aprendizado"
    }
    
    recommended_content = content_map.get(action, "Conteúdo Padrão")
    content_id = f"content_{action}_{user_id}_{datetime.now().timestamp()}"
    
    # Obtém confiança (valor Q da ação)
    _, confidence = agent.get_best_action(state)
    # Normaliza confiança para 0-1
    confidence = max(0.0, min(1.0, (confidence + 1) / 2))
    
    # Salva estado atualizado
    state_strategy.save_agent(user_id, agent)
    
    return RecommendationResponse(
        user_id=user_id,
        recommended_content=recommended_content,
        content_id=content_id,
        confidence=confidence,
        state=state,
        action=action,
        timestamp=datetime.now()
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recebe feedback do aluno sobre o conteúdo recomendado e atualiza o agente.
    
    APRENDIZADO CONTÍNUO:
    Este endpoint permite que o sistema aprenda com as interações do aluno:
    1. O aluno avalia o conteúdo recomendado (reward: 0.0 a 1.0)
    2. O sistema atualiza o desempenho do aluno baseado no feedback
    3. O agente Q-learning atualiza seus conhecimentos sobre qual conteúdo
       funciona melhor para cada tipo de aluno
    4. As próximas recomendações serão mais precisas e personalizadas
    
    Este é o mecanismo de aprendizado contínuo que diferencia este sistema
    de uma simples recomendação baseada em regras fixas.
    """
    # Verifica permissão
    if current_user.id != feedback.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Obtém estratégia de estado
    state_strategy = get_state_strategy(db)
    
    # Carrega agente
    agent = state_strategy.get_agent(feedback.user_id)
    
    # Obtém desempenho atual
    user_performance = get_user_performance(feedback.user_id, db)
    current_state = agent.get_state(user_performance)
    
    # CONTEXTO EDUCACIONAL: Atualiza o desempenho do aluno baseado no feedback
    # sobre o conteúdo recomendado. Se o aluno teve boa experiência (reward alto),
    # seu desempenho melhora, indicando que o conteúdo foi adequado e efetivo.
    # Se o feedback foi negativo (reward baixo), o desempenho pode piorar,
    # sugerindo que o conteúdo não foi adequado ao nível do aluno.
    performance_delta = (feedback.reward - 0.5) * 0.2
    new_performance = max(0.0, min(1.0, user_performance + performance_delta))
    next_state = agent.get_state(new_performance)
    
    # Extrai ação do content_id (formato: content_{action}_{user_id}_{timestamp})
    action = feedback.content_id.split("_")[1] if "_" in feedback.content_id else "basico"
    
    # Atualiza Q-value
    agent.update_q_value(current_state, action, feedback.reward, next_state)
    agent.increment_episodes()
    
    # Salva estado atualizado
    state_strategy.save_agent(feedback.user_id, agent)
    
    return FeedbackResponse(
        user_id=feedback.user_id,
        content_id=feedback.content_id,
        reward=feedback.reward,
        updated=True,
        message="Feedback processado com sucesso. Agente atualizado.",
        timestamp=datetime.now()
    )


@router.get("/stats/{user_id}", response_model=AgentStats)
def get_agent_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas do agente Q-learning do usuário.
    """
    # Verifica permissão
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Obtém estratégia de estado
    state_strategy = get_state_strategy(db)
    
    # Obtém estatísticas
    stats = state_strategy.get_stats(user_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found for this user"
        )
    
    return AgentStats(
        user_id=stats["user_id"],
        total_episodes=stats["total_episodes"],
        learning_rate=stats["learning_rate"],
        discount_factor=stats["discount_factor"],
        epsilon=stats["epsilon"],
        q_table_size=stats["q_table_size"],
        last_updated=stats["last_updated"]
    )
