import sys
from pathlib import Path

# Adiciona raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, get_connection
import backend.crud as crud

def run_tests():
    print("=== INICIANDO TESTE DO ISOLAMENTO MULTI-USUÁRIO E PARTILHAMENTO ===")
    init_db()

    # 1. Obter usuários
    users = crud.get_users()
    print(f"Usuários encontrados: {[u['username'] for u in users]}")
    u1 = users[0]["id"] # admin
    u2 = users[1]["id"] if len(users) > 1 else None # Gabriel
    u3 = users[2]["id"] if len(users) > 2 else None # Camilla

    assert u1 is not None, "Usuário admin não encontrado"
    assert u2 is not None, "Usuário 2 não encontrado"
    assert u3 is not None, "Usuário 3 não encontrado"

    # Limpar shares prévios para ambiente de teste limpo
    with get_connection() as conn:
        conn.execute("DELETE FROM user_shares")
        conn.commit()

    # 2. Testar Isolamento estrito por padrão
    print("\n[Teste 1] Isolamento estrito por padrão:")
    u1_ids = crud.get_accessible_user_ids(u1)
    u2_ids = crud.get_accessible_user_ids(u2)
    u3_ids = crud.get_accessible_user_ids(u3)

    assert u1_ids == [u1], f"Esperado {[u1]}, obtido {u1_ids}"
    assert u2_ids == [u2], f"Esperado {[u2]}, obtido {u2_ids}"
    assert u3_ids == [u3], f"Esperado {[u3]}, obtido {u3_ids}"
    print("  -> IDs acessíveis isolados com sucesso!")

    t_u1 = crud.get_transactions(user_id=u1)
    t_u2 = crud.get_transactions(user_id=u2)
    t_u3 = crud.get_transactions(user_id=u3)
    print(f"  -> Transações: Admin={len(t_u1)}, User2={len(t_u2)}, User3={len(t_u3)}")
    assert all(t["user_id"] == u1 for t in t_u1), "Transações de outros usuários vazaram para u1"
    assert all(t["user_id"] == u2 for t in t_u2), "Transações de outros usuários vazaram para u2"
    assert len(t_u3) == 0, "Usuário 3 não deveria ter transações ainda"

    # 3. Testar Orçamentos por Usuário
    print("\n[Teste 2] Metas e Orçamentos isolados:")
    crud.set_budget(u1, "Alimentação", 1200.0)
    crud.set_budget(u2, "Alimentação", 800.0)
    
    b_u1 = crud.get_budgets(u1)
    b_u2 = crud.get_budgets(u2)
    assert len(b_u1) == 1 and b_u1[0]["monthly_limit"] == 1200.0, f"Falha no teto do u1: {b_u1}"
    assert len(b_u2) == 1 and b_u2[0]["monthly_limit"] == 800.0, f"Falha no teto do u2: {b_u2}"
    print(f"  -> U1 teto Alimentação: R$ {b_u1[0]['monthly_limit']}, U2 teto Alimentação: R$ {b_u2[0]['monthly_limit']}")

    # 4. Testar Partilhamento como 'viewer' (Visualizador)
    print("\n[Teste 3] Partilhamento de U1 com U3 como 'viewer':")
    crud.add_user_share(owner_id=u1, shared_with_user_id=u3, permission_level="viewer")
    
    u3_ids_shared = crud.get_accessible_user_ids(u3)
    assert set(u3_ids_shared) == {u1, u3}, f"Esperado {u1, u3}, obtido {u3_ids_shared}"
    
    t_u3_shared = crud.get_transactions(user_id=u3)
    assert len(t_u3_shared) == len(t_u1), f"Esperado {len(t_u1)} transações compartilhadas, obtido {len(t_u3_shared)}"
    
    # Checar permissão de edição
    perm_u3_on_u1 = crud.get_user_permission(owner_id=u1, user_id=u3)
    can_edit_u3 = crud.can_user_edit_resource(user_id=u3, resource_owner_id=u1)
    assert perm_u3_on_u1 == "viewer", f"Esperado 'viewer', obtido {perm_u3_on_u1}"
    assert can_edit_u3 is False, "Usuário viewer não deveria ter permissão de edição em dados do owner"
    print(f"  -> U3 agora visualiza dados de U1 ({len(t_u3_shared)} transações), com can_edit={can_edit_u3}!")

    # 5. Testar Partilhamento como 'editor'
    print("\n[Teste 4] Partilhamento de U1 com U2 como 'editor':")
    crud.add_user_share(owner_id=u1, shared_with_user_id=u2, permission_level="editor")
    
    perm_u2_on_u1 = crud.get_user_permission(owner_id=u1, user_id=u2)
    can_edit_u2 = crud.can_user_edit_resource(user_id=u2, resource_owner_id=u1)
    assert perm_u2_on_u1 == "editor", f"Esperado 'editor', obtido {perm_u2_on_u1}"
    assert can_edit_u2 is True, "Usuário editor deveria ter permissão de edição"
    print(f"  -> U2 agora tem permissão 'editor' sobre dados de U1 (can_edit={can_edit_u2})!")

    # 6. Testar Listagens de Compartilhamento
    print("\n[Teste 5] Consultas de compartilhamento concedido e recebido:")
    shares_u1 = crud.get_user_shares_by_owner(u1)
    assert len(shares_u1) == 2, f"Esperado 2 shares concedidos por U1, obtido {len(shares_u1)}"
    
    received_u2 = crud.get_user_shares_received(u2)
    assert len(received_u2) == 1 and received_u2[0]["owner_id"] == u1, f"Falha nas partilhas recebidas por u2: {received_u2}"
    print(f"  -> U1 concedeu {len(shares_u1)} acessos. U2 recebeu {len(received_u2)} acesso de {received_u2[0]['owner_username']}.")

    # 7. Testar Revogação de Compartilhamento
    print("\n[Teste 6] Revogação de compartilhamento:")
    share_to_remove = [s for s in shares_u1 if s["shared_with_user_id"] == u3][0]
    crud.delete_user_share(share_to_remove["id"], owner_id=u1)
    
    u3_ids_after_rev = crud.get_accessible_user_ids(u3)
    assert u3_ids_after_rev == [u3], f"Esperado apenas {[u3]} após revogação, obtido {u3_ids_after_rev}"
    t_u3_after_rev = crud.get_transactions(user_id=u3)
    assert len(t_u3_after_rev) == 0, f"Transações ainda visíveis para u3 após revogação: {len(t_u3_after_rev)}"
    print("  -> Revogação concluída com sucesso! U3 não acessa mais os dados de U1.")

    print("\n[SUCESSO] TODOS OS 6 TESTES DE ISOLAMENTO E PARTILHAMENTO PASSARAM COM SUCESSO TOTAL!")

if __name__ == "__main__":
    run_tests()
