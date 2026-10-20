import os
import sys
import tempfile
import warnings
from pathlib import Path

# Adiciona o diretório raiz ao sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import (
    get_connection, get_database_url, get_turso_auth_token,
    init_db, DB_PATH
)

def test_database_connections():
    print("Iniciando teste da Fase 3: Suporte flexivel a Banco de Dados / Nuvem...")

    # 1. Teste Conexao Padrao (financas.db)
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "TURSO_DATABASE_URL" in os.environ:
        del os.environ["TURSO_DATABASE_URL"]

    conn_default = get_connection()
    cur = conn_default.cursor()
    cur.execute("SELECT 1 as teste;")
    res = cur.fetchone()
    assert res["teste"] == 1, "Falha na conexao SQLite padrao"
    conn_default.close()
    print("[OK] Conexao padrao (financas.db) validada com sucesso.")

    # 2. Teste Conexao SQLite Personalizada via DATABASE_URL
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db_path = tmp.name

    try:
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
        assert get_database_url() == f"sqlite:///{tmp_db_path}"

        conn_custom = get_connection()
        cur_custom = conn_custom.cursor()
        cur_custom.execute("CREATE TABLE teste_custom (id INTEGER PRIMARY KEY, valor TEXT);")
        cur_custom.execute("INSERT INTO teste_custom (valor) VALUES ('nuvem_ok');")
        conn_custom.commit()

        cur_custom.execute("SELECT valor FROM teste_custom WHERE id = 1;")
        row = cur_custom.fetchone()
        assert row["valor"] == "nuvem_ok", "Falha na gravacao do banco customizado"
        conn_custom.close()
        print("[OK] Conexao SQLite personalizada via DATABASE_URL validada com sucesso.")
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass

    # 3. Teste Conexao Nuvem com Turso Cloud (DATABASE_URL + DATABASE_AUTH_TOKEN)
    os.environ["DATABASE_URL"] = "libsql://controle-financeiro-programzip.aws-sa-east-1.turso.io"
    os.environ["DATABASE_AUTH_TOKEN"] = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTI1Mjk5NjAsImlkIjoiMDFhMTVhZTYtMzcwMS03MDBjLWIwYzEtM2E2MGViOGMwODk5Iiwia2lkIjoiZm9BSzVoWFF2ZWZpOFoxeEJKbDIyVkZ0UGcxb1RUZi1FTFJxMlpQTHppQSIsInJpZCI6IjZlOTk0ODE2LWIwZDYtNDUyZC1hOThjLWIzMjgzZDdiYmZlMyJ9.pzj8X-Cd3cUKv1si7HVKyqpe2EK-aYWUhBDoLY0-9COq5pWeCy6IOe8qRAmwzF3GdhhPG2a9tZ2nHIc5PtJJCA"

    assert get_database_url() == "libsql://controle-financeiro-programzip.aws-sa-east-1.turso.io"
    assert get_turso_auth_token() is not None

    with get_connection() as conn_turso:
        cur_t = conn_turso.cursor()
        cur_t.execute("SELECT 1 as turso_live;")
        row_t = cur_t.fetchone()
        assert row_t["turso_live"] == 1
        print("[OK] Conexao real Turso Cloud validada com sucesso!")

    print("[SUCESSO] TESTE DA FASE 3 CONCLUIDO COM 100% DE EXITO!")

if __name__ == "__main__":
    test_database_connections()
