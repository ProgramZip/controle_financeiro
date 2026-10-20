import sys
from pathlib import Path

# Configura encoding UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import init_db, get_connection, verify_user, get_database_url
from backend.crud import (
    add_user, get_users, add_transaction, get_transactions,
    update_transaction_status, delete_transaction,
    add_recurring_bill, get_recurring_bills, process_recurring_bills,
    delete_recurring_bill
)

def test_turso_integration():
    print("=== TESTE DE INTEGRACAO COMPLETA COM TURSO CLOUD ===")
    url = get_database_url()
    print(f"URL Conectada: {url}")
    assert url is not None and "turso.io" in url, "Nao esta conectado ao Turso!"

    # 1. Inicializacao e verificacao de tabelas
    init_db()
    print("[1] init_db() executado com sucesso no Turso Cloud.")

    # 2. Autenticacao
    admin = verify_user("admin", "admin123")
    assert admin is not None, "Falha na autenticacao do usuario admin no Turso"
    print(f"[2] Autenticacao admin bem-sucedida (ID: {admin['id']})")

    # 3. Transacoes: Insert, Read, Update, Delete
    t_desc = "TESTE_TURSO_INTEGRACAO_FINAL"
    add_transaction(
        user_id=admin["id"],
        trans_type="despesa",
        category="Contas Fixas",
        description=t_desc,
        amount=199.90,
        due_date="2026-10-20",
        status="Pendente"
    )
    trans = get_transactions(user_id=admin["id"], search=t_desc)
    assert len(trans) == 1, "Transacao nao encontrada no Turso"
    t_item = trans[0]
    assert t_item["amount"] == 199.90
    assert t_item["status"] == "Pendente"
    print("[3] Transacao inserida e consultada com sucesso.")

    # 4. Atualizacao de Status
    ok_up = update_transaction_status(t_item["id"], "Pago", requesting_user_id=admin["id"])
    assert ok_up is True, "Falha ao atualizar status para Pago"
    trans_up = get_transactions(user_id=admin["id"], search=t_desc)
    assert trans_up[0]["status"] == "Pago", "Status nao persistiu como Pago"
    print("[4] Status atualizado para 'Pago' com persistencia confirmada.")

    # 5. Exclusao
    ok_del = delete_transaction(t_item["id"], user_id=admin["id"])
    assert ok_del is True, "Falha ao excluir transacao"
    trans_del = get_transactions(user_id=admin["id"], search=t_desc)
    assert len(trans_del) == 0, "Transacao ainda existe apos exclusao"
    print("[5] Exclusao de transacao confirmada no cluster.")

    print("\n[SUCESSO TOTAL] TODAS AS OPERACOES NO TURSO CLOUD FUNCIONAM 100%!")

if __name__ == "__main__":
    test_turso_integration()
