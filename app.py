import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests
import yfinance as yf

# -------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM PREMIUM (CSS)
# -------------------------------------------------------------
st.set_page_config(
    page_title="Finances AI | Dashboard Financeiro", 
    page_icon="💳", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS Avançada (UI Design Premium, Botão Flutuante & noindex)
custom_css = """
<meta name="robots" content="noindex, nofollow">
<style>
    .stApp {
        background-color: #0B0E14;
        font-family: 'Inter', sans-serif;
    }
    .kpi-card {
        background: linear-gradient(145deg, #161B26 0%, #0F131C 100%);
        border: 1px solid #232D3F;
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        border-color: #3B82F6;
        transform: translateY(-3px);
        box-shadow: 0 12px 30px -5px rgba(59, 130, 246, 0.2);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 0.825rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    .kpi-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 20px;
        font-size: 0.725rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .badge-pos { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-neg { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-neu { background: rgba(107, 114, 128, 0.15); color: #9CA3AF; border: 1px solid rgba(107, 114, 128, 0.3); }

    .val-green { color: #10B981; }
    .val-red { color: #EF4444; }
    .val-blue { color: #3B82F6; }
    .val-purple { color: #A855F7; }

    /* Botões de Navegação Rápida (Navbar Estilizada) */
    .nav-link-btn {
        display: block;
        text-align: center;
        background: #161B26;
        color: #9CA3AF !important;
        padding: 10px 14px;
        border-radius: 10px;
        text-decoration: none !important;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #232D3F;
        transition: all 0.2s ease;
    }
    .nav-link-btn:hover {
        background-color: #1F2937;
        color: #3B82F6 !important;
        border-color: #3B82F6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }

    /* 🚀 BOTÃO FLUTUANTE DE VOLTAR AO TOPO */
    .back-to-top-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 9999;
        background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
        color: #3B82F6 !important;
        border: 1px solid #3B82F6;
        border-radius: 50px;
        padding: 10px 18px;
        font-size: 0.85rem;
        font-weight: 700;
        text-decoration: none !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .back-to-top-btn:hover {
        background: #3B82F6;
        color: #FFFFFF !important;
        transform: translateY(-3px);
        box-shadow: 0 12px 25px rgba(59, 130, 246, 0.4);
    }

    [data-testid="stSidebar"] {
        background-color: #0F131C;
        border-right: 1px solid #1F2937;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------
# 1.1 MECANISMO DE LOGIN COM BOTÃO "ACESSAR" & BLOQUEIO
# -------------------------------------------------------------
def check_password():
    """Retorna True se a senha estiver correta e exibe pop-up (toast) de erro se incorreta."""
    MAX_TENTATIVAS = 3

    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0
    if "lockout_time" not in st.session_state:
        st.session_state["lockout_time"] = 0

    if st.session_state["login_attempts"] >= MAX_TENTATIVAS:
        remaining_time = int(300 - (time.time() - st.session_state["lockout_time"]))
        if remaining_time > 0:
            st.markdown("<h2 style='text-align: center; color: #EF4444;'>🚫 Acesso Temporariamente Bloqueado</h2>", unsafe_allow_html=True)
            st.error(f"Muitas tentativas incorretas ({MAX_TENTATIVAS} erros). Por razões de segurança, aguarde {remaining_time} segundos para tentar novamente.")
            return False
        else:
            st.session_state["login_attempts"] = 0

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; color: #3B82F6;'>🔐 Acesso Restrito ao Painel</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                password_input = st.text_input("Digite sua senha de acesso:", type="password")
                submit_button = st.form_submit_button("🔑 Acessar", use_container_width=True)

                if submit_button:
                    try:
                        target_password = st.secrets["PASSWORD"]
                    except Exception:
                        target_password = "123456"

                    if password_input == target_password:
                        st.session_state["password_correct"] = True
                        st.session_state["login_attempts"] = 0
                        st.rerun()
                    else:
                        st.session_state["password_correct"] = False
                        st.session_state["login_attempts"] += 1
                        if st.session_state["login_attempts"] >= MAX_TENTATIVAS:
                            st.session_state["lockout_time"] = time.time()
                            st.rerun()
                        else:
                            tentativas_restantes = MAX_TENTATIVAS - st.session_state["login_attempts"]
                            st.toast(f"⚠️ Senha incorreta! Tentativas restantes: {tentativas_restantes}", icon="🚨")
                            st.error(f"😕 Senha incorreta. Tentativas restantes: {tentativas_restantes}")
        return False
    return True

if not check_password():
    st.stop()

# -------------------------------------------------------------
# 1.2 CONSULTA DA API DO BANCO CENTRAL & COTAÇÃO DO MXRF11
# -------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_market_indicators():
    """Busca Selic, CDI e cotação com variação do MXRF11 na B3."""
    try:
        url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        res_selic = requests.get(url_selic, timeout=5).json()
        selic_val = float(res_selic[0]["valor"])
        cdi_val = selic_val - 0.10
        selic_str, cdi_str = f"{selic_val:.2f}% a.a.", f"{cdi_val:.2f}% a.a."
    except Exception:
        selic_str, cdi_str = "10.75% a.a.", "10.65% a.a."

    try:
        ticker = yf.Ticker("MXRF11.SA")
        hist = ticker.history(period="5d")
        
        if len(hist) >= 2:
            last_price = float(hist["Close"].iloc[-1])
            prev_price = float(hist["Close"].iloc[-2])
            diff_abs = last_price - prev_price
            diff_pct = (diff_abs / prev_price) * 100
        else:
            last_price = float(hist["Close"].iloc[-1])
            diff_abs = 0.0
            diff_pct = 0.0

        mxrf_str = f"R$ {last_price:.2f}"
        
        if diff_abs >= 0:
            var_html = f"<span style='color: #10B981; font-weight: 600; font-size: 0.85rem;'>+{diff_abs:.2f} (+{diff_pct:.2f}%)</span>"
        else:
            var_html = f"<span style='color: #EF4444; font-weight: 600; font-size: 0.85rem;'>{diff_abs:.2f} ({diff_pct:.2f}%)</span>"
    except Exception:
        mxrf_str = "R$ 9.45"
        var_html = "<span style='color: #10B981; font-weight: 600; font-size: 0.85rem;'>+0.10 (+1.07%)</span>"

    return selic_str, cdi_str, mxrf_str, var_html

selic_str, cdi_str, mxrf11_price_str, mxrf11_var_html = fetch_market_indicators()

# -------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS DO GOOGLE SHEETS
# -------------------------------------------------------------
try:
    SPREADSHEET_ID = st.secrets.get("SPREADSHEET_ID", "1t_jPaLp5lP8Yg5yJQb_U8NaIF7BS0DyLfqJaoAvehr4")
except Exception:
    SPREADSHEET_ID = "1t_jPaLp5lP8Yg5yJQb_U8NaIF7BS0DyLfqJaoAvehr4"

# -------------------------------------------------------------
# 3. SIDEBAR DE CONFIGURAÇÃO (ANO, MESES & LOGOUT)
# -------------------------------------------------------------
st.sidebar.markdown("### ⚙️ Painel de Controle")

ano_selecionado = st.sidebar.selectbox(
    "Ano / Aba da Planilha", 
    ["2025", "2026", "2027"], 
    index=1
)

SHEET_NAME = ano_selecionado
csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)
def load_data(url):
    return pd.read_csv(url)

try:
    df_raw = load_data(csv_url)
    
    df_raw.rename(columns={df_raw.columns[0]: "Categoria"}, inplace=True)
    df_raw["Categoria"] = df_raw["Categoria"].astype(str).str.strip()
    
    meses_ordem_cronologica = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    meses = [c for c in meses_ordem_cronologica if c in df_raw.columns]
    
    mes_selecionado = st.sidebar.multiselect(
        "Filtro por Mês", 
        meses, 
        default=[m for m in meses if m in ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out']]
    )
    
    st.sidebar.divider()
    
    col_sb1, col_sb2 = st.sidebar.columns(2)
    with col_sb1:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_sb2:
        if st.button("🔒 Sair", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()

    # -------------------------------------------------------------
    # 4. PROCESSAMENTO DAS REGRAS FINANCEIRAS
    # -------------------------------------------------------------
    if mes_selecionado:
        mes_selecionado = [m for m in meses_ordem_cronologica if m in mes_selecionado]
        df_raw['linha_excel'] = df_raw.index + 2
        
        df_melted = df_raw.melt(
            id_vars=["linha_excel", "Categoria"], 
            value_vars=mes_selecionado, 
            var_name="Mês", 
            value_name="Valor_Raw"
        )
        
        df_melted["Mês"] = pd.Categorical(df_melted["Mês"], categories=meses_ordem_cronologica, ordered=True)
        
        def parse_br_val(v):
            if pd.isna(v): return 0.0
            v_str = str(v).replace("R$", "").strip()
            if not v_str or v_str == "-": return 0.0
            if "," in v_str:
                v_str = v_str.replace(".", "").replace(",", ".")
            return pd.to_numeric(v_str, errors="coerce") or 0.0

        df_melted["Valor"] = df_melted["Valor_Raw"].apply(parse_br_val)
        
        df_receitas = df_melted[df_melted["linha_excel"].isin([2, 3])]
        df_despesas = df_melted[df_melted["linha_excel"].isin([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17])]
        df_saldo_investido = df_melted[df_melted["linha_excel"] == 16]
        
        df_carteira_investimentos = df_melted[
            (df_melted["linha_excel"].between(20, 30)) & 
            (~df_melted["Categoria"].str.upper().str.contains("TOTAL")) &
            (df_melted["Categoria"].str.upper() != "INVESTIMENTOS")
        ]
        
        total_rec = df_receitas["Valor"].sum()
        total_desp = df_despesas["Valor"].sum()
        total_investido_mes = df_saldo_investido["Valor"].sum()
        
        ultimo_mes = mes_selecionado[-1]
        patrimonio_total_ultimo_mes = df_carteira_investimentos[df_carteira_investimentos["Mês"] == ultimo_mes]["Valor"].sum()

        if len(mes_selecionado) > 1:
            mes_penultimo = mes_selecionado[-2]
            
            patrimonio_penultimo = df_carteira_investimentos[df_carteira_investimentos["Mês"] == mes_penultimo]["Valor"].sum()
            rec_ultimo = df_receitas[df_receitas["Mês"] == ultimo_mes]["Valor"].sum()
            rec_penultimo = df_receitas[df_receitas["Mês"] == mes_penultimo]["Valor"].sum()
            desp_ultimo = df_despesas[df_despesas["Mês"] == ultimo_mes]["Valor"].sum()
            desp_penultimo = df_despesas[df_despesas["Mês"] == mes_penultimo]["Valor"].sum()

            var_patrimonio_pct = ((patrimonio_total_ultimo_mes - patrimonio_penultimo) / patrimonio_penultimo * 100) if patrimonio_penultimo > 0 else 0.0
            var_rec_pct = ((rec_ultimo - rec_penultimo) / rec_penultimo * 100) if rec_penultimo > 0 else 0.0
            var_desp_pct = ((desp_ultimo - desp_penultimo) / desp_penultimo * 100) if desp_penultimo > 0 else 0.0
        else:
            var_patrimonio_pct = var_rec_pct = var_desp_pct = 0.0

        def get_badge_html(val, is_expense=False):
            if val == 0.0:
                return "<div class='kpi-badge badge-neu'>• Estável</div>"
            if is_expense:
                if val > 0:
                    return f"<div class='kpi-badge badge-neg'>▲ +{val:.1f}% vs mês ant.</div>"
                else:
                    return f"<div class='kpi-badge badge-pos'>▼ {val:.1f}% vs mês ant.</div>"
            else:
                if val > 0:
                    return f"<div class='kpi-badge badge-pos'>▲ +{val:.1f}% vs mês ant.</div>"
                else:
                    return f"<div class='kpi-badge badge-neg'>▼ {val:.1f}% vs mês ant.</div>"

        # -------------------------------------------------------------
        # ⚓ ÂNCORA DO TOPO DA PÁGINA + BOTÃO FLUTUANTE DE VOLTAR AO TOPO
        # -------------------------------------------------------------
        st.markdown("<a id='topo'></a>", unsafe_allow_html=True)
        st.markdown("<a href='#topo' class='back-to-top-btn'>⬆️ Topo</a>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 5. HEADER DO DASHBOARD & BENCHMARKS MACRO
        # -------------------------------------------------------------
        st.markdown(f"<h2 style='margin-bottom: 0px;'>💎 Gestão Financeira & Patrimonial ({ano_selecionado})</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #6B7280; font-size: 0.9rem; margin-bottom: 15px;'>Visão executiva de fluxo de caixa, alocação e indicadores de mercado</p>", unsafe_allow_html=True)

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.caption("🏛️ Meta Selic (BCB)")
            st.markdown(f"**{selic_str}**")
        with col_m2:
            st.caption("📉 CDI Estimado")
            st.markdown(f"**{cdi_str}**")
        with col_m3:
            st.caption("🏢 MXRF11 (B3)")
            st.markdown(f"**{mxrf11_price_str}** &nbsp; {mxrf11_var_html}", unsafe_allow_html=True)
        with col_m4:
            st.caption("📅 Mês de Referência")
            st.markdown(f"**{ultimo_mes.upper()} / {ano_selecionado}**")

        st.markdown("<hr style='border-color: #1F2937; margin-top: 10px; margin-bottom: 15px;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 🚀 MENU DE NAVEGAÇÃO RÁPIDA (QUICK LINKS)
        # -------------------------------------------------------------
        st.markdown("##### 🧭 Navegação Rápida")
        nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
        with nav_col1:
            st.markdown("<a class='nav-link-btn' href='#fluxo-de-caixa'>💳 Fluxo de Caixa</a>", unsafe_allow_html=True)
        with nav_col2:
            st.markdown("<a class='nav-link-btn' href='#investimentos'>📊 Investimentos</a>", unsafe_allow_html=True)
        with nav_col3:
            st.markdown("<a class='nav-link-btn' href='#lucro-prejuizo'>💵 Lucro / Prejuízo</a>", unsafe_allow_html=True)
        with nav_col4:
            st.markdown("<a class='nav-link-btn' href='#raio-x'>🔍 Raio-X Ativo</a>", unsafe_allow_html=True)
        with nav_col5:
            st.markdown("<a class='nav-link-btn' href='#diversificacao'>🍩 Alocação</a>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 6. CARDS (KPIs COM BADGES DE DESEMPENHO)
        # -------------------------------------------------------------
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Receita Total</div>
                <div class="kpi-value val-green">R$ {total_rec:,.2f}</div>
                {get_badge_html(var_rec_pct)}
            </div>
            """, unsafe_allow_html=True)

        with kpi2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Despesas Operacionais</div>
                <div class="kpi-value val-red">R$ {total_desp:,.2f}</div>
                {get_badge_html(var_desp_pct, is_expense=True)}
            </div>
            """, unsafe_allow_html=True)

        with kpi3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Saldo Investido (Mês)</div>
                <div class="kpi-value val-blue">R$ {total_investido_mes:,.2f}</div>
                <div class="kpi-badge badge-neu">Aportes do Período</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Carteira Total ({ultimo_mes.upper()})</div>
                <div class="kpi-value val-purple">R$ {patrimonio_total_ultimo_mes:,.2f}</div>
                {get_badge_html(var_patrimonio_pct)}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        plotly_theme = {
            "layout": {
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#E5E7EB", "family": "Inter"},
                "xaxis": {"gridcolor": "#1F2937", "zerolinecolor": "#1F2937"},
                "yaxis": {"gridcolor": "#1F2937", "zerolinecolor": "#1F2937"}
            }
        }

        # -------------------------------------------------------------
        # 7. FLUXO DE CAIXA
        # -------------------------------------------------------------
        st.markdown("<a id='fluxo-de-caixa'></a>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns([1.2, 1])
        
        with col_g1:
            st.markdown("##### 📌 Distribuição de Despesas Operacionais")
            df_desp_cat = df_despesas.groupby("Categoria")["Valor"].sum().reset_index()
            df_desp_cat = df_desp_cat[df_desp_cat["Valor"] > 0].sort_values(by="Valor", ascending=True)
            
            fig_cat = px.bar(
                df_desp_cat,
                x="Valor", y="Categoria", orientation="h",
                labels={"Valor": "R$", "Categoria": ""},
                color="Valor", 
                color_continuous_scale=["#3B82F6", "#EF4444"]
            )
            fig_cat.update_layout(plotly_theme["layout"], coloraxis_showscale=False, height=350)
            fig_cat.update_xaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with col_g2:
            st.markdown("##### 📈 Evolução das Receitas Mês a Mês")
            df_rec_evo = df_receitas.groupby("Mês", observed=False)["Valor"].sum().reset_index()
            df_rec_evo = df_rec_evo.sort_values("Mês")
            
            fig_evo = px.area(
                df_rec_evo,
                x="Mês", y="Valor", 
                markers=True,
                color_discrete_sequence=["#10B981"]
            )
            fig_evo.update_layout(plotly_theme["layout"], height=350)
            fig_evo.update_yaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_evo, use_container_width=True)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 8. INVESTIMENTOS
        # -------------------------------------------------------------
        st.markdown("<a id='investimentos'></a>", unsafe_allow_html=True)
        st.markdown("### 📊 Posição & Evolução Patrimonial dos Investimentos")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Acompanhamento individual e evolução de cada ativo da carteira</p>", unsafe_allow_html=True)
        
        df_inv_ultimo = df_carteira_investimentos[df_carteira_investimentos["Mês"] == ultimo_mes].copy()
        df_inv_ultimo = df_inv_ultimo[df_inv_ultimo["Valor"] > 0].sort_values(by="Valor", ascending=True)
        
        df_total = pd.DataFrame([{
            "linha_excel": 999,
            "Categoria": "Total Investimentos",
            "Mês": ultimo_mes,
            "Valor_Raw": str(patrimonio_total_ultimo_mes),
            "Valor": patrimonio_total_ultimo_mes
        }])

        df_inv_bar_data = pd.concat([df_total, df_inv_ultimo], ignore_index=True)
        
        fig_inv_bar = px.bar(
            df_inv_bar_data,
            x="Valor", y="Categoria", orientation="h",
            title=f"🏛️ Saldo de Ativos da Carteira em {ultimo_mes.upper()}",
            labels={"Valor": "R$ (Saldo em Carteira)", "Categoria": ""},
            color="Valor", 
            color_continuous_scale="Greens",
            text_auto='.2f'
        )
        fig_inv_bar.update_layout(
            plotly_theme["layout"], 
            coloraxis_showscale=False, 
            height=450,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        fig_inv_bar.update_xaxes(tickprefix="R$ ", tickformat="~s")
        fig_inv_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_inv_bar, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_carteira_investimentos = df_carteira_investimentos.sort_values("Mês")
        fig_inv_line = px.line(
            df_carteira_investimentos,
            x="Mês", y="Valor", color="Categoria",
            title="📈 Curva de Crescimento por Ativo (Rendimentos + Aportes Mês a Mês)",
            markers=True,
            labels={"Valor": "R$", "Categoria": "Ativo da Carteira"},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_inv_line.update_layout(
            plotly_theme["layout"], 
            height=550,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.02
            ),
            margin=dict(l=20, r=180, t=50, b=40)
        )
        fig_inv_line.update_yaxes(tickprefix="R$ ", tickformat="~s")
        st.plotly_chart(fig_inv_line, use_container_width=True)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 9. VARIAÇÃO DE RENDIMENTO MÊS A MÊS
        # -------------------------------------------------------------
        st.markdown("<a id='lucro-prejuizo'></a>", unsafe_allow_html=True)
        st.markdown("### 💵 Lucro / Prejuízo dos Investimentos (Variação Mês a Mês)")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Comparativo da evolução do patrimônio investido entre meses consecutivos</p>", unsafe_allow_html=True)

        df_carteira_mensal = df_carteira_investimentos.groupby("Mês", observed=False)["Valor"].sum().reset_index()
        df_carteira_mensal = df_carteira_mensal.sort_values("Mês")
        df_carteira_mensal = df_carteira_mensal[df_carteira_mensal["Valor"] > 0].reset_index(drop=True)

        if len(df_carteira_mensal) > 1:
            registros_variacao = []
            
            for i in range(1, len(df_carteira_mensal)):
                m_ant = df_carteira_mensal.loc[i-1, "Mês"]
                val_ant = df_carteira_mensal.loc[i-1, "Valor"]
                
                m_atual = df_carteira_mensal.loc[i, "Mês"]
                val_atual = df_carteira_mensal.loc[i, "Valor"]
                
                diff_abs = val_atual - val_ant
                diff_pct = (diff_abs / val_ant * 100) if val_ant > 0 else 0.0
                status = "🟢 Lucro" if diff_abs >= 0 else "🔴 Prejuízo"
                
                registros_variacao.append({
                    "Período Comparado": f"{str(m_ant).upper()} ➔ {str(m_atual).upper()}",
                    "Saldo Mês Anterior": f"R$ {val_ant:,.2f}",
                    "Saldo Mês Atual": f"R$ {val_atual:,.2f}",
                    "Resultado (R$)": f"R$ {diff_abs:+,.2f}",
                    "Rendimento (%)": f"{diff_pct:+.2f}%",
                    "Status": status
                })
            
            df_var_display = pd.DataFrame(registros_variacao)
            
            st.dataframe(
                df_var_display, 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Selecione pelo menos 2 meses no filtro para visualizar a comparação de variação patrimonial.")

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 10. RAIO-X INDIVIDUAL
        # -------------------------------------------------------------
        st.markdown("<a id='raio-x'></a>", unsafe_allow_html=True)
        st.markdown("### 🔍 Raio-X & Análise Individual de cada Ativo")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Selecione um ativo para analisar seu histórico de rendimento e evolução mensal isolada</p>", unsafe_allow_html=True)

        ativos_encerrados = [
            "C6 - CDB C6 Prefixado 1 ano (15,7% a.a.) Venc em 03/06/26",
            "Nubank Caixinha 115% CDI (líquido)",
            "Nubank LCA - Banco BV - Venc: 13/03/2026 liquido",
            "C6 - Carbon Ouro"
        ]

        todos_ativos = df_carteira_investimentos["Categoria"].unique()
        lista_ativos_raiox = sorted([a for a in todos_ativos if a not in ativos_encerrados])

        if lista_ativos_raiox:
            col_sel, _ = st.columns([2, 1])
            with col_sel:
                ativo_escolhido = st.selectbox("Escolha um investimento para detalhar:", lista_ativos_raiox)

            df_ativo_filtro = df_carteira_investimentos[df_carteira_investimentos["Categoria"] == ativo_escolhido].sort_values("Mês")
            df_ativo_validos = df_ativo_filtro[df_ativo_filtro["Valor"] > 0].reset_index(drop=True)
            
            val_inicial = df_ativo_validos["Valor"].iloc[0] if not df_ativo_validos.empty else 0.0
            val_final = df_ativo_validos["Valor"].iloc[-1] if not df_ativo_validos.empty else 0.0
            var_total_abs = val_final - val_inicial
            var_total_pct = (var_total_abs / val_inicial * 100) if val_inicial > 0 else 0.0

            c_a1, c_a2, c_a3, c_a4 = st.columns(4)
            c_a1.metric("Valor Inicial", f"R$ {val_inicial:,.2f}")
            c_a2.metric("Valor Atual", f"R$ {val_final:,.2f}")
            c_a3.metric("Evolução (R$)", f"R$ {var_total_abs:+,.2f}", delta=f"R$ {var_total_abs:+,.2f}")
            c_a4.metric("Evolução (%)", f"{var_total_pct:+.2f}%", delta=f"{var_total_pct:+.2f}%")

            st.markdown("<br>", unsafe_allow_html=True)

            if len(df_ativo_validos) > 0:
                st.markdown(f"##### 📑 Histórico de Crescimento Mês a Mês: `{ativo_escolhido}`")
                
                registros_ativo_m = []
                for idx in range(len(df_ativo_validos)):
                    m_curr = str(df_ativo_validos.loc[idx, "Mês"]).upper()
                    val_curr = df_ativo_validos.loc[idx, "Valor"]
                    
                    if idx == 0:
                        var_m_abs = 0.0
                        var_m_pct = 0.0
                        txt_var_abs = "-"
                        txt_var_pct = "-"
                    else:
                        val_prev = df_ativo_validos.loc[idx - 1, "Valor"]
                        var_m_abs = val_curr - val_prev
                        var_m_pct = (var_m_abs / val_prev * 100) if val_prev > 0 else 0.0
                        txt_var_abs = f"R$ {var_m_abs:+,.2f}"
                        txt_var_pct = f"{var_m_pct:+.2f}%"

                    registros_ativo_m.append({
                        "Mês": m_curr,
                        "Saldo em Carteira": f"R$ {val_curr:,.2f}",
                        "Variação Mês (R$)": txt_var_abs,
                        "Variação Mês (%)": txt_var_pct
                    })

                df_ativo_tab = pd.DataFrame(registros_ativo_m)
                st.dataframe(df_ativo_tab, use_container_width=True, hide_index=True)
                st.markdown("<br>", unsafe_allow_html=True)

            fig_ativo_single = px.area(
                df_ativo_filtro,
                x="Mês", y="Valor",
                title=f"📈 Gráfico de Evolução: {ativo_escolhido}",
                markers=True,
                color_discrete_sequence=["#8B5CF6"],
                labels={"Valor": "R$ (Saldo em Carteira)", "Mês": ""}
            )
            fig_ativo_single.update_layout(plotly_theme["layout"], height=380)
            fig_ativo_single.update_yaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_ativo_single, use_container_width=True)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 11. DIVERSIFICAÇÃO & ALOCAÇÃO POR CLASSE DE ATIVO
        # -------------------------------------------------------------
        st.markdown("<a id='diversificacao'></a>", unsafe_allow_html=True)
        st.markdown("### 🍩 Diversificação Patrimonial por Classe de Ativo")
        st.markdown(f"<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Análise de risco e distribuição percentual da carteira em <b>{ultimo_mes.upper()} / {ano_selecionado}</b></p>", unsafe_allow_html=True)

        def classificar_ativo(nome):
            nome_upper = str(nome).upper()
            if "IPCA" in nome_upper:
                return "Inflação (IPCA)"
            elif "PREFIXADO" in nome_upper or "PRE" in nome_upper:
                return "Pré-fixado"
            elif "MXRF11" in nome_upper or "FII" in nome_upper or "AÇÕES" in nome_upper:
                return "Renda Variável / FIIs"
            elif "CAIXINHA" in nome_upper or "CDI" in nome_upper or "CDB" in nome_upper:
                return "Pós-fixado / Liquidez"
            else:
                return "Outros / Proteção"

        df_ultimo_mes = df_carteira_investimentos[df_carteira_investimentos["Mês"] == ultimo_mes].copy()
        df_ultimo_mes = df_ultimo_mes[df_ultimo_mes["Valor"] > 0]
        df_ultimo_mes["Classe"] = df_ultimo_mes["Categoria"].apply(classificar_ativo)

        df_classes = df_ultimo_mes.groupby("Classe")["Valor"].sum().reset_index()
        df_classes["Percentual"] = (df_classes["Valor"] / df_classes["Valor"].sum()) * 100

        col_donut, col_tabela_classes = st.columns([1.2, 1])

        with col_donut:
            fig_donut = px.pie(
                df_classes,
                names="Classe",
                values="Valor",
                hole=0.55,
                title=f"Distribuição da Carteira ({ultimo_mes.upper()})",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_donut.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Saldo: R$ %{value:,.2f}<br>Participação: %{percent:.2f}%"
            )
            fig_donut.update_layout(
                plotly_theme["layout"],
                height=400,
                showlegend=False,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_tabela_classes:
            st.markdown("##### 📑 Detalhamento da Alocação")
            df_classes_display = df_classes.sort_values(by="Valor", ascending=False).copy()
            df_classes_display["Valor Formatado"] = df_classes_display["Valor"].apply(lambda v: f"R$ {v:,.2f}")
            df_classes_display["% Carteira"] = df_classes_display["Percentual"].apply(lambda p: f"{p:.2f}%")
            
            st.dataframe(
                df_classes_display[["Classe", "Valor Formatado", "% Carteira"]],
                use_container_width=True,
                hide_index=True
            )

except Exception as e:
    st.error(f"Aba '{ano_selecionado}' não encontrada ou sem dados no Google Sheets.")
