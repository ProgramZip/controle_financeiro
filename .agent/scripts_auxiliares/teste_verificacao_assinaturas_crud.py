import os
import sys
from datetime import date
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.database import init_db, verify_user
from backend.crud import (
    get_transactions, process_recurring_bills, delete_transactions_by_month,
    get_recurring_bills, get_investments, get_budgets, get_users, get_user_profile
)

def test_signatures():
    print("=== INICIANDO TESTE DE ASSINATURAS E PARÂMETROS EM CRUD.PY ===")
    init_db()
    admin = verify_user("admin", "admin123")
    assert admin is not None, "Usuário admin não encontrado"
    user_id = admin["id"]
    hoje = date.today()
    mes_atual = hoje.strftime("%Y-%m")

    # 1. Teste process_recurring_bills com force_manual=True e force_manual=False
    print("\n[1/5] Testando process_recurring_bills:")
    # Chamada com argumentos nomeados
    res1 = process_recurring_bills(user_id=user_id, force_manual=False)
    print(f"  ✓ process_recurring_bills(user_id={user_id}, force_manual=False) -> {res1}")
    
    res2 = process_recurring_bills(user_id=user_id, force_manual=True)
    print(f"  ✓ process_recurring_bills(user_id={user_id}, force_manual=True) -> {res2}")

    # Chamada com month_year explícito
    res3 = process_recurring_bills(month_year=mes_atual, user_id=user_id, force_manual=True)
    print(f"  ✓ process_recurring_bills(month_year='{mes_atual}', user_id={user_id}, force_manual=True) -> {res3}")

    # Chamada posicional antiga
    res4 = process_recurring_bills(mes_atual, user_id, False)
    print(f"  ✓ process_recurring_bills('{mes_atual}', {user_id}, False) -> {res4}")

    # 2. Teste get_transactions com month_year e year_month e limit
    print("\n[2/5] Testando get_transactions:")
    t1 = get_transactions(user_id=user_id, month_year=mes_atual)
    print(f"  ✓ get_transactions(user_id={user_id}, month_year='{mes_atual}') -> {len(t1)} itens")

    t2 = get_transactions(user_id=user_id, year_month=mes_atual)
    print(f"  ✓ get_transactions(user_id={user_id}, year_month='{mes_atual}') -> {len(t2)} itens")
    assert len(t1) == len(t2), "Filtros month_year e year_month devem ser equivalentes"

    t3 = get_transactions(user_id=user_id, limit=5)
    print(f"  ✓ get_transactions(user_id={user_id}, limit=5) -> {len(t3)} itens (limite respeitado: {len(t3) <= 5})")
    assert len(t3) <= 5, "Limite de registros deve ser respeitado"

    # 3. Teste get_recurring_bills, get_investments, get_budgets com kwargs safety
    print("\n[3/5] Testando funções com cache e kwargs safety:")
    b1 = get_recurring_bills(user_id=user_id, include_shared=False, custom_kwarg="ignorado_com_sucesso")
    print(f"  ✓ get_recurring_bills(user_id={user_id}) -> {len(b1)} contas")

    i1 = get_investments(user_id=user_id, include_shared=False, custom_kwarg="ignorado_com_sucesso")
    print(f"  ✓ get_investments(user_id={user_id}) -> {len(i1)} investimentos")

    bg1 = get_budgets(user_id=user_id, include_shared=False, custom_kwarg="ignorado_com_sucesso")
    print(f"  ✓ get_budgets(user_id={user_id}) -> {len(bg1)} orçamentos")

    # 4. Teste delete_transactions_by_month com month_year e year_month
    print("\n[4/5] Testando delete_transactions_by_month (assinatura):")
    # Teste de validação de formato
    try:
        delete_transactions_by_month(user_id=user_id, month_year="mes-invalido")
        assert False, "Deveria lançar ValueError para formato inválido"
    except ValueError as ve:
        print(f"  ✓ Validação de formato inválido funcionou: {ve}")

    # 5. Teste get_users e get_user_profile
    print("\n[5/5] Testando get_users e get_user_profile:")
    users = get_users()
    print(f"  ✓ get_users() -> {len(users)} usuários")
    profile = get_user_profile(user_id=user_id)
    print(f"  ✓ get_user_profile(user_id={user_id}) -> {profile['username'] if profile else None}")

    print("\n=======================================================")
    print("✅ TODAS AS ASSINATURAS E PARÂMETROS VALIDADOS COM 100% DE SUCESSO!")
    print("=======================================================")

if __name__ == "__main__":
    test_signatures()
