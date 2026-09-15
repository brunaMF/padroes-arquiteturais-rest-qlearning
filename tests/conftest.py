import pytest
import os
from app.config import settings

# Configurações para testes
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/tcc_learning_api_test")
