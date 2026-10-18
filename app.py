import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import requests
import yfinance as yf
import urllib.parse
import os
import gspread

# -------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM EXECUTIVE
# -------------------------------------------------------------
st.set_page_config(
    page_title="Finances AI | Fabio Pelegrino", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

executive_css = """
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background-color: #0D1117;
        color: #C9D1D9;
    }
    
    /* Executive Card Glassmorphism */
    .kpi-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.95) 100%);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 12px;
    }
    .kpi-card:hover {
        border-color: #58A6FF;
        transform: translateY(-2px);
    }
    .kpi-title {
        color: #8B949E;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.25;
    }
    .kpi-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .badge-pos { background: rgba(46, 160, 67, 0.15); color: #3FB950; border: 1px solid rgba(46, 160, 67, 0.3); }
    .badge-neg { background: rgba(248, 81, 73, 0.15); color: #F85149; border: 1px solid rgba(248, 81, 73, 0.3); }
    .badge-neu { background: rgba(139, 148, 158, 0.15); color: #8B949E; border: 1px solid rgba(139, 148, 158, 0.3); }

    .val-green { color: #3FB950; }
    .val-red { color: #F85149; }
    .val-blue { color: #58A6FF; }
    .val-purple { color: #A371F7; }

    /* Estilização de Tabs Corporativas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161B22;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #30363D;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #8B949E;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0 16px;
        border: none !important;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262D !important;
        color: #58A6FF !important;
        border: 1px solid #30363D !important;
    }

    .c6-logo-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #000;
        color: #FFF;
        font-weight: 900;
        font-size: 0.85rem;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #30363D;
        letter-spacing: -0.05em;
        margin-right: 8px;
    }

    [data-testid="stImage"] img {
        border-radius: 50% !important;
        border: 2px solid #58A6FF !important;
        box-shadow: 0 0 20px rgba(88, 166, 255, 0.25) !important;
        object-fit: cover !important;
    }

    .ai-box {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.95) 100%);
        border: 1px solid #58A6FF;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    @media (max-width: 768px) {
        .kpi-value { font-size: 1.35rem; }
        .kpi-card { padding: 14px; }
    }

    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(executive_css, unsafe_allow_html=True)

plotly_config = {'displayModeBar': False, 'responsive': True}

plotly_theme = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#C9D1D9", "family": "Inter"},
        "xaxis": {"gridcolor": "#21262D", "zerolinecolor": "#21262D"},
        "yaxis": {"gridcolor": "#21262D", "zerolinecolor": "#21262D"}
    }
}

def simplificar_categoria_fatura(cat_orig):
    c = str(cat_orig).strip()
    c_upper = c.upper()
    
    if "SUPERMERCADO" in c_upper or "CONVENIÊNCIA" in c_upper or "MERCEARIA" in c_upper:
        return "Mercado / Padaria"
    elif "RESTAURANTE" in c_upper or "LANCHONETE" in c_upper or "BAR" in c_upper:
        return "Restaurantes & Bares"
    elif "ASSISTÊNCIA MÉDICA" in c_upper or "ODONTOLÓGICA" in c_upper or "SAÚDE" in c_upper:
        return "Saúde & Médica"
    elif "TV POR ASSINATURA" in c_upper or "RÁDIO" in c_upper or "STREAMING" in c_upper:
        return "Streaming & TV"
    elif "AUTOMOTIVO" in c_upper or "VEÍCULO" in c_upper:
        return "Automotivo"
    elif "DEPARTAMENTO" in c_upper or "DESCONTO" in c_upper:
        return "Lojas de Depto."
    elif "SERVIÇOS PESSOAIS" in c_upper:
        return "Serviços Pessoais"
    elif "VESTUÁRIO" in c_upper or "ROUPAS" in c_upper:
        return "Vestuário & Roupas"
    elif "EMPRESA PARA EMPRESA" in c_upper:
        return "B2B / Serviços"
    elif "ESPECIALIDADE VAREJO" in c_upper:
        return "Varejo Geral"
    elif "ENTRETENIMENTO" in c_upper:
        return "Entretenimento"
    elif "TRANSPORTE" in c_upper:
        return "Transporte / App"
    else:
        return c

def quebrar_linha_nome(texto, max_chars=18):
    texto_str = str(texto).strip()
    if len(texto_str) <= max_chars:
        return texto_str
    
    if " - " in texto_str:
        partes = texto_str.split(" - ", 1)
        return f"{partes[0]} -<br>{partes[1]}"
    if " / " in texto_str:
        partes = texto_str.split(" / ", 1)
        return f"{partes[0]} /<br>{partes[1]}"
    
    palavras = texto_str.split(" ")
    meio = len(palavras) // 2
    return "<br>".join([" ".join(palavras[:meio]), " ".join(palavras[meio:])])

# -------------------------------------------------------------
# 1.1 AUTENTICAÇÃO SEGURA COM DESIGN MINIMALISTA EXECUTIVO
# -------------------------------------------------------------
def check_password():
    MAX_TENTATIVAS = 3

    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0
    if "lockout_time" not in st.session_state:
        st.session_state["lockout_time"] = 0

    if st.session_state["login_attempts"] >= MAX_TENTATIVAS:
        remaining_time = int(300 - (time.time() - st.session_state["lockout_time"]))
        if remaining_time > 0:
            st.markdown("<h2 style='text-align: center; color: #F85149;'>🚫 Acesso Bloqueado</h2>", unsafe_allow_html=True)
            st.error(f"Muitas tentativas. Aguarde {remaining_time}s.")
            return False
        else:
            st.session_state["login_attempts"] = 0

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 1.4, 1])
        with col2:
            st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)
            
            if os.path.exists("eu.jpg"):
                c_img1, c_img2, c_img3 = st.columns([1, 1.1, 1])
                with c_img2:
                    st.image("eu.jpg", use_container_width=True)
            
            st.markdown("""
            <h2 style='text-align: center; background: linear-gradient(180deg, #F0F6FC 0%, #58A6FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: -0.02em; margin-top: 15px; margin-bottom: 4px;'>
                Gestão Patrimonial
            </h2>
            <p style='text-align: center; color: #8B949E; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 25px;'>
                TERMINAL EXECUTIVO | FABIO PELEGRINO
            </p>
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                password_input = st.text_input("Senha de acesso:", type="password", placeholder="Digite sua credencial...")
                submit_button = st.form_submit_button("🔑 Acessar Terminal", use_container_width=True)

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
                            st.toast(f"⚠️ Senha incorreta! Tentativas: {tentativas_restantes}", icon="🚨")
                            st.error(f"😕 Credencial incorreta. Tentativas restantes: {tentativas_restantes}")
        return False
    return True

if not check_password():
    st.stop()

# -------------------------------------------------------------
# 1.2 INDICADORES DE MERCADO FINANCEIRO (BCB & B3)
# -------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_market_indicators():
    try:
        url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        res_selic = requests.get(url_selic, timeout=5).json()
        selic_val = float(res_selic[0]["valor"])
        cdi_val = selic_val - 0.10
        selic_str, cdi_str = f"{selic_val:.2f}% a.a.", f"{cdi_val:.2f}% a.a."
    except Exception:
        selic_val = 10.75
        cdi_val = 10.65
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
            var_html = f"<span style='color: #3FB950; font-weight: 600; font-size: 0.78rem;'>+{diff_abs:.2f} (+{diff_pct:.2f}%)</span>"
        else:
            var_html = f"<span style='color: #F85149; font-weight: 600; font-size: 0.78rem;'>{diff_abs:.2f} ({diff_pct:.2f}%)</span>"
    except Exception:
        last_price = 9.45
        mxrf_str = "R$ 9.45"
        var_html = "<span style='color: #3FB950; font-weight: 600; font-size: 0.78rem;'>+0.10 (+1.07%)</span>"

    return selic_str, cdi_str, mxrf_str, var_html, cdi_val, last_price

selic_str, cdi_str, mxrf11_price_str, mxrf11_var_html, cdi_num, mxrf11_preco_num = fetch_market_indicators()

# -------------------------------------------------------------
# 2. CONEXÃO COM GOOGLE SHEETS (LEITURA & ESCRITA VIA GSPREAD)
# -------------------------------------------------------------
try:
    SPREADSHEET_ID = st.secrets.get("SPREADSHEET_ID", "1t_jPaLp5lP8Yg5yJQb_U8NaIF7BS0DyLfqJaoAvehr4")
    FATURA_SHEET_ID = st.secrets.get("FATURA_SHEET_ID", "1PUXXGAfn8dmqqR1qCcrJMMF32wUGng_MHpQ7-5GSbOY")
except Exception:
    SPREADSHEET_ID = "1t_jPaLp5lP8Yg5yJQb_U8NaIF7BS0DyLfqJaoAvehr4"
    FATURA_SHEET_ID = "1PUXXGAfn8dmqqR1qCcrJMMF32wUGng_MHpQ7-5GSbOY"

def get_gspread_client():
    try:
        credentials = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(credentials)
        return gc
    except Exception:
        return None

@st.cache_data(ttl=300)
def load_sheet_by_gid(spreadsheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    return pd.read_csv(url)

# Mapeamento dos meses para colunas do Excel/Google Sheets na aba principal
MES_PARA_COLUNA = {
    'jan': 'B', 'fev': 'C', 'mar': 'D', 'abr': 'E',
    'mai': 'F', 'jun': 'G', 'jul': 'H', 'ago': 'I',
    'set': 'J', 'out': 'K', 'nov': 'L', 'dez': 'M'
}

# -------------------------------------------------------------
# 3. HEADER EXECUTIVE & BENCHMARKS DE MERCADO
# -------------------------------------------------------------
st.markdown("<h2 style='margin-bottom: 0px; font-weight: 800; color: #F0F6FC;'>Terminal Financeiro & Patrimonial</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8B949E; font-size: 0.85rem; margin-bottom: 15px;'>Visão Consolidada de Ativos, DRE, Cartão de Crédito e Mercado | <b>Fabio Pelegrino</b></p>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.caption("🏛️ Meta Selic (BCB)")
m1.markdown(f"**{selic_str}**")
m2.caption("📉 Taxa CDI Ref.")
m2.markdown(f"**{cdi_str}**")
m3.caption("🏢 Cotação MXRF11 (B3)")
m3.markdown(f"**{mxrf11_price_str}** {mxrf11_var_html}", unsafe_allow_html=True)
m4.caption("⚡ Status dos Motores")
m4.markdown("**🟢 Conectado ao Google Sheets**")

st.markdown("<hr style='border-color: #21262D; margin-top: 12px; margin-bottom: 18px;'>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🎛️ FILTROS PRINCIPAIS
# -------------------------------------------------------------
f_col1, f_col2, f_col3 = st.columns([1, 2.5, 0.8])

with f_col1:
    ano_selecionado = st.selectbox("Ano Fiscal", ["2025", "2026", "2027"], index=1, key="main_ano")

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
    
    with f_col2:
        mes_selecionado = st.multiselect(
            "Período em Análise", 
            meses, 
            default=[m for m in meses if m in ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov']],
            key="main_meses"
        )

    with f_col3:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Recarregar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Sidebar compacta
    st.sidebar.markdown("### ⚙️ Terminal")
    st.sidebar.info(f"👤 **Fabio Pelegrino**\n📅 **Ano Fiscal:** {ano_selecionado}")
    if st.sidebar.button("🔒 Encerrar Sessão", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 4. TRATAMENTO DOS DADOS FINANCEIROS
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
            (df_melted["linha_excel"].between(22, 30)) & 
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
                    return f"<div class='kpi-badge badge-neg'>▲ +{val:.1f}% MoM</div>"
                else:
                    return f"<div class='kpi-badge badge-pos'>▼ {val:.1f}% MoM</div>"
            else:
                if val > 0:
                    return f"<div class='kpi-badge badge-pos'>▲ +{val:.1f}% MoM</div>"
                else:
                    return f"<div class='kpi-badge badge-neg'>▼ {val:.1f}% MoM</div>"

        # -------------------------------------------------------------
        # 5. CARDS DE KPIS EXECUTIVOS
        # -------------------------------------------------------------
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Receita Acumulada</div>
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
                <div class="kpi-title">Aportes no Período (Linha 16)</div>
                <div class="kpi-value val-blue">R$ {total_investido_mes:,.2f}</div>
                <div class="kpi-badge badge-neu">Investimento Líquido</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Patrimônio ({ultimo_mes.upper()})</div>
                <div class="kpi-value val-purple">R$ {patrimonio_total_ultimo_mes:,.2f}</div>
                {get_badge_html(var_patrimonio_pct)}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 🚀 ESTRUTURA PRINCIPAL EM TABS CORPORATIVAS
        # -------------------------------------------------------------
        tab_exec, tab_c6, tab_invest, tab_ia_hub, tab_lancamento = st.tabs([
            "🏠 Resumo Executivo",
            "🖤 Cartão C6 & Faturas",
            "🏛️ Carteira de Ativos",
            "🔮 Projeções & IA",
            "📝 Lançar Dados"
        ])

        # =========================================================
        # TAB 1: RESUMO EXECUTIVO (DRE & CAIXA)
        # =========================================================
        with tab_exec:
            st.markdown("### 📊 Demonstrativo de Resultados & Fluxo de Caixa")
            st.markdown("<p style='color: #8B949E; font-size: 0.85rem;'>Evolução de receitas e detalhamento por centro de custo</p>", unsafe_allow_html=True)

            col_g1, col_g2 = st.columns([1.2, 1])
            
            with col_g1:
                st.markdown("##### 📌 Despesas Operacionais por Categoria")
                df_desp_cat = df_despesas.groupby("Categoria")["Valor"].sum().reset_index()
                df_desp_cat = df_desp_cat[df_desp_cat["Valor"] > 0].sort_values(by="Valor", ascending=True)
                df_desp_cat["Categoria_Label"] = df_desp_cat["Categoria"].apply(quebrar_linha_nome)

                fig_cat = px.bar(
                    df_desp_cat,
                    x="Valor", y="Categoria_Label", orientation="h",
                    labels={"Valor": "R$", "Categoria_Label": ""},
                    color="Valor", 
                    color_continuous_scale=["#58A6FF", "#F85149"]
                )
                fig_cat.update_layout(
                    plotly_theme["layout"], 
                    coloraxis_showscale=False, 
                    height=380,
                    margin=dict(l=110, r=20, t=20, b=20)
                )
                fig_cat.update_xaxes(tickprefix="R$ ", tickformat="~s")
                st.plotly_chart(fig_cat, use_container_width=True, config=plotly_config)
                
            with col_g2:
                st.markdown("##### 📈 Curva de Receita Mês a Mês")
                df_rec_evo = df_receitas.groupby("Mês", observed=False)["Valor"].sum().reset_index()
                df_rec_evo = df_rec_evo.sort_values("Mês")
                
                fig_evo = px.area(
                    df_rec_evo,
                    x="Mês", y="Valor", 
                    markers=True,
                    color_discrete_sequence=["#3FB950"]
                )
                fig_evo.update_layout(
                    plotly_theme["layout"], 
                    height=380,
                    margin=dict(l=50, r=20, t=20, b=30)
                )
                fig_evo.update_yaxes(tickprefix="R$ ", tickformat="~s")
                st.plotly_chart(fig_evo, use_container_width=True, config=plotly_config)

        # =========================================================
        # TAB 2: CARTÃO C6 BANK & COMPROMISSOS FUTUROS
        # =========================================================
        with tab_c6:
            st.markdown("""
            <h3 style='display: flex; align-items: center; margin-bottom: 0px;'>
                <span class="c6-logo-badge">C6</span>
                Gestão da Fatura C6 Bank & Compromissos
            </h3>
            """, unsafe_allow_html=True)
            st.markdown("<p style='color: #8B949E; font-size: 0.85rem; margin-bottom: 20px;'>Acompanhamento de compras, parcelamento futuro e faturamento</p>", unsafe_allow_html=True)

            try:
                aba_encoded = urllib.parse.quote("Out / 26")
                fatura_csv_url = f"https://docs.google.com/spreadsheets/d/{FATURA_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={aba_encoded}"
                
                try:
                    df_fatura_raw = load_data(fatura_csv_url)
                except Exception:
                    fatura_csv_fallback = f"https://docs.google.com/spreadsheets/d/{FATURA_SHEET_ID}/gviz/tq?tqx=out:csv"
                    df_fatura_raw = load_data(fatura_csv_fallback)

                df_fatura_raw.columns = [str(c).strip() for c in df_fatura_raw.columns]
                col_valor = [c for c in df_fatura_raw.columns if "Valor" in c and "R$" in c]
                col_valor_str = col_valor[0] if col_valor else "Valor (em R$)"

                if col_valor_str in df_fatura_raw.columns:
                    df_fatura = df_fatura_raw.copy()
                    df_fatura["Valor_Num"] = df_fatura[col_valor_str].apply(parse_br_val)
                    df_fatura_compras = df_fatura[df_fatura["Valor_Num"] > 0].copy()
                    
                    total_fatura = df_fatura_compras["Valor_Num"].sum()
                    num_compras = len(df_fatura_compras)
                    
                    parcelas_futuras_list = []
                    total_parcelado_futuro = 0.0

                    if "Parcela" in df_fatura_compras.columns:
                        for idx, row in df_fatura_compras.iterrows():
                            p_str = str(row["Parcela"]).strip()
                            if "/" in p_str:
                                try:
                                    atual, total_p = map(int, p_str.split("/"))
                                    rest = total_p - atual
                                    if rest > 0:
                                        v_mensal = row["Valor_Num"]
                                        v_futuro = v_mensal * rest
                                        total_parcelado_futuro += v_futuro
                                        
                                        desc_item = row["Descrição"] if "Descrição" in row else "-"
                                        cat_item = row["Categoria"] if "Categoria" in row else "-"
                                        
                                        parcelas_futuras_list.append({
                                            "Estabelecimento / Compra": desc_item,
                                            "Categoria": cat_item,
                                            "Parcela Atual": f"{atual}/{total_p}",
                                            "Restantes": f"{rest} x",
                                            "Valor Mensal": f"R$ {v_mensal:,.2f}",
                                            "Total a Vencer": f"R$ {v_futuro:,.2f}",
                                            "val_futuro_num": v_futuro
                                        })
                                except Exception:
                                    continue

                    cf1, cf2, cf3, cf4 = st.columns(4)
                    with cf1:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-color: #F85149;">
                            <div class="kpi-title">Fatura Atual (Out/26)</div>
                            <div class="kpi-value val-red">R$ {total_fatura:,.2f}</div>
                            <div class="kpi-badge badge-neg">{num_compras} Compras</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with cf2:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-color: #A371F7;">
                            <div class="kpi-title">Total Parcelado Futuro</div>
                            <div class="kpi-value val-purple">R$ {total_parcelado_futuro:,.2f}</div>
                            <div class="kpi-badge badge-neu">A Vencer</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with cf3:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-title">Itens Parcelados Ativos</div>
                            <div class="kpi-value val-blue">{len(parcelas_futuras_list)}</div>
                            <div class="kpi-badge badge-neu">Em Aberto</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with cf4:
                        media_compra = (total_fatura / num_compras) if num_compras > 0 else 0.0
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-title">Ticket Médio / Item</div>
                            <div class="kpi-value val-green">R$ {media_compra:,.2f}</div>
                            <div class="kpi-badge badge-neu">Média Gasto</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    if parcelas_futuras_list:
                        st.markdown("##### ⏳ Compromissos Parcelados e Saldos a Vencer")
                        df_pf_display = pd.DataFrame(parcelas_futuras_list).sort_values(by="val_futuro_num", ascending=False)
                        st.dataframe(
                            df_pf_display[["Estabelecimento / Compra", "Categoria", "Parcela Atual", "Restantes", "Valor Mensal", "Total a Vencer"]],
                            use_container_width=True,
                            hide_index=True
                        )
                        st.markdown("<br>", unsafe_allow_html=True)

                    col_fat1, col_fat2 = st.columns([1.2, 1])

                    with col_fat1:
                        st.markdown("##### 📌 Gastos da Fatura por Categoria")
                        if "Categoria" in df_fatura_compras.columns:
                            df_fatura_compras["Categoria_Limpa"] = df_fatura_compras["Categoria"].apply(simplificar_categoria_fatura)
                            
                            df_fat_cat = df_fatura_compras.groupby("Categoria_Limpa")["Valor_Num"].sum().reset_index()
                            df_fat_cat = df_fat_cat[df_fat_cat["Categoria_Limpa"] != "-"].sort_values(by="Valor_Num", ascending=True)

                            fig_fat_cat = px.bar(
                                df_fat_cat,
                                x="Valor_Num", y="Categoria_Limpa", orientation="h",
                                labels={"Valor_Num": "R$", "Categoria_Limpa": ""},
                                color="Valor_Num",
                                color_continuous_scale="Reds"
                            )
                            fig_fat_cat.update_layout(
                                plotly_theme["layout"],
                                coloraxis_showscale=False,
                                height=480,
                                margin=dict(l=140, r=20, t=20, b=20)
                            )
                            fig_fat_cat.update_xaxes(tickprefix="R$ ", tickformat="~s")
                            st.plotly_chart(fig_fat_cat, use_container_width=True, config=plotly_config)

                    with col_fat2:
                        st.markdown("##### 🏆 Top 10 Maiores Lançamentos do Mês")
                        if "Descrição" in df_fatura_compras.columns:
                            df_top10 = df_fatura_compras.sort_values(by="Valor_Num", ascending=False).head(10).copy()
                            df_top10["Descrição_Label"] = df_top10["Descrição"].apply(lambda d: quebrar_linha_nome(d, max_chars=16))
                            df_top10 = df_top10.sort_values(by="Valor_Num", ascending=True)

                            fig_top10 = px.bar(
                                df_top10,
                                x="Valor_Num", y="Descrição_Label", orientation="h",
                                labels={"Valor_Num": "R$", "Descrição_Label": ""},
                                color="Valor_Num",
                                color_continuous_scale="Purples"
                            )
                            fig_top10.update_layout(
                                plotly_theme["layout"],
                                coloraxis_showscale=False,
                                height=480,
                                margin=dict(l=130, r=20, t=20, b=20)
                            )
                            fig_top10.update_xaxes(tickprefix="R$ ", tickformat="~s")
                            st.plotly_chart(fig_top10, use_container_width=True, config=plotly_config)

                    st.markdown("##### 🔎 Pesquisa Rápida na Fatura")
                    busca_compra = st.text_input("Buscar por loja, estabelecimento ou categoria:", "", placeholder="Digite para filtrar...")
                    
                    cols_exibir = [c for c in ["Data de compra", "Descrição", "Categoria", "Parcela", col_valor_str] if c in df_fatura_compras.columns]
                    df_fat_display = df_fatura_compras[cols_exibir].copy()
                    
                    if busca_compra:
                        mask = pd.Series(False, index=df_fat_display.index)
                        if "Descrição" in df_fat_display.columns:
                            mask |= df_fat_display["Descrição"].str.contains(busca_compra, case=False, na=False)
                        if "Categoria" in df_fat_display.columns:
                            mask |= df_fat_display["Categoria"].str.contains(busca_compra, case=False, na=False)
                        df_fat_display = df_fat_display[mask]
                    
                    st.dataframe(df_fat_display, use_container_width=True, hide_index=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### 🍕 Visão Percentual por Categoria da Fatura")

                    if "Categoria" in df_fatura_compras.columns:
                        df_fatura_compras["Categoria_Limpa"] = df_fatura_compras["Categoria"].apply(simplificar_categoria_fatura)
                        
                        df_cat_summary = df_fatura_compras.groupby("Categoria_Limpa").agg(
                            Valor_Total=("Valor_Num", "sum"),
                            Qtd_Lançamentos=("Valor_Num", "count")
                        ).reset_index()

                        df_cat_summary = df_cat_summary[df_cat_summary["Categoria_Limpa"] != "-"].sort_values(by="Valor_Total", ascending=False)
                        total_fatura_sum = df_cat_summary["Valor_Total"].sum()
                        df_cat_summary["% do Cartão"] = (df_cat_summary["Valor_Total"] / total_fatura_sum) * 100

                        col_f_donut, col_f_topico = st.columns([1.1, 1])

                        with col_f_donut:
                            fig_fat_donut = px.pie(
                                df_cat_summary,
                                names="Categoria_Limpa",
                                values="Valor_Total",
                                hole=0.55,
                                title="Participação na Fatura",
                                color_discrete_sequence=px.colors.qualitative.Pastel
                            )
                            fig_fat_donut.update_traces(
                                textinfo="percent+label",
                                hovertemplate="<b>%{label}</b><br>Total: R$ %{value:,.2f}<br>Participação: %{percent:.1%}"
                            )
                            fig_fat_donut.update_layout(
                                plotly_theme["layout"],
                                height=360,
                                showlegend=False,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            st.plotly_chart(fig_fat_donut, use_container_width=True, config=plotly_config)

                        with col_f_topico:
                            st.markdown("###### 📑 Resumo das Categorias")
                            df_cat_display = df_cat_summary.copy()
                            df_cat_display["Valor (R$)"] = df_cat_display["Valor_Total"].apply(lambda v: f"R$ {v:,.2f}")
                            df_cat_display["% Fatura"] = df_cat_display["% do Cartão"].apply(lambda p: f"{p:.1f}%")
                            df_cat_display.rename(columns={
                                "Categoria_Limpa": "Categoria",
                                "Qtd_Lançamentos": "Compras"
                            }, inplace=True)

                            st.dataframe(
                                df_cat_display[["Categoria", "Valor (R$)", "% Fatura", "Compras"]],
                                use_container_width=True,
                                hide_index=True
                            )

            except Exception as e_fat:
                st.warning("⚠️ Dados da Fatura C6 indisponíveis no momento. Verifique a permissão de acesso à planilha.")

        # =========================================================
        # TAB 3: CARTEIRA DE INVESTIMENTOS & CALENDÁRIO DE EVENTOS
        # =========================================================
        with tab_invest:
            st.markdown("### 🏛️ Posição Patrimonial & Estrutura de Ativos")
            st.markdown("<p style='color: #8B949E; font-size: 0.85rem; margin-bottom: 20px;'>Evolução de ativos e análise de alocação por classe</p>", unsafe_allow_html=True)

            df_inv_ultimo = df_carteira_investimentos[df_carteira_investimentos["Mês"] == ultimo_mes].copy()
            df_inv_ultimo = df_inv_ultimo[df_inv_ultimo["Valor"] > 0].sort_values(by="Valor", ascending=True)

            st.markdown(f"""
            <div class="kpi-card" style="margin-bottom: 15px; border-color: #3FB950;">
                <div class="kpi-title">Patrimônio Investido em {ultimo_mes.upper()}</div>
                <div class="kpi-value val-green">R$ {patrimonio_total_ultimo_mes:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

            df_inv_ultimo["Categoria_Label"] = df_inv_ultimo["Categoria"].apply(quebrar_linha_nome)
            df_inv_ultimo["Texto_Valor"] = df_inv_ultimo["Valor"].apply(lambda v: f"R$ {v:,.2f}")

            fig_inv_bar = px.bar(
                df_inv_ultimo,
                x="Valor", y="Categoria_Label", orientation="h",
                title=f"Saldo por Ativo em {ultimo_mes.upper()}",
                labels={"Valor": "R$", "Categoria_Label": ""},
                color="Valor", 
                color_continuous_scale="Greens",
                text="Texto_Valor"
            )
            fig_inv_bar.update_layout(
                plotly_theme["layout"], 
                coloraxis_showscale=False, 
                height=450,
                margin=dict(l=110, r=40, t=40, b=30)
            )
            fig_inv_bar.update_xaxes(tickprefix="R$ ", tickformat="~s")
            fig_inv_bar.update_traces(textposition="outside", textfont=dict(size=11, color="#3FB950"))
            st.plotly_chart(fig_inv_bar, use_container_width=True, config=plotly_config)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            df_carteira_investimentos = df_carteira_investimentos.sort_values("Mês")
            fig_inv_line = px.line(
                df_carteira_investimentos,
                x="Mês", y="Valor", color="Categoria",
                title="📈 Curva Histórica de Crescimento por Ativo",
                markers=True,
                labels={"Valor": "R$", "Categoria": ""},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_inv_line.update_layout(
                plotly_theme["layout"], 
                height=520,
                legend=dict(orientation="h", yanchor="top", y=-0.20, xanchor="center", x=0.5, font=dict(size=10)),
                margin=dict(l=50, r=20, t=40, b=150)
            )
            fig_inv_line.update_yaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_inv_line, use_container_width=True, config=plotly_config)

            st.markdown("<hr style='border-color: #21262D;'>", unsafe_allow_html=True)

            # DIVERSIFICAÇÃO POR CLASSE DE ATIVO
            st.markdown("##### 🍩 Diversificação por Classe de Ativo")
            
            def classificar_ativo(nome):
                nome_upper = str(nome).upper()
                if "IPCA" in nome_upper: return "Inflação (IPCA)"
                elif "PREFIXADO" in nome_upper or "PRE" in nome_upper: return "Pré-fixado"
                elif "MXRF11" in nome_upper or "FII" in nome_upper or "AÇÕES" in nome_upper: return "Renda Variável / FIIs"
                elif "CAIXINHA" in nome_upper or "CDI" in nome_upper or "CDB" in nome_upper: return "Pós-fixado / Liquidez"
                else: return "Outros / Proteção"

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
                    title=f"Alocação em {ultimo_mes.upper()}",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_donut.update_traces(textinfo="percent+label", hovertemplate="<b>%{label}</b><br>Saldo: R$ %{value:,.2f}<br>Participação: %{percent:.2f}%")
                fig_donut.update_layout(plotly_theme["layout"], height=360, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_donut, use_container_width=True, config=plotly_config)

            with col_tabela_classes:
                st.markdown("###### 📑 Resumo da Estrutura de Alocação")
                df_classes_display = df_classes.sort_values(by="Valor", ascending=False).copy()
                df_classes_display["Valor Formatado"] = df_classes_display["Valor"].apply(lambda v: f"R$ {v:,.2f}")
                df_classes_display["% Carteira"] = df_classes_display["Percentual"].apply(lambda p: f"{p:.2f}%")
                
                st.dataframe(
                    df_classes_display[["Classe", "Valor Formatado", "% Carteira"]],
                    use_container_width=True,
                    hide_index=True
                )

            # =========================================================
            # CALENDÁRIO DE EVENTOS & PROVENTOS AUTOMÁTICOS
            # =========================================================
            st.markdown("<hr style='border-color: #21262D;'>", unsafe_allow_html=True)
            st.markdown("### 📅 Calendário de Eventos & Proventos Futuros (Cash Flow Timeline)")
            st.markdown("<p style='color: #8B949E; font-size: 0.85rem;'>Mapeamento automático de dividendos e linha do tempo de vencimentos da carteira</p>", unsafe_allow_html=True)

            # 1. Leitura de Cotas da Planilha
            cotas_mxrf_cal = 423
            try:
                df_mxrf_cal = load_sheet_by_gid(SPREADSHEET_ID, "1282765175").dropna(how='all')
                tot_c = pd.to_numeric(df_mxrf_cal.iloc[:, 1], errors='coerce').sum()
                if tot_c > 0: cotas_mxrf_cal = tot_c
            except Exception: pass

            # 2. Busca Automática do Último Dividendo por Cota (Brapi API)
            @st.cache_data(ttl=3600)
            def get_ultimo_dividendo_mxrf():
                try:
                    url = "https://brapi.dev/api/quote/MXRF11?dividends=true"
                    res = requests.get(url, timeout=5).json()
                    dividends_list = res['results'][0]['dividendsData']['cashDividends']
                    
                    if dividends_list:
                        df_divs = pd.DataFrame(dividends_list)
                        df_divs['paymentDate'] = pd.to_datetime(df_divs['paymentDate'], errors='coerce')
                        df_divs = df_divs.sort_values(by='paymentDate', ascending=False)
                        val_cota = float(df_divs.iloc[0]['rate'])
                        return val_cota
                except Exception:
                    pass
                return 0.10

            valor_cota_atual = get_ultimo_dividendo_mxrf()
            dyd_mensal_est = cotas_mxrf_cal * valor_cota_atual

            # 3. Exibição nos Cards com o Valor Atualizado
            c_ev1, c_ev2, c_ev3 = st.columns(3)
            with c_ev1:
                st.markdown(f"""
                <div class="kpi-card" style="border-color: #3FB950;">
                    <div class="kpi-title">Proventos MXRF11 (Est. Mensal)</div>
                    <div class="kpi-value val-green">R$ {dyd_mensal_est:,.2f}</div>
                    <div class="kpi-badge badge-pos">~{cotas_mxrf_cal:.0f} Cotas × R$ {valor_cota_atual:.2f}/cota</div>
                </div>
                """, unsafe_allow_html=True)
            with c_ev2:
                st.markdown("""
                <div class="kpi-card" style="border-color: #58A6FF;">
                    <div class="kpi-title">Data-Com MXRF11</div>
                    <div class="kpi-value val-blue">Último Dia Útil</div>
                    <div class="kpi-badge badge-neu">Fechamento do Mês</div>
                </div>
                """, unsafe_allow_html=True)
            with c_ev3:
                st.markdown("""
                <div class="kpi-card" style="border-color: #A371F7;">
                    <div class="kpi-title">Data Pagamento FII</div>
                    <div class="kpi-value val-purple">10º Dia Útil</div>
                    <div class="kpi-badge badge-neu">Crédito Automático</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### ⏳ Linha do Tempo de Vencimentos & Resgates da Carteira")

            eventos_vencimento = [
                {"Ano": "2026", "Ativo / Título": "C6 - CDB Prefixado 15,7% a.a.", "Classe": "Pré-Fixado", "Status / Ação": "Vencimento em 03/06/2026", "Impacto": "Liquidação em Conta"},
                {"Ano": "2026", "Ativo / Título": "Nubank LCA Banco BV", "Classe": "Isento (LCA)", "Status / Ação": "Vencimento em 13/03/2026", "Impacto": "Resgate de Capital"},
                {"Ano": "2027", "Ativo / Título": "C6 - CDB IPCA + 7,9% a.a.", "Classe": "Inflação (IPCA)", "Status / Ação": "Vencimento em 19/04/2027", "Impacto": "Realocação Estratégica"},
                {"Ano": "2035", "Ativo / Título": "C6 - Tesouro 2035 Juros Semestrais", "Classe": "Tesouro Direto", "Status / Ação": "Vencimento Principal em 2035", "Impacto": "Cupons Semestrais Ativos"},
                {"Ano": "2050", "Ativo / Título": "C6 - Tesouro IPCA+ 2050", "Classe": "Aposentadoria / Longo Prazo", "Status / Ação": "Acúmulo de Longo Prazo", "Impacto": "Foco na Curva de Juros Compostos"}
            ]

            df_timeline = pd.DataFrame(eventos_vencimento)
            st.dataframe(df_timeline, use_container_width=True, hide_index=True)

        # =========================================================
        # TAB 4: HUB DE INTELIGÊNCIA ARTIFICIAL, PROJEÇÕES & INFLAÇÃO REAL
        # =========================================================
        with tab_ia_hub:
            st.markdown("### 🤖 Hub de Inteligência, Projeções & Inflação")
            st.markdown("<p style='color: #8B949E; font-size: 0.85rem; margin-bottom: 20px;'>Simulação dinâmica conectada com as abas do Google Sheets, monitor de inflação e análise algorítmica</p>", unsafe_allow_html=True)

            aba_ia1, aba_ia_ipca, aba_ia2, aba_ia3, aba_ia4, aba_ia5 = st.tabs([
                "🔮 Projeções Patrimoniais",
                "🛡️ Inflação Real & Poder de Compra",
                "💬 Copilot Financeiro",
                "📜 Diagnóstico Executivo",
                "🚨 Detector de Anomalias",
                "🎯 Rebalanceamento"
            ])

            # --- 1. PROJEÇÕES PREDITIVAS REALISTAS ---
            with aba_ia1:
                st.markdown("##### 🔮 Simulação de Projeção Dinâmica do Patrimônio")
                st.caption("Cálculos configurados conforme regras e contratos das abas reais da planilha:")

                opcoes_ativos_proj = [
                    "🌐 Visão Consolidada (Carteira Toda)",
                    "🏛️ C6 - Tesouro IPCA+ 2050",
                    "🏛️ C6 - Tesouro 2035 (Juros Semestrais)",
                    "📈 C6 - MXRF11 (Com Média de Aportes do Histórico)",
                    "🔒 C6 - CDB IPCA + 7,9% (Venc. 19/04/2027)",
                    "📱 Mercado Pago (120% CDI)"
                ]

                col_fj1, col_fj2 = st.columns([2, 1])
                with col_fj1:
                    ativo_proj_sel = st.selectbox("Ativo / Visão para Simular:", opcoes_ativos_proj)
                with col_fj2:
                    ano_alvo_proj = st.slider("Horizonte (Ano Alvo):", 2026, 2050, 2035)

                dados_grafico_proj = []
                ano_corrente = 2026

                saldo_2050 = 15000.0
                try:
                    df_2050 = load_sheet_by_gid(SPREADSHEET_ID, "1265273668")
                    val_investido_2050 = pd.to_numeric(df_2050.iloc[:, 3].apply(parse_br_val), errors='coerce').sum()
                    if val_investido_2050 > 0: saldo_2050 = val_investido_2050
                except Exception: pass

                saldo_2035 = 12000.0
                try:
                    df_2035 = load_sheet_by_gid(SPREADSHEET_ID, "1832710448")
                    val_investido_2035 = pd.to_numeric(df_2035.iloc[:, 1].apply(parse_br_val), errors='coerce').sum()
                    if val_investido_2035 > 0: saldo_2035 = val_investido_2035
                except Exception: pass

                cotas_mxrf = 500
                media_aporte_mensal_mxrf = 300.0
                
                try:
                    df_mxrf = load_sheet_by_gid(SPREADSHEET_ID, "1282765175")
                    df_mxrf_clean = df_mxrf.dropna(how='all')
                    
                    total_cotas_sheet = pd.to_numeric(df_mxrf_clean.iloc[:, 1], errors='coerce').sum()
                    if total_cotas_sheet > 0: cotas_mxrf = total_cotas_sheet
                    
                    valores_aportados = pd.to_numeric(df_mxrf_clean.iloc[:, 3].apply(parse_br_val), errors='coerce').dropna()
                    if len(valores_aportados) > 0: media_aporte_mensal_mxrf = valores_aportados.mean()
                except Exception: pass

                saldo_mxrf_inicial = cotas_mxrf * mxrf11_preco_num
                saldo_cdb_ipca = 5000.0
                saldo_mp = 8000.0

                for yr in range(ano_corrente, ano_alvo_proj + 1):
                    yrs_elapsed = yr - ano_corrente
                    
                    v_2050 = saldo_2050 * ((1 + 0.102) ** yrs_elapsed) + (yrs_elapsed * 12 * 300)
                    
                    if yr <= 2035:
                        v_2035 = saldo_2035 * ((1 + 0.095) ** yrs_elapsed)
                    else:
                        v_2035 = saldo_2035 * ((1 + 0.095) ** (2035 - ano_corrente))
                    
                    v_mxrf = saldo_mxrf_inicial + (media_aporte_mensal_mxrf * 12 * yrs_elapsed)
                    
                    if yr <= 2027:
                        v_cdb = saldo_cdb_ipca * ((1 + 0.119) ** yrs_elapsed)
                    else:
                        v_cdb = saldo_cdb_ipca * ((1 + 0.119) ** (2027 - ano_corrente))
                    
                    v_mp = saldo_mp * ((1 + (cdi_num * 1.20 / 100)) ** yrs_elapsed)

                    if "Consolidada" in ativo_proj_sel: v_exibir = v_2050 + v_2035 + v_mxrf + v_cdb + v_mp
                    elif "2050" in ativo_proj_sel: v_exibir = v_2050
                    elif "2035" in ativo_proj_sel: v_exibir = v_2035
                    elif "MXRF11" in ativo_proj_sel: v_exibir = v_mxrf
                    elif "CDB" in ativo_proj_sel: v_exibir = v_cdb
                    else: v_exibir = v_mp

                    dados_grafico_proj.append({
                        "Ano": str(yr),
                        "Patrimônio Projetado": v_exibir,
                        "Texto_Barra": f"R$ {v_exibir:,.0f}".replace(",", ".")
                    })

                df_proj_display = pd.DataFrame(dados_grafico_proj)

                if not df_proj_display.empty:
                    v_final_proj = df_proj_display.iloc[-1]["Patrimônio Projetado"]
                    v_inicial_proj = df_proj_display.iloc[0]["Patrimônio Projetado"]
                    lucro_proj = v_final_proj - v_inicial_proj
                    
                    if "MXRF11" in ativo_proj_sel: renda_m_est = v_final_proj * 0.009
                    else: renda_m_est = v_final_proj * 0.008

                    kp1, kp2, kp3, kp4 = st.columns(4)
                    kp1.metric(f"Saldo em {ano_alvo_proj}", f"R$ {v_final_proj:,.2f}")
                    kp2.metric("Saldo Inicial (2026)", f"R$ {v_inicial_proj:,.2f}")
                    kp3.metric("Crescimento Aportado", f"R$ {lucro_proj:+,.2f}", delta=f"+{((lucro_proj/v_inicial_proj)*100):.1f}%")
                    kp4.metric("Renda Passiva Est.", f"R$ {renda_m_est:,.2f}/mês")

                    st.markdown("<br>", unsafe_allow_html=True)

                    fig_proj = px.bar(
                        df_proj_display,
                        x="Ano", y="Patrimônio Projetado",
                        text="Texto_Barra",
                        color="Patrimônio Projetado",
                        color_continuous_scale="Purples",
                        title=f"📈 Projeção Patrimonial: {ativo_proj_sel}"
                    )
                    fig_proj.update_layout(
                        plotly_theme["layout"],
                        height=380,
                        coloraxis_showscale=False,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    fig_proj.update_traces(textposition="outside", textfont=dict(size=11, color="#C9D1D9"))
                    fig_proj.update_yaxes(tickprefix="R$ ", tickformat="~s")
                    st.plotly_chart(fig_proj, use_container_width=True, config=plotly_config)

            # --- MONITOR DE INFLAÇÃO REAL E PODER DE COMPRA ---
            with aba_ia_ipca:
                st.markdown("##### 🛡️ Monitor de Inflação Real e Preservação do Poder de Compra")
                st.caption("Acompanhamento do rendimento real descontando a inflação projetada (IPCA ~4.0% a.a.):")

                col_ip1, col_ip2, col_ip3 = st.columns(3)
                col_ip1.metric("Taxa Média IPCA+ Contratada", "IPCA + 6.85% a.a.", "Proteção de Longo Prazo")
                col_ip2.metric("IPCA Acumulado / Projeção", "4.00% a.a.", "Inflação de Referência")
                col_ip3.metric("Ganho Real Líquido Estimado", "+ 6.20% a.a.", "Acima da Inflação (Real)")

                st.markdown("<br>", unsafe_allow_html=True)
                
                anos_ipca = [str(y) for y in range(2026, 2036)]
                patrimonio_bruto = []
                patrimonio_real = []
                
                val_base = patrimonio_total_ultimo_mes if patrimonio_total_ultimo_mes > 0 else 50000.0
                
                for i, y in enumerate(range(2026, 2036)):
                    v_bruto = val_base * ((1 + 0.10) ** i)
                    v_real = val_base * ((1 + 0.06) ** i)
                    patrimonio_bruto.append(v_bruto)
                    patrimonio_real.append(v_real)

                fig_ipca_comp = go.Figure()
                fig_ipca_comp.add_trace(go.Scatter(x=anos_ipca, y=patrimonio_bruto, mode='lines+markers', name='Crescimento Bruto (Nominal)', line=dict(color='#3FB950', width=3)))
                fig_ipca_comp.add_trace(go.Scatter(x=anos_ipca, y=patrimonio_real, mode='lines+markers', name='Poder de Compra Real (Descontado IPCA)', line=dict(color='#58A6FF', width=3, dash='dash')))

                fig_ipca_comp.update_layout(
                    plotly_theme["layout"],
                    title="📈 Comparativo: Crescimento Nominal vs Poder de Compra Real (2026-2035)",
                    height=400,
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                    margin=dict(l=20, r=20, t=40, b=40)
                )
                fig_ipca_comp.update_yaxes(tickprefix="R$ ", tickformat="~s")
                st.plotly_chart(fig_ipca_comp, use_container_width=True, config=plotly_config)

            # --- 2. COPILOT FINANCEIRO DE LINGUAGEM NATURAL ---
            with aba_ia2:
                st.markdown("##### 💬 Assistente Virtual de Finanças")
                q_user = st.text_input("Consulte seus indicadores ou despesas:", placeholder="Ex: Qual foi meu maior gasto em outubro?")
                
                if q_user:
                    q_clean = q_user.lower()
                    with st.spinner("Processando base de dados do Google Sheets..."):
                        time.sleep(0.4)
                        if "maior despesa" in q_clean or "maior gasto" in q_clean:
                            df_desp_val = df_despesas[df_despesas["Mês"] == ultimo_mes].sort_values("Valor", ascending=False)
                            if not df_desp_val.empty:
                                top_desp = df_desp_val.iloc[0]
                                st.success(f"🤖 **Copilot:** Em **{ultimo_mes.upper()}**, a sua maior despesa cadastrada foi na categoria **{top_desp['Categoria']}** no valor de **R$ {top_desp['Valor']:,.2f}**.")
                            else: st.info("Sem despesas registradas no mês selecionado.")
                        elif "receita" in q_clean or "ganhei" in q_clean:
                            rec_m = df_receitas[df_receitas["Mês"] == ultimo_mes]["Valor"].sum()
                            st.info(f"🤖 **Copilot:** A receita total acumulada em **{ultimo_mes.upper()}** foi de **R$ {rec_m:,.2f}**.")
                        else:
                            taxa_poup = ((total_rec - total_desp) / total_rec * 100) if total_rec > 0 else 0
                            st.markdown(f"""
                            🤖 **Resumo dos Indicadores:**
                            - **Receita Total:** R$ {total_rec:,.2f}
                            - **Despesas Operacionais:** R$ {total_desp:,.2f}
                            - **Taxa de Sobra Líquida:** {taxa_poup:.1f}% da renda.
                            - **Patrimônio Atual ({ultimo_mes.upper()}):** R$ {patrimonio_total_ultimo_mes:,.2f}
                            """)

            # --- 3. DIAGNÓSTICO EXECUTIVO MENSAL ---
            with aba_ia3:
                taxa_poup = ((total_rec - total_desp) / total_rec * 100) if total_rec > 0 else 0
                poup_status = "🟢 Excelente (Acima da meta de 20%)" if taxa_poup >= 20 else "🟡 Atencioso (Abaixo da meta de 20%)"

                st.markdown(f"""
                <div class="ai-box">
                    <h4 style="margin-top:0; color:#58A6FF; font-weight:700;">📊 Relatório do Período ({ultimo_mes.upper()} / {ano_selecionado})</h4>
                    <ul>
                        <li><b>Retenção de Capital:</b> {taxa_poup:.1f}% das receitas foram preservadas. ({poup_status})</li>
                        <li><b>Variação de Despesas MoM:</b> {var_desp_pct:+.1f}%</li>
                        <li><b>Crescimento Patrimonial MoM:</b> {var_patrimonio_pct:+.1f}%</li>
                        <li><b>Direcionamento Recomendado:</b> Manter foco na alocação em IPCA+ para preservação do poder de compra real.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            # --- 4. DETECTOR DE ANOMALIAS ---
            with aba_ia4:
                st.markdown("##### 🚨 Identificação de Custos Atípicos")
                df_desp_m = df_despesas[df_despesas["Mês"] == ultimo_mes].copy()
                if not df_desp_m.empty and df_desp_m["Valor"].sum() > 0:
                    media_desp = df_desp_m[df_desp_m["Valor"] > 0]["Valor"].mean()
                    anomalias = df_desp_m[df_desp_m["Valor"] > (media_desp * 1.5)]
                    if not anomalias.empty:
                        st.warning(f"⚠️ Identificadas {len(anomalias)} categorias com despesas acima de 150% da média do período:")
                        st.dataframe(anomalias[["Categoria", "Valor"]].rename(columns={"Valor": "Valor (R$)"}), use_container_width=True, hide_index=True)
                    else: st.success("🟢 Nenhuma anomalia crítica de despesas encontrada no período.")
                else: st.info("Sem lançamentos de despesas suficientes para cálculo no período.")

            # --- 5. REBALANCEAMENTO DE CARTEIRA ---
            with aba_ia5:
                st.markdown("##### 🎯 Sugestão Algorítmica de Alocação")
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Pós-Fixado (Liquidez)", "42%", "Alocação Adequada")
                col_r2.metric("Inflação (IPCA+ 2050)", "38%", "+ R$ 1.200 (Sugerido)")
                col_r3.metric("Renda Variável / FIIs", "20%", "+ R$ 800 (Sugerido)")

        # =========================================================
        # TAB 5: 📝 FORMULÁRIO DE LANÇAMENTO DIRETO NA PLANILHA
        # =========================================================
        with tab_lancamento:
            st.markdown("### 📝 Lançamento Direto de Dados na Planilha")
            st.markdown("<p style='color: #8B949E; font-size: 0.85rem; margin-bottom: 25px;'>Preencha os valores abaixo para gravar diretamente no Google Sheets sem precisar abrir a planilha.</p>", unsafe_allow_html=True)

            sub_tab_2026, sub_tab_aportes = st.tabs(["📊 Aba Principal (2026)", "🏛️ Aportes de Ativos"])

            # --- SUB-TAB A: ABA PRINCIPAL (2026) ---
            with sub_tab_2026:
                st.markdown("##### 📅 Lançamento Mensal na Aba Principal (2026)")
                
                col_l1, col_l2 = st.columns([1, 2])
                with col_l1:
                    mes_lanc = st.selectbox("Selecione o Mês:", list(MES_PARA_COLUNA.keys()), index=10) # nov por padrão
                    coluna_excel = MES_PARA_COLUNA[mes_lanc]
                    st.info(f"📍 Os dados serão gravados na **Coluna {coluna_excel}** da aba **`2026`**.")

                st.markdown("---")
                
                with st.form("form_lancamento_2026"):
                    st.markdown("##### 🟢 Receitas")
                    cr1, cr2 = st.columns(2)
                    with cr1:
                        val_salario = st.number_input("Salário Líquido (Linha 2):", min_value=0.0, step=100.0, format="%.2f")
                    with cr2:
                        val_outras_rec = st.number_input("(+) Outras Entradas (Linha 3):", min_value=0.0, step=50.0, format="%.2f")

                    st.markdown("##### 🔴 Despesas Operacionais e Aporte do Mês")
                    cd1, cd2, cd3 = st.columns(3)
                    
                    dict_despesas = {
                        5: "(-) Energia",
                        6: "(-) Cartão C6",
                        7: "(-) Cartão Nubank",
                        8: "(-) Plano TIM",
                        9: "(-) Internet",
                        10: "(-) MEI",
                        11: "(-) Cartão Mercado Pago",
                        12: "(-) Plano de Saúde - Pais",
                        13: "(-) Outras despesas (lavanderia)",
                        14: "(-) Outras despesas (faculdade)",
                        15: "(-) Outras despesas - PIX",
                        16: "(-) Investimentos (Aporte do Mês)",
                        17: "(-) Vôlei"
                    }

                    valores_despesas = {}
                    for i, (lin, cat_nome) in enumerate(dict_despesas.items()):
                        target_col = [cd1, cd2, cd3][i % 3]
                        with target_col:
                            valores_despesas[lin] = st.number_input(f"{cat_nome} (Linha {lin}):", min_value=0.0, step=50.0, format="%.2f")

                    st.markdown("##### 🔵 Investimentos / Ativos (Saldos da Carteira)")
                    ci1, ci2, ci3 = st.columns(3)

                    dict_invest = {
                        22: "C6 - CDB C6 Prefixado (15,7% a.a.)",
                        23: "Nubank 115% CDI (líquido)",
                        24: "C6 - Tesouro IPCA 2050 (investido)",
                        25: "C6 - Tesouro 2035 Juros Semestrais (investido)",
                        26: "Mercado Pago - 120% CDI",
                        27: "Nubank LCA - líquido",
                        28: "C6 - MXRF11",
                        29: "C6 - Carbon Ouro",
                        30: "C6 - IPCA + 7,9% Venc em 19/04/2027"
                    }

                    valores_invest = {}
                    for i, (lin, inv_nome) in enumerate(dict_invest.items()):
                        target_col = [ci1, ci2, ci3][i % 3]
                        with target_col:
                            valores_invest[lin] = st.number_input(f"{inv_nome} (Linha {lin}):", min_value=0.0, step=50.0, format="%.2f")

                    btn_salvar_2026 = st.form_submit_button("💾 Salvar na Aba 2026", use_container_width=True)

                    if btn_salvar_2026:
                        gc = get_gspread_client()
                        if gc is None:
                            st.error("🚨 Erro na conexão. Verifique se as credenciais 'gcp_service_account' foram adicionadas nos Secrets do Streamlit.")
                        else:
                            try:
                                with st.spinner(f"Gravando dados do mês {mes_lanc.upper()} na aba 2026..."):
                                    sh = gc.open_by_key(SPREADSHEET_ID)
                                    ws = sh.worksheet("2026")

                                    batch_updates = []

                                    if val_salario > 0:
                                        batch_updates.append({'range': f'{coluna_excel}2', 'values': [[val_salario]]})
                                    if val_outras_rec > 0:
                                        batch_updates.append({'range': f'{coluna_excel}3', 'values': [[val_outras_rec]]})

                                    for lin, val in valores_despesas.items():
                                        if val > 0:
                                            batch_updates.append({'range': f'{coluna_excel}{lin}', 'values': [[val]]})

                                    for lin, val in valores_invest.items():
                                        if val > 0:
                                            batch_updates.append({'range': f'{coluna_excel}{lin}', 'values': [[val]]})

                                    if batch_updates:
                                        ws.batch_update(batch_updates)
                                        st.cache_data.clear()
                                        st.success(f"✅ Sucesso! {len(batch_updates)} células atualizadas para {mes_lanc.upper()} (Coluna {coluna_excel}).")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Nenhum valor maior que R$ 0,00 foi informado para salvar.")

                            except Exception as ex_gspread:
                                st.error(f"Erro ao salvar na planilha: {str(ex_gspread)}")

            # --- SUB-TAB B: APORTES EM ATIVOS (CÁLCULO E EXIBIÇÃO REATIVA EM TEMPO REAL) ---
            with sub_tab_aportes:
                st.markdown("##### 🏛️ Lançamento de Aporte nas Abas Individuais dos Ativos")
                
                ativo_alvo = st.selectbox("Selecione o Ativo:", ["IPCA +2050", "MXRF11"])
                
                if ativo_alvo == "IPCA +2050":
                    st.caption("📌 **Campos específicos para a aba IPCA +2050**")
                    ca1, ca2, ca3 = st.columns(3)
                    with ca1:
                        dt_app = st.date_input("Data da Aplicação:", key="dt_ipca")
                    with ca2:
                        qtd_titulos = st.number_input("Quantidade de Títulos (A):", min_value=0.0, step=0.01, format="%.2f", key="qtd_ipca")
                    with ca3:
                        preco_titulo = st.number_input("Preço do Título (R$) (B):", min_value=0.0, step=10.0, format="%.2f", key="pr_ipca")
                    
                    # Cálculo reativo fora do form
                    val_investido_calc_ipca = qtd_titulos * preco_titulo
                    
                    st.markdown(f"""
                    <div style='background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 16px; margin-top: 10px; margin-bottom: 15px;'>
                        <span style='color: #8B949E; font-size: 0.9rem; font-weight: 600;'>Valor Investido (R$) (A x B):</span>
                        <span style='font-size: 1.35rem; color: #3FB950; font-weight: 800; margin-left: 15px;'>R$ {val_investido_calc_ipca:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.form("form_ipca_submit"):
                        rentabilidade_contratada = st.text_input("Rentabilidade Contratada:", placeholder="Ex: IPCA + 6,85%")
                        btn_salvar_ipca = st.form_submit_button("💾 Registrar Aporte no IPCA +2050", use_container_width=True)

                        if btn_salvar_ipca:
                            gc = get_gspread_client()
                            if gc is None:
                                st.error("🚨 Erro na conexão com o Google Sheets.")
                            else:
                                try:
                                    with st.spinner("Registrando aporte na aba 'IPCA +2050'..."):
                                        sh = gc.open_by_key(SPREADSHEET_ID)
                                        ws_ativo = sh.worksheet("IPCA +2050")
                                        
                                        dt_str = dt_app.strftime("%d/%m/%Y")
                                        nova_linha = [dt_str, qtd_titulos, preco_titulo, val_investido_calc_ipca, rentabilidade_contratada]
                                        
                                        ws_ativo.append_row(nova_linha)
                                        st.cache_data.clear()
                                        st.success(f"✅ Aporte no IPCA +2050 (R$ {val_investido_calc_ipca:,.2f}) registrado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()

                                except Exception as ex_ipca:
                                    st.error(f"Erro ao registrar aporte no IPCA +2050: {str(ex_ipca)}")

                elif ativo_alvo == "MXRF11":
                    st.caption("📌 **Campos específicos para a aba MXRF11**")
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1:
                        dt_mxrf = st.date_input("Data:", key="dt_mx")
                    with cm2:
                        cotas_mxrf_in = st.number_input("Cotas (A):", min_value=0.0, step=1.0, format="%.2f", value=4.00, key="ct_mx")
                    with cm3:
                        val_cota_in = st.number_input("Valor Cota (R$) (B):", min_value=0.0, step=0.01, format="%.2f", value=float(mxrf11_preco_num), key="pr_mx")

                    # Cálculo reativo fora do form
                    val_inv_mxrf_calc = cotas_mxrf_in * val_cota_in

                    st.markdown(f"""
                    <div style='background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 16px; margin-top: 10px; margin-bottom: 15px;'>
                        <span style='color: #8B949E; font-size: 0.9rem; font-weight: 600;'>Valor Investido (R$) (A x B):</span>
                        <span style='font-size: 1.35rem; color: #3FB950; font-weight: 800; margin-left: 15px;'>R$ {val_inv_mxrf_calc:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.form("form_mxrf_submit"):
                        btn_salvar_mxrf = st.form_submit_button("💾 Registrar Aporte no MXRF11", use_container_width=True)

                        if btn_salvar_mxrf:
                            gc = get_gspread_client()
                            if gc is None:
                                st.error("🚨 Erro na conexão com o Google Sheets.")
                            else:
                                try:
                                    with st.spinner("Registrando aporte na aba 'MXRF11'..."):
                                        sh = gc.open_by_key(SPREADSHEET_ID)
                                        ws_ativo = sh.worksheet("MXRF11")
                                        
                                        dt_str = dt_mxrf.strftime("%d/%m/%Y")
                                        nova_linha = [dt_str, cotas_mxrf_in, val_cota_in, val_inv_mxrf_calc]
                                        
                                        ws_ativo.append_row(nova_linha)
                                        st.cache_data.clear()
                                        st.success(f"✅ Aporte no MXRF11 (R$ {val_inv_mxrf_calc:,.2f}) registrado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()

                                except Exception as ex_mxrf:
                                    st.error(f"Erro ao registrar aporte no MXRF11: {str(ex_mxrf)}")

    else:
        st.warning("⚠️ Selecione ao menos um mês no filtro para carregar os relatórios.")

except Exception as e:
    st.error(f"Não foi possível acessar os dados do ano '{ano_selecionado}'. Verifique a estrutura da planilha.")
