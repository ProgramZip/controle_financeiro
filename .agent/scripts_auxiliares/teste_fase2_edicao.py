import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, verify_user
from backend.crud import (
    add_transaction, get_transaction_by_id, update_transaction, delete_transaction,
    add_recurring_bill, get_recurring_bills, update_recurring_bill, delete_recurring_bill
)

def run_tests():
    print("Iniciando testes da Fase 2: Edicao de Movimentacoes e Contas...")
    init_db()

    # 1. Obter usuário admin para os testes
    admin = verify_user("admin", "admin123")
    assert admin is not None, "Usuario admin deve existir."
    user_id = admin["id"]

    # 2. Testar criação e edição de transação
    gid = add_transaction(
        user_id=user_id,
        trans_type="despesa",
        category="Alimentação",
        description="Almoço Restaurante Teste",
        amount=55.50,
        payment_method="À Vista",
        due_date="2026-10-20",
        status="Pendente"
    )
    assert gid is not None, "Falha ao criar transacao."
    
    # Obter transação criada
    from backend.crud import get_transactions
    created = [t for t in get_transactions(user_id=user_id) if t["description"] == "Almoço Restaurante Teste"]
    assert len(created) > 0, "Transacao nao encontrada."
    t_id = created[0]["id"]
    print(f"  [OK] Transacao criada com ID #{t_id}.")

    # 3. Testar alteração de múltiplos campos
    ok = update_transaction(
        transaction_id=t_id,
        requesting_user_id=user_id,
        type="despesa",
        category="Lazer",
        description="Jantar Especial Alterado",
        amount=120.00,
        due_date="2026-10-25",
        status="Pago",
        payment_method="À Vista"
    )
    assert ok, "Falha ao executar update_transaction."
    print("  [OK] update_transaction executado com sucesso.")

    # 4. Validar dados atualizados no banco
    updated = get_transaction_by_id(t_id)
    assert updated is not None, "Transacao nao encontrada apos update."
    assert updated["category"] == "Lazer", f"Categoria incorreta: {updated['category']}"
    assert updated["description"] == "Jantar Especial Alterado", f"Descricao incorreta: {updated['description']}"
    assert abs(updated["amount"] - 120.00) < 0.001, f"Valor incorreto: {updated['amount']}"
    assert updated["due_date"] == "2026-10-25", f"Data incorreta: {updated['due_date']}"
    assert updated["status"] == "Pago", f"Status incorreto: {updated['status']}"
    print("  [OK] Todos os campos da transacao foram alterados e validados no SQLite.")

    # 5. Testar bloqueio de edicao por usuario nao autorizado (ex: ID 99999)
    blocked = update_transaction(
        transaction_id=t_id,
        requesting_user_id=99999,
        description="Tentativa Hacker"
    )
    assert not blocked, "Usuario nao autorizado nao deveria conseguir editar a transacao."
    current_check = get_transaction_by_id(t_id)
    assert current_check["description"] == "Jantar Especial Alterado", "Descricao foi alterada indevidamente!"
    print("  [OK] Seguranca e bloqueio de edicao por terceiros validada.")

    # 6. Testar edicao de Conta Fixa Recorrente
    bill_id = add_recurring_bill(
        user_id=user_id,
        bill_type="despesa",
        category="Moradia",
        description="Internet Fibra 300MB",
        amount=99.90,
        due_day=10,
        is_active=1
    )
    assert bill_id is not None, "Falha ao criar conta recorrente."
    print(f"  [OK] Conta recorrente criada com ID #{bill_id}.")

    # Alterar conta recorrente
    ok_bill = update_recurring_bill(
        bill_id=bill_id,
        requesting_user_id=user_id,
        category="Serviços",
        description="Internet Fibra 600MB Upgrade",
        amount=129.90,
        due_day=15,
        is_active=0
    )
    assert ok_bill, "Falha ao atualizar conta recorrente."

    # Validar no banco
    bills = get_recurring_bills(user_id=user_id)
    b_updated = next((b for b in bills if b["id"] == bill_id), None)
    assert b_updated is not None, "Conta recorrente nao encontrada apos update."
    assert b_updated["category"] == "Serviços", f"Categoria incorreta: {b_updated['category']}"
    assert b_updated["description"] == "Internet Fibra 600MB Upgrade", f"Descricao incorreta: {b_updated['description']}"
    assert abs(b_updated["amount"] - 129.90) < 0.001, f"Valor incorreto: {b_updated['amount']}"
    assert b_updated["due_day"] == 15, f"Dia de vencimento incorreto: {b_updated['due_day']}"
    assert b_updated["is_active"] == 0, f"Estado is_active incorreto: {b_updated['is_active']}"
    print("  [OK] Conta recorrente alterada e validada no SQLite.")

    # Limpeza
    delete_transaction(t_id, user_id=user_id)
    delete_recurring_bill(bill_id, requesting_user_id=user_id)
    print("  [OK] Limpeza de registros de teste concluida.")

    print("\nTODOS OS TESTES DA FASE 2 PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    run_tests()
