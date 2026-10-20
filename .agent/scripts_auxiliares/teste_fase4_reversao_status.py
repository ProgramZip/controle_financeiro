import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, verify_user
from backend.crud import (
    add_transaction, get_transaction_by_id, revert_transaction_to_pending,
    update_transaction_status, delete_transaction
)

def run_tests():
    print("Iniciando testes da Fase 4: Reversao de Status (Concluidas/Pagas para Pendentes)...")
    init_db()

    admin = verify_user("admin", "admin123")
    assert admin is not None, "Usuario admin deve existir."
    u_id = admin["id"]

    # 1. Testar reversão de Despesa Paga para Pendente
    gid_desp = add_transaction(
        user_id=u_id,
        trans_type="despesa",
        category="Alimentação",
        description="Teste Fase 4 Despesa Paga",
        amount=89.90,
        payment_method="À Vista",
        due_date="2026-10-20",
        status="Pago"
    )
    from backend.crud import get_transactions
    desp_item = next((t for t in get_transactions(user_id=u_id) if t["description"] == "Teste Fase 4 Despesa Paga"), None)
    assert desp_item is not None, "Despesa de teste nao encontrada."
    assert desp_item["status"] == "Pago", "Status inicial deveria ser 'Pago'."

    # Executar reversão para Pendente
    ok_rev_desp = revert_transaction_to_pending(desp_item["id"], requesting_user_id=u_id)
    assert ok_rev_desp, "Falha ao reverter despesa para Pendente."

    # Validar no SQLite
    desp_revertida = get_transaction_by_id(desp_item["id"])
    assert desp_revertida["status"] == "Pendente", f"Status deveria ser 'Pendente', mas e: {desp_revertida['status']}"
    print(f"  [OK] Despesa #{desp_item['id']} revertida com sucesso de 'Pago' para 'Pendente'.")

    # 2. Testar reversão de Receita Recebida para Pendente
    gid_rec = add_transaction(
        user_id=u_id,
        trans_type="receita",
        category="Serviços",
        description="Teste Fase 4 Receita Recebida",
        amount=1200.00,
        payment_method="À Vista",
        due_date="2026-10-20",
        status="Recebido"
    )
    rec_item = next((t for t in get_transactions(user_id=u_id) if t["description"] == "Teste Fase 4 Receita Recebida"), None)
    assert rec_item is not None, "Receita de teste nao encontrada."
    assert rec_item["status"] == "Recebido", "Status inicial deveria ser 'Recebido'."

    # Executar reversão para Pendente
    ok_rev_rec = revert_transaction_to_pending(rec_item["id"], requesting_user_id=u_id)
    assert ok_rev_rec, "Falha ao reverter receita para Pendente."

    # Validar no SQLite
    rec_revertida = get_transaction_by_id(rec_item["id"])
    assert rec_revertida["status"] == "Pendente", f"Status deveria ser 'Pendente', mas e: {rec_revertida['status']}"
    print(f"  [OK] Receita #{rec_item['id']} revertida com sucesso de 'Recebido' para 'Pendente'.")

    # 3. Testar bloqueio de reversão por usuário não autorizado
    blocked = revert_transaction_to_pending(rec_item["id"], requesting_user_id=99999)
    assert not blocked, "Usuario nao autorizado nao deveria conseguir alterar status."
    print("  [OK] Seguranca contra alteracao de status por terceiros validada.")

    # 4. Limpeza
    delete_transaction(desp_item["id"], user_id=u_id)
    delete_transaction(rec_item["id"], user_id=u_id)
    print("  [OK] Limpeza de registros de teste concluida.")

    print("\nTODOS OS TESTES DA FASE 4 PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    run_tests()
