from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import api_router

# Cria aplicação FastAPI
app = FastAPI(
    title="API RESTful com Q-learning para Personalização Educacional",
    description="""
    MVP de API RESTful integrada a um agente de aprendizado por reforço (Q-learning) 
    para personalização de conteúdo educacional.
    
    Compara duas estratégias de gerenciamento de estado:
    - REST + Banco de Dados (PostgreSQL)
    - REST + Cache em Memória
    
    ## Autenticação
    
    A API utiliza JWT para autenticação. Para obter um token:
    1. Registre um usuário em `/api/v1/auth/register`
    2. Faça login em `/api/v1/auth/login`
    3. Use o token retornado no header: `Authorization: Bearer <token>`
    
    ## Endpoints Principais
    
    - `GET /api/v1/recommendations/{user_id}` - Obter recomendação personalizada
    - `POST /api/v1/recommendations/feedback` - Enviar feedback do usuário
    - `GET /api/v1/recommendations/stats/{user_id}` - Estatísticas do agente
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui rotas da API
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Inicializa banco de dados na inicialização da aplicação"""
    if settings.STATE_STRATEGY == "db":
        init_db()


@app.get("/")
def root():
    """Endpoint raiz"""
    return {
        "message": "API RESTful com Q-learning para Personalização Educacional",
        "version": "0.1.0",
        "docs": "/docs",
        "state_strategy": settings.STATE_STRATEGY
    }


@app.get("/health")
def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "state_strategy": settings.STATE_STRATEGY,
        "environment": settings.ENVIRONMENT
    }
