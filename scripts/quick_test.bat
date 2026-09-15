@echo off
REM Script rápido para Windows

echo ==========================================
echo TESTE RAPIDO - 2 ESTRATEGIAS
echo ==========================================

REM Criar pasta de resultados
if not exist results mkdir results

REM ESTRATEGIA 1: BD
echo.
echo ^>^>^> TESTANDO ESTRATEGIA: REST + BD
echo.

REM Teste de latência
echo Testando latencia...
python scripts/test_latency.py --strategy db --output results/db_quick.json

REM Teste de carga (2 minutos)
echo Testando carga (2 minutos)...
k6 run tests/k6_load_test.js --duration 2m --out json=results/db_load.json

echo.
echo ^>^>^> TESTANDO ESTRATEGIA: REST + CACHE
echo.

REM ESTRATEGIA 2: Cache
REM NOTA: Você precisa trocar STATE_STRATEGY no .env manualmente
REM e reiniciar a API antes de executar esta parte

REM Teste de latência
echo Testando latencia...
python scripts/test_latency.py --strategy cache --output results/cache_quick.json

REM Teste de carga (2 minutos)
echo Testando carga (2 minutos)...
k6 run tests/k6_load_test.js --duration 2m --out json=results/cache_load.json

REM Análise
echo.
echo ^>^>^> ANALISE COMPARATIVA
echo.
python scripts/analyze_results.py --bd results/db_quick.json --cache results/cache_quick.json --output results/comparison.json

echo.
echo ==========================================
echo TESTES CONCLUIDOS!
echo Resultados em: results/
echo ==========================================
pause
