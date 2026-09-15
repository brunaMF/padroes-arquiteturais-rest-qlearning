#!/usr/bin/env python3
"""
Script de diagnóstico para verificar se a API está configurada corretamente.
"""
import requests
import sys

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def check_api_running():
    """Verifica se a API está rodando"""
    print("1. Verificando se API está rodando...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("   [OK] API esta rodando")
            data = response.json()
            print(f"   -> Estrategia atual: {data.get('state_strategy', 'unknown')}")
            return True
        else:
            print(f"   [ERRO] API retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   [ERRO] API nao esta acessivel")
        print("   -> Inicie a API com: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def check_database():
    """Verifica se consegue criar usuário (testa banco)"""
    print("\n2. Verificando banco de dados (tentando criar usuário)...")
    try:
        user_data = {
            "username": "diagnostico_test",
            "email": "diagnostico@test.com",
            "password": "test123"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=user_data,
            timeout=5
        )
        if response.status_code == 201:
            print("   [OK] Usuario criado com sucesso (banco funcionando)")
            return True
        elif response.status_code == 400:
            print("   [OK] Usuario ja existe (banco funcionando)")
            return True
        else:
            print(f"   [ERRO] Erro ao criar usuario: status {response.status_code}")
            try:
                print(f"   Resposta: {response.text}")
            except:
                pass
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def check_login():
    """Verifica se consegue fazer login"""
    print("\n3. Verificando login...")
    try:
        # Primeiro, garantir que usuário existe
        user_data = {
            "username": "diagnostico_test",
            "email": "diagnostico@test.com",
            "password": "test123"
        }
        requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=user_data,
            timeout=5
        )
        
        # Tentar login
        login_data = {
            "username": "diagnostico_test",
            "password": "test123"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data=login_data,
            timeout=5
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                print("   [OK] Login funcionando")
                print(f"   -> Token obtido: {token[:20]}...")
                return True
            else:
                print("   [ERRO] Token nao retornado")
                return False
        else:
            print(f"   [ERRO] Erro no login: status {response.status_code}")
            try:
                print(f"   Resposta: {response.text}")
            except:
                pass
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def check_recommendations():
    """Verifica se endpoint de recomendações funciona"""
    print("\n4. Verificando endpoint de recomendações...")
    try:
        # Obter token
        login_data = {
            "username": "diagnostico_test",
            "password": "test123"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data=login_data,
            timeout=5
        )
        if response.status_code != 200:
            print("   ⚠️  Não foi possível obter token para teste")
            return False
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Testar endpoint
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/recommendations/1",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            print("   [OK] Endpoint de recomendacoes funcionando")
            return True
        else:
            print(f"   [AVISO] Endpoint retornou status {response.status_code}")
            try:
                print(f"   Resposta: {response.text[:200]}")
            except:
                pass
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("="*60)
    print("DIAGNÓSTICO DA API")
    print("="*60)
    
    results = {
        "api_running": check_api_running(),
        "database": check_database(),
        "login": check_login(),
        "recommendations": check_recommendations()
    }
    
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    
    all_ok = all(results.values())
    
    for check, status in results.items():
        status_icon = "[OK]" if status else "[ERRO]"
        print(f"{status_icon} {check.replace('_', ' ').title()}")
    
    if all_ok:
        print("\n[SUCESSO] Tudo funcionando! Voce pode executar os testes.")
        sys.exit(0)
    else:
        print("\n[ERRO] Alguns problemas foram encontrados.")
        print("\nSolucoes:")
        if not results["api_running"]:
            print("  -> PASSO 1: Inicie a API em outro terminal:")
            print("     uvicorn app.main:app --reload")
            print("     (Aguarde ver: 'Application startup complete')")
        if not results["database"]:
            print("  -> PASSO 2: Configure o banco:")
            print("     python scripts/create_database.py")
        if not results["login"]:
            print("  -> PASSO 3: Verifique logs da API para erros de autenticacao")
        sys.exit(1)

if __name__ == "__main__":
    main()
