import streamlit as st
from backend.database import init_db, verify_user
from backend.crud import process_recurring_bills
from frontend.components import apply_custom_css, modal_nova_movimentacao
from frontend.views import (
    view_dashboard,
    view_movimentacoes,
    view_contas_mensais,
    view_importacao_extratos,
    view_investimentos_orcamentos,
    view_consultor_configuracoes
)

# 1. Configuração da Página do Streamlit
st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inicialização do Banco e Aplicação do Design System
init_db()
apply_custom_css()

# 3. Gerenciamento do Estado de Sessão e Autenticação
if "user" not in st.session_state:
    st.session_state["user"] = None

def render_login():
    """Tela de login limpa, moderna e responsiva."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])

    with col_login:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h1 style="font-size: 2.2rem; margin-bottom: 0.2rem;">💰 Controle Financeiro</h1>
                <p style="color: #8b949e; font-size: 0.95rem;">Gestão de patrimônio inteligente e descomplicada</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            st.markdown("##### 🔐 Acesso ao Sistema")
            username = st.text_input("Usuário", placeholder="Usuário")
            password = st.text_input("Senha", type="password", placeholder="Senha")
            btn_entrar = st.form_submit_button("Entrar", type="primary", width="stretch")

            if btn_entrar:
                if not username.strip() or not password.strip():
                    st.error("Por favor, preencha o usuário e a senha.")
                else:
                    user_data = verify_user(username.strip(), password.strip())
                    if user_data:
                        st.session_state["user"] = user_data
                        # Dispara motor de recorrência na inicialização da sessão para o usuário logado
                        process_recurring_bills(user_id=user_data["id"])
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas. Tente novamente.")

        st.caption("ℹ️ Credencial padrão de primeiro acesso: **admin** / **admin123**")


# 4. Controle de Fluxo: Login vs Aplicação Principal
if not st.session_state["user"]:
    render_login()
else:
    user = st.session_state["user"]

    # Barra Lateral (Navegação & Perfil)
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 0.5rem 0 1rem 0;">
                <h2 style="margin: 0; font-size: 1.4rem;">💰 Finanças</h2>
                <span style="font-size: 0.8rem; color: #8b949e;">Olá, <strong>{user['username']}</strong> ({user['role'].upper()})</span>
            </div>
        """, unsafe_allow_html=True)

        # Botão principal de Ação: Nova Movimentação
        if st.button("➕ Nova Movimentação", type="primary", width="stretch"):
            modal_nova_movimentacao(user["id"])

        st.markdown("---")

        # Menu de Navegação Vertical Profissional (sem bolinhas de rádio)
        if "pagina_ativa" not in st.session_state:
            st.session_state["pagina_ativa"] = "📊 Dashboard Geral"

        menu_items = [
            ("📊 Dashboard Geral", "btn_nav_dashboard"),
            ("💳 Movimentações", "btn_nav_movimentacoes"),
            ("🔄 Contas Mensais", "btn_nav_contas_mensais"),
            ("📄 Importar Extrato", "btn_nav_importar_extrato"),
            ("📈 Investimentos & Orçamentos", "btn_nav_investimentos"),
            ("🤖 Consultor IA & Ajustes", "btn_nav_consultor_ia")
        ]

        st.caption("NAVEGAÇÃO")
        for nome_aba, btn_id in menu_items:
            is_active = (st.session_state["pagina_ativa"] == nome_aba)
            tipo_btn = "primary" if is_active else "secondary"
            if st.button(nome_aba, key=btn_id, type=tipo_btn, width="stretch"):
                if st.session_state["pagina_ativa"] != nome_aba:
                    st.session_state["pagina_ativa"] = nome_aba
                    st.rerun()

        escolha = st.session_state["pagina_ativa"]

        st.markdown("---")
        if st.button("🚪 Sair do Sistema", width="stretch", key="btn_logout"):
            st.session_state["user"] = None
            st.rerun()

    # Roteamento de Telas
    if escolha == "📊 Dashboard Geral":
        view_dashboard(user)
    elif escolha == "💳 Movimentações":
        view_movimentacoes(user)
    elif escolha == "🔄 Contas Mensais":
        view_contas_mensais(user)
    elif escolha == "📄 Importar Extrato":
        view_importacao_extratos(user)
    elif escolha == "📈 Investimentos & Orçamentos":
        view_investimentos_orcamentos(user)
    elif escolha == "🤖 Consultor IA & Ajustes":
        view_consultor_configuracoes(user)

