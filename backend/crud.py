import uuid
import calendar
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from backend.database import (
    get_connection, hash_password, get_user_by_id,
    update_user_password, change_password_with_verification
)


# =====================================================================
# FUNÇÕES AUXILIARES DE DATAS E ACESSO
# =====================================================================

def _add_months_to_date(base_date_str: str, months_to_add: int) -> str:
    """
    Soma meses a uma data em formato 'YYYY-MM-DD' preservando o dia se possível
    ou ajustando para o último dia válido do mês de destino.
    """
    dt = datetime.strptime(base_date_str, "%Y-%m-%d").date()
    new_dt = dt + relativedelta(months=months_to_add)
    return new_dt.strftime("%Y-%m-%d")


def _get_due_date_for_month(year: int, month: int, due_day: int) -> str:
    """Calcula a data de vencimento válida dado ano, mês e dia desejado."""
    max_days = calendar.monthrange(year, month)[1]
    safe_day = min(due_day, max_days)
    return f"{year:04d}-{month:02d}-{safe_day:02d}"


# =====================================================================
# GESTÃO DE PARTILHAMENTO (user_shares) E ACESSO MULTI-USUÁRIO
# =====================================================================

def get_accessible_user_ids(user_id: int) -> list[int]:
    """
    Retorna a lista de IDs de usuários cujos registros o user_id logado tem permissão para visualizar.
    Sempre inclui o próprio user_id.
    Inclui os owner_id que compartilharam seu espaço com shared_with_user_id == user_id.
    """
    if user_id is None:
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT owner_id FROM user_shares
            WHERE shared_with_user_id = ?
        """, (int(user_id),))
        rows = cursor.fetchall()
        accessible = {int(user_id)}
        for r in rows:
            accessible.add(int(r["owner_id"]))
        return list(accessible)


def get_user_shares_by_owner(owner_id: int):
    """
    Lista todos os compartilhamentos concedidos pelo owner_id (com quem ele compartilhou).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.owner_id, s.shared_with_user_id, s.permission_level, s.created_at,
                   u.username AS shared_with_username, u.role AS shared_with_role
            FROM user_shares s
            JOIN users u ON s.shared_with_user_id = u.id
            WHERE s.owner_id = ?
            ORDER BY s.created_at DESC
        """, (int(owner_id),))
        return [dict(r) for r in cursor.fetchall()]


def get_user_shares_received(shared_with_user_id: int):
    """
    Lista todos os compartilhamentos que este usuário recebeu de outros proprietários.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.owner_id, s.shared_with_user_id, s.permission_level, s.created_at,
                   u.username AS owner_username, u.role AS owner_role
            FROM user_shares s
            JOIN users u ON s.owner_id = u.id
            WHERE s.shared_with_user_id = ?
            ORDER BY s.created_at DESC
        """, (int(shared_with_user_id),))
        return [dict(r) for r in cursor.fetchall()]


def add_user_share(owner_id: int, shared_with_user_id: int, permission_level: str = "viewer") -> bool:
    """
    Cria ou atualiza um compartilhamento de espaço entre usuários.
    permission_level: 'viewer' ou 'editor'.
    """
    if int(owner_id) == int(shared_with_user_id):
        raise ValueError("Um usuário não pode compartilhar o espaço consigo mesmo.")

    if permission_level not in ("viewer", "editor"):
        raise ValueError("Nível de permissão inválido. Escolha 'viewer' ou 'editor'.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_shares (owner_id, shared_with_user_id, permission_level)
            VALUES (?, ?, ?)
            ON CONFLICT(owner_id, shared_with_user_id)
            DO UPDATE SET permission_level = excluded.permission_level
        """, (int(owner_id), int(shared_with_user_id), permission_level))
        conn.commit()
        return True


def delete_user_share(share_id: int, owner_id: int = None) -> bool:
    """
    Remove um compartilhamento existente. Se owner_id for fornecido, valida propriedade.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if owner_id is not None:
            cursor.execute("DELETE FROM user_shares WHERE id = ? AND owner_id = ?", (share_id, int(owner_id)))
        else:
            cursor.execute("DELETE FROM user_shares WHERE id = ?", (share_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_user_permission(owner_id: int, user_id: int) -> str | None:
    """
    Retorna o nível de permissão que user_id tem sobre os dados de owner_id.
    - 'owner': se for o mesmo usuário
    - 'editor' ou 'viewer': se compartilhado
    - None: sem acesso
    """
    if int(user_id) == int(owner_id):
        return "owner"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT permission_level FROM user_shares
            WHERE owner_id = ? AND shared_with_user_id = ?
        """, (int(owner_id), int(user_id)))
        row = cursor.fetchone()
        return row["permission_level"] if row else None


def can_user_edit_resource(user_id: int, resource_owner_id: int) -> bool:
    """
    Valida se user_id tem permissão para editar/excluir dados de resource_owner_id.
    """
    if user_id is None:
        return True
    if int(user_id) == int(resource_owner_id):
        return True

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (int(user_id),))
        u = cursor.fetchone()
        if u and u["role"] == "admin":
            return True

        cursor.execute("""
            SELECT permission_level FROM user_shares
            WHERE owner_id = ? AND shared_with_user_id = ?
        """, (int(resource_owner_id), int(user_id)))
        share = cursor.fetchone()
        return bool(share and share["permission_level"] == "editor")


# =====================================================================
# CRUD: TRANSAÇÕES (DESPESAS E RECEITAS)
# =====================================================================

def add_transaction(
    user_id: int,
    trans_type: str,
    category: str,
    description: str,
    amount: float,
    payment_method: str = "À Vista",
    installment_total: int = 1,
    due_date: str = None,
    status: str = "Pendente",
    invoice_path: str = None,
    is_recurring: int = 0,
    recurring_ref: str = None,
    group_id: str = None
) -> str:
    """
    Insere transação (despesa ou receita) vinculada estritamente ao user_id informado.
    Se pagamento for 'Parcelado' com installment_total > 1, gera automaticamente todas as parcelas
    com as datas calculadas mensalmente, vinculadas pelo mesmo group_id.
    Retorna o group_id gerado.
    """
    if due_date is None:
        due_date = date.today().strftime("%Y-%m-%d")

    assigned_group_id = group_id or str(uuid.uuid4())

    with get_connection() as conn:
        cursor = conn.cursor()

        if payment_method == "Parcelado" and installment_total > 1:
            base_installment_val = round(amount / installment_total, 2)
            # Diferença de arredondamento colocada na 1ª parcela
            diff = round(amount - (base_installment_val * installment_total), 2)

            for i in range(1, installment_total + 1):
                cur_amount = round(base_installment_val + (diff if i == 1 else 0.0), 2)
                cur_due_date = _add_months_to_date(due_date, i - 1)
                cur_ref = cur_due_date[:7]
                # Apenas a 1ª parcela herda o status informado. As parcelas futuras iniciam Pendentes.
                cur_status = status if i == 1 else "Pendente"

                cursor.execute("""
                    INSERT INTO transactions (
                        user_id, type, category, description, amount,
                        payment_method, installment_current, installment_total,
                        group_id, due_date, status, invoice_path,
                        is_recurring, recurring_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(user_id), trans_type, category, description, cur_amount,
                    payment_method, i, installment_total,
                    assigned_group_id, cur_due_date, cur_status, invoice_path if i == 1 else None,
                    is_recurring, cur_ref
                ))
        else:
            ref = recurring_ref or due_date[:7]
            cursor.execute("""
                INSERT INTO transactions (
                    user_id, type, category, description, amount,
                    payment_method, installment_current, installment_total,
                    group_id, due_date, status, invoice_path,
                    is_recurring, recurring_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(user_id), trans_type, category, description, round(amount, 2),
                payment_method, 1, 1,
                assigned_group_id, due_date, status, invoice_path,
                is_recurring, ref
            ))

        conn.commit()

    return assigned_group_id


def get_transactions(
    user_id: int = None,
    trans_type: str = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    group_id: str = None,
    search: str = None,
    include_shared: bool = False
):
    """
    Retorna lista de movimentações com filtros opcionais.
    POR PADRÃO (include_shared=False): filtra ESTRITAMENTE pelo próprio user_id logado.
    Se include_shared=True: expande para incluir dados de espaços compartilhados.
    """
    query = """
        SELECT t.*, u.username AS owner_username
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id is not None:
        if include_shared:
            accessible_ids = get_accessible_user_ids(user_id)
            if accessible_ids:
                placeholders = ", ".join(["?"] * len(accessible_ids))
                query += f" AND t.user_id IN ({placeholders})"
                params.extend(accessible_ids)
            else:
                query += " AND 1=0"
        else:
            query += " AND t.user_id = ?"
            params.append(int(user_id))

    if trans_type is not None:
        query += " AND t.type = ?"
        params.append(trans_type)

    if status is not None:
        query += " AND t.status = ?"
        params.append(status)

    if start_date is not None:
        query += " AND t.due_date >= ?"
        params.append(start_date)

    if end_date is not None:
        query += " AND t.due_date <= ?"
        params.append(end_date)

    if category is not None:
        query += " AND t.category = ?"
        params.append(category)

    if group_id is not None:
        query += " AND t.group_id = ?"
        params.append(group_id)

    if search:
        query += " AND (t.description LIKE ? OR t.category LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term])

    query += " ORDER BY t.due_date DESC, t.id DESC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def update_transaction_status(transaction_id: int, new_status: str, requesting_user_id: int = None) -> bool:
    """Ação rápida em 1 clique para alterar o status da transação (ex: Pendente -> Pago/Recebido)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,))
            t = cursor.fetchone()
            if t and not can_user_edit_resource(requesting_user_id, t["user_id"]):
                return False

        cursor.execute("""
            UPDATE transactions
            SET status = ?
            WHERE id = ?
        """, (new_status, transaction_id))
        conn.commit()
        return cursor.rowcount > 0


def revert_transaction_to_pending(transaction_id: int, requesting_user_id: int = None) -> bool:
    """Reverte o status de uma conta paga ou recebida de volta para 'Pendente'."""
    return update_transaction_status(transaction_id, "Pendente", requesting_user_id=requesting_user_id)


def get_transaction_by_id(transaction_id: int):
    """Retorna uma única transação pelo ID ou None."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (int(transaction_id),))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_transaction(transaction_id: int, requesting_user_id: int = None, **kwargs) -> bool:
    """Atualiza campos específicos de uma transação."""
    allowed_fields = {
        "type", "category", "description", "amount", "payment_method",
        "due_date", "status", "invoice_path"
    }
    updates = []
    params = []

    for key, val in kwargs.items():
        if key in allowed_fields:
            updates.append(f"{key} = ?")
            params.append(val)

    if not updates:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,))
            t = cursor.fetchone()
            if t and not can_user_edit_resource(requesting_user_id, t["user_id"]):
                return False

        params.append(transaction_id)
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0


def delete_transaction(transaction_id: int, user_id: int = None, requesting_user_id: int = None) -> bool:
    """
    Exclui uma transação individual com verificação de permissão do usuário.
    Se a transação for recorrente, registra em recurring_dismissals para não ser regenerada automaticamente.
    """
    u_id = user_id if user_id is not None else requesting_user_id
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, is_recurring, recurring_ref, description, category, type 
            FROM transactions 
            WHERE id = ?
        """, (transaction_id,))
        t = cursor.fetchone()
        if not t:
            return False

        if u_id is not None and not can_user_edit_resource(u_id, t["user_id"]):
            return False

        # Se for conta gerada por recorrência, registrar dispensa para não regenerar no mesmo mês
        if t["is_recurring"] and t["recurring_ref"]:
            cursor.execute("""
                INSERT OR IGNORE INTO recurring_dismissals (
                    user_id, recurring_ref, description, category, type
                ) VALUES (?, ?, ?, ?, ?)
            """, (t["user_id"], t["recurring_ref"], t["description"], t["category"], t["type"]))

        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0


def delete_transactions_by_month(user_id: int, year_month: str) -> int:
    """
    Remove todos os lançamentos pertencentes ao user_id para o mês específico (formato 'YYYY-MM').
    Registra dispensas para transações recorrentes apagadas para não regenerar no mesmo mês.
    """
    if not year_month or len(year_month) != 7 or "-" not in year_month:
        raise ValueError("Formato de mês inválido. Use 'YYYY-MM'.")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Registra dispensas das transações recorrentes que serão apagadas
        cursor.execute("""
            SELECT user_id, recurring_ref, description, category, type
            FROM transactions
            WHERE user_id = ?
              AND substr(due_date, 1, 7) = ?
              AND is_recurring = 1
        """, (int(user_id), year_month))
        for r in cursor.fetchall():
            ref = r["recurring_ref"] or year_month
            cursor.execute("""
                INSERT OR IGNORE INTO recurring_dismissals (
                    user_id, recurring_ref, description, category, type
                ) VALUES (?, ?, ?, ?, ?)
            """, (r["user_id"], ref, r["description"], r["category"], r["type"]))

        cursor.execute("""
            DELETE FROM transactions
            WHERE user_id = ?
              AND substr(due_date, 1, 7) = ?
        """, (int(user_id), year_month))
        conn.commit()
        return cursor.rowcount


def delete_transaction_group(group_id: str, requesting_user_id: int = None) -> int:
    """Exclui todas as parcelas pertencentes a um group_id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM transactions WHERE group_id = ? LIMIT 1", (group_id,))
            t = cursor.fetchone()
            if t and not can_user_edit_resource(requesting_user_id, t["user_id"]):
                return 0

        cursor.execute("DELETE FROM transactions WHERE group_id = ?", (group_id,))
        conn.commit()
        return cursor.rowcount


# =====================================================================
# CRUD: CONTAS MENSAIS RECORRENTES (recurring_bills)
# =====================================================================

def add_recurring_bill(
    user_id: int,
    bill_type: str,
    category: str,
    description: str,
    amount: float,
    due_day: int,
    is_active: int = 1
) -> int:
    """Cadastra uma conta ou recebimento fixo mensal vinculado ao user_id informado."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recurring_bills (
                user_id, type, category, description, amount, due_day, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (int(user_id), bill_type, category, description, round(amount, 2), due_day, is_active))
        conn.commit()
        return cursor.lastrowid


def get_recurring_bills(user_id: int = None, is_active: int = None, include_shared: bool = False):
    """
    Lista as contas recorrentes cadastradas.
    POR PADRÃO (include_shared=False): filtra ESTRITAMENTE pelo próprio user_id logado.
    """
    query = """
        SELECT r.*, u.username AS owner_username
        FROM recurring_bills r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id is not None:
        if include_shared:
            accessible_ids = get_accessible_user_ids(user_id)
            if accessible_ids:
                placeholders = ", ".join(["?"] * len(accessible_ids))
                query += f" AND r.user_id IN ({placeholders})"
                params.extend(accessible_ids)
            else:
                query += " AND 1=0"
        else:
            query += " AND r.user_id = ?"
            params.append(int(user_id))

    if is_active is not None:
        query += " AND r.is_active = ?"
        params.append(is_active)

    query += " ORDER BY r.due_day ASC, r.id ASC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def update_recurring_bill(bill_id: int, requesting_user_id: int = None, **kwargs) -> bool:
    """Atualiza dados de uma conta recorrente."""
    allowed = {"type", "category", "description", "amount", "due_day", "is_active"}
    updates = []
    params = []

    for k, v in kwargs.items():
        if k in allowed:
            updates.append(f"{k} = ?")
            params.append(v)

    if not updates:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM recurring_bills WHERE id = ?", (bill_id,))
            b = cursor.fetchone()
            if b and not can_user_edit_resource(requesting_user_id, b["user_id"]):
                return False

        params.append(bill_id)
        cursor.execute(f"UPDATE recurring_bills SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def delete_recurring_bill(bill_id: int, requesting_user_id: int = None) -> bool:
    """Exclui uma conta recorrente da matriz."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM recurring_bills WHERE id = ?", (bill_id,))
            b = cursor.fetchone()
            if b and not can_user_edit_resource(requesting_user_id, b["user_id"]):
                return False

        cursor.execute("DELETE FROM recurring_bills WHERE id = ?", (bill_id,))
        conn.commit()
        return cursor.rowcount > 0


def process_recurring_bills(year_month: str = None, user_id: int = None, force_manual: bool = False) -> int:
    """
    MOTOR DE RECORRÊNCIA INTELIGENTE E CONTROLADO:
    1. Nunca roda cegamente fora do dia 1 do mês, a menos que force_manual=True (acionado explicitamente pelo usuário).
    2. Checa duplicidade: se já existe em transactions para o mesmo mês e usuário, não recria.
    3. Respeita exclusões manuais: se o usuário apagou a conta no mês, ela está em recurring_dismissals e
       NÃO será regenerada automaticamente.
    4. Se for force_manual=True (botão 'Sincronizar Mês Vigente'), sincroniza as contas do mês e permite
       regenerar contas faltantes limpando as dispensas anteriores desse mês para esse usuário.
    """
    hoje = datetime.now()

    # Se não for acionamento manual e NÃO for o dia 1 do mês, não roda automaticamente
    if not force_manual and hoje.day != 1:
        return 0

    if year_month is None:
        year_month = hoje.strftime("%Y-%m")

    year, month = map(int, year_month.split("-"))
    generated_count = 0

    with get_connection() as conn:
        cursor = conn.cursor()

        # Se for acionamento manual explícito, limpa as dispensas do mês para restaurar as contas
        if force_manual and user_id is not None:
            cursor.execute("""
                DELETE FROM recurring_dismissals
                WHERE user_id = ? AND recurring_ref = ?
            """, (int(user_id), year_month))

        # Busca contas ativas estritamente do usuário
        q_bills = "SELECT * FROM recurring_bills WHERE is_active = 1"
        p_bills = []
        if user_id is not None:
            q_bills += " AND user_id = ?"
            p_bills.append(int(user_id))

        cursor.execute(q_bills, p_bills)
        active_bills = cursor.fetchall()

        for bill in active_bills:
            b_dict = dict(bill)

            # 1. Se for automático, checa se o usuário já excluiu essa conta nesta competência
            if not force_manual:
                cursor.execute("""
                    SELECT id FROM recurring_dismissals
                    WHERE user_id = ?
                      AND recurring_ref = ?
                      AND description = ?
                      AND category = ?
                      AND type = ?
                """, (b_dict["user_id"], year_month, b_dict["description"], b_dict["category"], b_dict["type"]))
                if cursor.fetchone() is not None:
                    continue  # Foi apagada manualmente pelo usuário neste mês, não regenerar!

            # 2. Checa se a conta já existe em transactions para a competência
            cursor.execute("""
                SELECT id FROM transactions
                WHERE recurring_ref = ?
                  AND user_id = ?
                  AND description = ?
                  AND category = ?
                  AND type = ?
            """, (year_month, b_dict["user_id"], b_dict["description"], b_dict["category"], b_dict["type"]))

            if cursor.fetchone() is None:
                due_date_str = _get_due_date_for_month(year, month, b_dict["due_day"])
                group_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO transactions (
                        user_id, type, category, description, amount,
                        payment_method, installment_current, installment_total,
                        group_id, due_date, status, invoice_path,
                        is_recurring, recurring_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    b_dict["user_id"],
                    b_dict["type"],
                    b_dict["category"],
                    b_dict["description"],
                    b_dict["amount"],
                    "À Vista",
                    1,
                    1,
                    group_id,
                    due_date_str,
                    "Pendente",
                    None,
                    1,
                    year_month
                ))
                generated_count += 1

        conn.commit()
    return generated_count


# =====================================================================
# CRUD: CARTEIRA DE INVESTIMENTOS (investments)
# =====================================================================

def add_investment(
    user_id: int,
    asset_name: str,
    category: str,
    invested_amount: float,
    current_value: float,
    update_date: str = None
) -> int:
    """Cadastra um novo ativo de investimento para o usuário."""
    if update_date is None:
        update_date = date.today().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (
                user_id, asset_name, category, invested_amount, current_value, update_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (int(user_id), asset_name, category, round(invested_amount, 2), round(current_value, 2), update_date))
        conn.commit()
        return cursor.lastrowid


def get_investments(user_id: int = None, include_shared: bool = False):
    """
    Lista os investimentos da carteira.
    POR PADRÃO (include_shared=False): filtra ESTRITAMENTE pelo próprio user_id logado.
    """
    query = """
        SELECT i.*, u.username AS owner_username
        FROM investments i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id is not None:
        if include_shared:
            accessible_ids = get_accessible_user_ids(user_id)
            if accessible_ids:
                placeholders = ", ".join(["?"] * len(accessible_ids))
                query += f" AND i.user_id IN ({placeholders})"
                params.extend(accessible_ids)
            else:
                query += " AND 1=0"
        else:
            query += " AND i.user_id = ?"
            params.append(int(user_id))

    query += " ORDER BY i.category ASC, i.asset_name ASC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def update_investment(
    investment_id: int,
    asset_name: str,
    category: str,
    invested_amount: float,
    current_value: float,
    update_date: str = None,
    requesting_user_id: int = None
) -> bool:
    """Atualiza os valores de um ativo de investimento."""
    if update_date is None:
        update_date = date.today().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM investments WHERE id = ?", (investment_id,))
            inv = cursor.fetchone()
            if inv and not can_user_edit_resource(requesting_user_id, inv["user_id"]):
                return False

        cursor.execute("""
            UPDATE investments
            SET asset_name = ?, category = ?, invested_amount = ?, current_value = ?, update_date = ?
            WHERE id = ?
        """, (asset_name, category, round(invested_amount, 2), round(current_value, 2), update_date, investment_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_investment(investment_id: int, requesting_user_id: int = None) -> bool:
    """Exclui um ativo da carteira."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM investments WHERE id = ?", (investment_id,))
            inv = cursor.fetchone()
            if inv and not can_user_edit_resource(requesting_user_id, inv["user_id"]):
                return False

        cursor.execute("DELETE FROM investments WHERE id = ?", (investment_id,))
        conn.commit()
        return cursor.rowcount > 0


# =====================================================================
# CRUD: METAS E ORÇAMENTOS (budgets)
# =====================================================================

def set_budget(user_id_or_cat, category_or_limit, monthly_limit: float = None) -> bool:
    """
    Cria ou atualiza o teto orçamentário mensal para uma categoria do usuário.
    Suporta chamada com (user_id, category, monthly_limit) ou retrocompatível (category, monthly_limit).
    """
    if monthly_limit is not None:
        u_id = int(user_id_or_cat)
        cat = str(category_or_limit)
        lim = float(monthly_limit)
    else:
        u_id = 1
        cat = str(user_id_or_cat)
        lim = float(category_or_limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO budgets (user_id, category, monthly_limit)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit = excluded.monthly_limit
        """, (u_id, cat, round(lim, 2)))
        conn.commit()
        return True


def get_budgets(user_id: int = None, include_shared: bool = False):
    """
    Lista todos os limites de orçamento configurados.
    POR PADRÃO (include_shared=False): filtra ESTRITAMENTE pelo próprio user_id logado.
    """
    query = """
        SELECT b.*, u.username AS owner_username
        FROM budgets b
        LEFT JOIN users u ON b.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id is not None:
        if include_shared:
            accessible_ids = get_accessible_user_ids(user_id)
            if accessible_ids:
                placeholders = ", ".join(["?"] * len(accessible_ids))
                query += f" AND b.user_id IN ({placeholders})"
                params.extend(accessible_ids)
            else:
                query += " AND 1=0"
        else:
            query += " AND b.user_id = ?"
            params.append(int(user_id))

    query += " ORDER BY b.category ASC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def delete_budget(budget_id: int, requesting_user_id: int = None) -> bool:
    """Remove a meta orçamentária de uma categoria."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if requesting_user_id is not None:
            cursor.execute("SELECT user_id FROM budgets WHERE id = ?", (budget_id,))
            b = cursor.fetchone()
            if b and not can_user_edit_resource(requesting_user_id, b["user_id"]):
                return False

        cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        conn.commit()
        return cursor.rowcount > 0


# =====================================================================
# CRUD: GESTÃO DE USUÁRIOS (users)
# =====================================================================

def get_users():
    """Retorna lista de todos os usuários cadastrados (sem a senha)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, role, full_name, address, cpf, created_at 
            FROM users 
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_user_profile(user_id: int) -> dict | None:
    """Busca o perfil completo do usuário pelo ID."""
    return get_user_by_id(user_id)


def add_user(username: str, password: str, role: str = "editor", 
             full_name: str = None, address: str = None, cpf: str = None) -> int:
    """Cria um novo usuário no sistema com perfil opcional expandido."""
    pwd_hash = hash_password(password)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, address, cpf)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username.strip(), 
            pwd_hash, 
            role,
            full_name.strip() if full_name else None,
            address.strip() if address else None,
            cpf.strip() if cpf else None
        ))
        conn.commit()
        return cursor.lastrowid


def update_user_profile(user_id: int, full_name: str = None, address: str = None, cpf: str = None) -> bool:
    """Atualiza as informações cadastrais de perfil do usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, address = ?, cpf = ?
            WHERE id = ?
        """, (
            full_name.strip() if full_name else None,
            address.strip() if address else None,
            cpf.strip() if cpf else None,
            int(user_id)
        ))
        conn.commit()
        return cursor.rowcount > 0


def update_user_role(user_id: int, new_role: str) -> bool:
    """Altera o perfil/cargo do usuário ('admin', 'editor', 'viewer')."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, int(user_id)))
        conn.commit()
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Remove um usuário do sistema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        conn.commit()
        return cursor.rowcount > 0


def change_user_password(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    """
    Permite que o usuário autenticado altere sua própria senha fornecendo a senha atual.
    Valida a senha atual via hash SHA-256 e grava a nova senha.
    """
    return change_password_with_verification(user_id, current_password, new_password)


def admin_set_user_password(admin_user_id: int, target_user_id: int, new_password: str) -> tuple[bool, str]:
    """
    Permite que um administrador redefina diretamente a senha de qualquer usuário (inclusive a do próprio admin).
    """
    if not new_password or len(new_password.strip()) < 4:
        return False, "A nova senha deve ter no mínimo 4 caracteres."

    with get_connection() as conn:
        cursor = conn.cursor()
        # Verificar se o solicitante é admin
        cursor.execute("SELECT role FROM users WHERE id = ?", (int(admin_user_id),))
        row = cursor.fetchone()
        if not row or row["role"] != "admin":
            return False, "Apenas administradores podem redefinir senhas diretamente."

        # Verificar se usuário alvo existe
        cursor.execute("SELECT username FROM users WHERE id = ?", (int(target_user_id),))
        target_row = cursor.fetchone()
        if not target_row:
            return False, "Usuário de destino não encontrado."

    try:
        ok = update_user_password(target_user_id, new_password.strip())
        if ok:
            return True, f"Senha do usuário '{target_row['username']}' atualizada com sucesso!"
        return False, "Não foi possível atualizar a senha."
    except Exception as e:
        return False, f"Erro ao atualizar senha: {e}"

