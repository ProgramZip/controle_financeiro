import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

# Caminho absoluto da raiz do projeto e do banco financas.db
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "financas.db"


def hash_password(password: str) -> str:
    """Gera hash SHA-256 seguro para senhas."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection():
    """Retorna uma conexão com o banco SQLite com Row factory ativado."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Inicializa o banco de dados criando as 5 tabelas estruturais
    e criando o usuário padrão admin / admin123 caso ainda não exista.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'editor', 'viewer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL CHECK(type IN ('despesa', 'receita')),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL CHECK(payment_method IN ('À Vista', 'Parcelado')),
                installment_current INTEGER DEFAULT 1,
                installment_total INTEGER DEFAULT 1,
                group_id TEXT,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Pago', 'Recebido', 'Pendente')),
                invoice_path TEXT,
                is_recurring INTEGER DEFAULT 0,
                recurring_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 3. recurring_bills
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL CHECK(type IN ('despesa', 'receita')),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                due_day INTEGER NOT NULL CHECK(due_day BETWEEN 1 AND 31),
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 4. investments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                asset_name TEXT NOT NULL,
                category TEXT NOT NULL,
                invested_amount REAL NOT NULL,
                current_value REAL NOT NULL,
                update_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 5. budgets
        cursor.execute("PRAGMA table_info(budgets)")
        budget_cols = [c[1] for c in cursor.fetchall()]
        if budget_cols and "user_id" not in budget_cols:
            cursor.execute("DROP TABLE IF EXISTS budgets")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, category)
            );
        """)

        # 6. user_shares (Partilhamento de Espaço entre Usuários)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                shared_with_user_id INTEGER NOT NULL,
                permission_level TEXT NOT NULL CHECK(permission_level IN ('viewer', 'editor')) DEFAULT 'viewer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(owner_id, shared_with_user_id)
            );
        """)

        # Migração defensiva: associar registros antigos sem user_id ao usuário admin (ID 1)
        cursor.execute("UPDATE transactions SET user_id = 1 WHERE user_id IS NULL;")
        cursor.execute("UPDATE recurring_bills SET user_id = 1 WHERE user_id IS NULL;")
        cursor.execute("UPDATE investments SET user_id = 1 WHERE user_id IS NULL;")

        # Criar usuário padrão admin se não existir
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone() is None:
            default_pass_hash = hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, ("admin", default_pass_hash, "admin"))

        conn.commit()


def verify_user(username: str, password: str):
    """
    Verifica credenciais de usuário.
    Retorna o dicionário com dados do usuário se válido, ou None se inválido.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        pwd_hash = hash_password(password)
        cursor.execute("""
            SELECT id, username, role, created_at
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, pwd_hash))
        row = cursor.fetchone()
        return dict(row) if row else None


if __name__ == "__main__":
    init_db()
    print("Banco de dados financas.db inicializado com sucesso!")
