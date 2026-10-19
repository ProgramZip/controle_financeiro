import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from pathlib import Path

from backend.crud import (
    get_transactions, update_transaction_status, delete_transaction, delete_transactions_by_month,
    add_recurring_bill, get_recurring_bills, update_recurring_bill, delete_recurring_bill, process_recurring_bills,
    add_investment, get_investments, update_investment, delete_investment,
    set_budget, get_budgets, delete_budget,
    get_users, add_user, update_user_role, delete_user,
    add_user_share, get_user_shares_by_owner, get_user_shares_received, delete_user_share,
    can_user_edit_resource
)
from backend.utils import (
    CATEGORIAS_DESPESA, CATEGORIAS_RECEITA,
    read_bank_statement_csv, read_bank_statement_pdf,
    get_db_backup_bytes, restore_db_from_bytes,
    export_transactions_to_excel, analyze_finances_with_ai,
    BASE_DIR
)
from frontend.components import render_metric_card, modal_nova_movimentacao, modal_nova_conta_recorrente


# =====================================================================
# 1. VIEW: DASHBOARD GERAL
# =====================================================================

def view_dashboard(user: dict):
    st.title("📊 Painel Financeiro")

    # Seletor de período e Ação Rápida
    col_per1, col_per2 = st.columns([3, 1])
    with col_per1:
        hoje = date.today()
        mes_atual_str = hoje.strftime("%Y-%m")
        # Gera opções dos últimos 12 meses
        meses_opcoes = [datetime(hoje.year, m, 1).strftime("%Y-%m") for m in range(1, 13)]
        if mes_atual_str not in meses_opcoes:
            meses_opcoes.append(mes_atual_str)
        meses_opcoes = sorted(list(set(meses_opcoes)), reverse=True)
        mes_sel = st.selectbox("Selecione o Mês de Referência", meses_opcoes, index=meses_opcoes.index(mes_atual_str) if mes_atual_str in meses_opcoes else 0)
    with col_per2:
        st.write("")
        st.write("")
        if st.button("➕ Nova Movimentação", type="primary", width='stretch', key="btn_dash_nova_mov"):
            modal_nova_movimentacao(user["id"])

    # Carrega transações estritamente do próprio usuário logado
    transacoes = get_transactions(user_id=user["id"])
    trans_mes = [t for t in transacoes if str(t.get("due_date", ""))[:7] == mes_sel]

    # Cálculos
    receitas_total = sum(t["amount"] for t in trans_mes if t["type"] == "receita")
    despesas_total = sum(t["amount"] for t in trans_mes if t["type"] == "despesa")
    saldo_mes = receitas_total - despesas_total

    investimentos = get_investments(user_id=user["id"])
    total_investido = sum(i["current_value"] for i in investimentos)

    taxa_poupanca = ((receitas_total - despesas_total) / receitas_total * 100) if receitas_total > 0 else 0.0

    # Cards de Resumo
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Receitas", f"R$ {receitas_total:,.2f}", "Entradas no mês", "#3fb950", "🟢")
    with c2:
        render_metric_card("Despesas", f"R$ {despesas_total:,.2f}", "Saídas no mês", "#f85149", "🔴")
    with c3:
        cor_saldo = "#3fb950" if saldo_mes >= 0 else "#f85149"
        render_metric_card("Saldo Líquido", f"R$ {saldo_mes:,.2f}", "Balanço mensal", cor_saldo, "💰")
    with c4:
        render_metric_card("Investimentos", f"R$ {total_investido:,.2f}", "Patrimônio ativo", "#58a6ff", "📈")
    with c5:
        cor_tx = "#3fb950" if taxa_poupanca >= 20 else ("#e3b341" if taxa_poupanca >= 0 else "#f85149")
        render_metric_card("Poupança", f"{taxa_poupanca:.1f}%", "Taxa do mês", cor_tx, "🛡️")

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos Interativos em Plotly
    g_col1, g_col2 = st.columns([1, 1])

    despesas_mes = [t for t in trans_mes if t["type"] == "despesa"]
    with g_col1:
        st.subheader("Despesas por Categoria")
        if despesas_mes:
            df_desp = pd.DataFrame(despesas_mes)
            df_cat = df_desp.groupby("category")["amount"].sum().reset_index()
            fig_pie = px.pie(
                df_cat,
                values="amount",
                names="category",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_pie, width='stretch')
        else:
            st.info("Nenhuma despesa registrada para o mês selecionado.")

    with g_col2:
        st.subheader("Receitas vs Despesas")
        df_comp = pd.DataFrame({
            "Tipo": ["Receitas", "Despesas"],
            "Total (R$)": [receitas_total, despesas_total]
        })
        fig_bar = px.bar(
            df_comp,
            x="Tipo",
            y="Total (R$)",
            color="Tipo",
            color_discrete_map={"Receitas": "#3fb950", "Despesas": "#f85149"},
            text_auto=".2f"
        )
        fig_bar.update_layout(
            margin=dict(t=20, b=20, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_bar, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)

    # Listagem das Últimas Movimentações Pessoais
    st.subheader("Últimos Lançamentos Pessoais")
    if trans_mes:
        df_ult = pd.DataFrame(trans_mes)[["due_date", "type", "category", "description", "amount", "status"]]
        df_ult.columns = ["Data", "Tipo", "Categoria", "Descrição", "Valor (R$)", "Status"]
        df_ult["Valor (R$)"] = df_ult["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_ult.head(10), width='stretch', hide_index=True)
    else:
        st.caption("Nenhum lançamento encontrado no mês de referência.")


# =====================================================================
# 2. VIEW: MOVIMENTAÇÕES
# =====================================================================

def view_movimentacoes(user: dict):
    st.title("💳 Gestão de Movimentações")

    # Carrega transações estritamente particulares do próprio usuário
    all_trans = get_transactions(user_id=user["id"])

    # Ações no topo: Nova Movimentação e Exportar Excel
    col_topo1, col_topo2, col_topo3 = st.columns([2, 1, 1])
    with col_topo2:
        if st.button("➕ Nova Movimentação", type="primary", width='stretch', key="btn_view_nova_mov"):
            modal_nova_movimentacao(user["id"])
    with col_topo3:
        excel_bytes = export_transactions_to_excel(all_trans)
        st.download_button(
            label="📥 Exportar Excel",
            data=excel_bytes,
            file_name=f"movimentacoes_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch'
        )

    # ---------------- ZONA DE EXCLUSÃO EM LOTE (MÊS COMPLETO) ----------------
    with st.expander("🗑️ Exclusão em Lote: Apagar Mês Completo", expanded=False):
        st.markdown("##### ⚠️ Excluir Todos os Lançamentos de um Mês")
        st.caption("Esta operação remove definitivamente todas as receitas e despesas do mês selecionado pertencentes à sua conta.")

        meses_com_dados = sorted(list(set(str(t["due_date"])[:7] for t in all_trans if t.get("due_date"))), reverse=True)
        if not meses_com_dados:
            meses_com_dados = [date.today().strftime("%Y-%m")]

        col_dm1, col_dm2 = st.columns([2, 2])
        with col_dm1:
            mes_del_sel = st.selectbox("Selecione o Mês a Excluir (YYYY-MM)", meses_com_dados, key="sel_mes_excluir")
            total_no_mes = len([t for t in all_trans if str(t.get("due_date", ""))[:7] == mes_del_sel])
            st.warning(f"Total encontrado em **{mes_del_sel}**: **{total_no_mes}** movimentação(ões).")
        with col_dm2:
            st.write("")
            st.write("")
            confirm_chk = st.checkbox(f"Confirmo que desejo apagar permanentemente todas as {total_no_mes} movimentações de {mes_del_sel}.", key="chk_conf_del_mes")
            if st.button("🗑️ Apagar Mês Completo", type="primary", width="stretch", disabled=not confirm_chk or total_no_mes == 0):
                apagados = delete_transactions_by_month(user["id"], mes_del_sel)
                st.success(f"✅ {apagados} movimentação(ões) de {mes_del_sel} foram excluídas com sucesso!")
                st.rerun()

    st.markdown("---")

    # Abas: Despesas e Receitas
    tab_despesas, tab_receitas = st.tabs(["🔴 Despesas", "🟢 Receitas"])

    # ---------------- ABA DESPESAS ----------------
    with tab_despesas:
        st.subheader("Despesas")
        despesas = [t for t in all_trans if t["type"] == "despesa"]

        # Filtros rápidos
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            cat_filter = st.selectbox("Filtrar por Categoria", ["Todas"] + CATEGORIAS_DESPESA, key="filter_cat_desp")
        with col_f2:
            busca_desp = st.text_input("Buscar por descrição", placeholder="Digite algo...", key="busca_desp")

        if cat_filter != "Todas":
            despesas = [d for d in despesas if d["category"] == cat_filter]
        if busca_desp.strip():
            despesas = [d for d in despesas if busca_desp.lower() in d["description"].lower()]

        # Separação: Pendentes e Pagas
        desp_pendentes = [d for d in despesas if d["status"] == "Pendente"]
        desp_pagas = [d for d in despesas if d["status"] == "Pago"]

        st.markdown("#### ⏳ Contas Pendentes / A Pagar")
        if desp_pendentes:
            for item in desp_pendentes:
                with st.container():
                    c_info, c_val, c_btn, c_del = st.columns([4, 2, 2, 2])
                    with c_info:
                        parc_info = f" ({item['installment_current']}/{item['installment_total']})" if item["installment_total"] > 1 else ""
                        st.markdown(f"**{item['description']}**{parc_info}  \n<small style='color:#8b949e;'>Vence em: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                        if item.get("invoice_path") and os.path.exists(item["invoice_path"]):
                            with st.expander("Ver Nota Fiscal"):
                                st.image(item["invoice_path"], width=250)
                    with c_val:
                        st.markdown(f"<h4 style='color:#f85149; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_btn:
                        if st.button("✅ Pagar", key=f"pay_{item['id']}", width='stretch'):
                            update_transaction_status(item["id"], "Pago", requesting_user_id=user["id"])
                            st.success("Conta quitada!")
                            st.rerun()
                    with c_del:
                        if st.button("🗑️ Apagar", key=f"del_dp_{item['id']}", width='stretch'):
                            delete_transaction(item["id"], user_id=user["id"])
                            st.success("Conta pendente excluída!")
                            st.rerun()
                    st.divider()
        else:
            st.info("Nenhuma conta pendente a pagar no momento.")

        st.markdown("#### ✅ Contas Pagas / Concluídas")
        if desp_pagas:
            total_pago = sum(d["amount"] for d in desp_pagas)
            st.caption(f"Total: {len(desp_pagas)} conta(s) paga(s) somando **R$ {total_pago:,.2f}**")
            for item in desp_pagas:
                with st.container():
                    c_info, c_val, c_del = st.columns([6, 3, 2])
                    with c_info:
                        parc_info = f" ({item['installment_current']}/{item['installment_total']})" if item.get('installment_total', 1) > 1 else ""
                        st.markdown(f"**{item['description']}**{parc_info}  \n<small style='color:#8b949e;'>Pago em: {item['due_date']} | Categoria: {item['category']} | {item.get('payment_method', 'À Vista')}</small>", unsafe_allow_html=True)
                    with c_val:
                        st.markdown(f"<h4 style='color:#f85149; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️ Apagar", key=f"del_paga_{item['id']}", width='stretch'):
                            delete_transaction(item["id"], user_id=user["id"])
                            st.success("Conta paga excluída!")
                            st.rerun()
                    st.divider()
        else:
            st.caption("Nenhuma conta paga encontrada.")

    # ---------------- ABA RECEITAS ----------------
    with tab_receitas:
        st.subheader("Receitas")
        receitas = [t for t in all_trans if t["type"] == "receita"]

        col_rf1, col_rf2 = st.columns([2, 2])
        with col_rf1:
            cat_r_filter = st.selectbox("Filtrar por Categoria", ["Todas"] + CATEGORIAS_RECEITA, key="filter_cat_rec")
        with col_rf2:
            busca_rec = st.text_input("Buscar por descrição", placeholder="Digite algo...", key="busca_rec")

        if cat_r_filter != "Todas":
            receitas = [r for r in receitas if r["category"] == cat_r_filter]
        if busca_rec.strip():
            receitas = [r for r in receitas if busca_rec.lower() in r["description"].lower()]

        rec_pendentes = [r for r in receitas if r["status"] == "Pendente"]
        rec_recebidas = [r for r in receitas if r["status"] in ("Recebido", "Pago")]

        st.markdown("#### ⏳ Valores a Receber (Pendentes)")
        if rec_pendentes:
            for item in rec_pendentes:
                with st.container():
                    c_info, c_val, c_btn, c_del = st.columns([4, 2, 2, 2])
                    with c_info:
                        st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Previsão: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                    with c_val:
                        st.markdown(f"<h4 style='color:#3fb950; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_btn:
                        if st.button("💵 Receber", key=f"rec_{item['id']}", width='stretch'):
                            update_transaction_status(item["id"], "Recebido", requesting_user_id=user["id"])
                            st.success("Recebimento confirmado!")
                            st.rerun()
                    with c_del:
                        if st.button("🗑️ Apagar", key=f"del_rp_{item['id']}", width='stretch'):
                            delete_transaction(item["id"], user_id=user["id"])
                            st.success("Receita pendente excluída!")
                            st.rerun()
                    st.divider()
        else:
            st.info("Nenhum valor pendente de recebimento.")

        st.markdown("#### 🟢 Valores Já Recebidos")
        if rec_recebidas:
            total_rec = sum(r["amount"] for r in rec_recebidas)
            st.caption(f"Total: {len(rec_recebidas)} recebimento(s) somando **R$ {total_rec:,.2f}**")
            for item in rec_recebidas:
                with st.container():
                    c_info, c_val, c_del = st.columns([6, 3, 2])
                    with c_info:
                        st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Recebido em: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                    with c_val:
                        st.markdown(f"<h4 style='color:#3fb950; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️ Apagar", key=f"del_rec_paga_{item['id']}", width='stretch'):
                            delete_transaction(item["id"], user_id=user["id"])
                            st.success("Receita excluída!")
                            st.rerun()
                    st.divider()
        else:
            st.caption("Nenhum recebimento registrado.")


# =====================================================================
# 3. VIEW: CONTAS MENSAIS RECORRENTES
# =====================================================================

def view_contas_mensais(user: dict):
    st.title("🔄 Matriz de Contas Mensais Recorrentes")
    st.write("Gerencie suas contas fixas e receitas automáticas. O motor de recorrência gera os lançamentos todo mês com trava anti-duplicação.")

    # Ações de Topo: Nova Conta Recorrente (Modal) e Sincronização
    col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
    with col_m2:
        if st.button("➕ Nova Conta Recorrente", type="primary", width='stretch', key="btn_nova_recorrente"):
            modal_nova_conta_recorrente(user["id"])
    with col_m3:
        if st.button("⚡ Sincronizar Mês Vigente", width='stretch', key="btn_sync_recorrente"):
            novas = process_recurring_bills(user_id=user["id"])
            if novas > 0:
                st.success(f"{novas} conta(s) gerada(s) para o mês atual!")
            else:
                st.info("Todas as contas do mês já estão atualizadas. Nenhuma duplicidade gerada.")
            st.rerun()

    st.markdown("---")
    contas = get_recurring_bills(user_id=user["id"])

    if contas:
        for b in contas:
            with st.container():
                c_icon, c_info, c_val, c_status, c_del = st.columns([1, 4, 2, 2, 2])
                with c_icon:
                    st.markdown("🔴" if b["type"] == "despesa" else "🟢")
                with c_info:
                    st.markdown(f"**{b['description']}**  \n<small style='color:#8b949e;'>Dia de vencimento: {b['due_day']} | Categoria: {b['category']}</small>", unsafe_allow_html=True)
                with c_val:
                    cor = "#f85149" if b["type"] == "despesa" else "#3fb950"
                    st.markdown(f"<h4 style='color:{cor}; margin:0;'>R$ {b['amount']:,.2f}</h4>", unsafe_allow_html=True)
                
                with c_status:
                    novo_estado = 0 if b["is_active"] else 1
                    btn_txt = "⏸️ Pausar" if b["is_active"] else "▶️ Ativar"
                    if st.button(btn_txt, key=f"tgl_{b['id']}", width="stretch"):
                        update_recurring_bill(b["id"], requesting_user_id=user["id"], is_active=novo_estado)
                        st.rerun()
                with c_del:
                    if st.button("🗑️ Apagar", key=f"del_rec_{b['id']}", width="stretch"):
                        delete_recurring_bill(b["id"], requesting_user_id=user["id"])
                        st.success("Conta recorrente excluída!")
                        st.rerun()
                st.divider()
    else:
        st.info("Nenhuma conta recorrente cadastrada. Use o botão acima para adicionar contas fixas.")


# =====================================================================
# 4. VIEW: IMPORTAÇÃO DE EXTRATOS (PDF / CSV) COM CONCILIAÇÃO
# =====================================================================

def view_importacao_extratos(user: dict):
    st.title("📄 Importação de Extratos & Conciliação")
    st.write("Carregue seu extrato bancário em PDF ou CSV. Revise e concilie os lançamentos antes de salvar no sistema.")

    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Selecione o arquivo de extrato", type=["csv", "pdf"])
    with col_up2:
        st.write("")
        st.write("")
        if st.button("🔄 Recarregar Extrato", width='stretch'):
            st.session_state.pop("df_importacao", None)
            st.session_state.pop("last_uploaded", None)
            st.rerun()

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name.lower()

        if "df_importacao" not in st.session_state or st.session_state.get("last_uploaded") != file_name:
            with st.spinner("Processando extrato bancário..."):
                if file_name.endswith(".csv"):
                    df_parsed = read_bank_statement_csv(file_bytes)
                else:
                    df_parsed = read_bank_statement_pdf(file_bytes)

                st.session_state["df_importacao"] = df_parsed
                st.session_state["last_uploaded"] = file_name

        df = st.session_state.get("df_importacao", pd.DataFrame())

        if not df.empty:
            st.markdown("### 🔍 Conciliação dos Lançamentos")
            st.caption("Desmarque as linhas que já foram inseridas manualmente ou que não deseja importar.")

            df["Data"] = df["Data"].astype(str)
            if "Hora" in df.columns:
                df["Hora"] = df["Hora"].astype(str)

            edited_df = st.data_editor(
                df,
                width='stretch',
                num_rows="dynamic",
                column_config={
                    "Selecionado": st.column_config.CheckboxColumn("Importar?", default=True),
                    "Data": st.column_config.TextColumn("Data", help="Formato AAAA-MM-DD", width="small"),
                    "Hora": st.column_config.TextColumn("Hora", help="Horário (HH:MM)", width="small"),
                    "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", width="small"),
                    "Tipo": st.column_config.SelectboxColumn("Tipo", options=["despesa", "receita"], width="small"),
                    "Categoria_Sugerida": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS_DESPESA + CATEGORIAS_RECEITA, width="medium")
                }
            )

            col_act1, col_act2 = st.columns([2, 1])
            with col_act2:
                if st.button("📥 Gravar Lançamentos Selecionados", type="primary", width='stretch'):
                    selecionados = edited_df[edited_df["Selecionado"] == True]
                    if selecionados.empty:
                        st.warning("Nenhum lançamento selecionado.")
                    else:
                        gravados = 0
                        from backend.crud import add_transaction
                        for _, row in selecionados.iterrows():
                            t_tipo = str(row["Tipo"]).lower()
                            cat = str(row["Categoria_Sugerida"])
                            desc = str(row["Descrição"]).strip()
                            val = float(row["Valor"])
                            dt_str = str(row["Data"])[:10]

                            add_transaction(
                                user_id=user["id"],
                                trans_type=t_tipo,
                                category=cat,
                                description=desc,
                                amount=val,
                                payment_method="À Vista",
                                installment_total=1,
                                due_date=dt_str,
                                status="Pago" if t_tipo == "despesa" else "Recebido"
                            )
                            gravados += 1

                        st.success(f"✅ {gravados} movimentações importadas e salvas com sucesso no banco de dados!")
                        del st.session_state["df_importacao"]
                        st.rerun()
        else:
            st.warning("Nenhuma movimentação válida detectada no arquivo. Verifique o layout do extrato.")


# =====================================================================
# 5. VIEW: INVESTIMENTOS & ORÇAMENTOS
# =====================================================================

def view_investimentos_orcamentos(user: dict):
    st.title("📈 Investimentos & Metas de Orçamento")

    tab_inv, tab_bud = st.tabs(["💰 Carteira de Investimentos", "🎯 Metas de Orçamento"])

    # ---------------- ABA INVESTIMENTOS ----------------
    with tab_inv:
        st.subheader("Carteira de Ativos")
        investimentos = get_investments(user_id=user["id"])

        total_investido = sum(i["invested_amount"] for i in investimentos)
        valor_atual = sum(i["current_value"] for i in investimentos)
        lucro_prejuizo = valor_atual - total_investido
        rentabilidade_pct = ((valor_atual - total_investido) / total_investido * 100) if total_investido > 0 else 0.0

        c_inv1, c_inv2, c_inv3 = st.columns(3)
        with c_inv1:
            render_metric_card("Total Aportado", f"R$ {total_investido:,.2f}", "Capital inicial", "#58a6ff", "💼")
        with c_inv2:
            render_metric_card("Patrimônio Atual", f"R$ {valor_atual:,.2f}", "Posição consolidada", "#3fb950", "💎")
        with c_inv3:
            cor_r = "#3fb950" if lucro_prejuizo >= 0 else "#f85149"
            render_metric_card("Rentabilidade", f"R$ {lucro_prejuizo:+,.2f}", f"{rentabilidade_pct:+.2f}%", cor_r, "📊")

        st.markdown("<br>", unsafe_allow_html=True)

        if investimentos:
            df_inv = pd.DataFrame(investimentos)
            col_chart, col_tbl = st.columns([1, 1])
            with col_chart:
                fig_inv = px.pie(
                    df_inv,
                    values="current_value",
                    names="category",
                    title="Alocação por Classe de Ativo",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_inv.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_inv, width='stretch')

            with col_tbl:
                st.write("#### Lista de Ativos")
                for at in investimentos:
                    with st.container():
                        ci1, ci2, ci3 = st.columns([4, 3, 2])
                        with ci1:
                            st.markdown(f"**{at['asset_name']}** ({at['category']})  \n<small>Aporte: R$ {at['invested_amount']:,.2f}</small>", unsafe_allow_html=True)
                        with ci2:
                            st.markdown(f"**R$ {at['current_value']:,.2f}**")
                        with ci3:
                            if st.button("🗑️ Apagar", key=f"del_inv_{at['id']}", width="stretch"):
                                delete_investment(at["id"], requesting_user_id=user["id"])
                                st.success("Ativo excluído!")
                                st.rerun()
                        st.divider()

        with st.expander("➕ Adicionar Novo Ativo à Carteira"):
            with st.form("form_novo_ativo"):
                a_nome = st.text_input("Nome do Ativo", placeholder="Ex: Tesouro Selic 2029, MXRF11, ITUB4...")
                a_cat = st.selectbox("Classe de Ativo", ["Renda Fixa", "Ações", "FIIs", "Cripto", "Exterior", "Reserva de Emergência", "Outros"])
                a_aport = st.number_input("Valor Aportado (R$)", min_value=0.01, step=100.0, format="%.2f")
                a_atual = st.number_input("Valor Atual (R$)", min_value=0.01, step=100.0, format="%.2f")
                a_data = st.date_input("Data da Posição", value=date.today())

                if st.form_submit_button("Salvar Ativo"):
                    if a_nome.strip():
                        add_investment(user["id"], a_nome.strip(), a_cat, a_aport, a_atual, a_data.strftime("%Y-%m-%d"))
                        st.success("Ativo registrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Informe o nome do ativo.")

    # ---------------- ABA ORÇAMENTOS ----------------
    with tab_bud:
        st.subheader("🎯 Limites Mensais de Gastos por Categoria")
        st.write("Defina um teto mensal para suas despesas e monitore em tempo real o cumprimento.")

        budgets = get_budgets(user_id=user["id"])
        mes_atual = date.today().strftime("%Y-%m")
        trans_mes = [t for t in get_transactions(user_id=user["id"]) if str(t.get("due_date", ""))[:7] == mes_atual and t["type"] == "despesa"]

        # Calcula gastos por categoria no mês atual
        gastos_cat = {}
        for t in trans_mes:
            c = t["category"]
            gastos_cat[c] = gastos_cat.get(c, 0.0) + t["amount"]

        if budgets:
            for b in budgets:
                cat = b["category"]
                teto = b["monthly_limit"]
                gasto = gastos_cat.get(cat, 0.0)
                pct = (gasto / teto) if teto > 0 else 0.0
                pct_clamp = min(pct, 1.0)

                col_b1, col_b2 = st.columns([4, 2])
                with col_b1:
                    st.markdown(f"**{cat}**: R$ {gasto:,.2f} de teto R$ {teto:,.2f} ({pct*100:.1f}%)")
                    st.progress(pct_clamp)
                    if pct > 1.0:
                        st.error(f"🚨 Teto estourado em R$ {(gasto - teto):,.2f}!")
                with col_b2:
                    if st.button("🗑️ Apagar", key=f"del_b_{b['id']}", width="stretch"):
                        delete_budget(b["id"], requesting_user_id=user["id"])
                        st.success("Meta orçamentária removida!")
                        st.rerun()
                st.divider()
        else:
            st.info("Nenhuma meta orçamentária cadastrada. Use o formulário abaixo.")

        with st.expander("⚙️ Definir / Ajustar Teto Orçamentário"):
            with st.form("form_set_budget"):
                b_cat = st.selectbox("Categoria", CATEGORIAS_DESPESA)
                b_lim = st.number_input("Limite Máximo Mensal (R$)", min_value=1.0, step=50.0, format="%.2f")
                if st.form_submit_button("Salvar Meta"):
                    set_budget(user["id"], b_cat, b_lim)
                    st.success(f"Meta de R$ {b_lim:,.2f} definida para {b_cat}!")
                    st.rerun()


# =====================================================================
# 6. VIEW: CONSULTOR IA & CONFIGURAÇÕES
# =====================================================================

def view_consultor_configuracoes(user: dict):
    st.title("🤖 Consultor Financeiro IA & Configurações")

    tab_ia, tab_partilha, tab_conf = st.tabs(["💡 Consultor IA (Gemini)", "🤝 Partilhamento de Conta", "⚙️ Configurações & Backup"])

    # ---------------- ABA CONSULTOR IA ----------------
    with tab_ia:
        st.subheader("Análise Inteligente de Gastos com Gemini")
        st.write("Receba diagnósticos precisos sobre seus padrões de consumo, alertas de metas estouradas e dicas práticas para poupar mais.")

        hoje = date.today()
        meses_opcoes = [datetime(hoje.year, m, 1).strftime("%Y-%m") for m in range(1, 13)]
        mes_ia = st.selectbox("Mês para Análise da IA", sorted(list(set(meses_opcoes)), reverse=True), key="mes_ia")
        duvida_usuario = st.text_area("Pergunta opcional para o Consultor IA", placeholder="Ex: Onde gastei demais este mês? Como economizar R$ 300 no próximo mês?")

        if st.button("🚀 Gerar Diagnóstico Financeiro", type="primary"):
            with st.spinner("O Consultor IA está analisando suas movimentações..."):
                trans = get_transactions(user_id=user["id"])
                buds = get_budgets(user_id=user["id"])
                resposta = analyze_finances_with_ai(
                    month_year=mes_ia,
                    transactions=trans,
                    budgets=buds,
                    user_question=duvida_usuario.strip() or None
                )
                st.markdown("### 📋 Diagnóstico da IA")
                st.markdown(resposta)

    # ---------------- ABA PARTILHAMENTO DE CONTA ----------------
    with tab_partilha:
        st.subheader("🤝 Gestão de Partilhamento de Conta")
        st.write("Compartilhe o seu espaço financeiro com outro usuário cadastrado para planejamento conjunto, definindo o nível de acesso apropriado.")

        # 1. Conceder novo compartilhamento
        with st.expander("➕ Partilhar Meu Espaço com Outro Usuário", expanded=True):
            todos_usuarios = get_users()
            outros_usuarios = [u for u in todos_usuarios if u["id"] != user["id"]]

            if outros_usuarios:
                with st.form("form_novo_share"):
                    map_users = {f"{u['username']} ({u['role'].upper()})": u["id"] for u in outros_usuarios}
                    sel_user_label = st.selectbox("Selecione o Usuário para Compartilhar", list(map_users.keys()))
                    sel_target_id = map_users[sel_user_label]

                    sel_perm = st.selectbox(
                        "Nível de Permissão",
                        ["viewer", "editor"],
                        format_func=lambda x: "👁️ Visualizador (Apenas Leitura)" if x == "viewer" else "✏️ Editor (Visualização e Edição)"
                    )

                    btn_compartilhar = st.form_submit_button("Partilhar Espaço", type="primary")
                    if btn_compartilhar:
                        try:
                            add_user_share(owner_id=user["id"], shared_with_user_id=sel_target_id, permission_level=sel_perm)
                            st.success(f"Espaço compartilhado com sucesso com {sel_user_label} como '{sel_perm}'!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao compartilhar espaço: {e}")
            else:
                st.info("Nenhum outro usuário cadastrado no sistema para compartilhar. Crie usuários na aba Configurações.")

        st.markdown("---")

        # 2. Compartilhamentos Concedidos por Mim
        st.subheader("📤 Acessos que Você Concedeu")
        minhas_partilhas = get_user_shares_by_owner(user["id"])
        if minhas_partilhas:
            for s in minhas_partilhas:
                with st.container():
                    c_user, c_perm, c_dt, c_rev = st.columns([3, 2, 2, 2])
                    with c_user:
                        st.markdown(f"**👤 {s['shared_with_username']}**")
                    with c_perm:
                        badge_color = "#3fb950" if s["permission_level"] == "editor" else "#58a6ff"
                        lbl = "✏️ Editor" if s["permission_level"] == "editor" else "👁️ Visualizador"
                        st.markdown(f"<span style='color:{badge_color}; font-weight:600;'>{lbl}</span>", unsafe_allow_html=True)
                    with c_dt:
                        st.caption(f"Desde: {s['created_at'][:10]}")
                    with c_rev:
                        if st.button("🗑️ Revogar", key=f"rev_{s['id']}", width="stretch"):
                            delete_user_share(s["id"], owner_id=user["id"])
                            st.success("Compartilhamento revogado com sucesso!")
                            st.rerun()
                    st.divider()
        else:
            st.info("Você ainda não compartilhou seu espaço com nenhum usuário.")

        st.markdown("---")

        # 3. Consulta Específica de Espaços Compartilhados Recebidos
        st.subheader("📥 Consulta Específica de Espaços Compartilhados")
        partilhas_recebidas = get_user_shares_received(user["id"])
        if partilhas_recebidas:
            st.write("Visualize os lançamentos e contas de outros usuários que concederam acesso a você (mantidos segregados do seu espaço particular):")
            map_partilhas = {f"🏠 Espaço de {r['owner_username']} ({r['permission_level'].upper()})": r for r in partilhas_recebidas}
            sel_partilha_label = st.selectbox("Selecione o Espaço para Consultar", list(map_partilhas.keys()), key="sel_space_preview")
            sel_partilha = map_partilhas[sel_partilha_label]
            owner_target_id = sel_partilha["owner_id"]

            trans_shared = get_transactions(user_id=owner_target_id)
            bills_shared = get_recurring_bills(user_id=owner_target_id)

            st.markdown(f"##### 📊 Lançamentos no Espaço de **{sel_partilha['owner_username']}** ({len(trans_shared)} transações, {len(bills_shared)} contas recorrentes)")
            if trans_shared:
                df_sh = pd.DataFrame(trans_shared)[["due_date", "type", "category", "description", "amount", "status"]]
                df_sh.columns = ["Data", "Tipo", "Categoria", "Descrição", "Valor (R$)", "Status"]
                df_sh["Valor (R$)"] = df_sh["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_sh, width='stretch', hide_index=True)
            else:
                st.caption("Nenhuma movimentação registrada no espaço deste usuário.")
        else:
            st.caption("Nenhum outro usuário compartilhou o espaço financeiro dele com você.")

    # ---------------- ABA CONFIGURAÇÕES ----------------
    with tab_conf:
        st.subheader("Chave de API do Gemini")
        chave_atual = os.getenv("GEMINI_API_KEY", "")
        if not chave_atual:
            try:
                chave_atual = str(st.secrets.get("GEMINI_API_KEY", ""))
            except Exception:
                pass
        nova_chave = st.text_input("GEMINI_API_KEY", value=chave_atual if chave_atual != "sua_chave_aqui" else "", type="password")
        if st.button("Salvar Chave"):
            if nova_chave.strip():
                env_path = BASE_DIR / ".env"
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f'GEMINI_API_KEY="{nova_chave.strip()}"\n')
                os.environ["GEMINI_API_KEY"] = nova_chave.strip()
                st.success("Chave salva com sucesso no arquivo .env!")
            else:
                st.error("Informe uma chave válida.")

        st.markdown("---")
        st.subheader("Backup & Restauração do Banco de Dados")
        col_bk1, col_bk2 = st.columns(2)
        with col_bk1:
            st.markdown("##### 💾 Fazer Backup")
            bk_bytes = get_db_backup_bytes()
            st.download_button(
                label="⬇️ Baixar Cópia do Banco (financas.db)",
                data=bk_bytes,
                file_name=f"financas_backup_{date.today().strftime('%Y%m%d')}.db",
                mime="application/x-sqlite3",
                width='stretch'
            )
        with col_bk2:
            st.markdown("##### 🔄 Restaurar Banco")
            restore_file = st.file_uploader("Carregue o arquivo financas.db", type=["db"])
            if restore_file is not None:
                if st.button("Confirmar Restauração", type="secondary", width='stretch'):
                    ok, msg = restore_db_from_bytes(restore_file.getvalue())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # Gestão de Usuários (Apenas Admin)
        if user.get("role") == "admin":
            st.markdown("---")
            st.subheader("👥 Gestão de Usuários")
            users = get_users()
            st.dataframe(pd.DataFrame(users)[["id", "username", "role", "created_at"]], width='stretch', hide_index=True)

            with st.expander("➕ Criar Novo Usuário"):
                with st.form("form_novo_user"):
                    u_name = st.text_input("Nome de Usuário")
                    u_pass = st.text_input("Senha", type="password")
                    u_role = st.selectbox("Perfil / Permissão", ["editor", "viewer", "admin"])
                    if st.form_submit_button("Criar Usuário"):
                        if u_name.strip() and u_pass.strip():
                            try:
                                add_user(u_name.strip(), u_pass.strip(), u_role)
                                st.success(f"Usuário '{u_name}' criado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao criar usuário: {e}")
                        else:
                            st.error("Preencha todos os campos.")
