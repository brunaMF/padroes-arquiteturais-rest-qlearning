#!/bin/bash
# Script rápido para executar todos os testes em sequência

echo "=========================================="
echo "TESTE RÁPIDO - 2 ESTRATÉGIAS"
echo "=========================================="

# Criar pasta de resultados
mkdir -p results

# ESTRATÉGIA 1: BD
echo ""
echo ">>> TESTANDO ESTRATÉGIA: REST + BD"
echo ""

# Configurar BD (assumindo que .env já está configurado)
export STATE_STRATEGY=db

# Teste de latência
echo "Testando latência..."
python scripts/test_latency.py --strategy db --output results/db_quick.json

# Teste de carga (2 minutos)
echo "Testando carga (2 minutos)..."
k6 run tests/k6_load_test.js --duration 2m --out json=results/db_load.json

echo ""
echo ">>> TESTANDO ESTRATÉGIA: REST + CACHE"
echo ""

# ESTRATÉGIA 2: Cache
export STATE_STRATEGY=cache

# Teste de latência
echo "Testando latência..."
python scripts/test_latency.py --strategy cache --output results/cache_quick.json

# Teste de carga (2 minutos)
echo "Testando carga (2 minutos)..."
k6 run tests/k6_load_test.js --duration 2m --out json=results/cache_load.json

# Análise
echo ""
echo ">>> ANÁLISE COMPARATIVA"
echo ""
python scripts/analyze_results.py --bd results/db_quick.json --cache results/cache_quick.json --output results/comparison.json

echo ""
echo "=========================================="
echo "TESTES CONCLUÍDOS!"
echo "Resultados em: results/"
echo "=========================================="
