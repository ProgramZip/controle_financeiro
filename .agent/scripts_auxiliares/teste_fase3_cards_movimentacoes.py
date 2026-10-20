import sys
from pathlib import Path
from datetime import date

# Adiciona a raiz do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, verify_user
from backend.crud import (
    get_transactions, add_transaction, delete_transaction
)
from frontend.components import render_metric_card

def run_tests():
    print("Iniciando testes da Fase 3: Cards de Resumo de Receitas e Despesas...")
    init_db()

    admin = verify_user("admin", "admin123")
    assert admin is not None, "Usuario admin deve existir."
    u_id = admin["id"]

    # 1. Inserir lançamentos de teste para validação de soma e contagem
    t1 = add_transaction(
        user_id=u_id,
        trans_type="despesa",
        category="Alimentação",
        description="Teste Fase 3 Despesa",
        amount=150.75,
        payment_method="À Vista",
        due_date="2026-10-20",
        status="Pago"
    )
    t2 = add_transaction(
        user_id=u_id,
        trans_type="receita",
        category="Salário",
        description="Teste Fase 3 Receita",
        amount=3500.00,
        payment_method="À Vista",
        due_date="2026-10-05",
        status="Recebido"
    )

    # 2. Consultar lançamentos do usuário
    all_trans = get_transactions(user_id=u_id)
    assert len(all_trans) >= 2, "Deveria haver pelo menos 2 transacoes."

    # 3. Testar agregação geral (Todos os Lançamentos)
    desp_geral = [t for t in all_trans if t["type"] == "despesa"]
    rec_geral = [t for t in all_trans if t["type"] == "receita"]

    tot_desp_geral = sum(t["amount"] for t in desp_geral)
    tot_rec_geral = sum(t["amount"] for t in rec_geral)

    assert tot_desp_geral >= 150.75, "Total de despesas incorreto."
    assert tot_rec_geral >= 3500.00, "Total de receitas incorreto."
    print(f"  [OK] Agregacao Geral: {len(desp_geral)} despesas (R$ {tot_desp_geral:,.2f}), {len(rec_geral)} receitas (R$ {tot_rec_geral:,.2f}).")

    # 4. Testar agregação por mês específico (2026-10)
    trans_mes = [t for t in all_trans if str(t.get("due_date", ""))[:7] == "2026-10"]
    desp_mes = [t for t in trans_mes if t["type"] == "despesa"]
    rec_mes = [t for t in trans_mes if t["type"] == "receita"]

    tot_desp_mes = sum(t["amount"] for t in desp_mes)
    tot_rec_mes = sum(t["amount"] for t in rec_mes)

    assert any(t["description"] == "Teste Fase 3 Despesa" for t in desp_mes), "Despesa de teste nao encontrada no mes 2026-10."
    assert any(t["description"] == "Teste Fase 3 Receita" for t in rec_mes), "Receita de teste nao encontrada no mes 2026-10."
    print(f"  [OK] Agregacao Mensal (2026-10): {len(desp_mes)} despesas (R$ {tot_desp_mes:,.2f}), {len(rec_mes)} receitas (R$ {tot_rec_mes:,.2f}).")

    # 5. Validar que as funções de visualização em frontend/views.py compilam e carregam sem erros
    import frontend.views as fv
    assert hasattr(fv, "view_movimentacoes"), "view_movimentacoes deve existir em frontend.views"
    print("  [OK] Modulo frontend/views e view_movimentacoes carregados com sucesso.")

    # Limpeza
    # Obter os IDs reais criados
    for t in all_trans:
        if t["description"] in ("Teste Fase 3 Despesa", "Teste Fase 3 Receita"):
            delete_transaction(t["id"], user_id=u_id)
    print("  [OK] Registros de teste limpos.")

    print("\nTODOS OS TESTES DA FASE 3 PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    run_tests()
