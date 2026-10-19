import os
import sys

# Garante que o diretório raiz esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import init_db, verify_user, DB_PATH
from backend.crud import (
    add_transaction, get_transactions, update_transaction_status,
    add_recurring_bill, process_recurring_bills,
    add_investment, get_investments,
    set_budget, get_budgets
)

def run_tests():
    print(f"1. Inicializando banco em: {DB_PATH}")
    init_db()
    assert os.path.exists(DB_PATH), "financas.db não foi criado!"

    print("2. Testando login do admin...")
    admin = verify_user("admin", "admin123")
    assert admin is not None, "Falha na autenticação do admin!"
    assert admin["role"] == "admin", "Role do admin incorreta!"
    print(f"   -> Sucesso! Admin ID: {admin['id']}")

    print("3. Testando inserção de compra parcelada (ex: R$ 300 em 3x)...")
    group_id = add_transaction(
        user_id=admin["id"],
        trans_type="despesa",
        category="Compras",
        description="Monitor Gamer",
        amount=300.0,
        payment_method="Parcelado",
        installment_total=3,
        due_date="2026-10-15",
        status="Pago"
    )
    installments = get_transactions(group_id=group_id)
    assert len(installments) == 3, f"Esperado 3 parcelas, obteve {len(installments)}"
    assert installments[2]["installment_current"] == 1 and installments[2]["status"] == "Pago"
    assert installments[1]["installment_current"] == 2 and installments[1]["status"] == "Pendente"
    assert installments[0]["installment_current"] == 3 and installments[0]["status"] == "Pendente"
    print(f"   -> Sucesso! 3 parcelas criadas com group_id: {group_id}")

    print("4. Testando ação rápida de quitação em 1 clique...")
    target_id = installments[1]["id"]
    success = update_transaction_status(target_id, "Pago")
    assert success is True, "Falha ao atualizar status!"
    updated_trans = get_transactions()
    target_trans = next(t for t in updated_trans if t["id"] == target_id)
    assert target_trans["status"] == "Pago", "Status não mudou para Pago!"
    print("   -> Sucesso! Status atualizado para Pago em 1 clique.")

    print("5. Testando motor de contas recorrentes com trava...")
    import time
    test_desc = f"Netflix Teste {int(time.time())}"
    bill_id = add_recurring_bill(
        user_id=admin["id"],
        bill_type="despesa",
        category="Assinaturas",
        description=test_desc,
        amount=55.90,
        due_day=10
    )
    gen_first = process_recurring_bills("2026-10")
    assert gen_first >= 1, "Deveria ter gerado pelo menos 1 conta recorrente!"
    # Rodar novamente no mesmo mês para testar a trava de duplicação
    gen_second = process_recurring_bills("2026-10")
    assert gen_second == 0, f"Trava falhou! Gerou {gen_second} contas duplicadas!"
    print("   -> Sucesso! Conta recorrente gerada e trava anti-duplicidade validada.")

    print("6. Testando orçamentos e investimentos...")
    set_budget("Alimentação", 1200.0)
    budgets = get_budgets()
    assert any(b["category"] == "Alimentação" and b["monthly_limit"] == 1200.0 for b in budgets)

    add_investment(admin["id"], "Tesouro Selic 2029", "Renda Fixa", 5000.0, 5250.0, "2026-10-16")
    invs = get_investments(admin["id"])
    assert len(invs) >= 1
    print("   -> Sucesso! Orçamentos e Investimentos funcionando perfeitamente.")

    print("\n[SUCESSO] TODOS OS TESTES DA FASE 3 PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    run_tests()

