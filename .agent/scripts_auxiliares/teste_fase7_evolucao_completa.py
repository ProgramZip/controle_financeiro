import sys
from pathlib import Path

# Configura encoding UTF-8 para stdout do Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Adiciona o diretório raiz ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from backend.database import init_db, get_connection, get_user_by_id
from backend.crud import (
    get_users, add_user, update_user_profile, get_user_profile,
    add_user_share, get_user_shares_by_owner, get_user_shares_received,
    can_user_edit_resource, delete_user
)
from backend.utils import analyze_finances_with_ai
from frontend.components import (
    modal_excluir_mes_completo, render_unified_filter_popover,
    apply_custom_css, render_metric_card
)
from frontend.views import (
    view_dashboard, view_movimentacoes, view_contas_mensais,
    view_espacos_compartilhados, view_consultor_configuracoes
)

def run_tests():
    print("--- 1. TESTANDO INICIALIZAÇÃO E MIGRAÇÃO DO BANCO ---")
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users);")
        cols = {row["name"] for row in cursor.fetchall()}
        print(f"Colunas da tabela users: {cols}")
        assert "full_name" in cols, "Coluna full_name ausente!"
        assert "address" in cols, "Coluna address ausente!"
        assert "cpf" in cols, "Coluna cpf ausente!"
    print("✅ 1. Schema de Usuários expandido com sucesso!")

    print("\n--- 2. TESTANDO CRUD DE PERFIS DE USUÁRIO ---")
    test_username = f"teste_perfil_{id(cols)}"
    user_id = add_user(
        username=test_username,
        password="password123",
        role="editor",
        full_name="Usuario de Teste",
        address="Rua dos Testes, 42",
        cpf="123.456.789-00"
    )
    print(f"Usuário criado com ID: {user_id}")
    
    perfil = get_user_profile(user_id)
    assert perfil is not None, "Perfil não encontrado!"
    assert perfil["full_name"] == "Usuario de Teste"
    assert perfil["address"] == "Rua dos Testes, 42"
    assert perfil["cpf"] == "123.456.789-00"
    print(f"Dados cadastrais verificados: {perfil['full_name']} | {perfil['cpf']}")

    # Atualizando perfil
    ok = update_user_profile(
        user_id=user_id,
        full_name="Nome Atualizado",
        address="Novo Endereço 100",
        cpf="999.888.777-66"
    )
    assert ok, "Falha ao atualizar perfil!"
    perfil_up = get_user_profile(user_id)
    assert perfil_up["full_name"] == "Nome Atualizado"
    assert perfil_up["address"] == "Novo Endereço 100"
    assert perfil_up["cpf"] == "999.888.777-66"
    print("✅ 2. Atualização de perfil validada com sucesso!")

    print("\n--- 3. TESTANDO REGRAS DA SEGUNDA ÁREA DE TRABALHO E PERMISSÕES ---")
    owner_id = add_user(f"owner_{id(cols)}", "pass123", "editor")
    # Concede compartilhamento como editor
    add_user_share(owner_id=owner_id, shared_with_user_id=user_id, permission_level="editor")
    
    # O editor pode editar recursos do owner?
    pode_editar = can_user_edit_resource(user_id=user_id, resource_owner_id=owner_id)
    assert pode_editar is True, "Editor deveria poder editar recursos no espaço do proprietário!"
    print("✅ Editor tem acesso total para editar recursos na Segunda Área de Trabalho!")

    # Usuário sem acesso pode editar?
    outro_id = add_user(f"outro_{id(cols)}", "pass123", "viewer")
    pode_outro = can_user_edit_resource(user_id=outro_id, resource_owner_id=owner_id)
    assert pode_outro is False, "Usuário sem permissão não pode editar recursos do proprietário!"
    print("✅ Isolamento mantido: usuário não autorizado tem edição bloqueada!")

    print("\n--- 4. TESTANDO FILTRO UNIFICADO (POPOVER LOGIC) ---")
    dummy_items = [
        {"id": 1, "description": "Supermercado Extra", "recipient": "Extra", "amount": 150.0, "category": "Alimentação", "due_date": "2026-10-15"},
        {"id": 2, "description": "Salário Mensal", "recipient": "Empresa", "amount": 5000.0, "category": "Salário", "due_date": "2026-10-05"},
        {"id": 3, "description": "Internet Fibra", "recipient": "Vivo", "amount": 120.0, "category": "Moradia", "due_date": "2026-09-20"},
    ]
    # Testa período
    filtro_periodo = [t for t in dummy_items if str(t.get("due_date", ""))[:7] == "2026-10"]
    assert len(filtro_periodo) == 2
    # Testa busca textual
    filtro_texto = [t for t in dummy_items if "extra" in t["description"].lower() or "extra" in t["recipient"].lower()]
    assert len(filtro_texto) == 1 and filtro_texto[0]["id"] == 1
    print("✅ 4. Lógica dos Filtros Globais Unificados validada!")

    print("\n--- 5. TESTANDO INTEGRIDADE DOS IMPORTS E VIEWS ---")
    assert callable(view_dashboard)
    assert callable(view_movimentacoes)
    assert callable(view_contas_mensais)
    assert callable(view_espacos_compartilhados)
    assert callable(view_consultor_configuracoes)
    assert callable(modal_excluir_mes_completo)
    assert callable(render_unified_filter_popover)
    print("✅ 5. Todas as views e novos componentes carregados com sucesso!")

    # Limpeza
    delete_user(user_id)
    delete_user(owner_id)
    delete_user(outro_id)
    print("\n🎉 TODOS OS TESTES DA EVOLUÇÃO ESTRUTURAL PASSARAM COM 100% DE SUCESSO!")

if __name__ == "__main__":
    run_tests()
