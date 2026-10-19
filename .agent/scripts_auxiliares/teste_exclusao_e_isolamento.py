import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import backend.crud as crud
from backend.database import get_connection

def test():
    print("=== TESTANDO ISOLAMENTO E EXCLUSÃO (UNITÁRIA E MÊS COMPLETO) ===")

    # 1. Testar Isolamento estrito por padrão (mesmo com user_shares presente no banco)
    # user_shares tem (1, 2) e (2, 3)
    t_u1 = crud.get_transactions(user_id=1)
    t_u2 = crud.get_transactions(user_id=2)
    t_u3 = crud.get_transactions(user_id=3)

    assert all(t["user_id"] == 1 for t in t_u1), "Transações de outros vazaram para user 1"
    assert all(t["user_id"] == 2 for t in t_u2), "Transações de outros vazaram para user 2"
    assert len(t_u3) == 0, "User 3 não deveria ver nada no seu espaço particular"
    print(f"[OK] Isolamento estrito padrão: User 1={len(t_u1)}, User 2={len(t_u2)}, User 3={len(t_u3)}")

    # 2. Testar Exclusão Unitária
    gid = crud.add_transaction(
        user_id=2,
        trans_type="despesa",
        category="Outros",
        description="Teste Exclusao Unitaria",
        amount=55.50,
        due_date="2026-07-15",
        status="Pago"
    )
    t_created = [t for t in crud.get_transactions(user_id=2) if t["description"] == "Teste Exclusao Unitaria"]
    assert len(t_created) == 1, "Transação temporária não foi criada"
    t_id = t_created[0]["id"]
    
    # Testar exclusão com delete_transaction(id, user_id)
    ok = crud.delete_transaction(t_id, user_id=2)
    assert ok is True, "delete_transaction retornou False"
    t_check = [t for t in crud.get_transactions(user_id=2) if t["id"] == t_id]
    assert len(t_check) == 0, "Transação ainda existe após delete_transaction"
    print("[OK] Exclusão unitária funcionou perfeitamente!")

    # 3. Testar Exclusão por Mês Inteiro
    crud.add_transaction(user_id=2, trans_type="despesa", category="Alimentação", description="Item Mes 1", amount=10.0, due_date="2026-05-10")
    crud.add_transaction(user_id=2, trans_type="despesa", category="Transporte", description="Item Mes 2", amount=20.0, due_date="2026-05-15")
    crud.add_transaction(user_id=2, trans_type="receita", category="Salário", description="Item Mes 3", amount=30.0, due_date="2026-05-20")
    
    # Também adicionar uma para User 1 em 2026-05 para provar que a do User 1 NÃO será apagada
    crud.add_transaction(user_id=1, trans_type="despesa", category="Alimentação", description="Item User 1 Não Apagar", amount=99.0, due_date="2026-05-10")

    count_user2_before = len(crud.get_transactions(user_id=2, start_date="2026-05-01", end_date="2026-05-31"))
    assert count_user2_before == 3, f"Esperado 3 transações criadas em 2026-05, obtido {count_user2_before}"

    # Executar delete_transactions_by_month para User 2
    deleted = crud.delete_transactions_by_month(user_id=2, year_month="2026-05")
    assert deleted == 3, f"Esperado 3 registros excluídos, obtido {deleted}"

    count_user2_after = len(crud.get_transactions(user_id=2, start_date="2026-05-01", end_date="2026-05-31"))
    assert count_user2_after == 0, f"Ainda restam {count_user2_after} transações para user 2 em 2026-05"

    # Verificar que o User 1 manteve intacta a sua transação de 2026-05
    u1_items_may = [t for t in crud.get_transactions(user_id=1) if t["description"] == "Item User 1 Não Apagar"]
    assert len(u1_items_may) == 1, "Transação do User 1 foi afetada indevidamente!"
    crud.delete_transaction(u1_items_may[0]["id"], user_id=1) # Limpar registro de teste do User 1
    print("[OK] Exclusão por mês completo funcionou perfeitamente e respeitou o isolamento do outro usuário!")

    print("\n[SUCESSO] TODOS OS TESTES DE EXCLUSÃO E ISOLAMENTO PASSARAM COM ÊXITO!")

if __name__ == "__main__":
    test()
