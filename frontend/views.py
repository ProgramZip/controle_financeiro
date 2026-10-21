import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from pathlib import Path

from backend.crud import (
    get_transactions, update_transaction_status, revert_transaction_to_pending, delete_transaction, delete_transactions_by_month,
    add_recurring_bill, get_recurring_bills, update_recurring_bill, delete_recurring_bill, process_recurring_bills,
    add_investment, get_investments, update_investment, delete_investment,
    set_budget, get_budgets, delete_budget,
    get_users, add_user, update_user_role, delete_user,
    change_user_password, admin_set_user_password,
    add_user_share, get_user_shares_by_owner, get_user_shares_received, delete_user_share,
    can_user_edit_resource, update_user_profile, get_user_profile
)
from backend.utils import (
    CATEGORIAS_DESPESA, CATEGORIAS_RECEITA,
    read_bank_statement_csv, read_bank_statement_pdf,
    get_db_backup_bytes, restore_db_from_bytes,
    export_transactions_to_excel, analyze_finances_with_ai,
    BASE_DIR
)
from frontend.components import (
    render_metric_card, modal_nova_movimentacao, modal_nova_conta_recorrente,
    modal_editar_movimentacao, modal_editar_conta_recorrente,
    modal_excluir_mes_completo, render_unified_filter_popover,
    render_standard_period_filter, render_floating_ai_assistant
)


# =====================================================================
# 1. VIEW: DASHBOARD GERAL
# =====================================================================

def _render_alert_item_row(item: dict, user_id: int):
    """Renderiza uma linha individual de conta no card de alerta com botão de quitação rápida."""
    c_info, c_val, c_btn = st.columns([5.5, 2.5, 2])
    with c_info:
        parc = f" ({item['installment_current']}/{item['installment_total']})" if item.get("installment_total", 1) > 1 else ""
        badge = f"<span style='background-color:{item['tag_bg']}; color:{item['tag_color']}; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; margin-right: 6px;'>{item['tag_label']}</span>"
        st.markdown(f"{badge} **{item['description']}**{parc}  \n<small style='color:#8b949e;'>Vencimento: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
    with c_val:
        st.markdown(f"<h4 style='color:#f85149; margin: 0.2rem 0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
    with c_btn:
        if st.button("✅ Quitar", key=f"quick_pay_dash_{item['id']}", width="stretch", help="Marcar conta como Paga imediatamente"):
            update_transaction_status(item["id"], "Pago", requesting_user_id=user_id)
            st.toast(f"Conta '{item['description']}' quitada com sucesso!", icon="✅")
            st.rerun()


def render_due_date_alerts(user: dict):
    """
    Renderiza um card/banner de destaque no topo do Dashboard Geral alertando
    sobre contas pendentes de vencimento hoje ou nos próximos 3 dias (e contas em atraso),
    com botão de quitação rápida em 1 clique.
    """
    hoje = date.today()
    limite_3dias = hoje + timedelta(days=3)

    # Busca despesas pendentes estritamente do usuário logado até o limite de 3 dias
    pendentes = get_transactions(
        user_id=user["id"],
        trans_type="despesa",
        status="Pendente",
        end_date=limite_3dias.strftime("%Y-%m-%d")
    )

    alert_items = []
    for item in pendentes:
        raw_date = item.get("due_date")
        if not raw_date:
            continue
        try:
            d_date = date.fromisoformat(str(raw_date)[:10])
        except Exception:
            continue

        if d_date <= limite_3dias:
            dias_dif = (d_date - hoje).days
            if dias_dif < 0:
                tag_label = f"Vencida há {abs(dias_dif)}d"
                tag_bg = "#f85149"
                tag_color = "#ffffff"
                urgency = 0
            elif dias_dif == 0:
                tag_label = "Vence Hoje!"
                tag_bg = "#e3b341"
                tag_color = "#000000"
                urgency = 1
            elif dias_dif == 1:
                tag_label = "Vence Amanhã"
                tag_bg = "#58a6ff"
                tag_color = "#ffffff"
                urgency = 2
            else:
                tag_label = f"Vence em {dias_dif}d"
                tag_bg = "#388bfd"
                tag_color = "#ffffff"
                urgency = 3

            alert_items.append({
                **item,
                "d_date": d_date,
                "dias_dif": dias_dif,
                "tag_label": tag_label,
                "tag_bg": tag_bg,
                "tag_color": tag_color,
                "urgency": urgency
            })

    if not alert_items:
        return

    # Ordena por urgência (atrasadas primeiro, depois hoje, depois próximos dias) e data
    alert_items.sort(key=lambda x: (x["urgency"], x["d_date"], -x["amount"]))

    qtd_total = len(alert_items)
    valor_total = sum(i["amount"] for i in alert_items)
    atrasadas = sum(1 for i in alert_items if i["dias_dif"] < 0)
    hoje_count = sum(1 for i in alert_items if i["dias_dif"] == 0)

    # Subtítulo explicativo
    sub_parts = []
    if atrasadas > 0:
        sub_parts.append(f"{atrasadas} em atraso")
    if hoje_count > 0:
        sub_parts.append(f"{hoje_count} vencendo hoje")
    proximos_count = qtd_total - atrasadas - hoje_count
    if proximos_count > 0:
        sub_parts.append(f"{proximos_count} nos próximos 3 dias")
    sub_text = " • ".join(sub_parts)

    cor_borda = "#f85149" if atrasadas > 0 else "#e3b341"
    icone = "🚨" if atrasadas > 0 else "⚠️"

    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(227, 179, 65, 0.12), rgba(248, 81, 73, 0.08));
            border: 1px solid {cor_borda};
            border-left: 6px solid {cor_borda};
            border-radius: 12px;
            padding: 1rem 1.25rem 0.8rem 1.25rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <h4 style="margin: 0; color: #ffffff; font-size: 1.05rem; display: flex; align-items: center; gap: 8px;">
                        <span>{icone}</span> <span>Alerta de Vencimentos Imediatos</span>
                    </h4>
                    <p style="margin: 4px 0 0 0; color: #c9d1d9; font-size: 0.9rem;">
                        Você possui <b>{qtd_total}</b> conta(s) a pagar somando <b style="color: #f85149;">R$ {valor_total:,.2f}</b> ({sub_text}).
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Renderiza as contas com quitação rápida
    top_items = alert_items[:3]
    rest_items = alert_items[3:]

    with st.container():
        for item in top_items:
            _render_alert_item_row(item, user["id"])

        if rest_items:
            with st.expander(f"➕ Ver outras {len(rest_items)} conta(s) com vencimento próximo"):
                for item in rest_items:
                    _render_alert_item_row(item, user["id"])

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)


def view_dashboard(user: dict):
    st.title("📊 Painel Financeiro")

    # Alerta de Vencimento Imediato no topo do Dashboard
    render_due_date_alerts(user)

    # 1. Carrega todas as movimentações do usuário para apurar meses e consolidado geral
    all_user_trans = get_transactions(user_id=user["id"])
    meses_com_dados = sorted(list(set(str(t["due_date"])[:7] for t in all_user_trans if t.get("due_date"))), reverse=True)
    hoje = date.today()
    mes_atual_str = hoje.strftime("%Y-%m")
    if mes_atual_str not in meses_com_dados:
        meses_com_dados.insert(0, mes_atual_str)

    # 2. Seletor de Período Padronizado (Padrão: 🌐 Todo o Histórico Geral)
    col_per1, col_per2 = st.columns([3.5, 1])
    with col_per1:
        filtro_periodo = render_standard_period_filter(
            available_months=meses_com_dados,
            key_prefix="dash_period",
            default_mode_index=0  # Padrão: 🌐 Todo o Histórico (Geral)
        )
    with col_per2:
        st.write("")
        st.write("")
        if st.button("➕ Nova Movimentação", type="primary", width='stretch', key="btn_dash_nova_mov"):
            modal_nova_movimentacao(user["id"])

    # 3. Filtragem das movimentações para apuração dos indicadores
    if filtro_periodo["mode"] == "geral":
        trans_ativas = all_user_trans
        sub_rotulo = "histórico consolidado"
    elif filtro_periodo["mode"] == "mes":
        m_sel = filtro_periodo["month_year"]
        trans_ativas = [t for t in all_user_trans if str(t.get("due_date", ""))[:7] == m_sel]
        sub_rotulo = f"mês {m_sel}"
    else:  # personalizado
        d_ini = filtro_periodo["start_date"]
        d_fim = filtro_periodo["end_date"]
        trans_ativas = [t for t in all_user_trans if d_ini <= str(t.get("due_date", "")) <= d_fim]
        sub_rotulo = "período selecionado"

    # Cálculos
    receitas_total = sum(t["amount"] for t in trans_ativas if t["type"] == "receita")
    despesas_total = sum(t["amount"] for t in trans_ativas if t["type"] == "despesa")
    saldo_periodo = receitas_total - despesas_total

    investimentos = get_investments(user_id=user["id"])
    total_investido = sum(i["current_value"] for i in investimentos)

    taxa_poupanca = ((receitas_total - despesas_total) / receitas_total * 100) if receitas_total > 0 else 0.0

    # Cards de Resumo
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Receitas", f"R$ {receitas_total:,.2f}", f"Entradas ({sub_rotulo})", "#3fb950", "🟢")
    with c2:
        render_metric_card("Despesas", f"R$ {despesas_total:,.2f}", f"Saídas ({sub_rotulo})", "#f85149", "🔴")
    with c3:
        cor_saldo = "#3fb950" if saldo_periodo >= 0 else "#f85149"
        render_metric_card("Saldo Líquido", f"R$ {saldo_periodo:,.2f}", f"Balanço ({sub_rotulo})", cor_saldo, "💰")
    with c4:
        render_metric_card("Investimentos", f"R$ {total_investido:,.2f}", "Patrimônio ativo", "#58a6ff", "📈")
    with c5:
        cor_tx = "#3fb950" if taxa_poupanca >= 20 else ("#e3b341" if taxa_poupanca >= 0 else "#f85149")
        render_metric_card("Poupança", f"{taxa_poupanca:.1f}%", f"Taxa ({sub_rotulo})", cor_tx, "🛡️")

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos Interativos em Plotly
    g_col1, g_col2 = st.columns([1, 1])

    despesas_ativas = [t for t in trans_ativas if t["type"] == "despesa"]
    with g_col1:
        st.subheader("Despesas por Categoria")
        if despesas_ativas:
            df_desp = pd.DataFrame(despesas_ativas)
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
            st.info("Nenhuma despesa registrada para o período selecionado.")

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

    # Evolução Temporal Mensal no modo consolidado geral
    if filtro_periodo["mode"] == "geral" and len(trans_ativas) > 0:
        df_all = pd.DataFrame(trans_ativas)
        if "due_date" in df_all.columns and not df_all.empty:
            df_all["mes_ano"] = df_all["due_date"].astype(str).str[:7]
            meses_distintos = df_all["mes_ano"].nunique()
            if meses_distintos > 1:
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📈 Evolução Temporal Mensal (Histórico Consolidado)")
                evol_grp = df_all.groupby(["mes_ano", "type"])["amount"].sum().reset_index()
                evol_grp = evol_grp.sort_values("mes_ano")
                evol_grp["type_label"] = evol_grp["type"].apply(lambda x: "Receitas" if x == "receita" else "Despesas")
                fig_evol = px.bar(
                    evol_grp,
                    x="mes_ano",
                    y="amount",
                    color="type_label",
                    barmode="group",
                    color_discrete_map={"Receitas": "#3fb950", "Despesas": "#f85149"},
                    labels={"mes_ano": "Mês", "amount": "Total (R$)", "type_label": "Tipo"}
                )
                fig_evol.update_layout(
                    margin=dict(t=20, b=20, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(type="category")
                )
                st.plotly_chart(fig_evol, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)

    # Listagem das Últimas Movimentações Pessoais
    st.subheader(f"Últimos Lançamentos ({sub_rotulo.title()})")
    if trans_ativas:
        df_ult = pd.DataFrame(trans_ativas)[["due_date", "type", "category", "description", "amount", "status"]]
        df_ult.columns = ["Data", "Tipo", "Categoria", "Descrição", "Valor (R$)", "Status"]
        df_ult["Valor (R$)"] = df_ult["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_ult.head(10), width='stretch', hide_index=True)
    else:
        st.caption("Nenhum lançamento encontrado no período selecionado.")


# =====================================================================
# 2. VIEW: MOVIMENTAÇÕES
# =====================================================================

def view_movimentacoes(user: dict):
    st.title("💳 Gestão de Movimentações")

    # Carrega transações estritamente particulares do próprio usuário
    all_trans = get_transactions(user_id=user["id"])

    # Ações e Filtros no topo (Responsivo Desktop & Mobile)
    hoje = date.today()
    mes_atual_str = hoje.strftime("%Y-%m")
    meses_com_dados = sorted(list(set(str(t["due_date"])[:7] for t in all_trans if t.get("due_date"))), reverse=True)
    if mes_atual_str not in meses_com_dados:
        meses_com_dados.insert(0, mes_atual_str)

    col_filtros, col_del, col_nova, col_exp = st.columns([1.5, 1.2, 1.4, 1.2])

    with col_filtros:
        trans_ativas = render_unified_filter_popover(all_trans, meses_com_dados, key_prefix="mov_filters")
    with col_del:
        if st.button("🗑️ Excluir Mês", width="stretch", help="Exclusão em lote por modal seguro"):
            modal_excluir_mes_completo(user["id"], meses_com_dados)
    with col_nova:
        if st.button("➕ Nova Movimentação", type="primary", width='stretch', key="btn_view_nova_mov"):
            modal_nova_movimentacao(user["id"])
    with col_exp:
        excel_bytes = export_transactions_to_excel(trans_ativas)
        st.download_button(
            label="📥 Exportar Excel",
            data=excel_bytes,
            file_name=f"movimentacoes_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch'
        )

    despesas_ativas = [t for t in trans_ativas if t["type"] == "despesa"]
    receitas_ativas = [t for t in trans_ativas if t["type"] == "receita"]

    total_despesas = sum(t["amount"] for t in despesas_ativas)
    total_receitas = sum(t["amount"] for t in receitas_ativas)

    # ---------------- CARDS DE RESUMO (DESPESAS E RECEITAS) ----------------
    col_card1, col_card2 = st.columns(2)
    with col_card1:
        render_metric_card(
            title="Total das Despesas Filtradas",
            value=f"R$ {total_despesas:,.2f}",
            sub=f"{len(despesas_ativas)} despesa(s) ativa(s)",
            color="#f85149",
            icon="🔴"
        )
    with col_card2:
        render_metric_card(
            title="Total das Receitas Filtradas",
            value=f"R$ {total_receitas:,.2f}",
            sub=f"{len(receitas_ativas)} receita(s) ativa(s)",
            color="#3fb950",
            icon="🟢"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Abas: Despesas e Receitas
    tab_despesas, tab_receitas = st.tabs(["🔴 Despesas", "🟢 Receitas"])

    # ---------------- ABA DESPESAS ----------------
    with tab_despesas:
        st.subheader("Despesas")
        despesas = despesas_ativas

        # Separação: Pendentes e Pagas
        desp_pendentes = [d for d in despesas if d["status"] == "Pendente"]
        desp_pagas = [d for d in despesas if d["status"] == "Pago"]

        st.markdown("#### ⏳ Contas Pendentes / A Pagar")
        if desp_pendentes:
            for item in desp_pendentes:
                with st.container():
                    c_info, c_val, c_btn, c_edit, c_del = st.columns([4, 2, 1.5, 1.5, 1.5])
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
                    with c_edit:
                        if st.button("✏️ Alterar", key=f"edit_dp_{item['id']}", width='stretch'):
                            modal_editar_movimentacao(item, user["id"])
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
                    c_info, c_val, c_rev, c_edit, c_del = st.columns([4, 2, 1.5, 1.5, 1.5])
                    with c_info:
                        parc_info = f" ({item['installment_current']}/{item['installment_total']})" if item.get('installment_total', 1) > 1 else ""
                        st.markdown(f"**{item['description']}**{parc_info}  \n<small style='color:#8b949e;'>Pago em: {item['due_date']} | Categoria: {item['category']} | {item.get('payment_method', 'À Vista')}</small>", unsafe_allow_html=True)
                    with c_val:
                        st.markdown(f"<h4 style='color:#f85149; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_rev:
                        if st.button("🔄 Retornar", key=f"rev_paga_{item['id']}", width='stretch', help="Reverter status desta conta para Pendente"):
                            revert_transaction_to_pending(item["id"], requesting_user_id=user["id"])
                            st.success("Conta retornada para Pendentes!")
                            st.rerun()
                    with c_edit:
                        if st.button("✏️ Alterar", key=f"edit_paga_{item['id']}", width='stretch'):
                            modal_editar_movimentacao(item, user["id"])
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
        receitas = receitas_ativas
        rec_pendentes = [r for r in receitas if r["status"] == "Pendente"]
        rec_recebidas = [r for r in receitas if r["status"] in ("Recebido", "Pago")]

        st.markdown("#### ⏳ Valores a Receber (Pendentes)")
        if rec_pendentes:
            for item in rec_pendentes:
                with st.container():
                    c_info, c_val, c_btn, c_edit, c_del = st.columns([4, 2, 1.5, 1.5, 1.5])
                    with c_info:
                        st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Previsão: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                    with c_val:
                        st.markdown(f"<h4 style='color:#3fb950; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_btn:
                        if st.button("💵 Receber", key=f"rec_{item['id']}", width='stretch'):
                            update_transaction_status(item["id"], "Recebido", requesting_user_id=user["id"])
                            st.success("Recebimento confirmado!")
                            st.rerun()
                    with c_edit:
                        if st.button("✏️ Alterar", key=f"edit_rp_{item['id']}", width='stretch'):
                            modal_editar_movimentacao(item, user["id"])
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
                    c_info, c_val, c_rev, c_edit, c_del = st.columns([4, 2, 1.5, 1.5, 1.5])
                    with c_info:
                        st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Recebido em: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                    with c_val:
                        st.markdown(f"<h4 style='color:#3fb950; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_rev:
                        if st.button("🔄 Retornar", key=f"rev_rec_{item['id']}", width='stretch', help="Reverter status desta receita para Pendente"):
                            revert_transaction_to_pending(item["id"], requesting_user_id=user["id"])
                            st.success("Receita retornada para Pendentes!")
                            st.rerun()
                    with c_edit:
                        if st.button("✏️ Alterar", key=f"edit_rec_paga_{item['id']}", width='stretch'):
                            modal_editar_movimentacao(item, user["id"])
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

    # Carrega contas recorrentes do usuário
    all_contas = get_recurring_bills(user_id=user["id"])

    # Ações de Topo: Popover de Filtros Globais, Nova Conta Recorrente (Modal) e Sincronização
    col_filtros, col_sync, col_nova = st.columns([1.5, 1.3, 1.4])
    with col_filtros:
        contas_ativas = render_unified_filter_popover(
            all_contas, 
            available_months=[], 
            key_prefix="contas_filters", 
            show_categories=True
        )
    with col_sync:
        if st.button("⚡ Sincronizar Mês Vigente", width='stretch', key="btn_sync_recorrente"):
            novas = process_recurring_bills(user_id=user["id"], force_manual=True)
            if novas > 0:
                st.success(f"{novas} conta(s) gerada(s) para o mês atual!")
            else:
                st.info("Todas as contas do mês já estão atualizadas. Nenhuma duplicidade gerada.")
            st.rerun()
    with col_nova:
        if st.button("➕ Nova Conta Recorrente", type="primary", width='stretch', key="btn_nova_recorrente"):
            modal_nova_conta_recorrente(user["id"])

    # Separação de Despesas e Receitas Fixas
    desp_fixas = [b for b in contas_ativas if b.get("type", "despesa") == "despesa"]
    rec_fixas = [b for b in contas_ativas if b.get("type") == "receita"]

    total_desp_fixas = sum(b["amount"] for b in desp_fixas if b.get("is_active", 1))
    total_rec_fixas = sum(b["amount"] for b in rec_fixas if b.get("is_active", 1))

    # ---------------- CARDS DE RESUMO (DESPESAS E RECEITAS FIXAS) ----------------
    col_card1, col_card2 = st.columns(2)
    with col_card1:
        render_metric_card(
            title="Total Despesas Fixas (Ativas)",
            value=f"R$ {total_desp_fixas:,.2f}",
            sub=f"{len([b for b in desp_fixas if b.get('is_active', 1)])} conta(s) ativa(s) | {len(desp_fixas)} cadastrada(s)",
            color="#f85149",
            icon="🔴"
        )
    with col_card2:
        render_metric_card(
            title="Total Receitas Fixas (Ativas)",
            value=f"R$ {total_rec_fixas:,.2f}",
            sub=f"{len([b for b in rec_fixas if b.get('is_active', 1)])} receita(s) ativa(s) | {len(rec_fixas)} cadastrada(s)",
            color="#3fb950",
            icon="🟢"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Abas: Despesas e Receitas
    tab_desp, tab_rec = st.tabs(["🔴 Contas a Pagar (Despesas Fixas)", "🟢 Receitas Fixas"])

    # --- ABA DESPESAS FIXAS ---
    with tab_desp:
        st.subheader("Despesas Fixas")
        if desp_fixas:
            for b in desp_fixas:
                with st.container():
                    c_info, c_val, c_status, c_edit, c_del = st.columns([4, 2, 1.5, 1.5, 1.5])
                    with c_info:
                        status_badge = "🟢 Ativa" if b["is_active"] else "⏸️ Pausada"
                        st.markdown(
                            f"**{b['description']}** ({status_badge})  \n"
                            f"<small style='color:#8b949e;'>Vencimento: Dia {b['due_day']} | Categoria: {b['category']}</small>",
                            unsafe_allow_html=True
                        )
                    with c_val:
                        cor = "#f85149" if b["is_active"] else "#8b949e"
                        st.markdown(f"<h4 style='color:{cor}; margin:0;'>R$ {b['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_status:
                        novo_estado = 0 if b["is_active"] else 1
                        btn_txt = "⏸️ Pausar" if b["is_active"] else "▶️ Ativar"
                        if st.button(btn_txt, key=f"tgl_desp_{b['id']}", width="stretch"):
                            update_recurring_bill(b["id"], requesting_user_id=user["id"], is_active=novo_estado)
                            st.rerun()
                    with c_edit:
                        if st.button("✏️ Alterar", key=f"edit_rec_desp_{b['id']}", width="stretch"):
                            modal_editar_conta_recorrente(b, user["id"])
                    with c_del:
                        if st.button("🗑️ Apagar", key=f"del_rec_desp_{b['id']}", width="stretch"):
                            delete_recurring_bill(b["id"], requesting_user_id=user["id"])
                            st.success("Conta recorrente excluída!")
                            st.rerun()
                    st.divider()
        else:
            st.info("Nenhuma despesa fixa recorrente cadastrada ou encontrada com os filtros.")

    # --- ABA RECEITAS FIXAS ---
    with tab_rec:
        st.subheader("Receitas Fixas")
        if rec_fixas:
            for b in rec_fixas:
                with st.container():
                    c_info, c_val, c_status, c_edit, c_del = st.columns([4, 2, 1.5, 1.5, 1.5])
                    with c_info:
                        status_badge = "🟢 Ativa" if b["is_active"] else "⏸️ Pausada"
                        st.markdown(
                            f"**{b['description']}** ({status_badge})  \n"
                            f"<small style='color:#8b949e;'>Recebimento: Dia {b['due_day']} | Categoria: {b['category']}</small>",
                            unsafe_allow_html=True
                        )
                    with c_val:
                        cor = "#3fb950" if b["is_active"] else "#8b949e"
                        st.markdown(f"<h4 style='color:{cor}; margin:0;'>R$ {b['amount']:,.2f}</h4>", unsafe_allow_html=True)
                    with c_status:
                        novo_estado = 0 if b["is_active"] else 1
                        btn_txt = "⏸️ Pausar" if b["is_active"] else "▶️ Ativar"
                        if st.button(btn_txt, key=f"tgl_rec_{b['id']}", width="stretch"):
                            update_recurring_bill(b["id"], requesting_user_id=user["id"], is_active=novo_estado)
                            st.rerun()
                    with c_edit:
                        if st.button("✏️ Alterar", key=f"edit_rec_rec_{b['id']}", width="stretch"):
                            modal_editar_conta_recorrente(b, user["id"])
                    with c_del:
                        if st.button("🗑️ Apagar", key=f"del_rec_rec_{b['id']}", width="stretch"):
                            delete_recurring_bill(b["id"], requesting_user_id=user["id"])
                            st.success("Receita recorrente excluída!")
                            st.rerun()
                    st.divider()
        else:
            st.info("Nenhuma receita fixa recorrente cadastrada ou encontrada com os filtros.")


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

def view_configuracoes_perfil(user: dict):
    st.title("⚙️ Configurações & Perfil")
    st.caption("Gerenciamento de dados cadastrais, chaves de integração, backups do banco e segurança.")

    # 1. PERFIL DO USUÁRIO
    st.subheader("👤 Meu Perfil Cadastral")
    st.caption("Mantenha seus dados atualizados. O nome de usuário é estritamente usado para login e identificação no partilhamento.")

    perfil_atual = st.session_state.get("user") or user

    with st.form("form_meu_perfil"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.text_input("Nome de Usuário (Login)", value=perfil_atual.get("username", ""), disabled=True, help="Identificador único para login e compartilhamento de espaços")
            full_name_val = st.text_input("Nome Completo", value=perfil_atual.get("full_name") or "", placeholder="Ex: João da Silva")
        with col_p2:
            cpf_val = st.text_input("CPF / Documento", value=perfil_atual.get("cpf") or "", placeholder="000.000.000-00")
            address_val = st.text_input("Endereço", value=perfil_atual.get("address") or "", placeholder="Ex: Rua das Flores, 123 - Cidade/UF")

        if st.form_submit_button("💾 Salvar Perfil", type="primary"):
            ok = update_user_profile(
                user_id=user["id"],
                full_name=full_name_val,
                address=address_val,
                cpf=cpf_val
            )
            if ok:
                user["full_name"] = full_name_val
                user["address"] = address_val
                user["cpf"] = cpf_val
                st.session_state["user"] = user
                st.success("✅ Informações de perfil atualizadas com sucesso!")
                st.rerun()
            else:
                st.error("Não foi possível atualizar o perfil cadastral.")

    st.markdown("---")

    # 2. CHAVE DE API DO GEMINI
    st.subheader("🔑 Chave de API do Gemini")
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

    # 3. BACKUP & RESTAURAÇÃO
    st.subheader("💾 Backup & Restauração do Banco de Dados")
    col_bk1, col_bk2 = st.columns(2)
    with col_bk1:
        st.markdown("##### ⬇️ Fazer Backup")
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

    # 4. SEGURANÇA & ALTERAÇÃO DE SENHA
    st.markdown("---")
    st.subheader("🔐 Segurança & Alteração de Senha")
    st.write(f"Altere a sua senha de acesso ao sistema (Usuário conectado: **{user['username']}**).")

    with st.form("form_alterar_propria_senha"):
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            senha_atual = st.text_input("Senha Atual", type="password", key="sec_curr_pass")
        with col_s2:
            nova_senha = st.text_input("Nova Senha", type="password", help="Mínimo de 4 caracteres", key="sec_new_pass")
        with col_s3:
            confirma_nova = st.text_input("Confirmar Nova Senha", type="password", key="sec_conf_pass")

        btn_trocar_senha = st.form_submit_button("Atualizar Minha Senha", type="primary")
        if btn_trocar_senha:
            if not senha_atual:
                st.error("Por favor, informe sua senha atual.")
            elif len(nova_senha.strip()) < 4:
                st.error("A nova senha deve ter no mínimo 4 caracteres.")
            elif nova_senha != confirma_nova:
                st.error("A nova senha e a confirmação não coincidem.")
            else:
                ok, msg = change_user_password(user["id"], senha_atual, nova_senha)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # 5. GESTÃO DE USUÁRIOS (ADMIN)
    if user.get("role") == "admin":
        st.markdown("---")
        st.subheader("👥 Gestão de Usuários")
        users = get_users()
        df_users = pd.DataFrame(users)[["id", "username", "full_name", "cpf", "role", "created_at"]]
        df_users.columns = ["ID", "Usuário", "Nome Completo", "CPF", "Função", "Criado em"]
        st.dataframe(df_users, width='stretch', hide_index=True)

        col_adm_u1, col_adm_u2 = st.columns(2)
        with col_adm_u1:
            with st.expander("➕ Criar Novo Usuário"):
                with st.form("form_novo_user"):
                    u_name = st.text_input("Nome de Usuário (Login) *")
                    u_pass = st.text_input("Senha Inicial *", type="password")
                    u_role = st.selectbox("Perfil / Permissão", ["editor", "viewer", "admin"])
                    u_full_name = st.text_input("Nome Completo (Opcional)")
                    u_cpf = st.text_input("CPF (Opcional)")
                    u_address = st.text_input("Endereço (Opcional)")
                    if st.form_submit_button("Criar Usuário", type="primary"):
                        if u_name.strip() and u_pass.strip():
                            try:
                                add_user(
                                    username=u_name.strip(),
                                    password=u_pass.strip(),
                                    role=u_role,
                                    full_name=u_full_name,
                                    address=u_address,
                                    cpf=u_cpf
                                )
                                st.success(f"Usuário '{u_name}' criado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao criar usuário: {e}")
                        else:
                            st.error("Preencha o nome de usuário e a senha.")

        with col_adm_u2:
            with st.expander("🔑 Redefinir Senha de Usuário (Admin)"):
                with st.form("form_admin_reset_senha"):
                    users_list = get_users()
                    map_users_reset = {f"{u['username']} (ID: {u['id']} - {u['role'].upper()})": u["id"] for u in users_list}
                    sel_user_label = st.selectbox("Usuário Alvo", list(map_users_reset.keys()), key="adm_reset_target")
                    target_user_id = map_users_reset[sel_user_label]
                    adm_new_pass = st.text_input("Nova Senha", type="password", key="adm_new_pass")
                    adm_conf_pass = st.text_input("Confirmar Senha", type="password", key="adm_conf_pass")

                    if st.form_submit_button("Redefinir Senha"):
                        if len(adm_new_pass.strip()) < 4:
                            st.error("A nova senha deve ter no mínimo 4 caracteres.")
                        elif adm_new_pass != adm_conf_pass:
                            st.error("As senhas não coincidem.")
                        else:
                            ok, msg = admin_set_user_password(user["id"], target_user_id, adm_new_pass)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)


# Compatibilidade retrocompatível de nome
view_consultor_configuracoes = view_configuracoes_perfil


# =====================================================================
# 7. VIEW: ESPAÇOS COMPARTILHADOS ("SEGUNDA ÁREA DE TRABALHO")
# =====================================================================

def view_espacos_compartilhados(user: dict):
    st.title("🤝 Espaços Compartilhados")
    st.write("Acesse a **Segunda Área de Trabalho** compartilhada com você ou gerencie os acessos ao seu próprio espaço.")

    tab_segunda_area, tab_gerir_partilhas = st.tabs([
        "💻 Segunda Área de Trabalho (Acessos Recebidos)", 
        "📤 Gerenciar Meus Compartilhamentos (Concedidos)"
    ])

    # =================================================================
    # ABA 1: SEGUNDA ÁREA DE TRABALHO (EDITOR OU VISUALIZADOR)
    # =================================================================
    with tab_segunda_area:
        partilhas_recebidas = get_user_shares_received(user["id"])

        if not partilhas_recebidas:
            st.info(f"Nenhum usuário compartilhou o espaço financeiro com você ainda. Peça a outro usuário que conceda acesso ao seu usuário (**{user['username']}**).")
        else:
            map_partilhas = {
                f"🏠 Espaço de {r['owner_username']} ({'✏️ Editor' if r['permission_level'] == 'editor' else '👁️ Visualizador'})": r 
                for r in partilhas_recebidas
            }
            sel_label = st.selectbox("Selecione o Espaço de Trabalho", list(map_partilhas.keys()), key="sel_shared_workspace")
            sel_share = map_partilhas[sel_label]
            owner_id = sel_share["owner_id"]
            owner_username = sel_share["owner_username"]
            is_editor = (sel_share["permission_level"] == "editor")

            # Dados do Proprietário
            trans_prop = get_transactions(user_id=owner_id)
            bills_prop = get_recurring_bills(user_id=owner_id)

            meses_com_dados = sorted(list(set(str(t["due_date"])[:7] for t in trans_prop if t.get("due_date"))), reverse=True)
            hoje = date.today()
            mes_atual_str = hoje.strftime("%Y-%m")
            if mes_atual_str not in meses_com_dados:
                meses_com_dados.insert(0, mes_atual_str)

            if is_editor:
                # ---------------- MODO SEGUNDA ÁREA DE TRABALHO (EDITOR) ----------------
                st.success(f"✏️ **Modo Editor Conectado:** Você está na **Segunda Área de Trabalho** de **{owner_username}**. Todas as alterações, inclusões e quitações serão gravadas diretamente no espaço dele.")

                col_sf1, col_sf2 = st.columns([3, 1.5])
                with col_sf1:
                    trans_ativas = render_unified_filter_popover(trans_prop, meses_com_dados, key_prefix=f"sh_ed_{owner_id}")
                with col_sf2:
                    if st.button(f"➕ Nova Movimentação em {owner_username}", type="primary", width="stretch", key=f"btn_sh_new_{owner_id}"):
                        modal_nova_movimentacao(user_id=owner_id)

                despesas_ativas = [t for t in trans_ativas if t["type"] == "despesa"]
                receitas_ativas = [t for t in trans_ativas if t["type"] == "receita"]
                total_desp = sum(t["amount"] for t in despesas_ativas)
                total_rec = sum(t["amount"] for t in receitas_ativas)
                saldo = total_rec - total_desp

                c1, c2, c3 = st.columns(3)
                with c1:
                    render_metric_card(f"Receitas ({owner_username})", f"R$ {total_rec:,.2f}", f"{len(receitas_ativas)} entrada(s)", "#3fb950", "🟢")
                with c2:
                    render_metric_card(f"Despesas ({owner_username})", f"R$ {total_desp:,.2f}", f"{len(despesas_ativas)} saída(s)", "#f85149", "🔴")
                with c3:
                    cor_s = "#3fb950" if saldo >= 0 else "#f85149"
                    render_metric_card(f"Saldo ({owner_username})", f"R$ {saldo:,.2f}", "Balanço das movimentações", cor_s, "💰")

                st.markdown("<br>", unsafe_allow_html=True)

                tab_m_desp, tab_m_rec, tab_m_contas = st.tabs([
                    "🔴 Despesas do Espaço", "🟢 Receitas do Espaço", "🔄 Contas Recorrentes do Espaço"
                ])

                with tab_m_desp:
                    st.subheader(f"Despesas no Espaço de {owner_username}")
                    desp_pend = [d for d in despesas_ativas if d["status"] == "Pendente"]
                    desp_pagas = [d for d in despesas_ativas if d["status"] == "Pago"]

                    st.markdown("#### ⏳ Contas Pendentes / A Pagar")
                    if desp_pend:
                        for item in desp_pend:
                            with st.container():
                                ci, cv, cb, ce, cd = st.columns([4, 2, 1.5, 1.5, 1.5])
                                with ci:
                                    st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Vence em: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                                with cv:
                                    st.markdown(f"<h4 style='color:#f85149; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                                with cb:
                                    if st.button("✅ Pagar", key=f"sh_pay_{item['id']}", width="stretch"):
                                        update_transaction_status(item["id"], "Pago", requesting_user_id=user["id"])
                                        st.success("Conta quitada no espaço compartilhado!")
                                        st.rerun()
                                with ce:
                                    if st.button("✏️ Alterar", key=f"sh_ed_dp_{item['id']}", width="stretch"):
                                        modal_editar_movimentacao(item, user["id"])
                                with cd:
                                    if st.button("🗑️ Apagar", key=f"sh_del_dp_{item['id']}", width="stretch"):
                                        delete_transaction(item["id"], user_id=user["id"])
                                        st.success("Conta pendente excluída do espaço compartilhado!")
                                        st.rerun()
                                st.divider()
                    else:
                        st.info("Nenhuma conta pendente no espaço compartilhado.")

                    st.markdown("#### ✅ Contas Pagas")
                    if desp_pagas:
                        for item in desp_pagas:
                            with st.container():
                                ci, cv, cr, ce, cd = st.columns([4, 2, 1.5, 1.5, 1.5])
                                with ci:
                                    st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Pago em: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                                with cv:
                                    st.markdown(f"<h4 style='color:#f85149; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                                with cr:
                                    if st.button("🔄 Retornar", key=f"sh_rev_{item['id']}", width="stretch"):
                                        revert_transaction_to_pending(item["id"], requesting_user_id=user["id"])
                                        st.rerun()
                                with ce:
                                    if st.button("✏️ Alterar", key=f"sh_ed_paga_{item['id']}", width="stretch"):
                                        modal_editar_movimentacao(item, user["id"])
                                with cd:
                                    if st.button("🗑️ Apagar", key=f"sh_del_paga_{item['id']}", width="stretch"):
                                        delete_transaction(item["id"], user_id=user["id"])
                                        st.rerun()
                                st.divider()
                    else:
                        st.caption("Nenhuma conta paga no espaço compartilhado.")

                with tab_m_rec:
                    st.subheader(f"Receitas no Espaço de {owner_username}")
                    rec_pend = [r for r in receitas_ativas if r["status"] == "Pendente"]
                    rec_rec = [r for r in receitas_ativas if r["status"] in ("Recebido", "Pago")]

                    st.markdown("#### ⏳ Valores a Receber (Pendentes)")
                    if rec_pend:
                        for item in rec_pend:
                            with st.container():
                                ci, cv, cb, ce, cd = st.columns([4, 2, 1.5, 1.5, 1.5])
                                with ci:
                                    st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Previsão: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                                with cv:
                                    st.markdown(f"<h4 style='color:#3fb950; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                                with cb:
                                    if st.button("💵 Receber", key=f"sh_rec_{item['id']}", width="stretch"):
                                        update_transaction_status(item["id"], "Recebido", requesting_user_id=user["id"])
                                        st.success("Recebimento registrado no espaço compartilhado!")
                                        st.rerun()
                                with ce:
                                    if st.button("✏️ Alterar", key=f"sh_ed_rp_{item['id']}", width="stretch"):
                                        modal_editar_movimentacao(item, user["id"])
                                with cd:
                                    if st.button("🗑️ Apagar", key=f"sh_del_rp_{item['id']}", width="stretch"):
                                        delete_transaction(item["id"], user_id=user["id"])
                                        st.rerun()
                                st.divider()
                    else:
                        st.info("Nenhuma receita pendente.")

                    st.markdown("#### 🟢 Valores Recebidos")
                    if rec_rec:
                        for item in rec_rec:
                            with st.container():
                                ci, cv, cr, ce, cd = st.columns([4, 2, 1.5, 1.5, 1.5])
                                with ci:
                                    st.markdown(f"**{item['description']}**  \n<small style='color:#8b949e;'>Recebido em: {item['due_date']} | Categoria: {item['category']}</small>", unsafe_allow_html=True)
                                with cv:
                                    st.markdown(f"<h4 style='color:#3fb950; margin:0;'>R$ {item['amount']:,.2f}</h4>", unsafe_allow_html=True)
                                with cr:
                                    if st.button("🔄 Retornar", key=f"sh_rev_r_{item['id']}", width="stretch"):
                                        revert_transaction_to_pending(item["id"], requesting_user_id=user["id"])
                                        st.rerun()
                                with ce:
                                    if st.button("✏️ Alterar", key=f"sh_ed_rec_{item['id']}", width="stretch"):
                                        modal_editar_movimentacao(item, user["id"])
                                with cd:
                                    if st.button("🗑️ Apagar", key=f"sh_del_rec_{item['id']}", width="stretch"):
                                        delete_transaction(item["id"], user_id=user["id"])
                                        st.rerun()
                                st.divider()
                    else:
                        st.caption("Nenhum recebimento registrado.")

                with tab_m_contas:
                    st.subheader(f"Contas Recorrentes no Espaço de {owner_username}")
                    if bills_prop:
                        for b in bills_prop:
                            with st.container():
                                ci, cv, cs, ce, cd = st.columns([4, 2, 1.5, 1.5, 1.5])
                                with ci:
                                    st_txt = "🟢 Ativa" if b["is_active"] else "⏸️ Pausada"
                                    st.markdown(f"**{b['description']}** ({st_txt})  \n<small style='color:#8b949e;'>Dia: {b['due_day']} | Categoria: {b['category']}</small>", unsafe_allow_html=True)
                                with cv:
                                    cor = "#f85149" if b["type"] == "despesa" else "#3fb950"
                                    st.markdown(f"<h4 style='color:{cor}; margin:0;'>R$ {b['amount']:,.2f}</h4>", unsafe_allow_html=True)
                                with cs:
                                    novo_st = 0 if b["is_active"] else 1
                                    lbl_st = "⏸️ Pausar" if b["is_active"] else "▶️ Ativar"
                                    if st.button(lbl_st, key=f"sh_tgl_{b['id']}", width="stretch"):
                                        update_recurring_bill(b["id"], requesting_user_id=user["id"], is_active=novo_st)
                                        st.rerun()
                                with ce:
                                    if st.button("✏️ Alterar", key=f"sh_ed_rec_b_{b['id']}", width="stretch"):
                                        modal_editar_conta_recorrente(b, user["id"])
                                with cd:
                                    if st.button("🗑️ Apagar", key=f"sh_del_rec_b_{b['id']}", width="stretch"):
                                        delete_recurring_bill(b["id"], requesting_user_id=user["id"])
                                        st.rerun()
                                st.divider()
                    else:
                        st.info("Nenhuma conta recorrente no espaço deste usuário.")

            else:
                # ---------------- MODO DASHBOARD RESTRITO (VISUALIZADOR) ----------------
                st.info(f"👁️ **Modo Visualizador (Apenas Leitura):** Você está visualizando o Dashboard consolidado de **{owner_username}**. Todas as informações estão em modo estritamente consultivo.")

                rec_prop = [t for t in trans_prop if t["type"] == "receita"]
                desp_prop = [t for t in trans_prop if t["type"] == "despesa"]
                tot_rec = sum(t["amount"] for t in rec_prop)
                tot_desp = sum(t["amount"] for t in desp_prop)
                saldo = tot_rec - tot_desp

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    render_metric_card("Total Receitas", f"R$ {tot_rec:,.2f}", f"{len(rec_prop)} entradas", "#3fb950", "🟢")
                with c2:
                    render_metric_card("Total Despesas", f"R$ {tot_desp:,.2f}", f"{len(desp_prop)} saídas", "#f85149", "🔴")
                with c3:
                    cor_sd = "#3fb950" if saldo >= 0 else "#f85149"
                    render_metric_card("Saldo Acumulado", f"R$ {saldo:,.2f}", "Resultado geral", cor_sd, "💰")
                with c4:
                    render_metric_card("Contas Recorrentes", f"{len(bills_prop)} contas", "Compromissos fixos", "#58a6ff", "🔄")

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader(f"📊 Extrato Consolidado ({owner_username})")
                if trans_prop:
                    df_v = pd.DataFrame(trans_prop)[["due_date", "type", "category", "description", "amount", "status"]]
                    df_v.columns = ["Vencimento/Data", "Tipo", "Categoria", "Descrição", "Valor", "Status"]
                    df_v["Valor"] = df_v["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                    st.dataframe(df_v, width="stretch", hide_index=True)
                else:
                    st.caption("Nenhuma movimentação registrada no espaço deste usuário.")

                st.subheader(f"🔄 Contas Recorrentes Fixas ({owner_username})")
                if bills_prop:
                    df_b = pd.DataFrame(bills_prop)[["description", "type", "category", "due_day", "amount", "is_active"]]
                    df_b.columns = ["Descrição", "Tipo", "Categoria", "Dia Vencimento", "Valor", "Ativa"]
                    df_b["Valor"] = df_b["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                    df_b["Ativa"] = df_b["Ativa"].apply(lambda x: "Sim" if x == 1 else "Não")
                    st.dataframe(df_b, width="stretch", hide_index=True)

    # =================================================================
    # ABA 2: GERENCIAR MEUS COMPARTILHAMENTOS (CONCEDIDOS)
    # =================================================================
    with tab_gerir_partilhas:
        st.subheader("📤 Compartilhar Meu Espaço com Outros Usuários")
        st.write("Permita que outro usuário cadastrado acesse os seus lançamentos como Editor (Segunda Área de Trabalho) ou como Visualizador (Apenas Leitura).")

        todos_usuarios = get_users()
        outros_usuarios = [u for u in todos_usuarios if u["id"] != user["id"]]

        if outros_usuarios:
            with st.form("form_novo_share_page"):
                map_u = {f"{u['username']} ({u['role'].upper()})": u["id"] for u in outros_usuarios}
                sel_u_label = st.selectbox("Selecione o Usuário para Conceder Acesso", list(map_u.keys()))
                sel_target_id = map_u[sel_u_label]
                sel_perm = st.selectbox(
                    "Nível de Permissão",
                    ["editor", "viewer"],
                    format_func=lambda x: "✏️ Editor (Segunda Área de Trabalho Completa)" if x == "editor" else "👁️ Visualizador (Apenas Leitura Consolidada)"
                )
                if st.form_submit_button("Conceder Compartilhamento", type="primary"):
                    try:
                        add_user_share(owner_id=user["id"], shared_with_user_id=sel_target_id, permission_level=sel_perm)
                        st.success(f"Espaço compartilhado com sucesso com {sel_u_label}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao conceder acesso: {e}")
        else:
            st.info("Nenhum outro usuário cadastrado no sistema para compartilhar.")

        st.markdown("---")
        st.subheader("📋 Acessos Atualmente Concedidos")
        minhas_partilhas = get_user_shares_by_owner(user["id"])
        if minhas_partilhas:
            for s in minhas_partilhas:
                with st.container():
                    cu, cp, cd, cr = st.columns([3, 2.5, 2, 2])
                    with cu:
                        st.markdown(f"**👤 {s['shared_with_username']}**")
                    with cp:
                        cor_b = "#3fb950" if s["permission_level"] == "editor" else "#58a6ff"
                        lbl = "✏️ Editor (Área de Trabalho)" if s["permission_level"] == "editor" else "👁️ Visualizador (Leitura)"
                        st.markdown(f"<span style='color:{cor_b}; font-weight:600;'>{lbl}</span>", unsafe_allow_html=True)
                    with cd:
                        st.caption(f"Desde: {s['created_at'][:10]}")
                    with cr:
                        if st.button("🗑️ Revogar", key=f"pg_rev_{s['id']}", width="stretch"):
                            delete_user_share(s["id"], owner_id=user["id"])
                            st.success("Compartilhamento revogado!")
                            st.rerun()
                    st.divider()
        else:
            st.info("Você ainda não concedeu acesso ao seu espaço para nenhum usuário.")


