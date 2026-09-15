#!/usr/bin/env python3
"""
Script para inicializar o banco de dados.
Cria as tabelas necessárias.
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine
from app.config import settings

def main():
    """Inicializa o banco de dados"""
    print(f"Inicializando banco de dados: {settings.DATABASE_URL}")
    print("Criando tabelas...")
    
    try:
        init_db()
        print("✓ Banco de dados inicializado com sucesso!")
        print(f"✓ Tabelas criadas: users, qlearning_states")
    except Exception as e:
        print(f"✗ Erro ao inicializar banco de dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
