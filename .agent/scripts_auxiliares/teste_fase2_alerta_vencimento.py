import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Adiciona o diretório raiz ao sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import init_db, get_connection
from backend.crud import (
    add_user, get_users, add_transaction, get_transactions,
    update_transaction_status, delete_transaction
)

def test_due_date_alerts():
    print("Iniciando teste automatizado da Fase 2: Alerta de Vencimento Imediato...")
    init_db()

    # Cria ou obtém usuários de teste
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE description LIKE 'TEST_ALERT_%'")
        cursor.execute("DELETE FROM users WHERE username IN ('user_alert_test', 'user_alert_other')")
        conn.commit()

    add_user("user_alert_test", "Alert123!", "viewer")
    add_user("user_alert_other", "Other123!", "viewer")

    users = get_users()
    u1 = next(u for u in users if u["username"] == "user_alert_test")
    u2 = next(u for u in users if u["username"] == "user_alert_other")

    hoje = date.today()
    d_atrasada = (hoje - timedelta(days=2)).isoformat()
    d_hoje = hoje.isoformat()
    d_amanha = (hoje + timedelta(days=1)).isoformat()
    d_3dias = (hoje + timedelta(days=3)).isoformat()
    d_longe = (hoje + timedelta(days=10)).isoformat()

    # 1. Cria contas de teste para u1
    id_atrasada = add_transaction(u1["id"], "despesa", "Contas Fixas", "TEST_ALERT_Atrasada", 100.0, due_date=d_atrasada, status="Pendente")
    id_hoje = add_transaction(u1["id"], "despesa", "Alimentação", "TEST_ALERT_Hoje", 200.0, due_date=d_hoje, status="Pendente")
    id_amanha = add_transaction(u1["id"], "despesa", "Transporte", "TEST_ALERT_Amanha", 300.0, due_date=d_amanha, status="Pendente")
    id_3dias = add_transaction(u1["id"], "despesa", "Saúde", "TEST_ALERT_3Dias", 150.0, due_date=d_3dias, status="Pendente")
    
    # Contas que NÃO devem entrar no alerta:
    id_longe = add_transaction(u1["id"], "despesa", "Lazer", "TEST_ALERT_Longe", 500.0, due_date=d_longe, status="Pendente")
    id_paga = add_transaction(u1["id"], "despesa", "Outros", "TEST_ALERT_Paga", 900.0, due_date=d_hoje, status="Pago")
    id_receita = add_transaction(u1["id"], "receita", "Salário", "TEST_ALERT_Receita", 2500.0, due_date=d_hoje, status="Pendente")
    id_outro_user = add_transaction(u2["id"], "despesa", "Contas Fixas", "TEST_ALERT_OutroUser", 999.0, due_date=d_hoje, status="Pendente")

    # 2. Executa a lógica de filtragem do alerta
    limite_3dias = hoje + timedelta(days=3)
    pendentes_u1 = get_transactions(user_id=u1["id"], trans_type="despesa", status="Pendente")

    alert_items = []
    for item in pendentes_u1:
        raw_date = item.get("due_date")
        if not raw_date:
            continue
        try:
            d_date = date.fromisoformat(str(raw_date)[:10])
        except Exception:
            continue

        if d_date <= limite_3dias:
            alert_items.append(item)

    print(f"Total de contas no alerta: {len(alert_items)}")
    for it in alert_items:
        print(f" - {it['description']} (R$ {it['amount']:.2f}) - Vencimento: {it['due_date']}")

    # Asserções
    assert len(alert_items) == 4, f"Esperado 4 contas no alerta, obteve {len(alert_items)}"
    total_val = sum(i["amount"] for i in alert_items)
    assert total_val == 750.0, f"Esperado total de R$ 750.00, obteve R$ {total_val:.2f}"

    descs = [i["description"] for i in alert_items]
    assert "TEST_ALERT_Atrasada" in descs
    assert "TEST_ALERT_Hoje" in descs
    assert "TEST_ALERT_Amanha" in descs
    assert "TEST_ALERT_3Dias" in descs
    assert "TEST_ALERT_Longe" not in descs
    assert "TEST_ALERT_Paga" not in descs
    assert "TEST_ALERT_Receita" not in descs
    assert "TEST_ALERT_OutroUser" not in descs

    # 3. Testa a Quitação Rápida
    conta_hoje = next(i for i in alert_items if i["description"] == "TEST_ALERT_Hoje")
    ok_pay = update_transaction_status(conta_hoje["id"], "Pago", requesting_user_id=u1["id"])
    assert ok_pay is True, "Falha ao quitar conta rapidamente"

    # Reavalia o alerta após quitação
    pendentes_pos_pay = get_transactions(user_id=u1["id"], trans_type="despesa", status="Pendente")
    alert_items_pos = [i for i in pendentes_pos_pay if date.fromisoformat(str(i["due_date"])[:10]) <= limite_3dias]
    assert len(alert_items_pos) == 3, f"Esperado 3 contas após quitação rápida, obteve {len(alert_items_pos)}"
    assert sum(i["amount"] for i in alert_items_pos) == 550.0

    # Limpeza
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE description LIKE 'TEST_ALERT_%'")
        cursor.execute("DELETE FROM users WHERE username IN ('user_alert_test', 'user_alert_other')")
        conn.commit()

    print("[SUCESSO] TESTE DA FASE 2 PASSOU COM 100% DE EXITO!")

if __name__ == "__main__":
    test_due_date_alerts()
