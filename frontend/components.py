import os
import streamlit as st
from datetime import date, datetime
from backend.database import get_connection
from backend.crud import (
    add_transaction, add_recurring_bill, update_transaction, update_recurring_bill,
    delete_transactions_by_month, get_transactions, get_budgets, get_investments
)
from backend.utils import (
    CATEGORIAS_DESPESA,
    CATEGORIAS_RECEITA,
    save_invoice_image,
    decode_qr_code,
    chat_with_financial_ai
)


def apply_custom_css():
    """Aplica estilos CSS modernos, responsivos e Mobile-First no Streamlit."""
    st.markdown("""
        <style>
        /* Importação de fonte moderna Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Otimizações Mobile-First */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 2rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
            .stMetric {
                padding: 10px !important;
            }
            .metric-card {
                margin-bottom: 0.8rem !important;
            }
        }

        /* Estilização de Cartões de Métricas */
        .metric-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 1.1rem;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(0, 200, 150, 0.4);
        }
        .metric-title {
            font-size: 0.85rem;
            color: #8b949e;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 0.3rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.2rem;
        }
        .metric-sub {
            font-size: 0.78rem;
            color: #3fb950;
        }

        /* ========================================================= */
        /* PADRONIZAÇÃO GLOBAL DE TODOS OS BOTÕES DO SISTEMA         */
        /* Formato retangular com cantos levemente arredondados (8px)*/
        /* ========================================================= */
        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        [data-testid="stPopover"] > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            min-height: 2.4rem !important;
            height: auto !important;
            width: auto;
            line-height: 1.4 !important;
            text-align: center !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
        }

        /* Botões Primários */
        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background-color: #238636 !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            color: #ffffff !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
        }
        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background-color: #2ea043 !important;
            border-color: #3fb950 !important;
            box-shadow: 0 4px 12px rgba(35, 134, 54, 0.35) !important;
            transform: translateY(-1px) !important;
        }

        /* Botões Secundários */
        div.stButton > button[kind="secondary"],
        div[data-testid="stFormSubmitButton"] > button[kind="secondary"],
        div[data-testid="stDownloadButton"] > button,
        [data-testid="stPopover"] > button {
            background-color: #21262d !important;
            border: 1px solid #30363d !important;
            color: #c9d1d9 !important;
        }
        div.stButton > button[kind="secondary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        [data-testid="stPopover"] > button:hover {
            background-color: #30363d !important;
            border-color: #8b949e !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
        }

        /* Estilização de botões da barra lateral (menu executivo) */
        section[data-testid="stSidebar"] div.stButton > button {
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 0.65rem 1rem !important;
            font-size: 0.92rem !important;
            border-radius: 8px !important;
            margin-bottom: 0.25rem !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }
        section[data-testid="stSidebar"] div.stButton > button:hover {
            border-color: rgba(63, 185, 80, 0.5) !important;
            transform: translateX(2px) !important;
        }

        /* Tabelas responsivas com cantos arredondados */
        [data-testid="stDataFrame"] {
            border-radius: 10px !important;
            overflow: hidden !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        /* Ajuste de divisores para visual limpo */
        hr {
            margin: 1.2rem 0 !important;
            border-color: rgba(255, 255, 255, 0.08) !important;
        }

        /* ========================================================= */
        /* BOTÃO FLUTUANTE DE IA (FAB - CANTO INFERIOR DIREITO)       */
        /* Isolamento estrito: NENHUM outro botão é afetado          */
        /* ========================================================= */
        .ai-fab-container,
        div[data-testid="element-container"]:has(#floating-ai-fab-anchor) + div[data-testid="element-container"] {
            position: fixed !important;
            bottom: 24px !important;
            right: 24px !important;
            z-index: 999999 !important;
            width: 60px !important;
            height: 60px !important;
            padding: 0 !important;
            margin: 0 !important;
            pointer-events: auto !important;
        }

        .ai-fab-container div.stButton,
        div[data-testid="element-container"]:has(#floating-ai-fab-anchor) + div[data-testid="element-container"] div.stButton {
            width: 60px !important;
            height: 60px !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        .ai-fab-button,
        .ai-fab-container div.stButton > button,
        div[data-testid="element-container"]:has(#floating-ai-fab-anchor) + div[data-testid="element-container"] div.stButton > button {
            width: 60px !important;
            height: 60px !important;
            min-height: 60px !important;
            max-height: 60px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #1f6feb 0%, #238636 100%) !important;
            color: #ffffff !important;
            border: 2px solid rgba(255, 255, 255, 0.4) !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5), 0 0 16px rgba(35, 134, 54, 0.6) !important;
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 !important;
            margin: 0 !important;
            cursor: pointer !important;
            transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }

        .ai-fab-button:hover,
        .ai-fab-container div.stButton > button:hover,
        div[data-testid="element-container"]:has(#floating-ai-fab-anchor) + div[data-testid="element-container"] div.stButton > button:hover {
            transform: scale(1.1) rotate(6deg) !important;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.7), 0 0 24px rgba(35, 134, 54, 0.85) !important;
            border-color: #58a6ff !important;
        }

        div[data-testid="element-container"]:has(#floating-ai-fab-anchor) {
            display: none !important;
        }

        /* ========================================================= */
        /* CHAT LATERAL DESLIZANTE (DRAWER DE IA)                    */
        /* ========================================================= */
        .ai-drawer-panel,
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] #ai-drawer-anchor),
        div[data-testid="stVerticalBlock"]:has(> div #ai-drawer-anchor) {
            position: fixed !important;
            top: 0 !important;
            right: 0 !important;
            width: 440px !important;
            max-width: 90vw !important;
            height: 100vh !important;
            background-color: #0d1117 !important;
            border-left: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: -10px 0 35px rgba(0, 0, 0, 0.75) !important;
            z-index: 999990 !important;
            padding: 1.2rem 1.2rem 2.5rem 1.2rem !important;
            overflow-y: auto !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 0.8rem !important;
            animation: drawerSlideInRight 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        div[data-testid="element-container"]:has(#ai-drawer-anchor) {
            display: none !important;
        }

        /* Botões dentro do drawer lateral */
        .ai-drawer-panel div.stButton > button,
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] #ai-drawer-anchor) div.stButton > button {
            border-radius: 8px !important;
            font-size: 0.85rem !important;
            padding: 0.45rem 0.6rem !important;
            min-height: 2.2rem !important;
            height: auto !important;
            width: 100% !important;
            line-height: 1.3 !important;
        }

        /* Perguntas Rápidas (Chips) dentro do drawer */
        .ai-drawer-panel div[data-testid="stHorizontalBlock"] div.stButton > button,
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] #ai-drawer-anchor) div[data-testid="stHorizontalBlock"] div.stButton > button {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            color: #e6edf3 !important;
            text-align: center !important;
            font-weight: 500 !important;
            margin-bottom: 0.35rem !important;
        }
        .ai-drawer-panel div[data-testid="stHorizontalBlock"] div.stButton > button:hover,
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] #ai-drawer-anchor) div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
            background-color: rgba(56, 139, 253, 0.15) !important;
            border-color: #58a6ff !important;
            color: #58a6ff !important;
        }

        @keyframes drawerSlideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        /* Card do Filtro Global Padronizado */
        .filter-period-box {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
        }
        </style>
    """, unsafe_allow_html=True)



def render_metric_card(title: str, value: str, sub: str = "", color: str = "#3fb950", icon: str = ""):
    """Renderiza um card visual de métrica responsivo."""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{icon} {title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-sub" style="color: {color};">{sub}</div>' if sub else ''}
        </div>
    """, unsafe_allow_html=True)


@st.dialog("➕ Nova Movimentação", width="large")
def modal_nova_movimentacao(user_id: int = None):
    """
    Modal pop-up para cadastro ágil de Despesas e Receitas seguindo
    integralmente as regras do projeto.md.
    """
    # 1. Seleção Obrigatória do Tipo
    tipo = st.radio(
        "Tipo de Movimentação",
        options=["Despesa", "Receita"],
        horizontal=True,
        index=0,
        key="modal_mov_tipo"
    )

    st.markdown("---")

    if tipo == "Despesa":
        # ------------------ FLUXO DE DESPESA ------------------
        col1, col2 = st.columns([1, 1])
        with col1:
            categoria = st.selectbox(
                "Categoria *",
                options=CATEGORIAS_DESPESA,
                index=0,
                key="modal_desp_categoria"
            )
        with col2:
            valor = st.number_input(
                "Valor Total (R$) *",
                min_value=0.01,
                value=10.0,
                step=1.0,
                format="%.2f",
                key="modal_desp_valor"
            )

        descricao = st.text_input(
            "Descrição *",
            placeholder="Ex: Almoço de negócios, Parcela do Celular...",
            key="modal_desp_descricao"
        )

        col3, col4 = st.columns([1, 1])
        with col3:
            forma_pagamento = st.radio(
                "Forma de Pagamento",
                options=["À Vista", "Parcelado"],
                horizontal=True,
                key="modal_desp_forma"
            )
        with col4:
            data_vencimento = st.date_input(
                "Data de Vencimento *",
                value=date.today(),
                key="modal_desp_data"
            )

        num_parcelas = 1
        if forma_pagamento == "Parcelado":
            st.markdown("##### 💳 Detalhes do Parcelamento")
            num_parcelas = st.number_input(
                "Número de Parcelas",
                min_value=2,
                max_value=72,
                value=2,
                step=1,
                key="modal_desp_parcelas"
            )
            valor_parcela = valor / num_parcelas
            st.info(f"💡 **Resumo do Parcelamento:** {num_parcelas}x de **R$ {valor_parcela:,.2f}** (primeira parcela em {data_vencimento.strftime('%d/%m/%Y')})")

        col5, col6 = st.columns([1, 1])
        with col5:
            status = st.radio(
                "Status da Despesa",
                options=["Pago", "Pendente"],
                horizontal=True,
                index=1,
                key="modal_desp_status"
            )
        with col6:
            conta_mensal = st.radio(
                "Salvar como Conta Mensal Recorrente?",
                options=["Não", "Sim"],
                horizontal=True,
                key="modal_desp_conta_mensal",
                help="Se marcado como Sim, esta despesa será adicionada à matriz de contas fixas que se repetem todo mês."
            )

        # Seção de Nota Fiscal
        st.markdown("##### 🧾 Nota Fiscal / Comprovante")
        tem_nota = st.radio(
            "Deseja anexar Nota Fiscal ou comprovante?",
            options=["Não", "Sim"],
            horizontal=True,
            key="modal_desp_tem_nota"
        )

        invoice_path = None
        if tem_nota == "Sim":
            metodo_foto = st.radio(
                "Forma de Envio",
                options=["Upload de Arquivo", "Câmera do Dispositivo"],
                horizontal=True,
                key="modal_desp_metodo_foto"
            )

            foto_file = None
            if metodo_foto == "Upload de Arquivo":
                foto_file = st.file_uploader("Selecione a foto da nota", type=["jpg", "jpeg", "png"], key="modal_desp_file_uploader")
            else:
                foto_file = st.camera_input("Tirar foto da nota fiscal", key="modal_desp_camera_input")

            if foto_file is not None:
                foto_bytes = foto_file.getvalue()
                # Tenta decodificar QR Code
                qr_conteudo = decode_qr_code(foto_bytes)
                if qr_conteudo:
                    st.success(f"🔍 **QR Code Decodificado com Sucesso:** {qr_conteudo}")
                else:
                    st.caption("ℹ️ Nenhum QR Code legível detectado nesta imagem, mas o comprovante será salvo.")

                # Gravação da imagem
                try:
                    invoice_path = save_invoice_image(foto_bytes)
                    st.caption(f"Arquivo salvo com sucesso em `{invoice_path}`")
                except Exception as e:
                    st.error(f"Erro ao salvar nota fiscal: {e}")

        st.markdown("---")

        if st.button("💾 Gravar Despesa", type="primary", width="stretch", key="modal_desp_btn_salvar"):
            if not descricao.strip():
                st.error("Por favor, preencha o campo Descrição.")
                return

            try:
                due_date_str = data_vencimento.strftime("%Y-%m-%d")
                gid = add_transaction(
                    user_id=user_id,
                    trans_type="despesa",
                    category=categoria,
                    description=descricao.strip(),
                    amount=valor,
                    payment_method=forma_pagamento,
                    installment_total=num_parcelas,
                    due_date=due_date_str,
                    status=status,
                    invoice_path=invoice_path,
                    is_recurring=1 if conta_mensal == "Sim" else 0
                )

                # Se marcou conta mensal, cadastra também em recurring_bills
                if conta_mensal == "Sim":
                    add_recurring_bill(
                        user_id=user_id,
                        bill_type="despesa",
                        category=categoria,
                        description=descricao.strip(),
                        amount=valor,
                        due_day=data_vencimento.day,
                        is_active=1
                    )

                st.success("✅ Despesa cadastrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar movimentação: {e}")

    else:
        # ------------------ FLUXO DE RECEITA ------------------
        col1, col2 = st.columns([1, 1])
        with col1:
            categoria = st.selectbox(
                "Categoria de Receita *",
                options=CATEGORIAS_RECEITA,
                index=0,
                key="modal_rec_categoria"
            )
        with col2:
            valor = st.number_input(
                "Valor do Recebimento (R$) *",
                min_value=0.01,
                value=100.0,
                step=10.0,
                format="%.2f",
                key="modal_rec_valor"
            )

        descricao = st.text_input(
            "Descrição *",
            placeholder="Ex: Salário da empresa, Venda de consultoria, Aluguel do imóvel...",
            key="modal_rec_descricao"
        )

        col3, col4 = st.columns([1, 1])
        with col3:
            data_recebimento = st.date_input(
                "Data do Recebimento *",
                value=date.today(),
                key="modal_rec_data"
            )
        with col4:
            status_rec = st.radio(
                "Status do Recebimento",
                options=["Recebido", "Pendente"],
                horizontal=True,
                index=0,
                key="modal_rec_status"
            )

        recebimento_mensal = st.radio(
            "Salvar como Recebimento Mensal Fixo?",
            options=["Não", "Sim"],
            horizontal=True,
            key="modal_rec_mensal",
            help="Se Sim, este recebimento será adicionado à matriz de recorrência que se repete mensalmente."
        )

        st.markdown("---")

        if st.button("💾 Gravar Receita", type="primary", width="stretch", key="modal_rec_btn_salvar"):
            if not descricao.strip():
                st.error("Por favor, preencha o campo Descrição.")
                return

            try:
                date_str = data_recebimento.strftime("%Y-%m-%d")
                status_val = "Recebido" if status_rec == "Recebido" else "Pendente"

                add_transaction(
                    user_id=user_id,
                    trans_type="receita",
                    category=categoria,
                    description=descricao.strip(),
                    amount=valor,
                    payment_method="À Vista",
                    installment_total=1,
                    due_date=date_str,
                    status=status_val,
                    is_recurring=1 if recebimento_mensal == "Sim" else 0
                )

                if recebimento_mensal == "Sim":
                    add_recurring_bill(
                        user_id=user_id,
                        bill_type="receita",
                        category=categoria,
                        description=descricao.strip(),
                        amount=valor,
                        due_day=data_recebimento.day,
                        is_active=1
                    )

                st.success("✅ Receita cadastrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar movimentação: {e}")


@st.dialog("➕ Nova Conta Fixa Recorrente", width="medium")
def modal_nova_conta_recorrente(user_id: int = None):
    """
    Modal pop-up flutuante para cadastro de contas mensais fixas recorrentes,
    eliminando formulários ou expanders estáticos inline.
    """
    c_tipo = st.radio("Tipo da Conta", ["despesa", "receita"], horizontal=True, key="modal_bill_tipo")
    c_cat = st.selectbox(
        "Categoria *",
        options=CATEGORIAS_DESPESA if c_tipo == "despesa" else CATEGORIAS_RECEITA,
        key="modal_bill_cat"
    )
    c_desc = st.text_input("Descrição *", placeholder="Ex: Internet Fibra, Aluguel, Salário...", key="modal_bill_desc")
    c_val = st.number_input("Valor Mensal (R$) *", min_value=0.01, step=10.0, format="%.2f", key="modal_bill_val")
    c_dia = st.number_input("Dia do Vencimento no Mês (1-31) *", min_value=1, max_value=31, value=10, key="modal_bill_dia")

    st.markdown("---")
    if st.button("💾 Salvar Conta Recorrente", type="primary", width="stretch", key="modal_bill_submit"):
        if c_desc.strip():
            try:
                add_recurring_bill(user_id, c_tipo, c_cat, c_desc.strip(), c_val, int(c_dia))
                st.success("✅ Conta recorrente cadastrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar conta: {e}")
        else:
            st.error("Por favor, preencha o campo Descrição.")


@st.dialog("✏️ Alterar Movimentação", width="large")
def modal_editar_movimentacao(item: dict, user_id: int):
    """
    Modal flutuante para edição completa de uma movimentação existente.
    Permite alterar tipo, categoria, descrição, valor, data, status e comprovante.
    """
    item_id = item["id"]
    st.caption(f"Editando Lançamento ID #{item_id}")

    # 1. Tipo
    cur_tipo = "Despesa" if item.get("type") == "despesa" else "Receita"
    tipo = st.radio(
        "Tipo de Movimentação",
        options=["Despesa", "Receita"],
        horizontal=True,
        index=0 if cur_tipo == "Despesa" else 1,
        key=f"edit_mov_tipo_{item_id}"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        cats = CATEGORIAS_DESPESA if tipo == "Despesa" else CATEGORIAS_RECEITA
        cur_cat = item.get("category", cats[0])
        cat_idx = cats.index(cur_cat) if cur_cat in cats else 0
        categoria = st.selectbox("Categoria *", options=cats, index=cat_idx, key=f"edit_mov_cat_{item_id}")
    with col2:
        cur_val = float(item.get("amount", 10.0))
        valor = st.number_input("Valor Total (R$) *", min_value=0.01, value=cur_val, step=1.0, format="%.2f", key=f"edit_mov_val_{item_id}")

    descricao = st.text_input("Descrição *", value=item.get("description", ""), key=f"edit_mov_desc_{item_id}")

    col3, col4 = st.columns(2)
    with col3:
        if tipo == "Despesa":
            cur_forma = item.get("payment_method", "À Vista")
            forma_idx = 0 if cur_forma == "À Vista" else 1
            forma_pag = st.radio("Forma de Pagamento", ["À Vista", "Parcelado"], index=forma_idx, horizontal=True, key=f"edit_mov_forma_{item_id}")
        else:
            forma_pag = "À Vista"
            st.info("Forma de Pagamento: À Vista")
    with col4:
        try:
            cur_dt = datetime.strptime(str(item.get("due_date", ""))[:10], "%Y-%m-%d").date()
        except Exception:
            cur_dt = date.today()
        data_venc = st.date_input("Data de Vencimento / Referência *", value=cur_dt, key=f"edit_mov_dt_{item_id}")

    col5, col6 = st.columns(2)
    with col5:
        if tipo == "Despesa":
            st_opts = ["Pendente", "Pago"]
        else:
            st_opts = ["Pendente", "Recebido"]
        cur_st = item.get("status", st_opts[0])
        st_idx = st_opts.index(cur_st) if cur_st in st_opts else 0
        status_sel = st.radio("Status *", st_opts, index=st_idx, horizontal=True, key=f"edit_mov_st_{item_id}")
    with col6:
        if item.get("installment_total", 1) > 1:
            st.caption(f"Parcela: **{item['installment_current']}/{item['installment_total']}** (Grupo: `{item.get('group_id', 'N/A')}`)")
        else:
            st.caption("Lançamento avulso (parcela única)")

    # Comprovante / Nota Fiscal
    st.markdown("##### 🧾 Comprovante / Nota Fiscal")
    current_invoice = item.get("invoice_path")
    invoice_path_final = current_invoice
    remover_comprovante = False

    if current_invoice and os.path.exists(current_invoice):
        col_inv1, col_inv2 = st.columns([1, 2])
        with col_inv1:
            st.image(current_invoice, caption="Comprovante Atual", width=150)
        with col_inv2:
            remover_comprovante = st.checkbox("Excluir este comprovante", key=f"chk_rem_inv_{item_id}")
    else:
        st.caption("Nenhum comprovante anexado atualmente.")

    novo_arquivo = st.file_uploader("Substituir / Anexar novo comprovante (JPG, PNG)", type=["jpg", "jpeg", "png"], key=f"upload_edit_inv_{item_id}")
    if novo_arquivo is not None:
        try:
            invoice_path_final = save_invoice_image(novo_arquivo.getvalue())
            st.success("Novo comprovante processado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar novo comprovante: {e}")
    elif remover_comprovante:
        invoice_path_final = None

    st.markdown("---")
    if st.button("💾 Salvar Alterações", type="primary", width="stretch", key=f"btn_salvar_edit_{item_id}"):
        if not descricao.strip():
            st.error("Por favor, preencha o campo Descrição.")
            return

        try:
            due_date_str = data_venc.strftime("%Y-%m-%d")
            ok = update_transaction(
                transaction_id=item_id,
                requesting_user_id=user_id,
                type=tipo.lower(),
                category=categoria,
                description=descricao.strip(),
                amount=round(valor, 2),
                payment_method=forma_pag,
                due_date=due_date_str,
                status=status_sel,
                invoice_path=invoice_path_final
            )
            if ok:
                st.success("✅ Movimentação alterada com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao atualizar a movimentação no banco de dados.")
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")


@st.dialog("✏️ Alterar Conta Mensal Recorrente", width="medium")
def modal_editar_conta_recorrente(bill: dict, user_id: int):
    """
    Modal flutuante para edição de uma conta fixa recorrente.
    """
    bill_id = bill["id"]
    st.caption(f"Editando Conta Recorrente ID #{bill_id}")

    cur_tipo = bill.get("type", "despesa")
    c_tipo = st.radio("Tipo da Conta", ["despesa", "receita"], index=0 if cur_tipo == "despesa" else 1, horizontal=True, key=f"edit_bill_tipo_{bill_id}")
    cats = CATEGORIAS_DESPESA if c_tipo == "despesa" else CATEGORIAS_RECEITA
    cur_cat = bill.get("category", cats[0])
    cat_idx = cats.index(cur_cat) if cur_cat in cats else 0
    c_cat = st.selectbox("Categoria *", options=cats, index=cat_idx, key=f"edit_bill_cat_{bill_id}")

    c_desc = st.text_input("Descrição *", value=bill.get("description", ""), key=f"edit_bill_desc_{bill_id}")
    c_val = st.number_input("Valor Mensal (R$) *", min_value=0.01, value=float(bill.get("amount", 10.0)), step=10.0, format="%.2f", key=f"edit_bill_val_{bill_id}")
    c_dia = st.number_input("Dia do Vencimento no Mês (1-31) *", min_value=1, max_value=31, value=int(bill.get("due_day", 10)), step=1, key=f"edit_bill_dia_{bill_id}")

    cur_active = int(bill.get("is_active", 1))
    c_active = st.radio("Situação da Recorrência", ["Ativa (gerar mensalmente)", "Pausada"], index=0 if cur_active == 1 else 1, horizontal=True, key=f"edit_bill_act_{bill_id}")

    st.markdown("---")
    if st.button("💾 Salvar Alterações", type="primary", width="stretch", key=f"btn_salvar_bill_{bill_id}"):
        if not c_desc.strip():
            st.error("Por favor, preencha o campo Descrição.")
            return

        try:
            is_active_val = 1 if "Ativa" in c_active else 0
            ok = update_recurring_bill(
                bill_id=bill_id,
                requesting_user_id=user_id,
                type=c_tipo,
                category=c_cat,
                description=c_desc.strip(),
                amount=round(c_val, 2),
                due_day=int(c_dia),
                is_active=is_active_val
            )
            if ok:
                st.success("✅ Conta recorrente atualizada com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao atualizar a conta recorrente.")
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")


@st.dialog("🗑️ Exclusão em Lote: Apagar Mês Completo", width="medium")
def modal_excluir_mes_completo(user_id: int, meses_disponiveis: list[str]):
    """
    Modal de confirmação rigorosa para exclusão em lote de todas as movimentações
    de um mês específico pertencente ao usuário.
    """
    st.markdown("##### ⚠️ Excluir Todos os Lançamentos de um Mês")
    st.caption("Esta operação remove definitivamente todas as receitas e despesas do mês selecionado pertencentes à sua conta.")

    if not meses_disponiveis or meses_disponiveis == ["Todos os Lançamentos"]:
        st.info("Não há meses com movimentações cadastradas para exclusão.")
        return

    meses_validos = [m for m in meses_disponiveis if m != "Todos os Lançamentos"]
    if not meses_validos:
        st.info("Não há meses com movimentações cadastradas.")
        return

    mes_del_sel = st.selectbox("Selecione o Mês a Excluir (YYYY-MM)", meses_validos, key="dialog_sel_mes_del")
    
    # Busca contagem no mês
    trans = get_transactions(user_id=user_id)
    total_no_mes = len([t for t in trans if str(t.get("due_date", ""))[:7] == mes_del_sel])
    
    st.warning(f"Total encontrado em **{mes_del_sel}**: **{total_no_mes}** movimentação(ões).")
    
    confirm_chk = st.checkbox(
        f"Confirmo que desejo apagar permanentemente todas as {total_no_mes} movimentações de {mes_del_sel}.",
        key="dialog_chk_conf_del_mes"
    )
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("Cancelar", width="stretch", key="btn_cancel_del_mes"):
            st.rerun()
    with col_d2:
        if st.button("🗑️ Apagar Mês Completo", type="primary", width="stretch", disabled=not confirm_chk or total_no_mes == 0, key="btn_exec_del_mes"):
            apagados = delete_transactions_by_month(user_id, mes_del_sel)
            st.success(f"✅ {apagados} movimentação(ões) de {mes_del_sel} foram excluídas com sucesso!")
            st.rerun()


def render_unified_filter_popover(
    all_items: list[dict], 
    available_months: list[str], 
    key_prefix: str = "global_filter",
    show_categories: bool = True
) -> list[dict]:
    """
    Renderiza um componente centralizado acionado por st.popover com todos os critérios
    avançados de filtro e retorna a lista filtrada de movimentações ou contas.
    """
    with st.popover("🔍 Filtros Globais", help="Filtros avançados por período, texto, vencimento, valor e categoria"):
        st.markdown("##### 🔍 Filtros Avançados")
        
        # 1. Período
        opcoes_per = ["Todos os Lançamentos"] + available_months
        sel_per = st.selectbox("📅 Período (YYYY-MM)", opcoes_per, index=0, key=f"{key_prefix}_per")
        
        # 2. Pesquisa textual livre (descrição ou favorecido)
        busca_txt = st.text_input("📝 Busca Textual (Descrição ou Favorecido)", placeholder="Digite nome, descrição...", key=f"{key_prefix}_txt")
        
        # 3. Data de vencimento (intervalo ou específica)
        col_dt_tipo, col_dt_val = st.columns([1.2, 1.8])
        with col_dt_tipo:
            tipo_data = st.selectbox(
                "📅 Tipo de Data", 
                ["Qualquer Data", "Intervalo", "Data Específica"], 
                key=f"{key_prefix}_tipo_dt"
            )
        dt_ini, dt_fim, dt_esp = None, None, None
        with col_dt_val:
            if tipo_data == "Intervalo":
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    dt_ini = st.date_input("De", value=date.today().replace(day=1), key=f"{key_prefix}_dt_ini")
                with c_d2:
                    dt_fim = st.date_input("Até", value=date.today(), key=f"{key_prefix}_dt_fim")
            elif tipo_data == "Data Específica":
                dt_esp = st.date_input("Data Exata", value=date.today(), key=f"{key_prefix}_dt_esp")
            else:
                st.caption("Todas as datas de vencimento")
        
        # 4. Faixa de Valor (Mínimo e Máximo)
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            val_min = st.number_input("Valor Mínimo (R$)", min_value=0.0, value=0.0, step=10.0, key=f"{key_prefix}_vmin")
        with c_v2:
            val_max = st.number_input("Valor Máximo (R$)", min_value=0.0, value=0.0, step=50.0, key=f"{key_prefix}_vmax", help="Deixe 0.00 para não limitar o máximo")
        
        # 5. Categorias
        sel_cats = []
        if show_categories:
            todas_cats = sorted(list(set(t.get("category", "") for t in all_items if t.get("category"))))
            if not todas_cats:
                todas_cats = CATEGORIAS_DESPESA + CATEGORIAS_RECEITA
            sel_cats = st.multiselect("🏷️ Categorias", options=todas_cats, default=[], key=f"{key_prefix}_cats")

    # Aplicação dos filtros
    filtrados = all_items
    
    # 1. Período
    if sel_per != "Todos os Lançamentos":
        filtrados = [t for t in filtrados if str(t.get("due_date", ""))[:7] == sel_per]
        
    # 2. Pesquisa textual
    if busca_txt.strip():
        term = busca_txt.strip().lower()
        filtrados = [
            t for t in filtrados
            if term in str(t.get("description", "")).lower()
            or term in str(t.get("recipient", "")).lower()
        ]
        
    # 3. Data
    if tipo_data == "Intervalo" and dt_ini and dt_fim:
        ini_str = dt_ini.strftime("%Y-%m-%d")
        fim_str = dt_fim.strftime("%Y-%m-%d")
        filtrados = [t for t in filtrados if ini_str <= str(t.get("due_date", "")) <= fim_str]
    elif tipo_data == "Data Específica" and dt_esp:
        esp_str = dt_esp.strftime("%Y-%m-%d")
        filtrados = [t for t in filtrados if str(t.get("due_date", "")) == esp_str]
        
    # 4. Valor
    if val_min > 0:
        filtrados = [t for t in filtrados if float(t.get("amount", 0)) >= val_min]
    if val_max > 0 and val_max >= val_min:
        filtrados = [t for t in filtrados if float(t.get("amount", 0)) <= val_max]
        
    # 5. Categorias
    if sel_cats:
        filtrados = [t for t in filtrados if t.get("category") in sel_cats]
        
    return filtrados


def render_standard_period_filter(
    available_months: list[str], 
    key_prefix: str = "filter_period",
    default_mode_index: int = 0
) -> dict:
    """
    Componente padronizado e flexível de filtro de período para o Dashboard e demais páginas.
    Padrão do Sistema: Exibe os dados gerais consolidados de todo o histórico.
    Opções:
      1. 🌐 Todo o Histórico (Geral) - Padrão consolidado
      2. 📅 Mês Específico - Seletor direto de mês/ano
      3. 📆 Período Personalizado - Seletor tipo calendário (intervalo de/até)
    Retorna dicionário com:
      - mode: 'geral' | 'mes' | 'personalizado'
      - start_date: str (YYYY-MM-DD) ou None
      - end_date: str (YYYY-MM-DD) ou None
      - month_year: str (YYYY-MM) ou None
      - label: str explicativa do período ativo
    """
    opcoes_modo = [
        "🌐 Todo o Histórico (Geral)",
        "📅 Mês Específico",
        "📆 Período Personalizado (Calendário)"
    ]

    col_m, col_v = st.columns([1.5, 2.5])

    with col_m:
        modo_sel = st.selectbox(
            "Filtrar Período de Análise",
            opcoes_modo,
            index=default_mode_index,
            key=f"{key_prefix}_modo_sel"
        )

    res = {
        "mode": "geral",
        "start_date": None,
        "end_date": None,
        "month_year": None,
        "label": "Consolidado Geral (Todo o Histórico)"
    }

    with col_v:
        if modo_sel == "🌐 Todo o Histórico (Geral)":
            st.markdown(
                "<div style='padding-top: 1.8rem; color: #8b949e; font-size: 0.9rem;'>"
                "📊 Exibindo <b>métricas e balanço consolidados</b> de todo o seu histórico financeiro."
                "</div>",
                unsafe_allow_html=True
            )
            res = {
                "mode": "geral",
                "start_date": None,
                "end_date": None,
                "month_year": None,
                "label": "Consolidado Geral (Todo o Histórico)"
            }

        elif modo_sel == "📅 Mês Específico":
            hoje = date.today()
            mes_atual_str = hoje.strftime("%Y-%m")
            meses_validos = list(available_months)
            if mes_atual_str not in meses_validos:
                meses_validos.insert(0, mes_atual_str)
            meses_validos = sorted(list(set(meses_validos)), reverse=True)

            idx_default = meses_validos.index(mes_atual_str) if mes_atual_str in meses_validos else 0
            mes_escolhido = st.selectbox("Selecione o Mês (YYYY-MM)", meses_validos, index=idx_default, key=f"{key_prefix}_mes_sel")
            res = {
                "mode": "mes",
                "start_date": None,
                "end_date": None,
                "month_year": mes_escolhido,
                "label": f"Mês de Referência: {mes_escolhido}"
            }

        elif modo_sel == "📆 Período Personalizado (Calendário)":
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                hoje = date.today()
                dt_ini_val = hoje.replace(day=1)
                dt_ini = st.date_input("De (Data Inicial)", value=dt_ini_val, format="DD/MM/YYYY", key=f"{key_prefix}_dt_ini")
            with c_d2:
                dt_fim = st.date_input("Até (Data Final)", value=hoje, format="DD/MM/YYYY", key=f"{key_prefix}_dt_fim")

            ini_str = dt_ini.strftime("%Y-%m-%d")
            fim_str = dt_fim.strftime("%Y-%m-%d")
            res = {
                "mode": "personalizado",
                "start_date": ini_str,
                "end_date": fim_str,
                "month_year": None,
                "label": f"Período: {dt_ini.strftime('%d/%m/%Y')} até {dt_fim.strftime('%d/%m/%Y')}"
            }

    return res


def render_floating_ai_assistant(user: dict):
    """
    Renderiza o botão flutuante estilizado no canto inferior direito e o chat lateral deslizante (drawer).
    Regra de Fechamento Automático: O menu lateral principal fecha automaticamente quando o drawer abre (e vice-versa).
    """
    if "ai_chat_open" not in st.session_state:
        st.session_state["ai_chat_open"] = False
    if "ai_chat_messages" not in st.session_state:
        st.session_state["ai_chat_messages"] = []

    is_open = st.session_state["ai_chat_open"]

    # 1. Injeção condicional de estilo para fechar o sidebar principal quando o drawer de IA estiver aberto
    if is_open:
        st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            button[data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }
            </style>
        """, unsafe_allow_html=True)

    # 2. Botão Flutuante (FAB) fixo no canto inferior direito
    with st.container():
        st.markdown("""
            <div id="floating-ai-fab-anchor">
                <script>
                (function() {
                    const anchor = document.getElementById('floating-ai-fab-anchor');
                    if (anchor) {
                        const nextElem = anchor.closest('[data-testid="element-container"]')?.nextElementSibling;
                        if (nextElem) {
                            nextElem.classList.add('ai-fab-container');
                            const btn = nextElem.querySelector('button');
                            if (btn) btn.classList.add('ai-fab-button');
                        }
                    }
                })();
                </script>
            </div>
        """, unsafe_allow_html=True)
        fab_label = "✖" if is_open else "🤖"
        fab_help = "Fechar Consultor IA" if is_open else "Abrir Consultor Financeiro IA (Google Gemini)"
        if st.button(fab_label, key="btn_floating_ai_trigger", help=fab_help):
            st.session_state["ai_chat_open"] = not is_open
            st.rerun()

    # 3. Drawer Lateral Deslizante de IA (Chat Lateral)
    if is_open:
        with st.container():
            st.markdown("""
                <div id="ai-drawer-anchor">
                    <script>
                    (function() {
                        const anchor = document.getElementById('ai-drawer-anchor');
                        if (anchor) {
                            const block = anchor.closest('[data-testid="stVerticalBlock"]');
                            if (block) block.classList.add('ai-drawer-panel');
                        }
                    })();
                    </script>
                </div>
            """, unsafe_allow_html=True)

            # Cabeçalho do Drawer
            col_h1, col_h2 = st.columns([3.5, 1.2])
            with col_h1:
                st.markdown("""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <h3 style="margin: 0; font-size: 1.2rem; color: #ffffff;">🤖 Consultor IA</h3>
                        <span style="background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.4); padding: 2px 6px; border-radius: 10px; font-size: 0.7rem; font-weight: 600;">Online (Gemini)</span>
                    </div>
                    <small style="color: #8b949e;">Análise e suporte financeiro personalizado</small>
                """, unsafe_allow_html=True)
            with col_h2:
                if st.button("✖ Fechar", key="btn_close_ai_drawer", help="Fechar chat lateral"):
                    st.session_state["ai_chat_open"] = False
                    st.rerun()

            st.markdown("<hr style='margin: 0.7rem 0;'>", unsafe_allow_html=True)

            # Sugestões Rápidas de Pergunta (Chips)
            st.caption("💡 Perguntas Rápidas:")
            c_s1, c_s2 = st.columns(2)
            prompt_chip = None
            with c_s1:
                if st.button("💰 Saldo Acumulado", key="chip_saldo", width="stretch"):
                    prompt_chip = "Como está o meu saldo acumulado e a relação entre minhas receitas e despesas?"
                if st.button("🚨 Contas a Vencer", key="chip_vencimentos", width="stretch"):
                    prompt_chip = "Tenho contas a pagar vencendo em breve? O que preciso priorizar?"
            with c_s2:
                if st.button("📊 Maiores Gastos", key="chip_despesas", width="stretch"):
                    prompt_chip = "Quais categorias representam meus maiores gastos históricos?"
                if st.button("💡 Dicas para Poupar", key="chip_dicas", width="stretch"):
                    prompt_chip = "Com base no meu histórico financeiro, quais 3 dicas práticas você me dá para economizar?"

            st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)

            # Histórico de Mensagens
            if not st.session_state["ai_chat_messages"]:
                nome_u = user.get("username", "Usuário")
                st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 10px; padding: 0.9rem; text-align: center; margin-bottom: 0.8rem;">
                        <p style="margin: 0; color: #c9d1d9; font-size: 0.9rem;">
                            Olá, <strong>{nome_u}</strong>! 👋<br>
                            Sou seu consultor de patrimônio inteligente. Analiso suas receitas, despesas e metas em tempo real.
                        </p>
                        <small style="color: #8b949e;">Clique em uma pergunta acima ou digite abaixo.</small>
                    </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state["ai_chat_messages"]:
                    avatar = "👤" if msg["role"] == "user" else "🤖"
                    with st.chat_message(msg["role"], avatar=avatar):
                        st.markdown(msg["content"])

            # Formulário de Envio
            with st.form("form_chat_ai_drawer", clear_on_submit=True):
                user_input = st.text_input(
                    "Sua pergunta:", 
                    placeholder="Digite sua dúvida ou peça uma análise...", 
                    label_visibility="collapsed",
                    key="input_chat_drawer"
                )
                col_f1, col_f2 = st.columns([1.5, 2.5])
                with col_f1:
                    limpar = st.form_submit_button("🗑️ Limpar", type="secondary", width="stretch")
                with col_f2:
                    enviar = st.form_submit_button("Enviar 🚀", type="primary", width="stretch")

            if limpar:
                st.session_state["ai_chat_messages"] = []
                st.rerun()

            pergunta_final = prompt_chip or (user_input.strip() if enviar and user_input.strip() else None)

            if pergunta_final:
                st.session_state["ai_chat_messages"].append({"role": "user", "content": pergunta_final})
                
                with st.spinner("Consultor IA analisando suas finanças..."):
                    all_trans = get_transactions(user_id=user["id"])
                    all_budgets = get_budgets(user_id=user["id"])
                    all_investments = get_investments(user_id=user["id"])
                    
                    resposta = chat_with_financial_ai(
                        user_prompt=pergunta_final,
                        conversation_history=st.session_state["ai_chat_messages"],
                        transactions=all_trans,
                        budgets=all_budgets,
                        investments=all_investments,
                        user_name=user.get("full_name") or user.get("username") or "Usuário"
                    )
                    st.session_state["ai_chat_messages"].append({"role": "assistant", "content": resposta})
                st.rerun()





