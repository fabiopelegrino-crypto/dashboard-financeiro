import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests
import yfinance as yf
import urllib.parse
import os

# -------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM RESPONSIVO (CSS)
# -------------------------------------------------------------
st.set_page_config(
    page_title="Finances AI | Fabio Pelegrino", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS com Suporte a Telas Móveis
custom_css = """
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    .stApp {
        background-color: #0B0E14;
        font-family: 'Inter', sans-serif;
    }
    .kpi-card {
        background: linear-gradient(145deg, #161B26 0%, #0F131C 100%);
        border: 1px solid #232D3F;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 8px 20px -5px rgba(0, 0, 0, 0.5);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        margin-bottom: 10px;
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    .kpi-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 7px;
        border-radius: 20px;
        font-size: 0.70rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .badge-pos { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-neg { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-neu { background: rgba(107, 114, 128, 0.15); color: #9CA3AF; border: 1px solid rgba(107, 114, 128, 0.3); }

    .val-green { color: #10B981; }
    .val-red { color: #EF4444; }
    .val-blue { color: #3B82F6; }
    .val-purple { color: #A855F7; }

    .nav-container {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 15px;
    }
    .nav-link-btn {
        flex: 1 1 calc(16% - 8px);
        text-align: center;
        background: #161B26;
        color: #9CA3AF !important;
        padding: 8px 10px;
        border-radius: 8px;
        text-decoration: none !important;
        font-size: 0.80rem;
        font-weight: 600;
        border: 1px solid #232D3F;
        transition: all 0.2s ease;
        white-space: nowrap;
    }
    .nav-link-btn:hover {
        background-color: #1F2937;
        color: #3B82F6 !important;
        border-color: #3B82F6;
    }

    .back-to-top-btn {
        position: fixed;
        bottom: 20px;
        left: 15px;
        z-index: 9999;
        background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
        color: #3B82F6 !important;
        border: 1px solid #3B82F6;
        border-radius: 50px;
        padding: 8px 14px;
        font-size: 0.78rem;
        font-weight: 700;
        text-decoration: none !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
        transition: all 0.25s ease;
    }

    /* Estilo da Foto e Cabeçalho de Login Executivo */
    .profile-img-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
    }
    .profile-img {
        width: 130px;
        height: 130px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #3B82F6;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
    }

    .c6-logo-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #111;
        color: #FFF;
        font-weight: 900;
        font-size: 0.85rem;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #333;
        letter-spacing: -0.05em;
        vertical-align: middle;
        margin-right: 8px;
    }

    @media (max-width: 768px) {
        .nav-link-btn {
            flex: 1 1 calc(33% - 8px);
            font-size: 0.75rem;
            padding: 8px 6px;
        }
        .kpi-value {
            font-size: 1.35rem;
        }
        .kpi-card {
            padding: 14px 14px;
        }
        h2 {
            font-size: 1.4rem !important;
        }
        h3 {
            font-size: 1.2rem !important;
        }
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

plotly_config = {
    'displayModeBar': False, 
    'responsive': True
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
# 1.1 MECANISMO DE LOGIN PERSONALIZADO COM FOTO E NOME
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
            st.markdown("<h2 style='text-align: center; color: #EF4444;'>🚫 Acesso Bloqueado</h2>", unsafe_allow_html=True)
            st.error(f"Muitas tentativas. Aguarde {remaining_time}s.")
            return False
        else:
            st.session_state["login_attempts"] = 0

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 1.8, 1])
        with col2:
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
            
            # Exibição da Foto (verifica se o arquivo eu.jpg existe localmente)
            if os.path.exists("eu.jpg"):
                st.markdown("""
                <div class="profile-img-container">
                    <img src="app/static/eu.jpg" class="profile-img" alt="Fabio Pelegrino">
                </div>
                """, unsafe_allow_html=True)
                # Fallback Streamlit nativo caso estático não carregue
                col_i1, col_i2, col_i3 = st.columns([1, 1.2, 1])
                with col_i2:
                    st.image("eu.jpg", use_container_width=True)
            
            st.markdown("<h2 style='text-align: center; color: #3B82F6; margin-bottom: 2px;'>💎 Gestão Financeira & Patrimonial</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #9CA3AF; font-size: 0.95rem; font-weight: 600; margin-bottom: 20px;'>Acesso Exclusivo | <b>Fabio Pelegrino</b></p>", unsafe_allow_html=True)

            with st.form("login_form"):
                password_input = st.text_input("Senha de acesso:", type="password", placeholder="Digite sua senha...")
                submit_button = st.form_submit_button("🔑 Acessar Painel", use_container_width=True)

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
            var_html = f"<span style='color: #10B981; font-weight: 600; font-size: 0.80rem;'>+{diff_abs:.2f} (+{diff_pct:.2f}%)</span>"
        else:
            var_html = f"<span style='color: #EF4444; font-weight: 600; font-size: 0.80rem;'>{diff_abs:.2f} ({diff_pct:.2f}%)</span>"
    except Exception:
        mxrf_str = "R$ 9.45"
        var_html = "<span style='color: #10B981; font-weight: 600; font-size: 0.80rem;'>+0.10 (+1.07%)</span>"

    return selic_str, cdi_str, mxrf_str, var_html

selic_str, cdi_str, mxrf11_price_str, mxrf11_var_html = fetch_market_indicators()

# -------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS DO GOOGLE SHEETS
# -------------------------------------------------------------
try:
    SPREADSHEET_ID = st.secrets.get("SPREADSHEET_ID", "1t_jPaLp5lP8Yg5yJQb_U8NaIF7BS0DyLfqJaoAvehr4")
    FATURA_SHEET_ID = st.secrets.get("FATURA_SHEET_ID", "1PUXXGAfn8dmqqR1qCcrJMMF32wUGng_MHpQ7-5GSbOY")
except Exception:
    SPREADSHEET_ID = "1t_jPaLp5lP8Yg5yJQb_U8NaIF7BS0DyLfqJaoAvehr4"
    FATURA_SHEET_ID = "1PUXXGAfn8dmqqR1qCcrJMMF32wUGng_MHpQ7-5GSbOY"

st.markdown("<a id='topo'></a>", unsafe_allow_html=True)
st.markdown("<a href='#topo' class='back-to-top-btn'>⬆️ Topo</a>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. HEADER DO DASHBOARD & BENCHMARKS MACRO
# -------------------------------------------------------------
st.markdown("<h2 style='margin-bottom: 0px;'>💎 Gestão Financeira & Patrimonial</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 12px;'>Visão executiva de fluxo de caixa, alocação, cartão de crédito e mercado | <b>Fabio Pelegrino</b></p>", unsafe_allow_html=True)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.caption("🏛️ Meta Selic (BCB)")
    st.markdown(f"**{selic_str}**")
with col_m2:
    st.caption("📉 CDI Estimado")
    st.markdown(f"**{cdi_str}**")
with col_m3:
    st.caption("🏢 MXRF11 (B3)")
    st.markdown(f"**{mxrf11_price_str}** {mxrf11_var_html}", unsafe_allow_html=True)
with col_m4:
    st.caption("⚡ Status Conexão")
    st.markdown("**🟢 Planilhas Ativas**")

st.markdown("<hr style='border-color: #1F2937; margin-top: 10px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🎛️ PAINEL DE FILTROS DE PERÍODO (ANO & MESES)
# -------------------------------------------------------------
st.markdown("##### 🔍 Filtros do Período de Análise")
f_col1, f_col2, f_col3 = st.columns([1, 2.5, 1])

with f_col1:
    ano_selecionado = st.selectbox(
        "Ano de Referência", 
        ["2025", "2026", "2027"], 
        index=1,
        key="main_ano"
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
    
    with f_col2:
        mes_selecionado = st.multiselect(
            "Meses Selecionados", 
            meses, 
            default=[m for m in meses if m in ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out']],
            key="main_meses"
        )

    with f_col3:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Sidebar compacta
    st.sidebar.markdown("### ⚙️ Painel")
    st.sidebar.info(f"👤 **Fabio Pelegrino**\n📅 **Ano:** {ano_selecionado}")
    if st.sidebar.button("🔒 Sair", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 🚀 MENU DE NAVEGAÇÃO RÁPIDA
    # -------------------------------------------------------------
    st.markdown("##### 🧭 Navegação Rápida")
    st.markdown("""
    <div class="nav-container">
        <a class='nav-link-btn' href='#fluxo-de-caixa'>💳 Caixa</a>
        <a class='nav-link-btn' href='#fatura-c6'>🖤 Fatura C6</a>
        <a class='nav-link-btn' href='#investimentos'>📊 Ativos</a>
        <a class='nav-link-btn' href='#lucro-prejuizo'>💵 Lucro</a>
        <a class='nav-link-btn' href='#raio-x'>🔍 Raio-X</a>
        <a class='nav-link-btn' href='#diversificacao'>🍩 Alocação</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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
            df_desp_cat["Categoria_Label"] = df_desp_cat["Categoria"].apply(quebrar_linha_nome)

            fig_cat = px.bar(
                df_desp_cat,
                x="Valor", y="Categoria_Label", orientation="h",
                labels={"Valor": "R$", "Categoria_Label": ""},
                color="Valor", 
                color_continuous_scale=["#3B82F6", "#EF4444"]
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
            st.markdown("##### 📈 Evolução das Receitas Mês a Mês")
            df_rec_evo = df_receitas.groupby("Mês", observed=False)["Valor"].sum().reset_index()
            df_rec_evo = df_rec_evo.sort_values("Mês")
            
            fig_evo = px.area(
                df_rec_evo,
                x="Mês", y="Valor", 
                markers=True,
                color_discrete_sequence=["#10B981"]
            )
            fig_evo.update_layout(
                plotly_theme["layout"], 
                height=380,
                margin=dict(l=50, r=20, t=20, b=30)
            )
            fig_evo.update_yaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_evo, use_container_width=True, config=plotly_config)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 💳 DETALHAMENTO DA FATURA C6 BANK & COMPROMISSOS FUTUROS
        # -------------------------------------------------------------
        st.markdown("<a id='fatura-c6'></a>", unsafe_allow_html=True)
        st.markdown("""
        <h3 style='display: flex; align-items: center; margin-bottom: 0px;'>
            <span class="c6-logo-badge">C6</span>
            Raio-X da Fatura C6 Bank & Parcelas Futuras
        </h3>
        """, unsafe_allow_html=True)
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Análise detalhada dos lançamentos atuais e projeção de compromissos a vencer</p>", unsafe_allow_html=True)

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
                
                # CÁLCULO DE PARCELAS FUTURAS A VENCER
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

                # CARDS KPI DA FATURA + PARCELAS FUTURAS
                cf1, cf2, cf3, cf4 = st.columns(4)
                with cf1:
                    st.markdown(f"""
                    <div class="kpi-card" style="border-color: #EF4444;">
                        <div class="kpi-title">Fatura Atual (Out/26)</div>
                        <div class="kpi-value val-red">R$ {total_fatura:,.2f}</div>
                        <div class="kpi-badge badge-neg">{num_compras} Lançamentos</div>
                    </div>
                    """, unsafe_allow_html=True)

                with cf2:
                    st.markdown(f"""
                    <div class="kpi-card" style="border-color: #A855F7;">
                        <div class="kpi-title">Total Parcelado Futuro</div>
                        <div class="kpi-value val-purple">R$ {total_parcelado_futuro:,.2f}</div>
                        <div class="kpi-badge badge-neu">Compromisso Futuro</div>
                    </div>
                    """, unsafe_allow_html=True)

                with cf3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Compras Parceladas Ativas</div>
                        <div class="kpi-value val-blue">{len(parcelas_futuras_list)}</div>
                        <div class="kpi-badge badge-neu">Itens em Aberto</div>
                    </div>
                    """, unsafe_allow_html=True)

                with cf4:
                    media_compra = (total_fatura / num_compras) if num_compras > 0 else 0.0
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Ticket Médio / Compra</div>
                        <div class="kpi-value val-green">R$ {media_compra:,.2f}</div>
                        <div class="kpi-badge badge-neu">Média por Item</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # SEÇÃO DE PARCELAS A VENCER
                if parcelas_futuras_list:
                    st.markdown("##### ⏳ Compras Parceladas e Saldos a Vencer")
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
                            height=520,
                            margin=dict(l=140, r=20, t=20, b=20)
                        )
                        fig_fat_cat.update_yaxes(tickfont=dict(size=11))
                        fig_fat_cat.update_xaxes(tickprefix="R$ ", tickformat="~s")
                        st.plotly_chart(fig_fat_cat, use_container_width=True, config=plotly_config)

                with col_fat2:
                    st.markdown("##### 🏆 Top 10 Maiores Compras do Mês")
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
                            height=520,
                            margin=dict(l=130, r=20, t=20, b=20)
                        )
                        fig_top10.update_yaxes(tickfont=dict(size=11))
                        fig_top10.update_xaxes(tickprefix="R$ ", tickformat="~s")
                        st.plotly_chart(fig_top10, use_container_width=True, config=plotly_config)

                # Tabela Interativa de Busca na Fatura
                st.markdown("##### 🔎 Pesquisar Lançamento na Fatura")
                busca_compra = st.text_input("Digite o nome da loja, estabelecimento ou categoria:", "")
                
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

        except Exception as e_fat:
            st.warning("⚠️ Não foi possível carregar os dados da Fatura C6. Por favor, confirme se o compartilhamento da planilha está definido para 'Qualquer pessoa com el link'.")

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 8. INVESTIMENTOS
        # -------------------------------------------------------------
        st.markdown("<a id='investimentos'></a>", unsafe_allow_html=True)
        st.markdown("### 📊 Posição & Evolução Patrimonial dos Investimentos")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Acompanhamento individual e evolução de cada ativo da carteira</p>", unsafe_allow_html=True)
        
        df_inv_ultimo = df_carteira_investimentos[df_carteira_investimentos["Mês"] == ultimo_mes].copy()
        df_inv_ultimo = df_inv_ultimo[df_inv_ultimo["Valor"] > 0].sort_values(by="Valor", ascending=True)

        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom: 15px; border-color: #10B981;">
            <div class="kpi-title">Total Investimentos em {ultimo_mes.upper()}</div>
            <div class="kpi-value val-green">R$ {patrimonio_total_ultimo_mes:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        df_inv_ultimo["Categoria_Label"] = df_inv_ultimo["Categoria"].apply(quebrar_linha_nome)
        df_inv_ultimo["Texto_Valor"] = df_inv_ultimo["Valor"].apply(lambda v: f"R$ {v:,.2f}")

        fig_inv_bar = px.bar(
            df_inv_ultimo,
            x="Valor", y="Categoria_Label", orientation="h",
            title=f"🏛️ Saldo de Ativos em {ultimo_mes.upper()}",
            labels={"Valor": "R$", "Categoria_Label": ""},
            color="Valor", 
            color_continuous_scale="Greens",
            text="Texto_Valor"
        )
        fig_inv_bar.update_layout(
            plotly_theme["layout"], 
            coloraxis_showscale=False, 
            height=460,
            margin=dict(l=110, r=40, t=40, b=30)
        )
        fig_inv_bar.update_xaxes(tickprefix="R$ ", tickformat="~s")
        fig_inv_bar.update_traces(textposition="outside", textfont=dict(size=11, color="#10B981"))
        st.plotly_chart(fig_inv_bar, use_container_width=True, config=plotly_config)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_carteira_investimentos = df_carteira_investimentos.sort_values("Mês")
        fig_inv_line = px.line(
            df_carteira_investimentos,
            x="Mês", y="Valor", color="Categoria",
            title="📈 Curva de Crescimento por Ativo",
            markers=True,
            labels={"Valor": "R$", "Categoria": ""},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_inv_line.update_layout(
            plotly_theme["layout"], 
            height=580,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            ),
            margin=dict(l=50, r=20, t=40, b=180)
        )
        fig_inv_line.update_yaxes(tickprefix="R$ ", tickformat="~s")
        st.plotly_chart(fig_inv_line, use_container_width=True, config=plotly_config)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 9. VARIAÇÃO DE RENDIMENTO MÊS A MÊS
        # -------------------------------------------------------------
        st.markdown("<a id='lucro-prejuizo'></a>", unsafe_allow_html=True)
        st.markdown("### 💵 Lucro / Prejuízo dos Investimentos")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Comparativo da evolução patrimonial entre meses consecutivos</p>", unsafe_allow_html=True)

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
                    "Período": f"{str(m_ant).upper()} ➔ {str(m_atual).upper()}",
                    "Mês Anterior": f"R$ {val_ant:,.2f}",
                    "Mês Atual": f"R$ {val_atual:,.2f}",
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
            st.info("Selecione pelo menos 2 meses no filtro para comparar a variação.")

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 10. RAIO-X INDIVIDUAL
        # -------------------------------------------------------------
        st.markdown("<a id='raio-x'></a>", unsafe_allow_html=True)
        st.markdown("### 🔍 Raio-X & Análise Individual")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Selecione um ativo para analisar seu histórico de rendimento</p>", unsafe_allow_html=True)

        ativos_encerrados = [
            "C6 - CDB C6 Prefixado 1 ano (15,7% a.a.) Venc em 03/06/26",
            "Nubank Caixinha 115% CDI (líquido)",
            "Nubank LCA - Banco BV - Venc: 13/03/2026 liquido",
            "C6 - Carbon Ouro"
        ]

        todos_ativos = df_carteira_investimentos["Categoria"].unique()
        lista_ativos_raiox = sorted([a for a in todos_ativos if a not in ativos_encerrados])

        if lista_ativos_raiox:
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
                st.markdown(f"##### 📑 Histórico de Crescimento: `{ativo_escolhido}`")
                
                registros_ativo_m = []
                for idx in range(len(df_ativo_validos)):
                    m_curr = str(df_ativo_validos.loc[idx, "Mês"]).upper()
                    val_curr = df_ativo_validos.loc[idx, "Valor"]
                    
                    if idx == 0:
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
                        "Variação (R$)": txt_var_abs,
                        "Variação (%)": txt_var_pct
                    })

                df_ativo_tab = pd.DataFrame(registros_ativo_m)
                st.dataframe(df_ativo_tab, use_container_width=True, hide_index=True)
                st.markdown("<br>", unsafe_allow_html=True)

            fig_ativo_single = px.area(
                df_ativo_filtro,
                x="Mês", y="Valor",
                title=f"📈 Evolução: {ativo_escolhido}",
                markers=True,
                color_discrete_sequence=["#8B5CF6"],
                labels={"Valor": "R$", "Mês": ""}
            )
            fig_ativo_single.update_layout(
                plotly_theme["layout"], 
                height=350,
                margin=dict(l=50, r=20, t=30, b=20)
            )
            fig_ativo_single.update_yaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_ativo_single, use_container_width=True, config=plotly_config)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 11. DIVERSIFICAÇÃO & ALOCAÇÃO POR CLASSE DE ATIVO
        # -------------------------------------------------------------
        st.markdown("<a id='diversificacao'></a>", unsafe_allow_html=True)
        st.markdown("### 🍩 Diversificação por Classe de Ativo")
        st.markdown(f"<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Alocação em <b>{ultimo_mes.upper()} / {ano_selecionado}</b></p>", unsafe_allow_html=True)

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
                title=f"Distribuição ({ultimo_mes.upper()})",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_donut.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Saldo: R$ %{value:,.2f}<br>Participação: %{percent:.2f}%"
            )
            fig_donut.update_layout(
                plotly_theme["layout"],
                height=380,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_donut, use_container_width=True, config=plotly_config)

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
