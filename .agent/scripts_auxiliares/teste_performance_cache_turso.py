import time
import os
import sys
from dotenv import load_dotenv

# Garantir importações do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import init_db, get_connection, close_shared_libsql_client
from backend.crud import (
    get_transactions, get_budgets, get_investments,
    get_recurring_bills, get_users, add_transaction,
    delete_transaction, clear_app_cache
)

def run_performance_diagnostics():
    print("=" * 70)
    print("🚀 DIAGNÓSTICO DE PERFORMANCE & CACHE (TURSO CLOUD)")
    print("=" * 70)

    # 1. Teste de init_db() (Memoização vs Execução de Rede)
    print("\n[1/4] Testando inicialização de banco (init_db):")
    t0 = time.time()
    init_db(force=True)  # Força execução de rede
    t_init_cold = time.time() - t0
    print(f"  - Execução Direta / Cold (Rede Turso): {t_init_cold*1000:.1f} ms")

    t0 = time.time()
    init_db(force=False)  # Memoizado
    t_init_warm = time.time() - t0
    print(f"  - Execução Memoizada / Warm: {t_init_warm*1000:.3f} ms")
    if t_init_warm > 0:
        speedup_init = t_init_cold / max(t_init_warm, 0.00001)
        print(f"  - Ganho de Performance: {speedup_init:.1f}x mais rápido!")

    # 2. Teste de get_transactions()
    print("\n[2/4] Testando consulta de movimentações (get_transactions):")
    clear_app_cache()
    t0 = time.time()
    trans_cold = get_transactions(user_id=1)
    t_trans_cold = time.time() - t0
    print(f"  - Consulta Direta / Cold (Rede Turso): {t_trans_cold*1000:.1f} ms ({len(trans_cold)} registros)")

    t0 = time.time()
    trans_warm = get_transactions(user_id=1)
    t_trans_warm = time.time() - t0
    print(f"  - Consulta em Cache / Warm (@st.cache_data): {t_trans_warm*1000:.3f} ms ({len(trans_warm)} registros)")
    speedup_trans = t_trans_cold / max(t_trans_warm, 0.00001)
    print(f"  - Ganho de Performance: {speedup_trans:.1f}x mais rápido!")

    # 3. Teste de dados estáticos/frequentes (Orçamentos, Investimentos, Contas Fixas, Usuários)
    print("\n[3/4] Testando consultas de suporte (Orçamentos, Investimentos, Usuários):")
    clear_app_cache()
    
    # Orçamentos
    t0 = time.time()
    b_cold = get_budgets(user_id=1)
    t_b_cold = time.time() - t0
    t0 = time.time()
    b_warm = get_budgets(user_id=1)
    t_b_warm = time.time() - t0
    print(f"  - Orçamentos: Cold={t_b_cold*1000:.1f}ms | Warm={t_b_warm*1000:.3f}ms ({t_b_cold/max(t_b_warm, 0.00001):.1f}x mais rápido)")

    # Investimentos
    t0 = time.time()
    inv_cold = get_investments(user_id=1)
    t_inv_cold = time.time() - t0
    t0 = time.time()
    inv_warm = get_investments(user_id=1)
    t_inv_warm = time.time() - t0
    print(f"  - Investimentos: Cold={t_inv_cold*1000:.1f}ms | Warm={t_inv_warm*1000:.3f}ms ({t_inv_cold/max(t_inv_warm, 0.00001):.1f}x mais rápido)")

    # Contas Fixas
    t0 = time.time()
    rb_cold = get_recurring_bills(user_id=1)
    t_rb_cold = time.time() - t0
    t0 = time.time()
    rb_warm = get_recurring_bills(user_id=1)
    t_rb_warm = time.time() - t0
    print(f"  - Contas Recorrentes: Cold={t_rb_cold*1000:.1f}ms | Warm={t_rb_warm*1000:.3f}ms ({t_rb_cold/max(t_rb_warm, 0.00001):.1f}x mais rápido)")

    # Usuários
    t0 = time.time()
    u_cold = get_users()
    t_u_cold = time.time() - t0
    t0 = time.time()
    u_warm = get_users()
    t_u_warm = time.time() - t0
    print(f"  - Usuários: Cold={t_u_cold*1000:.1f}ms | Warm={t_u_warm*1000:.3f}ms ({t_u_cold/max(t_u_warm, 0.00001):.1f}x mais rápido)")

    # 4. Teste de Invalidação Ativa do Cache (Mutação e Atualização Instantânea)
    print("\n[4/4] Testando consistência e invalidação de cache em mutações:")
    gid = add_transaction(
        user_id=1,
        trans_type="despesa",
        category="Alimentação",
        description="Teste Performance Invalidação Cache",
        amount=19.90,
        due_date="2026-10-21",
        status="Pendente"
    )
    # A consulta deve refletir o novo registro imediatamente
    trans_pos_insert = get_transactions(user_id=1)
    achou = any(t["description"] == "Teste Performance Invalidação Cache" for t in trans_pos_insert)
    assert achou, "Erro: registro recém-inserido não encontrado após mutação!"
    print("  - Invalidação automática após INSERT: SUCESSO (novo registro detectado imediatamente)")

    # Exclusão do registro de teste
    item_teste = next(t for t in trans_pos_insert if t["description"] == "Teste Performance Invalidação Cache")
    delete_transaction(item_teste["id"], user_id=1)
    trans_pos_del = get_transactions(user_id=1)
    ainda_existe = any(t["description"] == "Teste Performance Invalidação Cache" for t in trans_pos_del)
    assert not ainda_existe, "Erro: registro excluído ainda visível no cache!"
    print("  - Invalidação automática após DELETE: SUCESSO (registro removido imediatamente)")

    close_shared_libsql_client()

    # Resumo Geral
    print("\n" + "=" * 70)
    print("✅ RESULTADO DO DIAGNÓSTICO: TODAS AS OTIMIZAÇÕES FORAM VALIDADAS COM SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    run_performance_diagnostics()
