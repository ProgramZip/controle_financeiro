import os
import sqlite3
import hashlib
import warnings
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
# Carrega variáveis de ambiente do .env se existir
load_dotenv()

# Caminho absoluto da raiz do projeto e do banco financas.db padrão
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "financas.db"


def hash_password(password: str) -> str:
    """Gera hash SHA-256 seguro para senhas."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_database_url() -> str | None:
    """
    Retorna a URL/string de conexão com banco de dados se configurada via:
    1. Variável de ambiente DATABASE_URL ou TURSO_DATABASE_URL (.env)
    2. Streamlit secrets st.secrets['DATABASE_URL'] (se executando no Streamlit Cloud)
    """
    url = os.getenv("DATABASE_URL") or os.getenv("TURSO_DATABASE_URL")
    if url:
        return url.strip()
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "DATABASE_URL" in st.secrets:
                return str(st.secrets["DATABASE_URL"]).strip()
            if "TURSO_DATABASE_URL" in st.secrets:
                return str(st.secrets["TURSO_DATABASE_URL"]).strip()
            if "turso" in st.secrets:
                turso_sec = st.secrets["turso"]
                if "DATABASE_URL" in turso_sec:
                    return str(turso_sec["DATABASE_URL"]).strip()
                if "url" in turso_sec:
                    return str(turso_sec["url"]).strip()
    except Exception:
        pass
    return None


def get_database_auth_token() -> str | None:
    """
    Retorna o token de autenticação Turso se configurado via DATABASE_AUTH_TOKEN
    ou TURSO_AUTH_TOKEN (.env / st.secrets).
    """
    token = os.getenv("DATABASE_AUTH_TOKEN") or os.getenv("TURSO_AUTH_TOKEN")
    if token:
        return token.strip()
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "DATABASE_AUTH_TOKEN" in st.secrets:
                return str(st.secrets["DATABASE_AUTH_TOKEN"]).strip()
            if "TURSO_AUTH_TOKEN" in st.secrets:
                return str(st.secrets["TURSO_AUTH_TOKEN"]).strip()
            if "turso" in st.secrets:
                turso_sec = st.secrets["turso"]
                if "DATABASE_AUTH_TOKEN" in turso_sec:
                    return str(turso_sec["DATABASE_AUTH_TOKEN"]).strip()
                if "auth_token" in turso_sec:
                    return str(turso_sec["auth_token"]).strip()
    except Exception:
        pass
    return None


# Alias de retrocompatibilidade
get_turso_auth_token = get_database_auth_token
# =====================================================================
# ADAPTADORES TURSO / LIBSQL (Compatibilidade DB-API 2.0 com SQLite)
# =====================================================================

class LibsqlRow:
    """
    Emulador de sqlite3.Row para o driver libsql-client.
    Permite acesso por nome de coluna (row['id']), por índice numérico (row[0]),
    método .get() e conversão transparente para dicionário dict(row).
    """
    def __init__(self, raw_row):
        self._raw = raw_row
        self._dict = raw_row.asdict()

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._raw[item]
        return self._dict[item]

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def keys(self):
        return self._dict.keys()

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return repr(self._dict)


_TURSO_CLIENT = None
_TURSO_CLIENT_PARAMS = None


def _get_turso_client(url: str, token: str | None, force_new: bool = False):
    """Gerencia e reutiliza a instância do cliente HTTP do Turso de forma resiliente."""
    global _TURSO_CLIENT, _TURSO_CLIENT_PARAMS
    params_key = (url, token)
    if force_new and _TURSO_CLIENT is not None:
        try:
            _TURSO_CLIENT.close()
        except Exception:
            pass
        _TURSO_CLIENT = None

    if _TURSO_CLIENT is None or getattr(_TURSO_CLIENT, "closed", False) or _TURSO_CLIENT_PARAMS != params_key:
        import libsql_client
        _TURSO_CLIENT = libsql_client.create_client_sync(url, auth_token=token)
        _TURSO_CLIENT_PARAMS = params_key
    return _TURSO_CLIENT


class LibsqlCursor:
    """Cursor DB-API 2.0 compatível para o cliente Turso."""
    def __init__(self, client, url: str, token: str | None):
        self._client = client
        self._url = url
        self._token = token
        self._rs = None
        self._idx = 0

    def execute(self, sql: str, params: tuple | list = ()):
        p = list(params) if params else []
        try:
            self._rs = self._client.execute(sql, p)
        except Exception:
            # Reconexão resiliente se a sessão caiu
            self._client = _get_turso_client(self._url, self._token, force_new=True)
            self._rs = self._client.execute(sql, p)
        self._idx = 0
        return self

    def executemany(self, sql: str, seq_of_params):
        for params in seq_of_params:
            self.execute(sql, params)
        return self

    def fetchone(self):
        if not self._rs or not self._rs.rows or self._idx >= len(self._rs.rows):
            return None
        row = LibsqlRow(self._rs.rows[self._idx])
        self._idx += 1
        return row

    def fetchall(self):
        if not self._rs or not self._rs.rows:
            return []
        rows = [LibsqlRow(r) for r in self._rs.rows[self._idx:]]
        self._idx = len(self._rs.rows)
        return rows

    def __iter__(self):
        while True:
            row = self.fetchone()
            if row is None:
                break
            yield row

    @property
    def rowcount(self) -> int:
        return self._rs.rows_affected if self._rs is not None else 0

    @property
    def lastrowid(self):
        return self._rs.last_insert_rowid if self._rs is not None else None

    def close(self):
        pass


_SHARED_LIBSQL_CLIENT = None
_SHARED_LIBSQL_KEY = None


def _patch_libsql_executor_daemon():
    """Garante que threads internas do libsql_client sejam daemon, evitando bloqueio de shutdown."""
    try:
        import threading
        import collections
        import asyncio
        import libsql_client.sync

        if getattr(libsql_client.sync, "_daemon_patched", False):
            return

        def _daemon_init(self):
            self._thread = threading.Thread(target=self._run, name="libsql_client", daemon=True)
            self._loop = asyncio.new_event_loop()
            self._lock = threading.Lock()
            self._closed = False
            self._queue = collections.deque()
            self._waker = None
            self._thread.start()

        libsql_client.sync._AsyncExecutor.__init__ = _daemon_init
        libsql_client.sync._daemon_patched = True
    except Exception:
        pass


def get_shared_libsql_client(url: str, token: str | None):
    """
    Retorna cliente libsql-client com pooling HTTP persistente.
    Evita abrir e fechar novas conexões e loops a cada instrução SQL.
    """
    global _SHARED_LIBSQL_CLIENT, _SHARED_LIBSQL_KEY
    key = (url, token)
    if _SHARED_LIBSQL_CLIENT is None or _SHARED_LIBSQL_KEY != key:
        _patch_libsql_executor_daemon()
        import libsql_client
        if _SHARED_LIBSQL_CLIENT is not None:
            try:
                _SHARED_LIBSQL_CLIENT.close()
            except Exception:
                pass
        _SHARED_LIBSQL_CLIENT = libsql_client.create_client_sync(url, auth_token=token)
        _SHARED_LIBSQL_KEY = key
    return _SHARED_LIBSQL_CLIENT


def close_shared_libsql_client():
    """Fecha explicitamente o cliente compartilhado (usado em testes e reinicializações)."""
    global _SHARED_LIBSQL_CLIENT, _SHARED_LIBSQL_KEY
    if _SHARED_LIBSQL_CLIENT is not None:
        try:
            _SHARED_LIBSQL_CLIENT.close()
        except Exception:
            pass
        _SHARED_LIBSQL_CLIENT = None
        _SHARED_LIBSQL_KEY = None


class LibsqlConnection:
    """Conexão compatível com SQLite para operações transparentes no Turso Cloud com pool HTTP persistente."""
    def __init__(self, url: str, token: str | None, client=None):
        self._url = url
        self._token = token
        if client is not None:
            self._client = client
            self._is_shared = False
        else:
            self._client = get_shared_libsql_client(url, token)
            self._is_shared = True

    def cursor(self):
        return LibsqlCursor(self._client, self._url, self._token)

    def execute(self, sql: str, params: tuple | list = ()):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        # Clientes compartilhados mantêm o pool HTTP keep-alive aberto para máxima performance
        if not getattr(self, "_is_shared", False):
            try:
                self._client.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_connection():
    """
    Retorna uma conexão ativa com o banco de dados com Row factory ativado.
    Suporta:
    1. Nuvem (Turso / LibSQL): Quando DATABASE_URL inicia com 'libsql://', 'https://' ou 'turso.io'.
       Conecta ao Turso Cloud utilizando o driver oficial 'libsql-client'.
    2. SQLite Personalizado: Quando DATABASE_URL aponta para 'sqlite:///...' ou arquivo local.
    3. SQLite Padrão Local (financas.db): Padrão automático offline quando DATABASE_URL não é informada.
    """
    db_url = get_database_url()

    if db_url:
        # Caso 1: Conexão Turso Cloud / LibSQL em Nuvem
        if db_url.startswith("libsql://") or db_url.startswith("https://") or "turso.io" in db_url:
            auth_token = get_database_auth_token()
            http_url = db_url
            if http_url.startswith("libsql://"):
                http_url = "https://" + http_url[len("libsql://"):]

            try:
                import libsql_client
                return LibsqlConnection(http_url, auth_token)
            except ImportError:
                warnings.warn(
                    "DATABASE_URL de nuvem (Turso) detectada, mas a biblioteca 'libsql-client' "
                    "não está instalada no ambiente. Usando banco SQLite local como fallback defensivo. "
                    "Para ativar a persistência em nuvem, adicione 'libsql-client' ao seu requirements.txt."
                )

        # Caso 2: Conexão SQLite local personalizada
        elif db_url.startswith("sqlite:///"):
            custom_path = db_url.replace("sqlite:///", "")
            conn = sqlite3.connect(custom_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        elif not db_url.startswith("http"):
            conn = sqlite3.connect(db_url)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn

    # Caso 3: SQLite padrão local (financas.db)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


_DB_INITIALIZED = False


def init_db(force: bool = False):
    """
    Inicializa o banco de dados criando as 5 tabelas estruturais
    e criando o usuário padrão admin / admin123 caso ainda não exista.
    Possui memoização em processo para evitar round-trips de rede a cada rerun do Streamlit.
    """
    global _DB_INITIALIZED
    if _DB_INITIALIZED and not force:
        return

    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'editor', 'viewer')),
                full_name TEXT,
                address TEXT,
                cpf TEXT,
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

        # 7. recurring_dismissals (Controle de exclusões manuais de contas recorrentes por mês)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_dismissals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recurring_ref TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, recurring_ref, description, category, type)
            );
        """)

        # Migração defensiva: associar registros antigos sem user_id ao usuário admin (ID 1)
        cursor.execute("UPDATE transactions SET user_id = 1 WHERE user_id IS NULL;")
        cursor.execute("UPDATE recurring_bills SET user_id = 1 WHERE user_id IS NULL;")
        cursor.execute("UPDATE investments SET user_id = 1 WHERE user_id IS NULL;")

        # Migração defensiva: adicionar colunas de perfil expandido na tabela users se não existirem
        cursor.execute("PRAGMA table_info(users);")
        col_names = [col["name"] for col in cursor.fetchall()]
        if "full_name" not in col_names:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT;")
        if "address" not in col_names:
            cursor.execute("ALTER TABLE users ADD COLUMN address TEXT;")
        if "cpf" not in col_names:
            cursor.execute("ALTER TABLE users ADD COLUMN cpf TEXT;")

        # Criar usuário padrão admin se não existir
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone() is None:
            default_pass_hash = hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, ("admin", default_pass_hash, "admin"))

        conn.commit()

    _DB_INITIALIZED = True


def verify_user(username: str, password: str):
    """
    Verifica credenciais de usuário.
    Retorna o dicionário com dados do usuário se válido, ou None se inválido.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        pwd_hash = hash_password(password)
        cursor.execute("""
            SELECT id, username, role, full_name, address, cpf, created_at
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, pwd_hash))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int):
    """Retorna os dados cadastrais do usuário (sem a senha)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, role, full_name, address, cpf, created_at
            FROM users
            WHERE id = ?
        """, (int(user_id),))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user_password(user_id: int, new_password: str) -> bool:
    """Atualiza a senha do usuário gravando o novo hash SHA-256."""
    if not new_password or len(new_password.strip()) < 4:
        raise ValueError("A nova senha deve ter pelo menos 4 caracteres.")
    pwd_hash = hash_password(new_password.strip())
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, int(user_id)))
        conn.commit()
        return cursor.rowcount > 0


def change_password_with_verification(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    """
    Valida a senha atual do usuário e, se correta, atualiza para a nova senha com hash SHA-256.
    Retorna uma tupla (sucesso: bool, mensagem: str).
    """
    if not current_password:
        return False, "Informe a senha atual."
    if not new_password or len(new_password.strip()) < 4:
        return False, "A nova senha deve ter no mínimo 4 caracteres."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (int(user_id),))
        row = cursor.fetchone()
        if not row:
            return False, "Usuário não encontrado."

        current_hash = hash_password(current_password.strip())
        if row["password_hash"] != current_hash:
            return False, "A senha atual informada está incorreta."

        new_hash = hash_password(new_password.strip())
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, int(user_id)))
        conn.commit()
        return True, "Senha alterada com sucesso!"


if __name__ == "__main__":
    init_db()
    print("Banco de dados financas.db inicializado com sucesso!")