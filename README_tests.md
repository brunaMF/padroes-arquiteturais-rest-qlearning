# Como rodar os testes de comparação

Pré-requisitos: API em execução (BASE_URL), Python 3.x, Node/k6 (ou Locust).

## 1) Testes funcionais rápidos (pytest)
Instale dependências mínimas:

```bash
pip install pytest requests
```

Execute apontando para sua API:

```bash
export BASE_URL=http://localhost:8000
pytest -q tests/test_endpoints.py
```

## 2) Carga com k6 (recomendado)
Instale o k6 e rode:

```bash
# Ajuste BASE_URL
BASE_URL=http://localhost:8000 \
K6_SUMMARY_EXPORT=summary.json \
k6 run tests/k6_load_test.js
```

- Resultado resumido no console e em `summary.json` (média/p95/p99).
- Ajuste o perfil via variáveis de ambiente, p.ex.: `USERS='[1,2,3,4,5,6]'`.

## 3) Carga com Locust (alternativa)

```bash
# Ajuste o host com --host
locust -f tests/locustfile.py --headless -u 200 -r 20 -t 2m --host http://localhost:8000
```

## 4) Comparar Padrões A vs. B
- Rode a API no Padrão A (REST + BD), execute os testes e salve os artefatos (summaryA.json).
- Reinicie no Padrão B (REST + Cache em memória), repita e salve (summaryB.json).
- Compare p95/p99 e throughput entre os dois arquivos. Exemplo rápido com `jq`:

```bash
jq '.metrics.http_req_duration' summaryA.json
jq '.metrics.http_req_duration' summaryB.json
```

## 5) Boas práticas do ensaio
- Faça aquecimento (warm-up) antes de medir.
- Repita cada cenário 5x e compute média/p95/p99 com IC 95% (planilha/Notebook).
- Fixe versões e registre commit do código para reprodutibilidade.
