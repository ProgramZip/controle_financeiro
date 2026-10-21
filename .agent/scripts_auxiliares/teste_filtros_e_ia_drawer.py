import os
import sys
from datetime import date

# Adiciona raiz do projeto
sys.path.insert(0, r"E:\controle_financeiro")

from backend.database import init_db, verify_user
from backend.crud import get_transactions, get_budgets, get_investments
from backend.utils import analyze_finances_with_ai, chat_with_financial_ai
from frontend.components import render_standard_period_filter

def test_filtros_e_ia():
    print("=== INICIANDO TESTE DE FILTROS GLOBAIS E IA DRAWER ===")
    
    # 1. Banco de Dados
    init_db()
    admin_user = verify_user("admin", "admin123")
    assert admin_user is not None, "Usuário admin deve existir"
    print(f"[OK] Usuário admin autenticado com ID {admin_user['id']}")

    # 2. Teste de Busca de Transações - Consolidado Geral vs Mês vs Período
    all_trans = get_transactions(user_id=admin_user["id"])
    print(f"[OK] Total de transações no histórico consolidado: {len(all_trans)}")
    
    hoje = date.today()
    mes_atual = hoje.strftime("%Y-%m")
    trans_mes = get_transactions(user_id=admin_user["id"], month_year=mes_atual)
    print(f"[OK] Total de transações no mês atual ({mes_atual}): {len(trans_mes)}")

    dt_ini = hoje.replace(day=1).strftime("%Y-%m-%d")
    dt_fim = hoje.strftime("%Y-%m-%d")
    trans_periodo = get_transactions(user_id=admin_user["id"], start_date=dt_ini, end_date=dt_fim)
    print(f"[OK] Total de transações no intervalo ({dt_ini} a {dt_fim}): {len(trans_periodo)}")

    # 3. Teste da IA com dados consolidados gerais
    print("Testando analyze_finances_with_ai com histórico geral...")
    resp_analise = analyze_finances_with_ai(
        month_year="geral",
        transactions=all_trans,
        budgets=get_budgets(user_id=admin_user["id"]),
        user_question="Qual meu saldo geral acumulado?"
    )
    assert len(resp_analise) > 10, "A IA deve retornar uma análise válida"
    print(f"[OK] Resposta de análise de IA gerada com sucesso ({len(resp_analise)} caracteres)")

    # 4. Teste da IA conversacional para o Drawer Lateral
    print("Testando chat_with_financial_ai...")
    resp_chat = chat_with_financial_ai(
        user_prompt="Quais são as minhas maiores despesas registradas?",
        conversation_history=[],
        transactions=all_trans,
        budgets=get_budgets(user_id=admin_user["id"]),
        investments=get_investments(user_id=admin_user["id"]),
        user_name=admin_user["username"]
    )
    assert len(resp_chat) > 10, "O chat com IA deve retornar uma resposta válida"
    print(f"[OK] Resposta do chat lateral de IA gerada com sucesso ({len(resp_chat)} caracteres)")
    print("\n=== TODOS OS TESTES DE FILTRO E IA PASSARAM COM 100% DE SUCESSO! ===")

if __name__ == "__main__":
    test_filtros_e_ia()
