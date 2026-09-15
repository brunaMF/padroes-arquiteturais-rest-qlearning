#!/bin/bash
# Script para executar testes

echo "Executando testes..."

# Testes unitários
echo "=== Testes Unitários ==="
pytest tests/test_qlearning.py -v

# Testes de estratégias
echo "=== Testes de Estratégias ==="
pytest tests/test_state_strategies.py -v

# Testes de endpoints (requer API rodando)
echo "=== Testes de Endpoints ==="
echo "Nota: Estes testes requerem a API rodando em http://localhost:8000"
pytest tests/test_endpoints.py -v

echo "Testes concluídos!"
