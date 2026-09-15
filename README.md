# API RESTful com Q-learning para Personalização Educacional

Este projeto implementa um MVP de API RESTful integrada a um agente de aprendizado por reforço (Q-learning) para personalização de conteúdo educacional, comparando duas estratégias de gerenciamento de estado: **REST + Banco de Dados** e **REST + Cache em Memória**.

## 📋 Estrutura do Projeto

```
tcc-mba/
├── app/                        # Código da API
│   ├── main.py                 # Aplicação FastAPI principal
│   ├── config.py               # Configurações (STATE_STRATEGY)
│   ├── database.py             # Engine e sessão SQLAlchemy
│   ├── models/                 # Modelos ORM
│   │   ├── user.py
│   │   └── qlearning.py
│   ├── schemas/                # Schemas Pydantic (contratos REST)
│   │   ├── auth.py
│   │   └── recommendation.py
│   ├── services/               # Lógica de negócio
│   │   ├── qlearning_agent.py  # Agente Q-learning
│   │   ├── state_db.py         # Estratégia Padrão A (PostgreSQL)
│   │   └── state_cache.py      # Estratégia Padrão B (memória)
│   └── api/                    # Endpoints
│       ├── auth.py
│       └── recommendations.py
├── tests/                      # 24 testes automatizados (pytest)
│   ├── conftest.py
│   ├── test_endpoints.py       # Contrato REST
│   ├── test_qlearning.py       # Lógica do agente
│   ├── test_state_strategies.py # Paridade entre as estratégias
│   └── locustfile.py           # Cenário de carga (Locust)
├── scripts/                    # Scripts de apoio e medição
│   ├── test_latency.py         # Teste de latência individual
│   ├── analyze_results.py      # Análise dos resultados
│   ├── analyze_locust_results.py
│   ├── compare_strategies.py
│   ├── generate_tables.py      # Geração das tabelas do trabalho
│   ├── create_database.py      # Criação do banco
│   ├── init_db.py
│   └── diagnostico_api.py
├── results/                    # Dados brutos do experimento
│   ├── latency/                # JSONs do teste de latência
│   ├── locust/                 # CSVs dos testes de carga
│   ├── figures/                # Gráficos gerados pelo Locust
│   └── tables/                 # Tabelas do trabalho (PNG)
├── docs/tcc/                   # Documentos do trabalho (fora do versionamento)
├── .env.example
├── requirements.txt
├── pytest.ini
└── README.md
```

## 🚀 Instalação

1. **Clone o repositório** (se aplicável)

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Configure o banco de dados PostgreSQL:**
```bash
# Crie o banco de dados
createdb tcc_learning_api

# Ou use o SQLAlchemy para criar as tabelas automaticamente
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tcc_learning_api

# JWT
SECRET_KEY=sua-chave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_PREFIX=/api/v1
ENVIRONMENT=development

# Strategy (db ou cache)
STATE_STRATEGY=db
```

## 🏃 Executando a Aplicação

### Modo Desenvolvimento

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Produção

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

A API estará disponível em: `http://localhost:8000`

## 📚 Documentação da API

Após iniciar a aplicação, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 Autenticação

A API utiliza JWT (JSON Web Tokens) para autenticação. Para obter um token:

```bash
POST /api/v1/auth/login
{
  "username": "usuario",
  "password": "senha"
}
```

Use o token retornado no header das requisições:
```
Authorization: Bearer <token>
```

## 🧪 Testes

### Testes Unitários

```bash
pytest tests/ -v
```

### Testes de Carga com Locust

```bash
locust -f tests/locustfile.py --host=http://localhost:8000
```

### Testes de Carga com k6

```bash
k6 run tests/k6_load_test.js
```

## 📊 Estratégias de Estado

### Padrão A: REST + Banco de Dados
- Estado persistido em PostgreSQL
- Garante durabilidade e consistência
- Configuração: `STATE_STRATEGY=db`

### Padrão B: REST + Cache em Memória
- Estado mantido em memória (Redis ou dict)
- Menor latência, maior throughput
- Configuração: `STATE_STRATEGY=cache`

## 🎯 Endpoints Principais

- `POST /api/v1/auth/register` - Registrar novo usuário
- `POST /api/v1/auth/login` - Autenticar e obter token
- `GET /api/v1/recommendations/{user_id}` - Obter recomendação personalizada
- `POST /api/v1/recommendations/feedback` - Enviar feedback do usuário
- `GET /api/v1/recommendations/stats/{user_id}` - Estatísticas do agente

## 📈 Métricas de Desempenho

O projeto coleta as seguintes métricas:
- Latência média (ms)
- Percentis p95 e p99 (ms)
- Throughput (req/s)
- Taxa de erro (%)

## 🔬 Resultados Preliminares

Este MVP serve como base para comparação das duas estratégias arquiteturais, permitindo análise quantitativa e qualitativa dos trade-offs entre performance, persistência e simplicidade.

## 📝 Licença

Este projeto é parte de um trabalho de conclusão de curso (TCC) e destina-se a fins acadêmicos.

## 👥 Autor

Desenvolvido como parte do TCC em Engenharia de Software - MBA.
