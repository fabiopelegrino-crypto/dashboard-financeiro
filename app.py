import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests
import yfinance as yf

# -------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM (CSS)
# -------------------------------------------------------------
st.set_page_config(
    page_title="Finances AI | Dashboard Financeiro", 
    page_icon="💳", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS e Proteção de Indexação (noindex, nofollow)
custom_css = """
<meta name="robots" content="noindex, nofollow">
<style>
    .stApp {
        background-color: #0E1117;
        font-family: 'Inter', sans-serif;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1A1F2C 0%, #141824 100%);
        border: 1px solid #2E3548;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 15px;
    }
    .kpi-card:hover {
        border-color: #3B82F6;
        transform: translateY(-2px);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .kpi-subtext {
        font-size: 0.75rem;
        color: #6B7280;
        margin-top: 6px;
    }
    .val-green { color: #10B981; }
    .val-red { color: #EF4444; }
    .val-blue { color: #3B82F6; }
    .val-purple { color: #8B5CF6; }

    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------
# 1.1 MECANISMO DE LOGIN, BLOQUEIO DE FORÇA BRUTA & LOGOUT
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

    def password_entered():
        try:
            target_password = st.secrets["PASSWORD"]
        except Exception:
            target_password = "123456"

        if st.session_state["password_input"] == target_password:
            st.session_state["password_correct"] = True
            st.session_state["login_attempts"] = 0
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False
            st.session_state["login_attempts"] += 1
            if st.session_state["login_attempts"] >= MAX_TENTATIVAS:
                st.session_state["lockout_time"] = time.time()
            else:
                tentativas_restantes = MAX_TENTATIVAS - st.session_state["login_attempts"]
                st.toast(f"⚠️ Senha incorreta! Tentativas restantes: {tentativas_restantes}", icon="🚨")

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; color: #3B82F6;'>🔐 Acesso Restrito ao Painel</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "Digite sua senha de acesso:", 
                type="password", 
                on_change=password_entered, 
                key="password_input"
            )
            if "password_correct" in st.session_state and not st.session_state["password_correct"] and "password_input" not in st.session_state:
                tentativas_restantes = MAX_TENTATIVAS - st.session_state["login_attempts"]
                if tentativas_restantes > 0:
                    st.error(f"😕 Senha incorreta. Tentativas restantes: {tentativas_restantes}")
        return False
    return True

if not check_password():
    st.stop()

# -------------------------------------------------------------
# 1.2 CONSULTA DA API DO BANCO CENTRAL & COTAÇÃO DO MXRF11
# -------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_market_indicators():
    """Busca Selic, CDI e cotação atual do MXRF11 na B3."""
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
        price = ticker.fast_info.get("lastPrice") or ticker.history(period="1d")["Close"].iloc[-1]
        mxrf_str = f"R$ {float(price):.2f}"
    except Exception:
        mxrf_str = "R$ 9.45"

    return selic_str, cdi_str, mxrf_str

selic_str, cdi_str, mxrf11_price_str = fetch_market_indicators()

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

# 🟢 Ordem cronológica ajustada: 2025, 2026, 2027 (com 2026 como padrão selecionado)
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
            st.caption("🏢 Cotação MXRF11 (B3)")
            st.markdown(f"**{mxrf11_price_str}**")
        with col_m4:
            st.caption("📅 Mês de Referência")
            st.markdown(f"**{ultimo_mes.upper()} / {ano_selecionado}**")

        st.markdown("<hr style='border-color: #1F2937; margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 6. CARDS (KPIs)
        # -------------------------------------------------------------
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Receita Total</div>
                <div class="kpi-value val-green">R$ {total_rec:,.2f}</div>
                <div class="kpi-subtext">Salário & Outras Entradas</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Despesas Operacionais</div>
                <div class="kpi-value val-red">R$ {total_desp:,.2f}</div>
                <div class="kpi-subtext">Contas fixas, cartões e consumo</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Saldo Investido (Mês)</div>
                <div class="kpi-value val-blue">R$ {total_investido_mes:,.2f}</div>
                <div class="kpi-subtext">Aportes destinados a investimentos</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Carteira Total ({ultimo_mes.upper()})</div>
                <div class="kpi-value val-purple">R$ {patrimonio_total_ultimo_mes:,.2f}</div>
                <div class="kpi-subtext">Patrimônio acumulado nos ativos</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        plotly_theme = {
            "layout": {
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#E5E7EB", "family": "Inter"},
                "xaxis": {"gridcolor": "#1F2937"},
                "yaxis": {"gridcolor": "#1F2937"}
            }
        }

        # -------------------------------------------------------------
        # 7. FLUXO DE CAIXA
        # -------------------------------------------------------------
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
            st.plotly_chart(fig_evo, use_container_width=True)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 8. INVESTIMENTOS
        # -------------------------------------------------------------
        st.markdown("### 📊 Posição & Evolução Patrimonial dos Investimentos")
        st.markdown("<p style='color: #6B7280; font-size: 0.85rem; margin-bottom: 20px;'>Acompanhamento individual de cada ativo com linha de Total na base do gráfico</p>", unsafe_allow_html=True)
        
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
            height=480,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=20, r=20, t=50, b=100)
        )
        st.plotly_chart(fig_inv_line, use_container_width=True)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 9. VARIAÇÃO DE RENDIMENTO MÊS A MÊS
        # -------------------------------------------------------------
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
        # 10. RAIO-X INDIVIDUAL (COM EVOLUÇÃO MÊS A MÊS DETALHADA)
        # -------------------------------------------------------------
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
            st.plotly_chart(fig_ativo_single, use_container_width=True)

        st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 11. DIVERSIFICAÇÃO & ALOCAÇÃO POR CLASSE DE ATIVO
        # -------------------------------------------------------------
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
                hovertemplate="<b>%{label}</b><br>Saldo: R$ %{value:,.2f}<br>Participação: %{percent}"
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
