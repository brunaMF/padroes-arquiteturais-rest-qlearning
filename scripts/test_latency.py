#!/usr/bin/env python3
"""
Script para medir latência de endpoints individuais.
"""
import argparse
import json
import requests
import statistics
import time
from typing import Dict, List

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def create_test_user(username: str, email: str, password: str) -> bool:
    """Cria usuário de teste se não existir"""
    try:
        user_data = {
            "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=user_data,
            timeout=5
        )
        # 201 = criado, 400 = já existe (ambos são OK)
        if response.status_code in [201, 400]:
            if response.status_code == 201:
                print(f"   ✓ Usuário criado com sucesso")
            else:
                print(f"   ✓ Usuário já existe")
            return True
        else:
            print(f"   ⚠️  Erro ao criar usuário: status {response.status_code}")
            try:
                print(f"   Resposta: {response.text}")
            except:
                pass
            return False
    except Exception as e:
        print(f"   ❌ Exceção ao criar usuário: {e}")
        return False


def get_auth_token(username: str, password: str) -> str:
    """Obtém token de autenticação, criando usuário se necessário"""
    # Primeiro, tenta criar o usuário (se não existir)
    email = f"{username}@example.com"
    user_created = create_test_user(username, email, password)
    
    if not user_created:
        print(f"   ⚠️  Não foi possível criar usuário, mas tentando login mesmo assim...")
    
    # Depois, faz login
    print(f"   Fazendo login...")
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data={"username": username, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"   ✓ Login bem-sucedido")
            return token
        else:
            print(f"   ❌ Erro no login: status {response.status_code}")
            try:
                print(f"   Resposta: {response.text}")
            except:
                pass
            if response.status_code == 401:
                print(f"   → Credenciais inválidas ou usuário não existe")
            elif response.status_code == 500:
                print(f"   → Erro interno do servidor (verifique logs da API)")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erro de conexão: API não está acessível em {BASE_URL}")
        print(f"   → Certifique-se de que a API está rodando")
    except Exception as e:
        print(f"   ❌ Exceção ao fazer login: {e}")
    
    return None


def measure_endpoint_latency(
    method: str,
    endpoint: str,
    headers: Dict = None,
    data: Dict = None,
    iterations: int = 100
) -> Dict:
    """Mede latência de um endpoint"""
    latencies = []
    errors = 0
    
    for i in range(iterations):
        start = time.time()
        try:
            response = None
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers, timeout=5)
            else:
                errors += 1
                continue
            
            if response is not None:
                elapsed = (time.time() - start) * 1000  # ms
                if response.status_code in [200, 201]:
                    latencies.append(elapsed)
                else:
                    errors += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
    
    if not latencies:
        return None
    
    latencies.sort()
    p95_index = int(len(latencies) * 0.95)
    p99_index = int(len(latencies) * 0.99)
    
    return {
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "p95": latencies[p95_index] if p95_index < len(latencies) else latencies[-1],
        "p99": latencies[p99_index] if p99_index < len(latencies) else latencies[-1],
        "min": min(latencies),
        "max": max(latencies),
        "errors": errors,
        "total": iterations,
        "success_rate": (len(latencies) / iterations) * 100
    }


def test_strategy(strategy: str, output_file: str):
    """Testa uma estratégia específica"""
    print(f"\n{'='*60}")
    print(f"Testando estratégia: {strategy.upper()}")
    print(f"{'='*60}\n")
    
    # Verificar se API está rodando
    print("Verificando se API está rodando...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ Erro: API retornou status {response.status_code}")
            print("   → Verifique se a API está rodando corretamente")
            return
        print("✓ API está rodando")
        health_data = response.json()
        current_strategy = health_data.get("state_strategy", "unknown")
        print(f"✓ Estratégia atual: {current_strategy}")
        if current_strategy != strategy:
            print(f"⚠️  Aviso: Estratégia configurada é '{current_strategy}', não '{strategy}'")
            print("   → Certifique-se de que a estratégia está correta no .env")
            print("   → Reinicie a API após mudar o .env")
    except requests.exceptions.ConnectionError:
        print(f"❌ Erro: Não foi possível conectar à API em {BASE_URL}")
        print("   → API não está rodando")
        print("   → Inicie com: uvicorn app.main:app --reload")
        return
    except Exception as e:
        print(f"❌ Erro ao verificar API: {e}")
        print("   → Verifique se a API está rodando")
        return
    
    # Criar usuário de teste e obter token
    username = f"latency_test_user_{strategy}"
    password = "test_password"
    
    print(f"Criando usuário de teste: {username}...")
    token = get_auth_token(username, password)
    
    if not token:
        print("\n" + "="*60)
        print("ERRO: Nao foi possivel obter token de autenticacao")
        print("="*60)
        print("\nCAUSA MAIS COMUM: API nao esta rodando!")
        print("\nSolucao:")
        print("1. Abra OUTRO terminal")
        print("2. Execute: uvicorn app.main:app --reload")
        print("3. Aguarde ver: 'Application startup complete'")
        print("4. DEIXE esse terminal aberto")
        print("5. Volte aqui e execute o teste novamente")
        print("\nOutras possiveis causas:")
        print("- Banco de dados nao configurado")
        print("  -> Execute: python scripts/create_database.py")
        print("- Erro de conexao")
        print("  -> Verifique: http://localhost:8000/health")
        print("\nPara diagnostico completo:")
        print("  -> Execute: python scripts/diagnostico_api.py")
        return
    
    print(f"✓ Token obtido com sucesso!")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obter ID do usuário criado (faz uma requisição para /auth/me)
    print("Obtendo ID do usuário...")
    try:
        me_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/auth/me",
            headers=headers,
            timeout=5
        )
        if me_response.status_code == 200:
            user_id = me_response.json()["id"]
            print(f"✓ Usuário ID: {user_id}")
        else:
            user_id = 1  # Fallback
            print(f"⚠️  Usando user_id=1 como fallback")
    except Exception as e:
        user_id = 1  # Fallback
        print(f"⚠️  Usando user_id=1 como fallback (erro: {e})")
    
    results = {
        "strategy": strategy,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {}
    }
    
    # Teste 1: GET /recommendations/{user_id}
    print("Testando GET /recommendations/{user_id}...")
    endpoint = f"{API_PREFIX}/recommendations/{user_id}"
    latency = measure_endpoint_latency("GET", endpoint, headers=headers, iterations=100)
    if latency:
        results["endpoints"]["get_recommendation"] = latency
        print(f"  ✓ Latência média: {latency['mean']:.2f}ms")
        print(f"  ✓ p95: {latency['p95']:.2f}ms")
        print(f"  ✓ p99: {latency['p99']:.2f}ms")
    
    # Teste 2: POST /recommendations/feedback
    print("\nTestando POST /recommendations/feedback...")
    endpoint = f"{API_PREFIX}/recommendations/feedback"
    feedback_data = {
        "user_id": user_id,
        "content_id": "content_basico_1_123456",
        "reward": 0.8,
        "interaction_type": "view"
    }
    latency = measure_endpoint_latency("POST", endpoint, headers=headers, data=feedback_data, iterations=100)
    if latency:
        results["endpoints"]["post_feedback"] = latency
        print(f"  ✓ Latência média: {latency['mean']:.2f}ms")
        print(f"  ✓ p95: {latency['p95']:.2f}ms")
        print(f"  ✓ p99: {latency['p99']:.2f}ms")
    
    # Teste 3: GET /recommendations/stats/{user_id}
    print("\nTestando GET /recommendations/stats/{user_id}...")
    endpoint = f"{API_PREFIX}/recommendations/stats/{user_id}"
    latency = measure_endpoint_latency("GET", endpoint, headers=headers, iterations=100)
    if latency:
        results["endpoints"]["get_stats"] = latency
        print(f"  ✓ Latência média: {latency['mean']:.2f}ms")
        print(f"  ✓ p95: {latency['p95']:.2f}ms")
        print(f"  ✓ p99: {latency['p99']:.2f}ms")
    
    # Salvar resultados
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Resultados salvos em: {output_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Mede latência de endpoints")
    parser.add_argument("--strategy", choices=["db", "cache"], required=True, help="Estratégia a testar")
    parser.add_argument("--output", default=None, help="Arquivo de saída JSON")
    
    args = parser.parse_args()
    
    output_file = args.output or f"results/latency/{args.strategy}_latency.json"
    
    test_strategy(args.strategy, output_file)


if __name__ == "__main__":
    main()