#!/usr/bin/env python3
"""
Script melhorado para criar banco de dados e tabelas.
Funciona mesmo se o banco não existir.
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import Base, engine
from app.config import settings
from app.models.user import User
from app.models.qlearning import QLearningState

def create_database_if_not_exists():
    """Cria o banco de dados se não existir"""
    # Extrai informações da URL
    db_url = settings.DATABASE_URL
    
    # Para PostgreSQL, precisamos conectar ao banco 'postgres' primeiro
    if db_url.startswith('postgresql'):
        # Extrai informações da URL
        # Formato: postgresql://user:password@host:port/database
        parts = db_url.replace('postgresql://', '').split('/')
        if len(parts) == 2:
            db_name = parts[1].split('?')[0]  # Remove query params
            base_url = f"postgresql://{parts[0]}/postgres"
            
            try:
                # Conecta ao banco 'postgres' para criar o banco
                temp_engine = create_engine(base_url)
                with temp_engine.connect() as conn:
                    # Verifica se o banco existe
                    result = conn.execute(
                        text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
                    )
                    exists = result.fetchone()
                    
                    if not exists:
                        # Cria o banco
                        conn.execute(text("COMMIT"))  # Termina transação
                        conn.execute(text(f"CREATE DATABASE {db_name}"))
                        print(f"✓ Banco de dados '{db_name}' criado!")
                    else:
                        print(f"✓ Banco de dados '{db_name}' já existe!")
            except Exception as e:
                print(f"⚠️  Não foi possível criar banco automaticamente: {e}")
                print(f"   Crie manualmente: CREATE DATABASE {db_name};")
    elif db_url.startswith('sqlite'):
        # SQLite cria automaticamente
        print("✓ SQLite criará o banco automaticamente")

def main():
    """Inicializa o banco de dados"""
    print("=" * 60)
    print("INICIALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    print(f"\nURL do banco: {settings.DATABASE_URL}")
    
    # Tenta criar o banco se não existir
    print("\n1. Verificando se o banco existe...")
    create_database_if_not_exists()
    
    # Importa todos os modelos para que sejam registrados
    print("\n2. Importando modelos...")
    from app.models import User, QLearningState
    print("   ✓ User")
    print("   ✓ QLearningState")
    
    # Cria as tabelas
    print("\n3. Criando tabelas...")
    try:
        Base.metadata.create_all(bind=engine)
        print("   ✓ Tabelas criadas com sucesso!")
        
        # Lista as tabelas criadas
        print("\n4. Tabelas criadas:")
        with engine.connect() as conn:
            if 'postgresql' in settings.DATABASE_URL:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
            else:  # SQLite
                result = conn.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table'
                """))
            
            tables = [row[0] for row in result]
            for table in tables:
                print(f"   - {table}")
        
        print("\n" + "=" * 60)
        print("✓ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Erro ao criar tabelas: {e}")
        print("\nPossíveis causas:")
        print("1. Banco de dados não existe - crie manualmente")
        print("2. Credenciais incorretas no .env")
        print("3. PostgreSQL não está rodando")
        print("4. Sem permissão para criar tabelas")
        print("\nSolução:")
        print("1. Verifique se PostgreSQL está rodando")
        print("2. Crie o banco: CREATE DATABASE tcc_learning_api;")
        print("3. Verifique as credenciais no arquivo .env")
        sys.exit(1)

if __name__ == "__main__":
    main()
