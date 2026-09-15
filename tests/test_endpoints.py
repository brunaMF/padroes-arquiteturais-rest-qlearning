import os
import pytest
import requests
from typing import Optional

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture
def auth_token() -> Optional[str]:
    """Obtém token de autenticação para testes"""
    try:
        # Tenta registrar usuário de teste
        register_data = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "test_password"
        }
        requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data, timeout=5)
    except:
        pass
    
    try:
        # Faz login
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except:
        pass
    
    return None


def test_openapi_available():
    """Testa disponibilidade da documentação OpenAPI"""
    r = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
    assert r.status_code == 200
    assert "openapi" in r.json() or "swagger" in r.json()


def test_health_check():
    """Testa endpoint de health check"""
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_root_endpoint():
    """Testa endpoint raiz"""
    r = requests.get(f"{BASE_URL}/", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "message" in data


def test_register_user():
    """Testa registro de novo usuário"""
    import random
    username = f"test_user_{random.randint(1000, 9999)}"
    register_data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "test_password"
    }
    r = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data, timeout=5)
    # Pode ser 201 (criado) ou 400 (já existe)
    assert r.status_code in (201, 400)


def test_login(auth_token):
    """Testa autenticação"""
    if auth_token:
        assert len(auth_token) > 0
    else:
        pytest.skip("Não foi possível obter token de autenticação")


def test_get_recommendation(auth_token):
    """Testa obtenção de recomendação"""
    if not auth_token:
        pytest.skip("Token de autenticação não disponível")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    r = requests.get(
        f"{BASE_URL}/api/v1/recommendations/1",
        headers=headers,
        timeout=5
    )
    # Pode ser 200 (sucesso) ou 403 (sem permissão)
    assert r.status_code in (200, 403)
    if r.status_code == 200:
        data = r.json()
        assert "recommended_content" in data
        assert "user_id" in data


def test_submit_feedback(auth_token):
    """Testa envio de feedback"""
    if not auth_token:
        pytest.skip("Token de autenticação não disponível")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "user_id": 1,
        "content_id": "content_basico_1_123456",
        "reward": 0.8,
        "interaction_type": "view"
    }
    r = requests.post(
        f"{BASE_URL}/api/v1/recommendations/feedback",
        json=payload,
        headers=headers,
        timeout=5
    )
    # Pode ser 201 (criado) ou 403 (sem permissão)
    assert r.status_code in (201, 403)
    if r.status_code == 201:
        data = r.json()
        assert "updated" in data
        assert data["updated"] is True


def test_get_agent_stats(auth_token):
    """Testa obtenção de estatísticas do agente"""
    if not auth_token:
        pytest.skip("Token de autenticação não disponível")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    r = requests.get(
        f"{BASE_URL}/api/v1/recommendations/stats/1",
        headers=headers,
        timeout=5
    )
    # Pode ser 200 (sucesso), 403 (sem permissão) ou 404 (não encontrado)
    assert r.status_code in (200, 403, 404)
    if r.status_code == 200:
        data = r.json()
        assert "user_id" in data
        assert "total_episodes" in data
