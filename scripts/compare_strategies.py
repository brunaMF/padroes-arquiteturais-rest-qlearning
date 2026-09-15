#!/usr/bin/env python3
"""
Script para comparar desempenho das duas estratégias de estado.
Executa testes de carga e compara métricas.
"""
import sys
import os
import time
import requests
import statistics
from typing import List, Dict

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def create_test_user(user_id: int) -> str:
    """Cria usuário de teste e retorna token"""
    username = f"test_user_{user_id}"
    
    # Tenta registrar
    register_data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "test_password"
    }
    requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=register_data)
    
    # Faz login
    login_data = {
        "username": username,
        "password": "test_password"
    }
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        data=login_data
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_recommendation(token: str, user_id: int) -> float:
    """Testa endpoint de recomendação e retorna tempo de resposta"""
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/recommendations/{user_id}",
        headers=headers
    )
    elapsed = (time.time() - start) * 1000  # em ms
    return elapsed if response.status_code == 200 else None

def test_feedback(token: str, user_id: int, content_id: str) -> float:
    """Testa endpoint de feedback e retorna tempo de resposta"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "user_id": user_id,
        "content_id": content_id,
        "reward": 0.8,
        "interaction_type": "view"
    }
    start = time.time()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/recommendations/feedback",
        json=payload,
        headers=headers
    )
    elapsed = (time.time() - start) * 1000  # em ms
    return elapsed if response.status_code == 201 else None

def run_benchmark(num_requests: int = 100) -> Dict:
    """Executa benchmark e retorna métricas"""
    print(f"Executando {num_requests} requisições...")
    
    # Cria usuário de teste
    user_id = 999
    token = create_test_user(user_id)
    if not token:
        print("Erro ao criar usuário de teste")
        return {}
    
    latencies = []
    errors = 0
    
    for i in range(num_requests):
        # Testa recomendação
        latency = test_recommendation(token, user_id)
        if latency:
            latencies.append(latency)
        else:
            errors += 1
        
        # Testa feedback (a cada 2 requisições)
        if i % 2 == 0:
            content_id = f"content_test_{i}"
            latency = test_feedback(token, user_id, content_id)
            if latency:
                latencies.append(latency)
            else:
                errors += 1
    
    if not latencies:
        return {"error": "Nenhuma requisição bem-sucedida"}
    
    latencies.sort()
    p95_index = int(len(latencies) * 0.95)
    p99_index = int(len(latencies) * 0.99)
    
    return {
        "total_requests": num_requests,
        "successful": len(latencies),
        "errors": errors,
        "mean_latency_ms": statistics.mean(latencies),
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": latencies[p95_index] if p95_index < len(latencies) else latencies[-1],
        "p99_latency_ms": latencies[p99_index] if p99_index < len(latencies) else latencies[-1],
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
    }

def main():
    """Função principal"""
    print("=" * 60)
    print("Comparação de Estratégias de Estado")
    print("=" * 60)
    
    # Verifica se API está rodando
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("Erro: API não está respondendo corretamente")
            sys.exit(1)
    except:
        print("Erro: API não está rodando. Inicie com: uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Obtém estratégia atual
    response = requests.get(f"{BASE_URL}/health")
    strategy = response.json().get("state_strategy", "unknown")
    print(f"\nEstratégia atual: {strategy}")
    print("\nExecutando benchmark...\n")
    
    # Executa benchmark
    metrics = run_benchmark(num_requests=100)
    
    if "error" in metrics:
        print(f"Erro: {metrics['error']}")
        sys.exit(1)
    
    # Exibe resultados
    print("\n" + "=" * 60)
    print("Resultados do Benchmark")
    print("=" * 60)
    print(f"Total de requisições: {metrics['total_requests']}")
    print(f"Bem-sucedidas: {metrics['successful']}")
    print(f"Erros: {metrics['errors']}")
    print(f"\nLatência (ms):")
    print(f"  Média:     {metrics['mean_latency_ms']:.2f}")
    print(f"  Mediana:   {metrics['median_latency_ms']:.2f}")
    print(f"  P95:       {metrics['p95_latency_ms']:.2f}")
    print(f"  P99:       {metrics['p99_latency_ms']:.2f}")
    print(f"  Mínima:    {metrics['min_latency_ms']:.2f}")
    print(f"  Máxima:    {metrics['max_latency_ms']:.2f}")
    print("=" * 60)
    
    print("\nPara comparar estratégias:")
    print("1. Configure STATE_STRATEGY=db no .env e execute novamente")
    print("2. Configure STATE_STRATEGY=cache no .env e execute novamente")
    print("3. Compare os resultados")

if __name__ == "__main__":
    main()
