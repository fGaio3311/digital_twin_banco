import os
import sys
from pymongo import MongoClient
from datetime import datetime
import subprocess
import shutil

def check_mongodb_running():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        return True
    except Exception:
        return False

def create_collections():
    client = MongoClient("mongodb://localhost:27017/")
    db = client.digital_twin

    # Criar coleções com validação
    db.create_collection("users")
    db.users.create_index("username", unique=True)

    db.create_collection("transactions")
    db.transactions.create_index("user_id")
    db.transactions.create_index("created_at")

    db.create_collection("logs")
    db.logs.create_index([("user_id", 1), ("timestamp", -1)])

    print("✅ Coleções criadas com sucesso!")

def backup_sqlite():
    src = "digital_twin.db"
    if os.path.exists(src):
        backup_name = f"digital_twin_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(src, backup_name)
        print(f"✅ Backup do SQLite criado: {backup_name}")

def main():
    print("🚀 Iniciando setup do MongoDB...")

    # Verificar MongoDB
    if not check_mongodb_running():
        print("❌ MongoDB não está rodando! Por favor:")
        print("1. Instale o MongoDB Community Server")
        print("2. Inicie o serviço do MongoDB")
        print("3. Execute este script novamente")
        sys.exit(1)

    print("✅ MongoDB está rodando!")

    # Criar coleções
    try:
        create_collections()
    except Exception as e:
        print(f"❌ Erro ao criar coleções: {e}")
        sys.exit(1)

    # Backup SQLite
    print("📦 Criando backup do SQLite...")
    backup_sqlite()

    # Executar migração
    print("🔄 Executando migração dos dados...")
    try:
        subprocess.run([sys.executable, "scripts/migrate_to_mongo.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)

    print("\n✨ Setup concluído! Próximos passos:")
    print("1. Atualize o .env com MONGODB_URL=mongodb://localhost:27017")
    print("2. Inicie a API com: python main_mongo.py")
    print("3. Teste os endpoints principais")

if __name__ == "__main__":
    main()
