import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path




st.set_page_config(
    page_title="FIDC - Estrutura de Cotas",
    layout="wide"
)


st.markdown(
    """
    <style>
    /* Ajuste do título do card (Label) */
    div[data-testid="stMetricLabel"] > label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #555;
    }
    
    /* Ajuste do valor do card (Número) */
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important; /* Reduzi levemente para caber melhor */
        font-weight: 700;
        word-wrap: break-word;       /* Permite quebrar linha se for muito longo */
        white-space: normal !important; /* OBRIGA a quebra de linha e impede o corte (...) */
        line-height: 1.2;
    }

    /* Estilo do Card (Borda e Sombra) */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Cabeçalhos de Seção */
    .section-header {
        background: linear-gradient(90deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 10px 15px;
        border-radius: 6px;
        margin: 20px 0 15px 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

"""LOGO_PATH = Path(r"C:\VS Code Projects\Risco_FIDC\Risco_FIDC\logo_rios_3d_redondo.png")
col_logo, col_title = st.columns([0.12, 0.88])
with col_logo:
    st.image(str(LOGO_PATH), width=350)
with col_title:
    st.title("FIDC - Estrutura de Cotas e P&L Diário")
st.markdown(
    """
    Modelo econômico-financeiro para analisar a estrutura de cotas de um FIDC, 
    o custo diário das classes, o retorno residual da Cota Júnior, a PDD e o colchão de subordinação.
    """
)"""

# -------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------------------------
def anual_to_diario(rate_aa, dias_uteis=252):
    return (1 + rate_aa) ** (1 / dias_uteis) - 1

def mensal_to_diario(rate_am, dias_uteis_ano=252):
    rate_aa = (1 + rate_am) ** 12 - 1
    return anual_to_diario(rate_aa, dias_uteis=dias_uteis_ano)

def format_pct(x):
    return f"{x*100:,.2f} %"

def format_brl(x):
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# -------------------------------------------------------------------
# SIDEBAR – PARÂMETROS
# -------------------------------------------------------------------
st.sidebar.header("⚙️ Parâmetros do FIDC")

# >>> Campo para você anotar melhorias / ideias:

st.sidebar.markdown("---")

# Estrutura de cotas – agora valores diretos, sem multiplicador
valor_junior = st.sidebar.number_input(
    "Valor da Cota Júnior (R$)",
    min_value=0.0,
    value=10_000_000.0,
    step=500_000.0,
    format="%.2f"
)
valor_mezz = st.sidebar.number_input(
    "Valor da Cota Mezzanino (R$)",
    min_value=0.0,
    value=10_000_000.0,
    step=500_000.0,
    format="%.2f"
)
valor_senior = st.sidebar.number_input(
    "Valor da Cota Sênior (R$)",
    min_value=0.0,
    value=10_000_000.0,
    step=500_000.0,
    format="%.2f"
)

pl_total = valor_junior + valor_mezz + valor_senior

# Índice de subordinação mínimo da Júnior
st.sidebar.markdown("---")
sub_min_pct = st.sidebar.number_input(
    "Índice mínimo de subordinação da Cota Júnior (% do PL)",
    min_value=0.0,
    max_value=100.0,
    value=20.0,
    step=1.0,
    format="%.2f"
)
sub_min = sub_min_pct / 100.0

st.sidebar.markdown("---")

# Taxas de mercado e carteira
cdi_aa_pct = st.sidebar.number_input(
    "CDI (% a.a.)",
    min_value=0.0,
    value=15.0,
    step=0.25,
    format="%.2f"
)
cdi_aa = cdi_aa_pct / 100.0
cdi_diario = anual_to_diario(cdi_aa)
cdi_am = (1 + cdi_aa) ** (1/12) - 1

taxa_carteira_am_pct = st.sidebar.number_input(
    "Taxa da carteira (% a.m. sobre recebíveis)",
    min_value=0.0,
    value=2.35,
    step=0.05,
    format="%.2f"
)
taxa_carteira_am = taxa_carteira_am_pct / 100.0
taxa_carteira_diaria = mensal_to_diario(taxa_carteira_am)

pct_recebiveis = st.sidebar.slider(
    "Percentual do PL em recebíveis (%)",
    min_value=0,
    max_value=100,
    value=80,
    step=1
) / 100.0

st.sidebar.markdown("---")

# Spreads das cotas
spread_senior_aa_pct = st.sidebar.number_input(
    "Spread da Cota Sênior (% a.a. sobre CDI)",
    min_value=0.0,
    value=5.0,
    step=0.25,
    format="%.2f"
)
spread_mezz_aa_pct = st.sidebar.number_input(
    "Spread da Cota Mezzanino (% a.a. sobre CDI)",
    min_value=0.0,
    value=6.5,
    step=0.25,
    format="%.2f"
)
spread_senior_aa = spread_senior_aa_pct / 100.0
spread_mezz_aa = spread_mezz_aa_pct / 100.0

taxa_senior_aa = cdi_aa + spread_senior_aa
taxa_mezz_aa = cdi_aa + spread_mezz_aa

taxa_senior_diaria = anual_to_diario(taxa_senior_aa)
taxa_mezz_diaria = anual_to_diario(taxa_mezz_aa)

st.sidebar.markdown("---")

# Taxas de administração, gestão e outros custos
taxa_adm_aa_pct = st.sidebar.number_input(
    "Taxa de Administração (% a.a. sobre PL)",
    min_value=0.0,
    value=0.3,
    step=0.05,
    format="%.2f"
)
taxa_gestao_aa_pct = st.sidebar.number_input(
    "Taxa de Gestão (% a.a. sobre PL)",
    min_value=0.0,
    value=0.5,
    step=0.05,
    format="%.2f"
)
taxa_adm_aa = taxa_adm_aa_pct / 100.0
taxa_gestao_aa = taxa_gestao_aa_pct / 100.0

taxa_adm_diaria = anual_to_diario(taxa_adm_aa)
taxa_gestao_diaria = anual_to_diario(taxa_gestao_aa)

outros_custos_mensais = st.sidebar.number_input(
    "Outros custos fixos (R$ / mês)",
    min_value=0.0,
    value=100_000.0,
    step=1_000.0,
    format="%.2f"
)
# Aproximação: 12 meses ~ 252 dias úteis
custo_outros_dia = outros_custos_mensais * 12.0 / 252.0

outros_receitas_mensais = st.sidebar.number_input(
    "Outras receitas (R$ / mês)",
    min_value=0.0,
    value=150_000.0,
    step=1_000.0,
    format="%.2f"
)
receita_outros_dia = outros_receitas_mensais * 12.0 / 252.0

st.sidebar.markdown("---")

# -------------------------------------------------------------------
# SIDEBAR — RISCO & PROVISÃO (PDD) COM CÁLCULO IMEDIATO
# -------------------------------------------------------------------
st.sidebar.header("📌 Risco & Provisão (PDD)")
st.sidebar.caption(
    "Preencha o % da carteira em cada faixa e a % de provisão. "
    "Os pesos são reescalados automaticamente para 100%."
)

st.sidebar.caption("Valores iniciais seguem a política interna: bucket 0–30 com 95% da carteira, demais 0,5% e último 1,5%.")

st.sidebar.markdown("**0–30 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_0_30 = st.number_input("% carteira", 0.0, 1000.0, 95.0, 0.1, key="pct_0_30")
with c2:
    prov_0_30 = st.number_input("% provisão", 0.0, 100.0, 0.0, 0.5, key="prov_0_30")

st.sidebar.markdown("**31–60 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_31_60 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_31_60")
with c2:
    prov_31_60 = st.number_input("% provisão", 0.0, 100.0, 5.0, 0.5, key="prov_31_60")

st.sidebar.markdown("**61–90 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_61_90 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_61_90")
with c2:
    prov_61_90 = st.number_input("% provisão", 0.0, 100.0, 15.0, 0.5, key="prov_61_90")

st.sidebar.markdown("**91–120 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_91_120 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_91_120")
with c2:
    prov_91_120 = st.number_input("% provisão", 0.0, 100.0, 20.0, 0.5, key="prov_91_120")

st.sidebar.markdown("**121–150 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_121_150 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_121_150")
with c2:
    prov_121_150 = st.number_input("% provisão", 0.0, 100.0, 40.0, 0.5, key="prov_121_150")

st.sidebar.markdown("**151–180 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_151_180 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_151_180")
with c2:
    prov_151_180 = st.number_input("% provisão", 0.0, 100.0, 50.0, 0.5, key="prov_151_180")

st.sidebar.markdown("**181–240 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_181_240 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_181_240")
with c2:
    prov_181_240 = st.number_input("% provisão", 0.0, 100.0, 70.0, 0.5, key="prov_181_240")

st.sidebar.markdown("**241–300 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_241_300 = st.number_input("% carteira", 0.0, 1000.0, 0.5, 0.1, key="pct_241_300")
with c2:
    prov_241_300 = st.number_input("% provisão", 0.0, 100.0, 85.0, 0.5, key="prov_241_300")

st.sidebar.markdown("**> 300 dias**")
c1, c2 = st.sidebar.columns(2)
with c1:
    pct_300p = st.number_input("% carteira", 0.0, 1000.0, 1.5, 0.1, key="pct_300p")
with c2:
    prov_300p = st.number_input("% provisão", 0.0, 100.0, 100.0, 0.5, key="prov_300p")

# --- CÁLCULO E NORMALIZAÇÃO ---
buckets_raw = np.array([
    pct_0_30, pct_31_60, pct_61_90, pct_91_120, pct_121_150,
    pct_151_180, pct_181_240, pct_241_300, pct_300p
])
provs_raw = np.array([
    prov_0_30, prov_31_60, prov_61_90, prov_91_120, prov_121_150,
    prov_151_180, prov_181_240, prov_241_300, prov_300p
])

total_raw = buckets_raw.sum()

if total_raw == 0:
    buckets_pct_norm = np.zeros_like(buckets_raw)
    pdd_ponderada_view = 0.0
    st.sidebar.warning("⚠️ Total da carteira = 0%.")
else:
    buckets_pct_norm = buckets_raw / total_raw
    # Cálculo da PDD Ponderada (%)
    pdd_ponderada_view = np.sum(buckets_pct_norm * provs_raw)

    if abs(total_raw - 100) > 0.01:
        st.sidebar.caption(f"Total informado: {total_raw:.1f}%. Normalizado para 100%.")

# --- DISPLAY DO RESULTADO NA SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.metric(
    "📉 PDD Ponderada do Portfólio",
    f"{pdd_ponderada_view:,.2f}%",
    help="Média ponderada das provisões aplicada à distribuição atual da carteira."
)

st.sidebar.markdown("---")
incluir_pdd = st.sidebar.checkbox(
    "Incluir PDD no P&L e DRE", value=True
)

# -------------------------------------------------------------------
# CÁLCULOS PRINCIPAIS – CENÁRIO ATUAL
# -------------------------------------------------------------------
# Alocação em recebíveis e caixa
valor_recebiveis = pl_total * pct_recebiveis
valor_caixa      = pl_total - valor_recebiveis

# Receitas com a taxa atual (para P&L e DRE)
receita_carteira_dia     = valor_recebiveis * taxa_carteira_diaria
receita_caixa_dia        = valor_caixa      * cdi_diario
receita_financeira_dia   = receita_carteira_dia + receita_caixa_dia
receita_total_dia        = receita_financeira_dia + receita_outros_dia

# Custos das cotas
custo_senior_dia = valor_senior * taxa_senior_diaria
custo_mezz_dia   = valor_mezz   * taxa_mezz_diaria

# Taxas adm / gestão
custo_adm_dia    = pl_total * taxa_adm_diaria
custo_gestao_dia = pl_total * taxa_gestao_diaria


# --- PDD (perda esperada anual, diária e impacto em taxa) ---

# taxas de provisão por bucket em DECIMAL (ex: 5% -> 0.05)
prov_rates = np.array([
    prov_0_30, prov_31_60, prov_61_90, prov_91_120, prov_121_150,
    prov_151_180, prov_181_240, prov_241_300, prov_300p
]) / 100.0

# taxa_perda_esperada: % a.a. de perda esperada SOBRE OS RECEBÍVEIS (decimal)
# ex.: 0.0292 = 2,92% a.a.
taxa_perda_esperada = float(np.sum(buckets_pct_norm * prov_rates))

# converte para taxa diária aproximada
taxa_perda_esp_diaria = taxa_perda_esperada / 252.0

# converte para taxa MENSAL equivalente (sobre os recebíveis)
taxa_perda_esp_am = (1 + taxa_perda_esp_diaria) ** 21 - 1

# PDD "econômica" ANUAL em R$ (sempre existe, para risco)
pdd_base = valor_recebiveis * taxa_perda_esperada

# PDD que ENTRA no P&L / DRE (controlada pelo checkbox)
pdd_ano = pdd_base if incluir_pdd else 0.0
pdd_dia = pdd_ano / 252.0


def taxa_carteira_necessaria_diaria(target_roe_jr_pct_aa: float) -> float:
    """
    Retorna a taxa DIÁRIA necessária nos RECEBÍVEIS (r_carteira_dia)
    para que a Cota Júnior tenha ROE alvo 'target_roe_jr_pct_aa' (% a.a.),
    usando retorno linear.

    Equação base (por dia):

        Resultado_Júnior_dia(r) = R * r
                                  + receita_caixa_dia
                                  + receita_outros_dia
                                  - custos_fixos_dia
                                  - pdd_dia

    Onde:
      - R = valor_recebiveis
      - custos_fixos_dia = senior + mezz + adm + gest + outros
      - receita_caixa_dia = valor_caixa * cdi_diario
      - pdd_dia = PDD econômica diária
    """

    if valor_recebiveis <= 0 or valor_junior <= 0:
        return 0.0

    # ROE alvo em decimal (ex.: 46% -> 0.46)
    roe_alvo = target_roe_jr_pct_aa / 100.0

    # Resultado diário NECESSÁRIO para a Júnior (linear)
    resultado_jr_ano_alvo = roe_alvo * valor_junior
    resultado_jr_dia_alvo = resultado_jr_ano_alvo / 252.0

    # Custos fixos por dia (não dependem da taxa da carteira)
    custos_fixos_dia = (
        custo_senior_dia
        + custo_mezz_dia
        + custo_adm_dia
        + custo_gestao_dia
        + custo_outros_dia
    )

    # Receitas FIXAS por dia (AGORA inclui o CDI do caixa)
    receitas_fixas_totais_dia = receita_caixa_dia + receita_outros_dia

    # K = receitas_fixas - custos_fixos - pdd_dia
    K = receitas_fixas_totais_dia - custos_fixos_dia - pdd_dia

    # Equação:
    #   Resultado_jr_dia_alvo = R * r + K
    # => R * r = Resultado_jr_dia_alvo - K
    # => r     = (Resultado_jr_dia_alvo - K) / R
    numerador = resultado_jr_dia_alvo - K
    r_dia = numerador / valor_recebiveis

    # Se por algum motivo ficar negativo (meta muito baixa), força 0%
    return max(0.0, r_dia)



# ----------------------------
# TAXA MÍNIMA DA CARTEIRA (CARD)
# ----------------------------

dias_uteis_ano = 252
dias_uteis_mes = dias_uteis_ano / 12  # ~21 dias úteis (aprox.)

# 1) Custos FIXOS por dia (independentes da taxa da carteira)
custos_fixos_dia = (
    custo_senior_dia
    + custo_mezz_dia
    + custo_adm_dia
    + custo_gestao_dia
    + custo_outros_dia
)

# 2) Receitas FIXAS consideradas para o break-even:
#    **APENAS outras receitas** (não entra o rendimento do caixa a CDI).
receitas_fixas_break_even_dia = receita_outros_dia

if valor_recebiveis > 0:
    # Break-even da Júnior (resultado_junior_dia = 0) em regime linear:
    #
    #   R * r_min + receitas_fixas_break_even_dia = custos_fixos_dia + pdd_dia
    #
    # => R * r_min = custos_fixos_dia + pdd_dia - receitas_fixas_break_even_dia
    # => r_min     = (custos_fixos_dia + pdd_dia - receitas_fixas_break_even_dia) / R
    numerador_dia = custos_fixos_dia + pdd_dia - receitas_fixas_break_even_dia

    taxa_carteira_min_diaria = numerador_dia / valor_recebiveis
    taxa_carteira_min_diaria = max(0.0, taxa_carteira_min_diaria)

    # Regime linear: diária * nº de dias úteis do mês
    taxa_carteira_min_am = taxa_carteira_min_diaria * dias_uteis_mes
else:
    taxa_carteira_min_diaria = 0.0
    taxa_carteira_min_am = 0.0



# Resultado diário
resultado_liquido_dia = (
    receita_total_dia
    - custo_senior_dia
    - custo_mezz_dia
    - custo_adm_dia
    - custo_gestao_dia
    - pdd_dia
    - custo_outros_dia
)

resultado_junior_dia = resultado_liquido_dia
resultado_junior_mes = resultado_junior_dia * dias_uteis_mes
resultado_junior_ano = resultado_junior_dia * dias_uteis_ano

if valor_junior > 0:
    # Retornos lineares da Cota Júnior
    retorno_diario_junior      = resultado_junior_dia  / valor_junior
    retorno_mensal_junior      = resultado_junior_mes  / valor_junior
    retorno_anualizado_junior  = resultado_junior_ano  / valor_junior
else:
    retorno_diario_junior      = 0.0
    retorno_mensal_junior      = 0.0
    retorno_anualizado_junior  = 0.0



retorno_anualizado_senior = taxa_senior_aa
retorno_mensal_senior     = taxa_senior_aa / 12.0
retorno_diario_senior     = taxa_senior_aa / 252.0

retorno_anualizado_mezz = taxa_mezz_aa
retorno_mensal_mezz     = taxa_mezz_aa / 12.0
retorno_diario_mezz     = taxa_mezz_aa / 252.0



# ------------------------------
# Projeção anual / mensal (DRE)
# ------------------------------
dias_uteis_ano = 252
meses_ano = 12
dias_uteis_mes = dias_uteis_ano / meses_ano  # ~21 dias úteis/mês

# Receitas (anual)
receita_carteira_ano       = receita_carteira_dia       * dias_uteis_ano
receita_caixa_ano          = receita_caixa_dia          * dias_uteis_ano
receita_financeira_ano     = receita_financeira_dia     * dias_uteis_ano
receita_outros_ano         = receita_outros_dia         * dias_uteis_ano
receita_total_ano          = receita_total_dia          * dias_uteis_ano

# Custos das cotas (anual)
custo_senior_ano = custo_senior_dia * dias_uteis_ano
custo_mezz_ano   = custo_mezz_dia   * dias_uteis_ano

# Taxas (anual)
custo_adm_ano    = custo_adm_dia    * dias_uteis_ano
custo_gestao_ano = custo_gestao_dia * dias_uteis_ano


# Outros custos (anual)
custo_outros_ano = custo_outros_dia * dias_uteis_ano

# Resultado (anual)
resultado_liquido_ano = resultado_liquido_dia * dias_uteis_ano
resultado_junior_ano  = resultado_junior_dia  * dias_uteis_ano

# Resultado (mensal)
receita_carteira_mes       = receita_carteira_dia       * dias_uteis_mes
receita_caixa_mes          = receita_caixa_dia          * dias_uteis_mes
receita_financeira_mes     = receita_financeira_dia     * dias_uteis_mes
receita_outros_mes         = receita_outros_dia         * dias_uteis_mes
receita_total_mes          = receita_total_dia          * dias_uteis_mes

custo_senior_mes = custo_senior_dia * dias_uteis_mes
custo_mezz_mes   = custo_mezz_dia   * dias_uteis_mes
custo_adm_mes    = custo_adm_dia    * dias_uteis_mes
custo_gestao_mes = custo_gestao_dia * dias_uteis_mes
pdd_mes          = pdd_dia          * dias_uteis_mes
custo_outros_mes = custo_outros_dia * dias_uteis_mes

resultado_liquido_mes = resultado_liquido_dia * dias_uteis_mes
resultado_junior_mes  = resultado_junior_dia  * dias_uteis_mes

# Subordinação: perda limite mantendo índice mínimo Júnior / PL ≥ sub_min
if pl_total > 0 and sub_min < 1:
    if valor_junior / pl_total <= sub_min:
        perda_lim_sub = 0.0
    else:
        # L = (J - s*P) / (1 - s)
        perda_lim_sub = (valor_junior - sub_min * pl_total) / (1 - sub_min)
else:
    perda_lim_sub = 0.0

perda_lim_sub_pct_recebiveis = (
    perda_lim_sub / valor_recebiveis if valor_recebiveis > 0 else 0.0
)

# -------------------------------------------------------------------
# TABS
# -------------------------------------------------------------------
tab_estrutura, tab_risco, tab_alvo, tab_dre, tab_rating = st.tabs([
    "📊 Estrutura & P&L",
    "🛡️ Gestão de Risco & Stress Test", # Aba unificada
    "🎯 Taxa de Juros & Simulações",
    "📑 DRE Projetado",
    "⭐ Modelo de Rating"
])

# -------------------------------------------------------------------
# ABA 1 – ESTRUTURA & P&L (Ajustado: Card de Captação + Waterfall Mensal)
# -------------------------------------------------------------------
with tab_estrutura:
    st.markdown('<div class="section-header">🏗️ Estrutura de Capital</div>', unsafe_allow_html=True)

    # 1. Preparar os dados na ordem correta (Sênior -> Mezz -> Júnior)
    dados_estrutura = [
        ["Sênior", valor_senior, valor_senior / pl_total if pl_total > 0 else 0, "#D1E7DD"], # Verde claro
        ["Mezzanino", valor_mezz, valor_mezz / pl_total if pl_total > 0 else 0, "#FFF3CD"],  # Amarelo claro
        ["Júnior (Subordinada)", valor_junior, valor_junior / pl_total if pl_total > 0 else 0, "#F8D7DA"], # Vermelho claro
    ]
    
    # Adicionando linha de total
    dados_estrutura.append(["TOTAL", pl_total, 1.0, "#E2E3E5"]) # Cinza

    df_struct = pd.DataFrame(dados_estrutura, columns=["Classe", "Valor", "Perc", "Color"])

    # Layout: Tabela Bonita + Gráfico Visual da Pilha
    c_tab, c_viz = st.columns([1.5, 1])

    with c_tab:
        # Tabela estilizada com Plotly
        fig_table = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Classe</b>', '<b>Valor (R$)</b>', '<b>Participação (%)</b>'],
                fill_color='#2c3e50',
                align='left',
                font=dict(color='white', size=14),
                height=35
            ),
            cells=dict(
                values=[
                    df_struct.Classe, 
                    [format_brl(v) for v in df_struct.Valor], 
                    [f"{p*100:.2f}%" for p in df_struct.Perc]
                ],
                fill_color=[df_struct.Color],
                align='left',
                font=dict(color='black', size=13),
                height=30
            )
        )])
        
        fig_table.update_layout(
            margin=dict(l=0, r=0, t=50, b=0), 
            height=200
        )
        st.plotly_chart(fig_table, use_container_width=True)

    with c_viz:
        # Gráfico de Pilha (Stacked Bar)
        fig_stack = go.Figure()
        
        fig_stack.add_trace(go.Bar(
            name='Júnior', x=['FIDC'], y=[valor_junior], 
            marker_color='#e74c3c', text=f"{df_struct.iloc[2]['Perc']*100:.0f}%", textposition='auto'
        ))
        fig_stack.add_trace(go.Bar(
            name='Mezzanino', x=['FIDC'], y=[valor_mezz], 
            marker_color='#f1c40f', text=f"{df_struct.iloc[1]['Perc']*100:.0f}%", textposition='auto'
        ))
        fig_stack.add_trace(go.Bar(
            name='Sênior', x=['FIDC'], y=[valor_senior], 
            marker_color='#27ae60', text=f"{df_struct.iloc[0]['Perc']*100:.0f}%", textposition='auto'
        ))

        # LINHA TRACEJADA DO MÍNIMO DE SUBORDINAÇÃO
        subordinacao_minima_valor = pl_total * sub_min
        fig_stack.add_shape(
            type="line", x0=-0.4, x1=0.4,
            y0=subordinacao_minima_valor, y1=subordinacao_minima_valor,
            line=dict(color="white", width=2, dash="dash")
        )
        
        fig_stack.add_annotation(
            x=0.5, y=-0.15, xref="paper", yref="paper",
            text=f"Mín. Subordinação ({sub_min_pct:.1f}%)",
            showarrow=False, font=dict(size=11, color="red"), align="center"
        )

        fig_stack.update_layout(
            barmode='stack',
            showlegend=True,
            margin=dict(l=20, r=20, t=50, b=20), 
            height=280,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor='center')
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    st.markdown("---")
    
    # CARDS DE INFORMAÇÕES FINANCEIRAS
    st.markdown('<div class="section-header">💰 Informações Financeiras</div>', unsafe_allow_html=True)
    
    min_recebiveis_regra = pl_total * 0.67
    
    # --- TAXAS MÉDIAS DO PL ---
    
    # 1) Taxa média bruta do PL (antes da PDD)
    taxa_media_pl_am = (
        pct_recebiveis * taxa_carteira_am
        + (1.0 - pct_recebiveis) * cdi_am
    )
    
    # 2) Impacto da PDD sobre o PL:
    #    PDD só incide sobre os recebíveis, então:
    #    impacto no PL = % do PL em recebíveis * taxa de perda esperada da carteira
    if incluir_pdd:
        impacto_pdd_pl_am = pct_recebiveis * taxa_perda_esp_am
    else:
        impacto_pdd_pl_am = 0.0
    
    # 3) Taxa média líquida de PDD
    taxa_media_pl_am_liq = taxa_media_pl_am - impacto_pdd_pl_am
    
    
    # ----------------------------
    # TAXA MÍNIMA DA CARTEIRA (CARD)
    # ----------------------------
    
    dias_uteis_ano = 252
    dias_uteis_mes = dias_uteis_ano / 12  # ~21 dias úteis
    
    # 1) Custos FIXOS por dia (não dependem da taxa da carteira)
    custos_fixos_dia = (
        custo_senior_dia
        + custo_mezz_dia
        + custo_adm_dia
        + custo_gestao_dia
        + custo_outros_dia
    )
    
    # 2) Receitas FIXAS por dia consideradas no break-even:
    #    SOMENTE outras receitas (sem caixa a CDI)
    receitas_fixas_dia = receita_outros_dia
    
    if valor_recebiveis > 0:
        # 0 = R * r_min + receitas_fixas_dia - (custos_fixos_dia + pdd_dia)
        # -> r_min = (custos_fixos_dia + pdd_dia - receitas_fixas_dia) / R
        numerador_dia = custos_fixos_dia + pdd_dia - receitas_fixas_dia
    
        taxa_carteira_min_diaria = numerador_dia / valor_recebiveis
        taxa_carteira_min_diaria = max(0.0, taxa_carteira_min_diaria)
    
        # aqui mantemos a conversão linear para mensal
        taxa_carteira_min_am = taxa_carteira_min_diaria * dias_uteis_mes
    else:
        taxa_carteira_min_diaria = 0.0
        taxa_carteira_min_am = 0.0
    
        
    
    # --- CÁLCULO DE CAPTAÇÃO DISPONÍVEL ---
    # Quanto o PL Total pode crescer mantendo a Júnior atual fixa, até bater no Sub_Min?
    # PL_Max = Valor_Junior / Sub_Min
    # Captação_Disp = PL_Max - PL_Atual
    if sub_min > 0:
        pl_max_teorico = valor_junior / sub_min
        captacao_disponivel = pl_max_teorico - pl_total
    else:
        captacao_disponivel = 0.0

    
        # AGORA SÃO 6 COLUNAS
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("Alocação em Recebíveis", format_brl(valor_recebiveis), f"{pct_recebiveis*100:.0f}% do PL")
    col2.metric("Caixa (a CDI)", format_brl(valor_caixa), f"{(1 - pct_recebiveis)*100:.0f}% do PL")
    col3.metric("Mínimo em Recebíveis", format_brl(min_recebiveis_regra), "67% do PL", delta_color="inverse")

    col5.metric(
        "Taxa média do PL (a.m.)",
        f"{taxa_media_pl_am*100:.2f}%",
        delta=f"Líq. de PDD: {taxa_media_pl_am_liq*100:.2f}%", 
        delta_color="off", 
        help="A taxa principal é bruta. O valor menor abaixo já desconta o custo da PDD mensal."
    )
    
    # CARD 5: Captação disponível (como já estava)
    lbl_cap = "Captação Disp. (Sênior/Mezz)"
    val_cap = format_brl(captacao_disponivel)
    if captacao_disponivel >= 0:
        delta_cap = "Espaço para crescer"
        cor_cap = "normal"
    else:
        delta_cap = "Desenquadrado"
        cor_cap = "inverse"
    col4.metric(
        lbl_cap, 
        val_cap, 
        delta=delta_cap, 
        delta_color=cor_cap,
        help="Quanto o fundo pode captar de cotas Sênior/Mezzanino mantendo a Subordinação Mínima atual."
    )

    # CARD 6: Taxa mínima da carteira para pagar TODOS os custos
    taxa_min_am_pct = taxa_carteira_min_am * 100.0
    delta_taxa_min = taxa_min_am_pct - taxa_carteira_am_pct

    col6.metric(
        "Taxa mín. Carteira (break-even)",
        f"{taxa_min_am_pct:.4f}% a.m.",
        delta=f"{(taxa_carteira_min_am*100 - taxa_carteira_am_pct):.4f} p.p. vs atual",
        delta_color="inverse" if delta_taxa_min > 0 else "normal",
        help=(
            "Taxa média mínima dos recebíveis necessária para que as receitas "
            "(carteira + caixa + outras) cubram todos os custos: Sênior, Mezz, "
            "adm, gestão, PDD e outros custos, deixando o resultado da Cota "
            "Júnior em zero."
        ),
    )


    


    st.markdown("---")
    st.markdown('<div class="section-header">📊 P&L Diário do Fundo</div>', unsafe_allow_html=True)
    

    col_rec, col_custos_gestora, col_cotas = st.columns(3)
    
    # 1) RECEITAS
    with col_rec:
        st.markdown("**Receitas (dia)**")
        st.metric("Receita da Carteira (dia)", format_brl(receita_carteira_dia))
        st.metric("Receita do Caixa (dia)", format_brl(receita_caixa_dia))
        st.metric("Outras receitas (dia)", format_brl(receita_outros_dia))
        st.metric("Receita Total (dia)", format_brl(receita_total_dia))
    
    # 2) CUSTOS DA GESTORA
    custo_total_gestora_dia = custo_adm_dia + custo_gestao_dia + custo_outros_dia
    
    with col_custos_gestora:
        st.markdown("**Custos da gestora (dia)**")
        st.metric("Custo Gestora (dia)", format_brl(custo_gestao_dia))
        st.metric("Custo Adm (dia)", format_brl(custo_adm_dia))
        st.metric("Outros custos (dia)", format_brl(custo_outros_dia))
        st.metric("Custos Totais (dia)", format_brl(custo_total_gestora_dia))
    
    # 3) COTAS + PDD
    with col_cotas:
        st.markdown("**Cotas & PDD (dia)**")
        st.metric("Custo Cota Sênior (dia)", format_brl(custo_senior_dia))
        st.metric("Custo Cota Mezzanino (dia)", format_brl(custo_mezz_dia))
        st.metric("Despesa de PDD (dia)", format_brl(pdd_dia) if incluir_pdd else "R$ 0,00")
        st.metric("Resultado da Cota Júnior (dia)", format_brl(resultado_junior_dia))
    
    
    # Retornos mensais projetados
    retorno_mensal_mezz    = (1 + retorno_anualizado_mezz)   ** (1/12) - 1
    retorno_mensal_senior  = (1 + retorno_anualizado_senior) ** (1/12) - 1
    
    st.markdown("---")
    st.markdown('<div class="section-header">📈 Retornos Efetivos</div>', unsafe_allow_html=True)
    
    col_jr, col_mezz, col_sen = st.columns(3)
    
    # Coluna 1 – Cota Júnior
    with col_jr:
        st.metric("Retorno Diário da Cota Júnior",  format_pct(retorno_diario_junior))
        st.metric("Retorno Mensal da Cota Júnior",  format_pct(retorno_mensal_junior))
        st.metric("Retorno Anualizado da Cota Júnior", format_pct(retorno_anualizado_junior))
    
    # Coluna 2 – Cota Mezzanino
    with col_mezz:
        st.metric("Retorno Diário da Cota Mezzanino",  format_pct(retorno_diario_mezz))
        st.metric("Retorno Mensal da Cota Mezzanino",  format_pct(retorno_mensal_mezz))
        st.metric("Retorno Anualizado da Cota Mezzanino", format_pct(retorno_anualizado_mezz))
    
    # Coluna 3 – Cota Sênior
    with col_sen:
        st.metric("Retorno Diário da Cota Sênior",  format_pct(retorno_diario_senior))
        st.metric("Retorno Mensal da Cota Sênior",  format_pct(retorno_mensal_senior))
        st.metric("Retorno Anualizado da Cota Sênior", format_pct(retorno_anualizado_senior))
    

    # -----------------------------
    # WATERFALL - Escolha Dia/Mês/Ano
    # -----------------------------
    st.markdown("---")
    st.markdown(
        '<div class="section-header">📊 Análise Gráfica: Waterfall do Resultado</div>',
        unsafe_allow_html=True,
    )
    
    # MUDANÇA AQUI: ADICIONADO 'MENSAL'
    modo_wf = st.radio(
     "Visualizar Waterfall por:",
     ["Diário", "Mensal", "Anual"],
     horizontal=True)
 
    # DEFINIÇÃO DOS FATORES E DO RESULTADO DA JÚNIOR NO PERÍODO
    if modo_wf == "Diário":
        fator = 1                    # 1 dia útil
        resultado_final = resultado_junior_dia
    elif modo_wf == "Mensal":
        fator = 21                   # ~21 dias úteis
        resultado_final = resultado_junior_mes
    else:  # "Anual"
        fator = 252                  # 252 dias úteis
        resultado_final = resultado_junior_ano
    
    # Ajustar valores conforme o período (sempre em R$)
    rec_carteira = receita_carteira_dia * fator
    rec_caixa    = receita_caixa_dia   * fator
    rec_outros   = receita_outros_dia  * fator
       
    c_senior   = custo_senior_dia   * fator
    c_mezz     = custo_mezz_dia     * fator
    c_adm      = custo_adm_dia      * fator
    c_gest     = custo_gestao_dia   * fator
    pdd_v      = pdd_dia            * fator
    c_outros_v = custo_outros_dia   * fator
       
    # Agora o resultado_final JÁ é o resultado da Cota Júnior no período
    labels_wf = [
        "Receita Carteira",
        "Receita Caixa",
        "Outras Receitas",
        "Custo Sênior",
        "Custo Mezz",
        "Taxa Adm",
        "Taxa Gestão",
        "PDD",
        "Outros Custos",
        "Resultado Final (Júnior)"
    ]
    
    values_wf = [
        rec_carteira,
        rec_caixa,
        rec_outros,
        -c_senior,
        -c_mezz,
        -c_adm,
        -c_gest,
        -pdd_v,
        -c_outros_v,
        resultado_final
    ]
    
    measures_wf = [
        "relative","relative","relative",
        "relative","relative","relative",
        "relative","relative","relative",
        "total"   # barra final: total = resultado da Júnior no período
    ]
    
    fig_wf = go.Figure(go.Waterfall(
        name="waterfall",
        orientation="v",
        measure=measures_wf,
        x=labels_wf,
        y=values_wf,
        text=[format_brl(v) for v in values_wf],
        textposition="outside",
        connector={"line": {"color": "rgb(63,63,63)"}}
    ))
    
    fig_wf.update_layout(
        title={
            "text": f"Waterfall do Resultado ({modo_wf})",
            "y": 0.95, "x": 0.5, "xanchor": "center"
        },
        margin=dict(l=40, r=40, t=100, b=40),
        yaxis=dict(automargin=True),
        height=500
    )
    
    st.plotly_chart(fig_wf, use_container_width=True)
    
        
    
# -------------------------------------------------------------------
# ABA 2 – GESTÃO DE RISCO & STRESS TEST (UNIFICADA E CORRIGIDA)
# -------------------------------------------------------------------
with tab_risco:
    st.markdown('<div class="section-header">🛡️ Gestão de Risco & Stress Test</div>', unsafe_allow_html=True)

    # ---- CÁLCULOS DOS KPIs ----
    folga_limite = perda_lim_sub - pdd_base
    folga_pct = folga_limite / perda_lim_sub * 100 if perda_lim_sub > 0 else 0.0
    cobertura_jr_x = valor_junior / pdd_base if pdd_base > 0 else np.inf

    # Cálculo do Aporte (Reenquadramento)
    pl_pos_pdd = max(0, pl_total - pdd_base)
    jr_pos_pdd = max(0, valor_junior - pdd_base)
    sub_atual_pos = jr_pos_pdd / pl_pos_pdd if pl_pos_pdd > 0 else 0.0
    
    if sub_atual_pos < sub_min and (1 - sub_min) != 0:
        aporte_necessario = (sub_min * pl_pos_pdd - jr_pos_pdd) / (1 - sub_min)
        aporte_necessario = max(0.0, aporte_necessario)
    else:
        aporte_necessario = 0.0

    # ---- SEÇÃO 1: PAINEL DE CONTROLE DE RISCO (KPIs) ----
    cR1, cR2, cR3, cR4, cR5 = st.columns(5)
    
    cR1.metric("PDD Base (estoque)", format_brl(pdd_base), delta=f"{taxa_perda_esperada*100:.2f}% da carteira", delta_color="off")
    cR2.metric("Limite por Subordinação", format_brl(perda_lim_sub), delta=f"{perda_lim_sub_pct_recebiveis*100:.2f}% da carteira", delta_color="off")
    cR3.metric("Folga vs Limite", format_brl(folga_limite), delta=f"{folga_pct:.1f}% de folga" if perda_lim_sub > 0 else "N/A", delta_color="normal" if folga_limite >= 0 else "inverse")
    cR4.metric("Cobertura Júnior vs PDD", f"{cobertura_jr_x:.1f}x" if np.isfinite(cobertura_jr_x) else "∞", delta=f"PL Jr: {format_brl(valor_junior)}", delta_color="off")
    
    cor_aporte = "off" if aporte_necessario == 0 else "inverse"
    cR5.metric("Aporte Necessário", format_brl(aporte_necessario), delta="Para reenquadrar" if aporte_necessario > 0 else "Enquadrado", delta_color=cor_aporte)

    st.markdown("---")

    # ---- SEÇÃO 2: VISÃO DETALHADA (Buckets e Limites) ----
    col_det1, col_det2 = st.columns([1.2, 1])

    with col_det1:
        st.markdown("#### 📊 Distribuição de PDD por Faixa")
        
        # --- CORREÇÃO DO ERRO DE ARRAY LENGTH ---
        # Detecta quantas faixas vêm da Sidebar e ajusta os labels dinamicamente
        num_faixas = len(buckets_pct_norm)
        
        if num_faixas == 6:
            buckets = ["0–15", "16–30", "31–60", "61–90", "91–180", ">180"]
        elif num_faixas == 9:
            buckets = ["0–30", "31–60", "61–90", "91–120", "121–150", "151–180", "181–240", "241–300", ">300"]
        else:
            buckets = [f"Faixa {i+1}" for i in range(num_faixas)]
            
        pct_vec = buckets_pct_norm * 100 
        prov_vec = prov_rates * 100       
        perda_base_bucket = valor_recebiveis * buckets_pct_norm * prov_rates

        df_pdd = pd.DataFrame({
            "Faixa (dias)": buckets,
            "Carteira (%)": pct_vec,
            "Provisão (%)": prov_vec,
            "Perda (R$)": perda_base_bucket
        })

        st.dataframe(df_pdd.style.format({"Carteira (%)": "{:.1f}%", "Provisão (%)": "{:.1f}%", "Perda (R$)": "R$ {:,.2f}"}), use_container_width=True, height=220, hide_index=True)

    with col_det2:
        st.markdown("#### 📉 Exposição vs. Limite")
        barra_folga = max(perda_lim_sub - pdd_base, 0)
        fig_limit = go.Figure()
        fig_limit.add_trace(go.Bar(y=["Carteira"], x=[pdd_base], orientation="h", name="PDD Base", marker_color="#c0392b", text=[format_brl(pdd_base)], textposition="inside"))
        fig_limit.add_trace(go.Bar(y=["Carteira"], x=[barra_folga], orientation="h", name="Folga", marker_color="#27ae60", text=[format_brl(barra_folga)], textposition="inside"))
        fig_limit.add_vline(x=perda_lim_sub, line_width=2, line_dash="dash", line_color="black", annotation_text="Limite Regulatório", annotation_position="top right")
        fig_limit.update_layout(barmode="stack", height=220, margin=dict(l=20, r=20, t=30, b=20), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_limit, use_container_width=True)

    # ---- SEÇÃO 3: STRESS TEST DINÂMICO (FLEXÍVEL) ----
    st.markdown("---")
    st.markdown("### 🧪 Stress Test Dinâmico")
    
    if pl_total <= 0:
        st.info("Informe um PL total maior que zero para simular.")
    else:
        # --- 1. CÁLCULO DO PONTO DE RUPTURA (BREAKEVEN) ---
        # Perda máxima (L) tal que: (Jr - L) / (PL - L) = Sub_min
        # L = (Jr - Sub_min * PL) / (1 - Sub_min)
        if sub_min >= 1.0:
            ruptura_rs = 0.0
        else:
            numerador = valor_junior - (sub_min * pl_total)
            denominador = 1 - sub_min
            ruptura_rs = max(0.0, numerador / denominador) if denominador != 0 else 0.0
            
            # A perda não pode ser maior que a própria cota júnior (equity floor)
            if ruptura_rs > valor_junior:
                ruptura_rs = valor_junior

        # Multiplicador de ruptura (Quantas vezes a PDD atual?)
        mult_ruptura = ruptura_rs / pdd_base if pdd_base > 0 else 0

        # --- 2. SELETOR DE MODO DE SIMULAÇÃO ---
        c_mode, _ = st.columns([1, 3])
        with c_mode:
            modo_simulacao = st.radio(
                "Forma de Simulação:", 
                ["Multiplicador de PDD (x)", "Valor Absoluto de Perda (R$)"],
                horizontal=True
            )

        # --- 3. CONFIGURAÇÃO DOS EIXOS E SLIDERS ---
        if modo_simulacao == "Multiplicador de PDD (x)":
            # MODO MULTIPLICADOR
            val_atual_x = 1.0
            val_ruptura_x = mult_ruptura
            
            # Slider
            max_slider = max(5.0, mult_ruptura * 1.5)
            val_sim_x = st.slider(
                "Multiplicar PDD Atual por:", 
                0.0, float(max_slider), 1.0, 0.1, 
                format="%.1fx"
            )
            
            # Valores para cálculo
            perda_simulada_rs = pdd_base * val_sim_x
            
            # Eixo X do gráfico
            x_grid = np.linspace(0, max_slider, 100)
            x_label = "Multiplicador sobre a PDD Base"
            
            # Função para converter X do grid em Perda R$
            def get_loss_from_x(x): return pdd_base * x
            
            # Formatação do tooltip
            hover_template = "Mult: %{x:.2f}x<br>Sub: %{y:.2f}%"

        else:
            # MODO VALOR ABSOLUTO (R$)
            val_atual_x = pdd_base
            val_ruptura_x = ruptura_rs
            
            # Slider
            max_slider = max(ruptura_rs * 1.5, pdd_base * 5.0, 10000.0)
            val_sim_x = st.slider(
                "Defina a Perda Total (R$)", 
                0.0, float(max_slider), float(pdd_base), 1000.0, 
                format="R$ %.2f"
            )
            
            # Valores para cálculo
            perda_simulada_rs = val_sim_x
            
            # Eixo X do gráfico
            x_grid = np.linspace(0, max_slider, 100)
            x_label = "Perda Total Acumulada (R$)"
            
            # Função para converter X do grid em Perda R$
            def get_loss_from_x(x): return x
            
            # Formatação do tooltip
            hover_template = "Perda: R$ %{x:,.2f}<br>Sub: %{y:.2f}%"

        # --- 4. CÁLCULO DAS CURVAS ---
        y_sub = []
        for x in x_grid:
            loss = get_loss_from_x(x)
            pl_s = max(pl_total - loss, 1e-9) # Evitar div/0
            jr_s = max(valor_junior - loss, 0.0)
            y_sub.append(jr_s / pl_s * 100)

        # Ponto Simulado (Bolinha Roxa)
        pl_pos_sim = max(pl_total - perda_simulada_rs, 1e-9)
        jr_pos_sim = max(valor_junior - perda_simulada_rs, 0.0)
        sub_pos_sim = jr_pos_sim / pl_pos_sim * 100

        # Ponto Atual (Quadrado Preto)
        pl_pos_atual = max(pl_total - pdd_base, 1e-9)
        jr_pos_atual = max(valor_junior - pdd_base, 0.0)
        sub_pos_atual = jr_pos_atual / pl_pos_atual * 100

        # Aporte Necessário (Se simulado < minimo)
        if sub_pos_sim < sub_min_pct:
            num = (sub_min * pl_pos_sim) - jr_pos_sim
            den = 1 - sub_min
            aporte_sim = max(0.0, num / den) if den != 0 else 0.0
        else:
            aporte_sim = 0.0

        # --- 5. PLOTAGEM DO GRÁFICO ---
        fig_stress = go.Figure()

        # Linha Azul (Curva)
        fig_stress.add_trace(go.Scatter(
            x=x_grid, y=y_sub, mode='lines', name='Índice Subordinação',
            line=dict(color='#2980b9', width=3),
            hovertemplate=hover_template
        ))

        # Linha Vermelha (Limite Regulatório)
        fig_stress.add_hline(
            y=sub_min_pct, 
            line_dash="dash", line_color="#c0392b",
            annotation_text=f"Mínimo: {sub_min_pct:.1f}%", 
            annotation_position="bottom right"
        )

        # Ponto de Ruptura (X Vermelho)
        if 0 <= val_ruptura_x <= max_slider:
            fig_stress.add_trace(go.Scatter(
                x=[val_ruptura_x], y=[sub_min_pct],
                mode='markers', name='Ponto de Ruptura',
                marker=dict(symbol='x', size=12, color='red'),
                hoverinfo='skip'
            ))
            # Linha vertical pontilhada no ponto de ruptura
            fig_stress.add_vline(x=val_ruptura_x, line_width=1, line_dash="dot", line_color="gray")

        # Ponto HOJE (Quadrado Preto)
        # Só mostramos se estiver dentro do range do gráfico
        if 0 <= val_atual_x <= max_slider:
            fig_stress.add_trace(go.Scatter(
                x=[val_atual_x], y=[sub_pos_atual],
                mode='markers+text', name='HOJE',
                text=["HOJE"], textposition="top right",
                marker=dict(symbol='square', size=10, color='black')
            ))

        # Ponto SIMULADO (Bolinha Roxa)
        label_sim = f"{val_sim_x:.1f}x" if modo_simulacao == "Multiplicador de PDD (x)" else "Simulado"
        fig_stress.add_trace(go.Scatter(
            x=[val_sim_x], y=[sub_pos_sim],
            mode='markers+text', name='SIMULAÇÃO',
            text=[label_sim], textposition="top center",
            marker=dict(size=14, color='#8e44ad', line=dict(width=2, color='white'))
        ))

        fig_stress.update_layout(
            title="Dinâmica de Enquadramento",
            xaxis_title=x_label,
            yaxis_title="Índice de Subordinação (%)",
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified"
        )
        
        col_graph, col_kpi = st.columns([2, 1])
        
        with col_graph:
            st.plotly_chart(fig_stress, use_container_width=True)

        with col_kpi:
            st.markdown("**Resultado do Choque:**")
            
            st.metric("Perda Total Simulada", format_brl(perda_simulada_rs))
            
            # Delta da Subordinação
            cor_delta_sub = "normal" if sub_pos_sim >= sub_min_pct else "inverse"
            st.metric(
                "Subordinação Resultante", 
                f"{sub_pos_sim:.2f}%", 
                delta=f"{sub_pos_sim - sub_min_pct:.2f} p.p. vs Mínimo",
                delta_color=cor_delta_sub
            )

            # Aporte
            lbl_aporte = "Aporte Necessário" if aporte_sim > 0 else "Situação"
            val_aporte = format_brl(aporte_sim) if aporte_sim > 0 else "Enquadrado"
            cor_aporte = "inverse" if aporte_sim > 0 else "off"
            
            st.metric(lbl_aporte, val_aporte, delta_color=cor_aporte)
            
            if aporte_sim > 0:
                st.warning(f"⚠️ O fundo desenquadrou! É necessário aportar **{format_brl(aporte_sim)}** na Cota Júnior.")


# -------------------------------------------------------------------
# ABA 3 – ANÁLISE DE SENSIBILIDADE E SIMULAÇÃO (VERSÃO FINAL DEFINITIVA)
# -------------------------------------------------------------------
with tab_alvo:
    st.markdown('<div class="section-header">🎯 Taxa de Juros & Simulações</div>', unsafe_allow_html=True)
    
    # Variáveis de apoio (Padronização)
    pct_caixa_aplicado_atual = 1.0 
    
    # Criar as 4 sub-tabs conforme sua estrutura (Sem a aba de sensibilidade isolada)
    subtab_sim_taxa, subtab_cenarios, subtab_taxa_alvo = st.tabs([
        "🚀 Simulador de Taxa (Unitário)",
        "🔥 Simulador de Cenários (Fundo)",
        "🎯 Taxa-Alvo do Fundo (Meta de Retorno)",
    ])
    
    # ============================================================
    # SUB-ABA 0: SIMULADOR DE TAXA UNITÁRIO (SEU CÓDIGO ORIGINAL)
    # ============================================================
    with subtab_sim_taxa:
        st.markdown("### 💰 Simulador de Taxa do Empréstimo")
        st.caption("Calcule a taxa efetiva considerando deságio (calculado pela taxa), TAC, mora/multa e PDD como redutor de rentabilidade")
        
        # ========== SEÇÃO 1: PARÂMETROS DE ENTRADA ==========
        st.markdown('<div class="section-header">📋 Parâmetros da Operação</div>', unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown("**Estrutura do Crédito:**")
            ticket = st.number_input("Valor de Face (R$)", min_value=1000.0, value=100000.0, step=50000.0, format="%.2f", help="Valor que o cliente pagará no vencimento")
            taxa_juros_am = st.number_input("Taxa de Juros (% a.m.)", min_value=0.0, value=float(taxa_carteira_am_pct), step=0.25, format="%.2f", help="Taxa que define o deságio na compra") / 100.0
            prazo_dias = st.number_input("Prazo (dias)", min_value=1, value=30, step=1)
        
        with col_b:
            st.markdown("**Taxas e Encargos:**")
            tac_val = st.number_input("Outras Taxas (R$)", min_value=0.0, value=2000.0, step=500.0, format="%.2f", help="Descontada do desembolso")
            mora_pct = st.number_input("Mora (% a.m.)", min_value=0.0, value=1.0, step=0.1, format="%.2f", help="Juros de mora sobre o valor de face") / 100.0
            multa_pct = st.number_input("Multa (% flat)", min_value=0.0, value=2.0, step=0.1, format="%.2f", help="Multa sobre o valor de face em caso de atraso") / 100.0
        
        with col_c:
            st.markdown("**Risco e Inadimplência:**")
            prob_pdd_pct = st.number_input("PDD - Probabilidade de Default (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, format="%.2f", help="Reduz a taxa efetiva")
            dias_atraso = st.number_input("Dias de Atraso Médio", min_value=0, value=0, step=5, help="Para cálculo de mora")
        
        prob_pdd = prob_pdd_pct / 100.0
        
        # ========== CÁLCULOS ==========
        prazo_meses = prazo_dias / 30.0
        # Deságio pelo valor de face: aplica taxa direto sobre o face para o período
        desagio_valor = ticket * taxa_juros_am * prazo_meses
        desagio_pct = (desagio_valor / ticket * 100) if ticket > 0 else 0
        
        preco_compra = ticket - desagio_valor
        desembolso_liquido = preco_compra - tac_val
        
        mora_dia = mora_pct / 30.0
        multa_val = ticket * multa_pct if dias_atraso > 0 else 0
        mora_val = ticket * mora_dia * dias_atraso
        penalidade_total = multa_val + mora_val
        recebimento_final = ticket + penalidade_total
        
        # TIR Bruta
        if recebimento_final > 0 and desembolso_liquido > 0:
            irr_d_bruto = (recebimento_final / desembolso_liquido) ** (1 / max(1, prazo_dias)) - 1
            irr_m_bruto = (1 + irr_d_bruto) ** 30 - 1
            irr_a_bruto = (1 + irr_d_bruto) ** 365 - 1
            retorno_periodo_bruto = (recebimento_final / desembolso_liquido) - 1
            irr_valid = True
        else:
            irr_d_bruto = irr_m_bruto = irr_a_bruto = retorno_periodo_bruto = 0
            irr_valid = False
        
        # TIR Líquida
        if irr_valid:
            irr_m_liquido = irr_m_bruto * (1 - prob_pdd)
            irr_a_liquido = (1 + irr_m_liquido) ** 12 - 1
            retorno_periodo_liquido = retorno_periodo_bruto * (1 - prob_pdd)
            irr_liq_valid = True
        else:
            irr_m_liquido = irr_a_liquido = retorno_periodo_liquido = 0
            irr_liq_valid = False
        
        receita_total_bruta = recebimento_final - desembolso_liquido
        pdd_esperada_valor = receita_total_bruta * prob_pdd
        receita_total_liquida = receita_total_bruta - pdd_esperada_valor
        
        # Impacto TAC
        desembolso_sem_tac = preco_compra
        if recebimento_final > 0 and desembolso_sem_tac > 0:
            irr_d_sem_tac = (recebimento_final / desembolso_sem_tac) ** (1 / max(1, prazo_dias)) - 1
            irr_m_sem_tac = (1 + irr_d_sem_tac) ** 30 - 1
            irr_m_sem_tac_liq = irr_m_sem_tac * (1 - prob_pdd)
            impacto_tac = (irr_m_bruto - irr_m_sem_tac) * 100
        else:
            irr_m_sem_tac_liq = np.nan
            impacto_tac = 0
        
        # ========== RESULTADOS ==========
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Resultados da Simulação</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Deságio", f"{desagio_pct:.2f}%", delta=format_brl(desagio_valor), delta_color="off")
        c2.metric("Desembolso Líquido", format_brl(desembolso_liquido), delta=f"TAC: -{format_brl(tac_val)}", delta_color="inverse")
        c3.metric("TIR Mensal Bruta", f"{irr_m_bruto*100:.2f}%" if irr_valid else "N/A")
        c4.metric("TIR Mensal Líquida", f"{irr_m_liquido*100:.2f}%" if irr_liq_valid else "N/A", delta="Líq. PDD", delta_color="inverse")
        c5.metric("TIR Anual Líquida", f"{irr_a_liquido*100:.2f}%" if irr_liq_valid else "N/A")
        
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Retorno Período", f"{retorno_periodo_liquido*100:.2f}%" if irr_valid else "N/A")
        m2.metric("Impacto TAC", f"+{impacto_tac:.2f} pp", delta_color="off")
        m3.metric("Receita Bruta", format_brl(receita_total_bruta))
        m4.metric("Receita Líquida", format_brl(receita_total_liquida), delta=f"PDD: -{format_brl(pdd_esperada_valor)}", delta_color="inverse")

        # Pizza Chart
        st.markdown("---")
        st.markdown('<div class="section-header">🥧 Composição das Receitas</div>', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns([1.5, 1])
        with col_p1:
            receitas_componentes = {'Deságio': desagio_valor, 'TAC': tac_val, 'Mora/Multa': penalidade_total}
            receitas_filtradas = {k: v for k, v in receitas_componentes.items() if v > 0}
            if receitas_filtradas:
                fig_pizza = go.Figure(data=[go.Pie(labels=list(receitas_filtradas.keys()), values=list(receitas_filtradas.values()), hole=0.4, textinfo='label+percent', marker=dict(colors=['#2ecc71', '#f39c12', '#e74c3c']))])
                fig_pizza.update_layout(height=350, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig_pizza, use_container_width=True)
            else:
                st.info("Sem receitas para exibir.")
        with col_p2:
             if receitas_filtradas:
                st.markdown("**Detalhamento:**")
                for k, v in receitas_filtradas.items():
                    st.markdown(f"**{k}:** {format_brl(v)}")
        
        # Cenários de Pagamento
        st.markdown("---")
        st.markdown('<div class="section-header">🎯 Comparação de Cenários de Pagamento</div>', unsafe_allow_html=True)
        # Cenários por faixa de PDD (usando as faixas da sidebar)
        cenarios_pag = [
            {'nome': '✅ No Prazo', 'dias': 0, 'pdd': 0.0, 'desc': 'Pontual'},
            {'nome': '⏰ Atraso 5d', 'dias': 5, 'pdd': 0.0, 'desc': 'Atraso curto'},
            {'nome': '0-30d', 'dias': 30, 'pdd': prov_0_30/100, 'desc': 'Faixa 0-30'},
            {'nome': '31-60d', 'dias': 60, 'pdd': prov_31_60/100, 'desc': 'Faixa 31-60'},
            {'nome': '61-90d', 'dias': 90, 'pdd': prov_61_90/100, 'desc': 'Faixa 61-90'},
            {'nome': '91-120d', 'dias': 120, 'pdd': prov_91_120/100, 'desc': 'Faixa 91-120'},
            {'nome': '121-150d', 'dias': 150, 'pdd': prov_121_150/100, 'desc': 'Faixa 121-150'},
            {'nome': '151-180d', 'dias': 180, 'pdd': prov_151_180/100, 'desc': 'Faixa 151-180'},
            {'nome': '181-240d', 'dias': 210, 'pdd': prov_181_240/100, 'desc': 'Faixa 181-240'},
            {'nome': '241-300d', 'dias': 270, 'pdd': prov_241_300/100, 'desc': 'Faixa 241-300'},
            {'nome': '>300d', 'dias': 330, 'pdd': prov_300p/100, 'desc': 'Faixa >300'},
        ]
        res_list = []
        for c in cenarios_pag:
            pen = (ticket * multa_pct if c['dias']>0 else 0) + (ticket * mora_dia * c['dias'])
            rec = ticket + pen
            pdd_c = c.get('pdd', 0.0)
            pdd_val = ticket * pdd_c  # provisão em R$
            rec_ajust = rec - pdd_val

            if rec_ajust > 0 and desembolso_liquido > 0:
                id_ = (rec_ajust / desembolso_liquido) ** (1/max(1, prazo_dias)) - 1
                im_ = ((1+id_)**30 - 1)
                ia_ = (1+im_)**12 - 1
                rec_l = rec_ajust - desembolso_liquido
            else:
                im_ = ia_ = rec_l = 0

            res_list.append({
                'Cenário': c['nome'], 'Descrição': c['desc'],
                'PDD %': f"{pdd_c*100:.2f}%",
                'PDD (R$)': format_brl(pdd_val),
                'TIR Mensal': f"{im_*100:.2f}%", 'TIR Anual': f"{ia_*100:.2f}%", 
                'Rec. Líquida (R$)': format_brl(rec_l)
            })
        st.dataframe(pd.DataFrame(res_list), use_container_width=True, hide_index=True)

    # ============================================================
    # SUB-ABA 1 (ou 2): SIMULADOR DE CENÁRIOS (AJUSTADO)
    # ============================================================
    with subtab_cenarios:
        st.markdown("### 🎛️ Simulador de Estratégia (Alocação & Taxas)")
        st.caption("Simule o impacto de alterar o **Volume da Carteira** (Alocação), Taxas e Custos.")
        
        # Variáveis globais de referência (Cenário Base - Diário)
        rec_dia_atual = receita_total_dia
        rec_cart_dia_atual = receita_carteira_dia # Nova referência para o delta da receita
        res_jr_dia_atual = resultado_junior_dia
        ret_jr_aa_atual = retorno_anualizado_junior
        
        # ========== PAINEL DE CONTROLE ==========
        st.markdown('<div class="section-header">⚙️ Painel de Controle</div>', unsafe_allow_html=True)
        col_sim1, col_sim2, col_sim3 = st.columns(3)

        with col_sim1:
            st.markdown("**💰 Receitas & Alocação:**")
            # Slider de ALOCAÇÃO DE VOLUME
            pct_alocacao_sim = st.slider(
                "🎯 % do PL em Recebíveis",
                min_value=0.0, max_value=100.0,
                value=float(pct_recebiveis * 100), step=5.0,
                format="%.0f%%", key="sim_aloc_rec",
                help="Define quanto do PL vai para a carteira. O restante fica em Caixa."
            ) / 100.0
            
            taxa_cart_sim = st.number_input("Taxa Carteira (% a.m.)", 0.0, 10.0, float(taxa_carteira_am_pct), 0.1, key="s_tx_c") / 100
            taxa_caixa_sim = st.number_input("Taxa Caixa (% a.a.)", 0.0, 20.0, float(cdi_aa * 100), 0.5, key="s_tx_cx") / 100
        
        with col_sim2:
            st.markdown("**💸 Custos das Cotas:**")
            spr_sr_sim = st.number_input("Spread Sênior", 0.0, 10.0, float(spread_senior_aa_pct), 0.25, key="s_spr_sr") / 100
            spr_mz_sim = st.number_input("Spread Mezz", 0.0, 10.0, float(spread_mezz_aa_pct), 0.25, key="s_spr_mz") / 100
            
            tx_sr_sim_d = anual_to_diario(cdi_aa + spr_sr_sim)
            tx_mz_sim_d = anual_to_diario(cdi_aa + spr_mz_sim)
            
            # Sliders de Variação de Custos/Receitas Fixas (Solicitados anteriormente)
            st.markdown("---")
            var_outros_custos_pct = st.slider("Var. Custos Fixos (%)", -50, 50, 0, 5, key="s_var_cf") / 100.0
            var_outras_rec_pct = st.slider("Var. Outras Receitas (%)", -50, 50, 0, 5, key="s_var_or") / 100.0

            custo_outros_sim = custo_outros_dia * (1 + var_outros_custos_pct)
            rec_outros_sim = receita_outros_dia * (1 + var_outras_rec_pct)
            
            custo_adm_gestao_sim = custo_adm_dia + custo_gestao_dia + custo_outros_sim
        
        with col_sim3:
            st.markdown("**⚠️ Risco (PDD):**")
            pdd_mul_sim = st.slider("Multiplicador de PDD", 0.0, 5.0, 1.0, 0.1, key="s_pdd_m")
            
            # Visualização da Estrutura Simulada
            val_rec_sim = pl_total * pct_alocacao_sim
            val_cx_sim = pl_total * (1 - pct_alocacao_sim)
            st.markdown("---")
            st.caption(f"**Nova Estrutura:**\n\n🟦 Recebíveis: {format_brl(val_rec_sim)}\n\n🟩 Caixa: {format_brl(val_cx_sim)}")

        # ========== CÁLCULOS SIMULADOS ==========
        rec_cart_s = val_rec_sim * mensal_to_diario(taxa_cart_sim)
        rec_caixa_s = val_cx_sim * anual_to_diario(taxa_caixa_sim)
        rec_tot_s = rec_cart_s + rec_caixa_s + rec_outros_sim
        
        custo_sr_s = valor_senior * tx_sr_sim_d
        custo_mz_s = valor_mezz * tx_mz_sim_d
        
        # PDD escala com volume E multiplicador
        pdd_val_s = (val_rec_sim * taxa_perda_esperada / 252.0) * pdd_mul_sim
        
        custo_tot_s = custo_sr_s + custo_mz_s + custo_adm_gestao_sim + pdd_val_s
        res_liq_s = rec_tot_s - custo_tot_s
        
        # Retorno (Simples/Linear)
        ret_jr_aa_s = (res_liq_s * 252) / valor_junior if valor_junior > 0 else 0
        
        # Deltas
        delta_res_dia = res_liq_s - res_jr_dia_atual
        delta_ret_aa = (ret_jr_aa_s - ret_jr_aa_atual) * 100
        delta_rec_cart = rec_cart_s - rec_cart_dia_atual
        delta_pdd = pdd_val_s - pdd_dia
        
        # --- Função auxiliar para formatar Delta corretamente (Sinal antes do R$) ---
        def format_delta_brl(val):
            sinal = "+" if val >= 0 else "-"
            return f"{sinal} {format_brl(abs(val))}"

        # ========== RESULTADOS ==========
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Resultados da Simulação</div>', unsafe_allow_html=True)
        
        k1, k2, k3, k4 = st.columns(4)
        
        # Card 1: Resultado Diário (Correção da Seta: Normal = Up is Good)
        k1.metric(
            "Resultado Diário", 
            format_brl(res_liq_s), 
            delta=format_delta_brl(delta_res_dia), # Formato "- R$ 100"
            delta_color="normal", # Se negativo, fica vermelho automaticamente pelo sinal
            help="Lucro líquido diário da cota Júnior"
        )
        
        # Card 2: Retorno Jr
        k2.metric(
            "Retorno Jr (% a.a.)", 
            f"{ret_jr_aa_s*100:.2f}%", 
            delta=f"{delta_ret_aa:+.2f} p.p.",
            help="Retorno anualizado linear (Dia * 252)"
        )
        
        # Card 3: Nova Receita Carteira (Correção: Mostra variação financeira, não taxa)
        k3.metric(
            "Nova Receita Carteira", 
            format_brl(rec_cart_s), 
            delta=format_delta_brl(delta_rec_cart), # Agora mostra quantos R$ aumentou/caiu
            delta_color="normal",
            help="Receita gerada apenas pelos recebíveis"
        )
        
        # Card 4: PDD
        k4.metric(
            "Nova PDD Diária", 
            format_brl(pdd_val_s), 
            delta=format_delta_brl(delta_pdd),
            delta_color="inverse", # Se PDD subir (positivo), fica vermelho
            help="Varia conforme o Volume da carteira E o Multiplicador de Risco"
        )
        
        # ========== TABELA COMPARATIVA ==========
        st.markdown("---")
        c_head, c_sel = st.columns([3, 1])
        with c_head:
            st.markdown("#### 🆚 Comparação: Cenário Base vs Simulado")
        with c_sel:
            visao_tempo = st.radio("Visualizar em:", ["Diário", "Mensal", "Anual"], horizontal=True, key="vis_tempo_sim")

        # Definição do Fator
        if visao_tempo == "Diário":
            fator = 1.0
            lbl = "(dia)"
        elif visao_tempo == "Mensal":
            fator = 21.0
            lbl = "(mês)"
        else:
            fator = 252.0
            lbl = "(ano)"

        df_comp_sim = pd.DataFrame({
            "Indicador": [
                f"Receita Carteira {lbl}", f"Receita Caixa {lbl}", f"Outras Receitas {lbl}",
                f"(-) Custo Cotas {lbl}", f"(-) Custos Fixos {lbl}", f"(-) PDD {lbl}", 
                f"= Resultado Júnior {lbl}", "ROE Júnior (% a.a.)"
            ],
            "Cenário Atual": [
                format_brl(receita_carteira_dia * fator), 
                format_brl(receita_caixa_dia * fator),
                format_brl(receita_outros_dia * fator),
                format_brl((custo_senior_dia + custo_mezz_dia) * fator), 
                format_brl((custo_adm_dia + custo_gestao_dia + custo_outros_dia) * fator),
                format_brl(pdd_dia * fator), 
                format_brl(resultado_junior_dia * fator), 
                f"{ret_jr_aa_atual*100:.2f}%"
            ],
            "Simulado": [
                format_brl(rec_cart_s * fator), 
                format_brl(rec_caixa_s * fator),
                format_brl(rec_outros_sim * fator),
                format_brl((custo_sr_s + custo_mz_s) * fator), 
                format_brl(custo_adm_gestao_sim * fator),
                format_brl(pdd_val_s * fator), 
                format_brl(res_liq_s * fator), 
                f"{ret_jr_aa_s*100:.2f}%"
            ],
            "Diferença": [
                format_brl((rec_cart_s - receita_carteira_dia) * fator), 
                format_brl((rec_caixa_s - receita_caixa_dia) * fator),
                format_brl((rec_outros_sim - receita_outros_dia) * fator),
                format_brl(((custo_sr_s + custo_mz_s) - (custo_senior_dia + custo_mezz_dia)) * fator), 
                format_brl((custo_adm_gestao_sim - (custo_adm_dia + custo_gestao_dia + custo_outros_dia)) * fator),
                format_brl((pdd_val_s - pdd_dia) * fator),
                format_brl((res_liq_s - resultado_junior_dia) * fator), 
                f"{delta_ret_aa:+.2f} p.p."
            ]
        })
        st.dataframe(df_comp_sim, use_container_width=True, hide_index=True)

       
        # ============================================================
        # SUB-ABA 3: TAXA-ALVO DO FUNDO (CÁLCULO POR CUSTO IMPLÍCITO)
        # ============================================================
        with subtab_taxa_alvo:
            st.markdown("### 🎯 Calculadora de Taxa-Alvo (Engenharia Reversa)")
        
            dias_uteis_ano = 252
            dias_uteis_mes = dias_uteis_ano / 12  # ~21 dias úteis
        
            # Custos fixos diários (mesmo racional da aba 1)
            custos_fixos_dia = (
                custo_senior_dia
                + custo_mezz_dia
                + custo_adm_dia
                + custo_gestao_dia
                + custo_outros_dia
            )
        
            # Receitas fixas diárias (CDI do caixa + outras receitas)
            receitas_fixas_dia = receita_caixa_dia + receita_outros_dia
        
            c_input, c_kpi = st.columns([1, 3])
        
            with c_input:
                st.markdown("**Defina sua Meta:**")
                target_roe_jr = st.number_input(
                    "ROE Alvo da Júnior (% a.a.)",
                    min_value=-100.0,
                    max_value=1000.0,
                    value=10.00,
                    step=1.0,
                    help="Quanto você quer que a cota Júnior renda ao ano?"
                )
        
            # --- CÁLCULO REVERSO: dado o ROE alvo da Júnior, qual taxa preciso na carteira? ---
            if target_roe_jr > -100.0 and valor_recebiveis > 0 and valor_junior > 0:
                # usa SEMPRE a função unificada (com CDI e PDD)
                taxa_dia_nec = taxa_carteira_necessaria_diaria(target_roe_jr)
                taxa_mes_nec = ((1 + taxa_dia_nec) ** dias_uteis_mes - 1) * 100.0
                rec_carteira_necessaria = valor_recebiveis * taxa_dia_nec
            else:
                taxa_dia_nec = 0.0
                taxa_mes_nec = 0.0
                rec_carteira_necessaria = 0.0
        
            # Diferença para a taxa atual da carteira (% a.m.)
            delta_taxa = taxa_mes_nec - taxa_carteira_am_pct
        
            with c_kpi:
                k1, k2, k3 = st.columns(3)
        
                if abs(delta_taxa) < 0.0001:
                    cor_delta = "off"
                    delta_msg = "Mantém Atual"
                else:
                    cor_delta = "inverse" if delta_taxa > 0 else "normal"
                    delta_msg = f"{delta_taxa:+.4f} p.p. vs Atual"
        
                k1.metric(
                    "Taxa Mínima na Carteira",
                    f"{taxa_mes_nec:.4f}% a.m.",
                    delta=delta_msg,
                    delta_color=cor_delta,
                    help="Taxa média mensal necessária nos recebíveis para bater a meta da Cota Júnior."
                )
        
                k2.metric(
                    "Receita Diária Necessária (Carteira)",
                    format_brl(rec_carteira_necessaria),
                    delta=format_brl(rec_carteira_necessaria - receita_carteira_dia),
                    delta_color=cor_delta
                )
        
                k3.metric(
                    "Spread Necessário vs CDI",
                    f"{(taxa_mes_nec - (cdi_am * 100.0)):.2f}% a.m.",
                    help="Taxa da carteira menos o CDI mensal."
                )
        
            st.markdown("---")
        
            # --- GRÁFICO DE EQUILÍBRIO: ROE vs Taxa Necessária ---
            st.markdown("#### 📊 Curva de Equilíbrio: ROE vs Taxa Necessária")
        
            # Faixa de ROE em torno da meta
            roe_min = max(0.0, target_roe_jr - 20)
            roe_max = max(roe_min + 1.0, target_roe_jr + 20)
            roe_range = np.linspace(roe_min, roe_max, 50)
        
            taxas_necessarias = []
            for roe in roe_range:
                t_dia_i = taxa_carteira_necessaria_diaria(roe)
                t_mes_i = ((1 + t_dia_i) ** dias_uteis_mes - 1) * 100.0
                taxas_necessarias.append(t_mes_i)
        
            fig_target = go.Figure()
        
            # Curva
            fig_target.add_trace(go.Scatter(
                x=roe_range, y=taxas_necessarias,
                mode='lines', name='Curva de Equilíbrio',
                line=dict(color='#2980b9', width=4)
            ))
        
            # Ponto META
            fig_target.add_trace(go.Scatter(
                x=[target_roe_jr], y=[taxa_mes_nec],
                mode='markers+text', name='Meta',
                text=['META'], textposition='top center',
                marker=dict(size=12, color='#e74c3c', symbol='diamond')
            ))
        
            # Ponto ATUAL
            fig_target.add_trace(go.Scatter(
                x=[retorno_anualizado_junior * 100.0], y=[taxa_carteira_am_pct],
                mode='markers+text', name='Atual',
                text=['ATUAL'], textposition='bottom right',
                marker=dict(size=14, color='#27ae60', symbol='star')
            ))
        
            # Linha de referência da taxa atual
            fig_target.add_hline(
                y=taxa_carteira_am_pct,
                line_dash="dash", line_color="green", opacity=0.4,
                annotation_text=f"Taxa Atual ({taxa_carteira_am_pct:.2f}%)",
                annotation_position="bottom right"
            )
        
            fig_target.update_layout(
                xaxis_title="ROE Alvo da Júnior (% a.a.)",
                yaxis_title="Taxa Média Mensal Necessária (%)",
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                hovermode="x unified",
                legend=dict(orientation="h", y=1.02, xanchor="center", x=0.5)
            )
        
            st.plotly_chart(fig_target, use_container_width=True)



    
# -------------------------------------------------------------------
# ABA 4 – DRE PROJETADO (MÊS A MÊS POR 1 ANO) - COM GRÁFICO DE COMPOSIÇÃO
# -------------------------------------------------------------------
with tab_dre:
    from io import BytesIO  # para exportar Excel

    st.subheader("DRE Projetado – 12 meses (mês a mês)")

    st.markdown(
        """
        Esta aba simula **12 meses** de operação do FIDC, permitindo:
        - Ajustar taxa da carteira e % do PL em recebíveis mês a mês  
        - Incluir aportes/resgates via **movimento líquido** em cada classe de cota  
        - Alterar outras receitas e outros custos mensais  
        - Usar o **PL final de um mês como ponto de partida do mês seguinte**
        """
    )

    # ---------------------------
    # TABELA EDITÁVEL DE PARÂMETROS POR MÊS
    # ---------------------------
    meses = [f"Mês {i}" for i in range(1, 13)]

    # Valores "base" vindos do cenário atual
    base_taxa_carteira = taxa_carteira_am_pct
    base_pct_recebiveis = pct_recebiveis * 100
    base_outras_receitas_mes = receita_outros_dia * (252 / 12)
    base_outros_custos_mes = custo_outros_dia * (252 / 12)

    df_param_base = pd.DataFrame({
        "Mês": meses,
        "Taxa carteira (% a.m.)": [base_taxa_carteira] * 12,
        "% PL em recebíveis": [base_pct_recebiveis] * 12,
        "Outras receitas (R$/mês)": [base_outras_receitas_mes] * 12,
        "Outros custos (R$/mês)": [base_outros_custos_mes] * 12,
        "PDD manual (R$/mês)": [0.0] * 12,
        "Movimento Júnior (R$/mês)": [0.0] * 12,
        "Movimento Mezz (R$/mês)": [0.0] * 12,
        "Movimento Sênior (R$/mês)": [0.0] * 12,
    })

    st.markdown("#### Parâmetros mês a mês")
    st.caption("Edite a tabela abaixo para simular diferentes condições em cada mês:")

    df_param = st.data_editor(
        df_param_base,
        num_rows="fixed",
        use_container_width=True
    )

    # ---------------------------
    # SIMULAÇÃO MÊS A MÊS
    # ---------------------------
    dias_uteis_ano = 252
    meses_ano = 12
    dias_uteis_mes = dias_uteis_ano / meses_ano

    # PL inicial por classe (mês 1)
    pl_junior = valor_junior
    pl_mezz   = valor_mezz
    pl_senior = valor_senior

    linhas_dre_mensal = []

    for idx, row in df_param.iterrows():
        mes_label = row["Mês"]

        # ----- PL INICIAL DO MÊS -----
        pl_inicial_junior = pl_junior
        pl_inicial_mezz   = pl_mezz
        pl_inicial_senior = pl_senior
        pl_inicial_total  = pl_inicial_junior + pl_inicial_mezz + pl_inicial_senior

        # ----- MOVIMENTOS (aporte/resgate líquido) -----
        mov_j = float(row["Movimento Júnior (R$/mês)"])
        mov_m = float(row["Movimento Mezz (R$/mês)"])
        mov_s = float(row["Movimento Sênior (R$/mês)"])

        pl_junior_mov = pl_inicial_junior + mov_j
        pl_mezz_mov   = pl_inicial_mezz   + mov_m
        pl_senior_mov = pl_inicial_senior + mov_s

        pl_total_mov = pl_junior_mov + pl_mezz_mov + pl_senior_mov

        # ----- PARÂMETROS ESPECÍFICOS DO MÊS -----
        taxa_carteira_am_mes = float(row["Taxa carteira (% a.m.)"]) / 100.0
        pct_recebiveis_mes   = float(row["% PL em recebíveis"]) / 100.0

        outras_receitas_mes  = float(row["Outras receitas (R$/mês)"])
        outros_custos_mes    = float(row["Outros custos (R$/mês)"])
        pdd_manual_mes       = float(row["PDD manual (R$/mês)"])

        taxa_carteira_diaria_mes = mensal_to_diario(taxa_carteira_am_mes)

        # ----- ALOCAÇÃO EM RECEBÍVEIS E CAIXA -----
        valor_recebiveis_mes = pl_total_mov * pct_recebiveis_mes
        valor_caixa_mes      = pl_total_mov - valor_recebiveis_mes

        # ----- RECEITAS DO MÊS -----
        receita_carteira_mes   = valor_recebiveis_mes * taxa_carteira_diaria_mes * dias_uteis_mes
        receita_caixa_mes      = valor_caixa_mes      * cdi_diario              * dias_uteis_mes
        receita_outros_mes_sim = outras_receitas_mes
        receita_total_mes      = receita_carteira_mes + receita_caixa_mes + receita_outros_mes_sim

        # ----- CUSTOS DO MÊS -----
        custo_senior_mes = pl_senior_mov * taxa_senior_diaria * dias_uteis_mes
        custo_mezz_mes   = pl_mezz_mov   * taxa_mezz_diaria   * dias_uteis_mes
        custo_adm_mes    = pl_total_mov  * taxa_adm_diaria    * dias_uteis_mes
        custo_gestao_mes = pl_total_mov  * taxa_gestao_diaria * dias_uteis_mes

        pdd_auto_mes = (
            valor_recebiveis_mes * taxa_perda_esperada / meses_ano
            if incluir_pdd else 0.0
        )
        pdd_mes = pdd_manual_mes + pdd_auto_mes

        custo_outros_mes_sim = outros_custos_mes

        # ----- RESULTADO DO MÊS -----
        resultado_fundo_mes = (
            receita_total_mes
            - custo_senior_mes
            - custo_mezz_mes
            - custo_adm_mes
            - custo_gestao_mes
            - pdd_mes
            - custo_outros_mes_sim
        )

        resultado_junior_mes = resultado_fundo_mes

        # ----- PL FINAL DO MÊS -----
        pl_mezz_final   = pl_mezz_mov + custo_mezz_mes
        pl_senior_final = pl_senior_mov + custo_senior_mes
        pl_junior_final = pl_junior_mov + resultado_junior_mes
        pl_total_final  = pl_mezz_final + pl_senior_final + pl_junior_final # Ajustado para PL Total Real

        # Retorno da Júnior no mês
        base_retorno_jr = pl_junior_mov if pl_junior_mov != 0 else 1.0
        retorno_jr_mes_pct = resultado_junior_mes / base_retorno_jr

        linhas_dre_mensal.append({
            "Mês": mes_label,
            "PL Inicial (R$)": pl_inicial_total,
            "PL Após Movimentos (R$)": pl_total_mov,
            "Receita Carteira (R$)": receita_carteira_mes,
            "Receita Caixa (R$)": receita_caixa_mes,
            "Outras Receitas (R$)": receita_outros_mes_sim,
            "Receita Total (R$)": receita_total_mes,
            "Custo Sênior (R$)": custo_senior_mes,
            "Custo Mezz (R$)": custo_mezz_mes,
            "Taxa Adm (R$)": custo_adm_mes,
            "Taxa Gestão (R$)": custo_gestao_mes,
            "PDD (R$)": pdd_mes,
            "Outros Custos (R$)": custo_outros_mes_sim,
            "Resultado Cota Júnior (R$)": resultado_junior_mes,
            "PL Final (R$)": pl_total_final,
            "PL Final Sênior (R$)": pl_senior_final, # Guardado para o gráfico novo
            "PL Final Mezz (R$)": pl_mezz_final,     # Guardado para o gráfico novo
            "PL Final Júnior (R$)": pl_junior_final,
            "Retorno Júnior no mês (%)": retorno_jr_mes_pct * 100,
        })

        pl_junior = pl_junior_final
        pl_mezz   = pl_mezz_final
        pl_senior = pl_senior_final

    # ---------------------------
    # TABELA FINAL DA DRE MENSAL
    # ---------------------------
    df_dre_mensal = pd.DataFrame(linhas_dre_mensal)

    st.markdown("#### DRE mês a mês (12 meses)")

    df_dre_show = df_dre_mensal.copy()
    for col in df_dre_show.columns:
        if col == "Mês": continue
        if "Retorno" in col and "(%)" in col:
            df_dre_show[col] = df_dre_show[col].apply(lambda x: f"{x:,.2f} %")
        else:
            df_dre_show[col] = df_dre_show[col].apply(format_brl)

    st.dataframe(df_dre_show, use_container_width=True, height=500)

    # ---------------------------
    # GRÁFICO FINAL: COMPOSIÇÃO DETALHADA (CORES CORPORATIVAS/SÓBRIAS)
    # ---------------------------
    st.markdown("---")
    st.markdown("#### Composição do Resultado: Origem da Receita vs. Distribuição (%)")
    st.caption(
        "**Direita (Distribuição):** Note a separação entre **Obrigações** (Tons de Cinza), **Risco** (Vermelho) e **Lucro Líquido** (Verde)."
    )

    # --- PREPARAÇÃO DOS DADOS ---
    p_rec_cart, p_rec_caixa, p_rec_outras = [], [], []
    p_pdd, p_taxas, p_senior, p_mezz, p_junior = [], [], [], [], []
    
    # Listas para Tooltip
    v_rec_cart, v_rec_caixa, v_rec_outras = [], [], []
    v_pdd, v_taxas, v_senior, v_mezz, v_junior = [], [], [], [], []

    for i, row in df_dre_mensal.iterrows():
        rev = row["Receita Total (R$)"]
        
        # Valores Absolutos
        v_rc = row["Receita Carteira (R$)"]
        v_rx = row["Receita Caixa (R$)"]
        v_ro = row["Outras Receitas (R$)"]
        
        v_pd = row["PDD (R$)"]
        v_tx = row["Taxa Adm (R$)"] + row["Taxa Gestão (R$)"] + row["Outros Custos (R$)"]
        v_sr = row["Custo Sênior (R$)"]
        v_mz = row["Custo Mezz (R$)"]
        v_jr = row["Resultado Cota Júnior (R$)"]
        
        # Tooltip
        v_rec_cart.append(v_rc); v_rec_caixa.append(v_rx); v_rec_outras.append(v_ro)
        v_pdd.append(v_pd); v_taxas.append(v_tx); v_senior.append(v_sr); v_mezz.append(v_mz); v_junior.append(v_jr)
        
        if rev > 0:
            p_rec_cart.append(v_rc/rev); p_rec_caixa.append(v_rx/rev); p_rec_outras.append(v_ro/rev)
            p_pdd.append(v_pd/rev); p_taxas.append(v_tx/rev); p_senior.append(v_sr/rev); p_mezz.append(v_mz/rev); p_junior.append(v_jr/rev)
        else:
            p_rec_cart.append(0); p_rec_caixa.append(0); p_rec_outras.append(0)
            p_pdd.append(0); p_taxas.append(0); p_senior.append(0); p_mezz.append(0); p_junior.append(0)

    fig_dual = go.Figure()

    # --- GRUPO 1: ORIGEM (AZUIS - Mantido) ---
    
    # 1. Juros Carteira
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_rec_cart, name="Rec. Carteira", offsetgroup=0,
        marker_color="#154360", # Azul Marinho
        text=[f"{p:.1%}" if p>0.05 else "" for p in p_rec_cart], textposition="auto", textfont=dict(color="white"),
        hovertemplate="Carteira: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_rec_cart]
    ))
    
    # 2. Rendimento Caixa
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_rec_caixa, name="Rec. Caixa", offsetgroup=0, base=p_rec_cart,
        marker_color="#5DADE2", # Azul Claro
        text=[f"{p:.1%}" if p>0.05 else "" for p in p_rec_caixa], textposition="auto", textfont=dict(color="black"),
        hovertemplate="Caixa: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_rec_caixa]
    ))

    # 3. Outras Receitas
    base_outras = [x + y for x, y in zip(p_rec_cart, p_rec_caixa)]
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_rec_outras, name="Outras Rec.", offsetgroup=0, base=base_outras,
        marker_color="#D6EAF8", # Azul Bebê
        text=[f"{p:.1%}" if p>0.05 else "" for p in p_rec_outras], textposition="auto", textfont=dict(color="black"),
        hovertemplate="Outras: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_rec_outras]
    ))


    # --- GRUPO 2: DESTINO (PALETA CORPORATIVA SÓBRIA) ---
    
    # 1. PDD (Vermelho Queimado - Destaque de Perda)
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_pdd, name="PDD", offsetgroup=1,
        marker_color="#B03A2E", # Vermelho Escuro
        text=[f"{p:.1%}" if p>0.03 else "" for p in p_pdd], textposition="auto", textfont=dict(color="white"),
        hovertemplate="PDD: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_pdd]
    ))

    # 2. Taxas (Cinza Claro - Operacional)
    base_taxas = p_pdd
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_taxas, name="Taxas/Desp.", offsetgroup=1, base=base_taxas,
        marker_color="#BDC3C7", # Prata
        text=[f"{p:.1%}" if p>0.03 else "" for p in p_taxas], textposition="auto", textfont=dict(color="black"),
        hovertemplate="Taxas: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_taxas]
    ))

    # 3. Sênior (Cinza Chumbo - Obrigação Principal)
    base_senior = [x + y for x, y in zip(base_taxas, p_taxas)]
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_senior, name="Sênior", offsetgroup=1, base=base_senior,
        marker_color="#566573", # Chumbo
        text=[f"{p:.1%}" if p>0.03 else "" for p in p_senior], textposition="auto", textfont=dict(color="white"),
        hovertemplate="Sênior: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_senior]
    ))

    # 4. Mezz (Cinza Médio - Obrigação Secundária)
    base_mezz = [x + y for x, y in zip(base_senior, p_senior)]
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_mezz, name="Mezzanino", offsetgroup=1, base=base_mezz,
        marker_color="#808B96", # Cinza Médio
        text=[f"{p:.1%}" if p>0.03 else "" for p in p_mezz], textposition="auto", textfont=dict(color="white"),
        hovertemplate="Mezz: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_mezz]
    ))

    # 5. Júnior (Verde Esmeralda - Lucro)
    base_junior = [x + y for x, y in zip(base_mezz, p_mezz)]
    fig_dual.add_trace(go.Bar(
        x=df_dre_mensal["Mês"], y=p_junior, name="Lucro Júnior", offsetgroup=1, base=base_junior,
        marker_color="#27AE60", # Verde
        text=[f"{p:.1%}" if p>0.03 else "" for p in p_junior], textposition="inside", textfont=dict(color="white", size=11, family="Arial Black"),
        hovertemplate="Lucro Jr: %{y:.1%}<br>R$ %{customdata}<extra></extra>", customdata=[format_brl(v) for v in v_junior]
    ))

    fig_dual.update_layout(
        title="Origem da Receita (Esq) vs. Destinação (Dir)",
        height=500,
        xaxis=dict(title="Mês"),
        yaxis=dict(
            title="% do Total", 
            tickformat=".0%", 
            range=[0, 1.05]
        ),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor='center'),
        margin=dict(l=50, r=50, t=50, b=60),
        hovermode="x unified",
        bargap=0.15,      
        bargroupgap=0.05  
    )
    
    st.plotly_chart(fig_dual, use_container_width=True)

   # ---------------------------
    # GRÁFICOS RESUMO (APENAS PERFORMANCE)
    # ---------------------------
    st.markdown("---")
    st.markdown("#### Visão Gráfica dos Resultados")

    # Cálculos para o gráfico de performance
    pdd_pct_sobre_junior = []
    retorno_acumulado = []
    acc = 1.0 # Fator acumulado inicial

    for i, row in df_dre_mensal.iterrows():
        # 1. Impacto PDD %
        base_j = row["PL Final Júnior (R$)"] - row["Resultado Cota Júnior (R$)"]
        if base_j != 0:
            val_pdd = (row["PDD (R$)"] / base_j * 100)
        else:
            val_pdd = 0.0
        pdd_pct_sobre_junior.append(val_pdd)
        
        # 2. Retorno Acumulado
        ret_mes = row["Retorno Júnior no mês (%)"] / 100.0
        acc = acc * (1 + ret_mes)
        retorno_acumulado.append((acc - 1) * 100)

    fig_ret = go.Figure()

    # Barras: Retorno Mensal (Eixo Y1 - Esquerda)
    fig_ret.add_trace(go.Bar(
        x=df_dre_mensal["Mês"],
        y=df_dre_mensal["Retorno Júnior no mês (%)"],
        name="Retorno Mensal",
        marker_color="#2980b9",
        text=[f"{v:.1f}%" for v in df_dre_mensal["Retorno Júnior no mês (%)"]],
        textposition="auto",
        opacity=0.7,
        yaxis="y1"
    ))

    # Linha: Impacto PDD (Eixo Y1 - Esquerda - Comparável ao retorno mensal)
    fig_ret.add_trace(go.Scatter(
        x=df_dre_mensal["Mês"],
        y=pdd_pct_sobre_junior,
        mode="lines+markers",
        name="Impacto PDD / PL Jr",
        line=dict(color="#c0392b", width=2, dash="dot"),
        marker=dict(symbol="x"),
        yaxis="y1", 
        hovertemplate="PDD consome: %{y:.2f}% do PL Jr<extra></extra>"
    ))

    # Linha: Retorno Acumulado (Eixo Y2 - Direita)
    fig_ret.add_trace(go.Scatter(
        x=df_dre_mensal["Mês"],
        y=retorno_acumulado,
        mode="lines+markers",
        name="Retorno Acumulado",
        line=dict(color="#27ae60", width=3),
        marker=dict(size=6),
        yaxis="y2", 
        hovertemplate="Acumulado: %{y:.2f}%<extra></extra>"
    ))

    fig_ret.update_layout(
        title="Performance da Cota Júnior (%)",
        height=500, 
        xaxis=dict(title="Mês"),
        
        # Eixo Y1 (Mensal)
        yaxis=dict(
            title="Retorno / Impacto Mensal (%)", 
            side="left",
            showgrid=True
        ),
        
        # Eixo Y2 (Acumulado)
        yaxis2=dict(
            title="Retorno Acumulado (%)", 
            overlaying="y", 
            side="right", 
            showgrid=False,
            zeroline=False
        ),
        
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor='center'),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode="x unified"
    )
    st.plotly_chart(fig_ret, use_container_width=True)

    # ---------------------------
    # 3) GRÁFICO DE CAPACIDADE DE CAPTAÇÃO (CORREÇÃO MATEMÁTICA DEFINITIVA)
    # ---------------------------
    st.markdown("---")
    st.markdown("#### Headroom: Capacidade de Captação (Sênior/Mezz)")
    st.caption(
        "**Racional:** Dado o saldo atual da Cota Júnior, quanto o fundo pode ter de PL Total?"
        "\n\n"
        "🟢 **Verde (Positivo):** Espaço livre para captar novas cotas Sênior/Mezz.\n\n"
        "🔴 **Vermelho (Negativo):** Excesso de Sênior/Mezz. Necessário resgate (amortização) ou aporte na Júnior."
    )
    
    # Recálculo Correto dos Indicadores
    subordinacao_real = []
    headroom_list = []
    
    for i, row in df_dre_mensal.iterrows():
        # --- CORREÇÃO DO ERRO AQUI ---
        # O "PL Final (R$)" da tabela já contém (Sênior + Mezz + Júnior).
        # Não devemos somar a Júnior novamente.
        pl_tot_real = row["PL Final (R$)"] 
        pl_jr_mes = row["PL Final Júnior (R$)"]
        
        # 1. Subordinação Real (%)
        sub_real = (pl_jr_mes / pl_tot_real * 100) if pl_tot_real > 0 else 0
        subordinacao_real.append(sub_real)
        
        # 2. Headroom (R$)
        # Conta: Se tenho 10MM de Júnior e preciso de 25% de subordinação:
        # PL Total Máximo Permitido = 10MM / 0.25 = 40MM.
        # Se meu PL Total atual é 40MM, o espaço é 0.
        if sub_min > 0:
            pl_total_maximo_teorico = pl_jr_mes / sub_min
            espaco = pl_total_maximo_teorico - pl_tot_real
        else:
            espaco = 0
        
        headroom_list.append(espaco)

    # Função de formatação para o gráfico
    def human_format(num):
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'k', 'M', 'B', 'T'][magnitude])

    fig_cap = go.Figure()

    # Barras: Headroom (Verde se positivo, Vermelho se negativo)
    # Usamos uma tolerância de R$ 1,00 para evitar que erros de arredondamento pintem 0.00 de vermelho
    colors_cap = ['#27ae60' if v >= -1.0 else '#c0392b' for v in headroom_list]
    text_barras = [human_format(v) for v in headroom_list]
    
    fig_cap.add_trace(go.Bar(
        x=df_dre_mensal["Mês"],
        y=headroom_list,
        name="Espaço Sênior/Mezz",
        marker_color=colors_cap,
        text=text_barras,          
        textposition="auto",       
        textfont=dict(size=11, color="white"), 
        hovertemplate="Mês: %{x}<br>Espaço: R$ %{y:,.2f}<br><i>(Captação/Resgate Sênior)</i><extra></extra>", 
        yaxis="y1",
        opacity=0.85
    ))

    # Linha: Índice de Subordinação Real
    fig_cap.add_trace(go.Scatter(
        x=df_dre_mensal["Mês"],
        y=subordinacao_real,
        name="Subordinação Real (%)",
        mode="lines+markers+text",
        text=[f"{v:.1f}%" for v in subordinacao_real],
        textposition="top center",
        textfont=dict(size=12, color="#2c3e50", family="Arial Black"), 
        line=dict(width=3, color="#2c3e50"),
        marker=dict(size=9, color="white", line=dict(width=2, color="#2c3e50")),
        hovertemplate="Mês: %{x}<br>Subordinação: %{y:.2f}%<extra></extra>",
        yaxis="y2"
    ))

    # Linha Tracejada: Subordinação Mínima
    fig_cap.add_hline(
        y=sub_min_pct, 
        line_dash="dash", 
        line_color="#c0392b", 
        annotation_text=f"Mín: {sub_min_pct:.1f}%",
        annotation_font=dict(color="#c0392b", size=10),
        annotation_position="top right",
        yref="y2"
    )
    
    # Linha Zero Reforçada (Referência visual para as barras)
    fig_cap.add_hline(y=0, line_color="black", line_width=1.5, yref="y1")

    # Sincronização Visual dos Eixos
    # Objetivo: Alinhar o Zero da Esquerda (R$) com o Limite Mínimo da Direita (%)
    max_y1 = max(max(headroom_list, default=0), 0)
    min_y1 = min(min(headroom_list, default=0), 0)
    max_y2 = max(max(subordinacao_real, default=0), sub_min_pct)
    
    # 1. Definimos o range do eixo da direita (Porcentagem)
    range_y2 = [0, max(40.0, max_y2 * 1.35)] 
    
    # 2. Calculamos onde a linha vermelha (%) está proporcionalmente nesse eixo
    ratio_limit = sub_min_pct / range_y2[1] 
    
    # Fallback de segurança para evitar divisão por zero ou layout quebrado
    if ratio_limit >= 0.9 or ratio_limit <= 0.1: 
        ratio_limit = 0.5 
    
    # 3. Calculamos o tamanho total do eixo da esquerda (R$) para que o Zero fique na mesma proporção
    # Altura necessaria acima do zero / (1 - ratio)
    # Altura necessaria abaixo do zero / ratio
    
    val_pos_max = max(1000.0, max_y1)
    val_neg_max = abs(min(-1000.0, min_y1))
    
    h_req1 = val_pos_max / (1 - ratio_limit)
    h_req2 = val_neg_max / ratio_limit
    total_height_y1 = max(h_req1, h_req2) * 1.2
    
    y1_top = total_height_y1 * (1 - ratio_limit)
    y1_bottom = - (total_height_y1 * ratio_limit)
    range_y1 = [y1_bottom, y1_top]

    fig_cap.update_layout(
        title="Headroom de Captação (Sênior/Mezz) e Enquadramento",
        height=480, 
        xaxis=dict(title="Mês"),
        yaxis=dict(
            title="Capacidade (R$)", 
            side="left",
            showgrid=False, 
            zeroline=False,
            range=range_y1
        ),
        yaxis2=dict(
            title="Índice de Subordinação (%)", 
            overlaying="y", 
            side="right", 
            showgrid=True,
            gridcolor='#eeeeee',
            range=range_y2
        ),
        legend=dict(
            orientation="h", 
            yanchor="top", y=-0.15, 
            xanchor="center", x=0.5,
            font=dict(color="black")
        ),
        margin=dict(l=50, r=50, t=60, b=60)
    )

    st.plotly_chart(fig_cap, use_container_width=True)

    # ---------------------------
    # NOVO GRÁFICO: COMPOSIÇÃO DO PL (VALOR + % - CORES SUAVES)
    # ---------------------------
    st.markdown("---")
    st.markdown("#### Composição do Patrimônio Líquido (Evolução)")
    st.caption("Evolução da proporção de cada classe. Rótulos mostram **Valor (MM)** e **Participação (%)**.")

    # Listas para armazenar porcentagens e textos formatados
    pct_senior, text_senior = [], []
    pct_mezz, text_mezz = [], []
    pct_junior, text_junior = [], []

    # Função lambda para formatar MM (Ex: 4.5MM)
    fmt_mm = lambda x: f"R$ {x/1_000_000:.1f}MM"

    for i, row in df_dre_mensal.iterrows():
        pl_tot = row["PL Final (R$)"]
        
        # Valores Absolutos
        v_s = row["PL Final Sênior (R$)"]
        v_m = row["PL Final Mezz (R$)"]
        v_j = row["PL Final Júnior (R$)"]
        
        if pl_tot > 0:
            # Cálculo dos %
            p_s = (v_s / pl_tot) * 100
            p_m = (v_m / pl_tot) * 100
            p_j = (v_j / pl_tot) * 100
            
            pct_senior.append(p_s)
            pct_mezz.append(p_m)
            pct_junior.append(p_j)
            
            # Criação do Texto Combinado (Valor <br> %)
            text_senior.append(f"<b>{fmt_mm(v_s)}</b><br>({p_s:.1f}%)")
            text_mezz.append(f"<b>{fmt_mm(v_m)}</b><br>({p_m:.1f}%)")
            text_junior.append(f"<b>{fmt_mm(v_j)}</b><br>({p_j:.1f}%)")
        else:
            pct_senior.append(0); text_senior.append("")
            pct_mezz.append(0); text_mezz.append("")
            pct_junior.append(0); text_junior.append("")

    fig_comp = go.Figure()

    # 1. Júnior (Base - Risco)
    fig_comp.add_trace(go.Bar(
        x=df_dre_mensal["Mês"],
        y=pct_junior,
        name="Júnior",
        marker_color="#EC7063", # Vermelho Suave
        text=text_junior,       # Texto com Valor e %
        textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="<b>Júnior</b><br>%{text}<extra></extra>"
    ))

    # 2. Mezzanino (Meio)
    fig_comp.add_trace(go.Bar(
        x=df_dre_mensal["Mês"],
        y=pct_mezz,
        name="Mezzanino",
        marker_color="#F7DC6F", # Amarelo Suave
        text=text_mezz,
        textposition="inside",
        textfont=dict(color="black", size=11), # Preto para contraste no amarelo
        hovertemplate="<b>Mezzanino</b><br>%{text}<extra></extra>"
    ))

    # 3. Sênior (Topo)
    fig_comp.add_trace(go.Bar(
        x=df_dre_mensal["Mês"],
        y=pct_senior,
        name="Sênior",
        marker_color="#7DCEA0", # Verde Suave
        text=text_senior,
        textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="<b>Sênior</b><br>%{text}<extra></extra>"
    ))
    
    # Linha de Subordinação Mínima (Branca pontilhada para contraste suave)
    fig_comp.add_hline(
        y=sub_min_pct,
        line_dash="dash",
        line_color="white",
        line_width=2,
        annotation_text=f"Mín: {sub_min_pct:.0f}%",
        annotation_position="bottom right",
        annotation_font=dict(color="white")
    )

    fig_comp.update_layout(
        barmode='stack',
        height=500, # Um pouco mais alto para caber as duas linhas de texto
        xaxis=dict(title="Mês"),
        yaxis=dict(title="Proporção do PL (%)", range=[0, 100]),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor='center'),
        margin=dict(l=50, r=50, t=40, b=40)
    )
    
    st.plotly_chart(fig_comp, use_container_width=True)

    # ---------------------------
    # GRÁFICO FINAL: DIAGRAMA DE SANKEY (COM % E LEGIBILIDADE MELHORADA)
    # ---------------------------
    st.markdown("---")
    st.markdown("#### Fluxo Financeiro: Da Origem ao Resultado (Acumulado 12 Meses)")
    st.caption(
        "**Esquerda:** Origem da Receita (Composição). | **Centro:** Receita Total (100%). | **Direita:** Para onde foi o dinheiro (Custos e Lucro)."
    )

    # 1. Calcular os totais acumulados do ano
    # -- Origens --
    tot_rec_cart = df_dre_mensal["Receita Carteira (R$)"].sum()
    tot_rec_caixa = df_dre_mensal["Receita Caixa (R$)"].sum()
    tot_rec_outras = df_dre_mensal["Outras Receitas (R$)"].sum()
    
    total_receita = tot_rec_cart + tot_rec_caixa + tot_rec_outras
    
    if total_receita > 0:
        # -- Destinos --
        tot_senior = df_dre_mensal["Custo Sênior (R$)"].sum()
        tot_mezz = df_dre_mensal["Custo Mezz (R$)"].sum()
        tot_pdd = df_dre_mensal["PDD (R$)"].sum()
        
        tot_taxas = (
            df_dre_mensal["Taxa Adm (R$)"].sum() + 
            df_dre_mensal["Taxa Gestão (R$)"].sum() + 
            df_dre_mensal["Outros Custos (R$)"].sum()
        )
        
        tot_junior = df_dre_mensal["Resultado Cota Júnior (R$)"].sum()

        # -- Cálculo de Percentuais --
        pct_cart = tot_rec_cart / total_receita
        pct_caixa = tot_rec_caixa / total_receita
        pct_outras = tot_rec_outras / total_receita
        
        pct_senior = tot_senior / total_receita
        pct_mezz = tot_mezz / total_receita
        pct_pdd = tot_pdd / total_receita
        pct_taxas = tot_taxas / total_receita
        pct_junior = tot_junior / total_receita

        # 2. Configurar Rótulos (Labels) com HTML para formatação
        # Estrutura: Nome <br> Valor <br> (Porcentagem)
        
        label_list = [
            f"Juros Carteira<br><b>{format_brl(tot_rec_cart)}</b><br>({pct_cart:.1%})",   # 0
            f"Rend. Caixa<br><b>{format_brl(tot_rec_caixa)}</b><br>({pct_caixa:.1%})",     # 1
            f"Outras Rec.<br><b>{format_brl(tot_rec_outras)}</b><br>({pct_outras:.1%})",    # 2
            f"RECEITA TOTAL<br><b>{format_brl(total_receita)}</b><br>(100%)",               # 3
            f"Sênior<br><b>{format_brl(tot_senior)}</b><br>({pct_senior:.1%})",             # 4
            f"Mezzanino<br><b>{format_brl(tot_mezz)}</b><br>({pct_mezz:.1%})",            # 5
            f"PDD (Risco)<br><b>{format_brl(tot_pdd)}</b><br>({pct_pdd:.1%})",           # 6
            f"Taxas/Desp.<br><b>{format_brl(tot_taxas)}</b><br>({pct_taxas:.1%})",         # 7
            f"Lucro Júnior<br><b>{format_brl(tot_junior)}</b><br>({pct_junior:.1%})"        # 8
        ]
        
        # Cores dos Nós (Levemente ajustadas para contraste com texto preto)
        color_nodes = [
            "#5DADE2", # Carteira (Azul Claro)
            "#BDC3C7", # Caixa (Cinza Claro)
            "#AF7AC5", # Outras (Roxo Claro)
            "#2E4053", # TOTAL (Escuro)
            "#58D68D", # Sênior (Verde Claro)
            "#F5B041", # Mezz (Laranja Claro)
            "#EC7063", # PDD (Vermelho Claro)
            "#AAB7B8", # Taxas (Cinza Médio)
            "#3498db"  # Júnior (Azul Forte)
        ]

        # 3. Configurar Fluxos
        source_indices = [0, 1, 2, 3, 3, 3, 3, 3]
        target_indices = [3, 3, 3, 4, 5, 6, 7, 8]
        values_list = [
            tot_rec_cart, tot_rec_caixa, tot_rec_outras,
            tot_senior, tot_mezz, tot_pdd, tot_taxas, tot_junior
        ]
        
        # Cores dos Links (Combinando com a origem/destino)
        color_links = [
            "rgba(93, 173, 226, 0.4)", # Azul
            "rgba(189, 195, 199, 0.4)", # Cinza
            "rgba(175, 122, 197, 0.4)", # Roxo
            "rgba(88, 214, 141, 0.4)",  # Verde
            "rgba(245, 176, 65, 0.4)",  # Laranja
            "rgba(236, 112, 99, 0.4)",  # Vermelho
            "rgba(170, 183, 184, 0.4)", # Cinza
            "rgba(52, 152, 219, 0.6)"   # Azul Forte
        ]

        fig_sankey = go.Figure(data=[go.Sankey(
            textfont=dict(size=12, color="black", family="Arial"), # Força fonte preta
            node=dict(
                pad=25,
                thickness=25,
                line=dict(color="gray", width=0.5),
                label=label_list,
                color=color_nodes,
                hovertemplate='%{label}<extra></extra>' # Tooltip limpo
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values_list,
                color=color_links,
                hovertemplate='Valor: R$ %{value:,.2f}<extra></extra>'
            )
        )])

        fig_sankey.update_layout(
            title_text="Mapa de Fluxo Financeiro (Composição %)",
            font_size=13,
            height=600, # Aumentei a altura para dar espaço aos textos
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        st.plotly_chart(fig_sankey, use_container_width=True)
        
    else:
        st.info("Gere uma simulação com receita positiva para visualizar o fluxo financeiro.")
        

with tab_rating:

    # =================================================================
    # 1. PARÂMETROS DO MODELO / CONSTANTES
    # =================================================================

    # Tabela de cortes de PD -> Rating
    RATING_CUTS = [
        ("A", 0.010, "Baixo Risco"),           # PD <= 1,0% a.a.
        ("B", 0.030, "Risco Moderado"),        # 1,0% < PD <= 3,0% a.a.
        ("C", 0.080, "Risco Elevado"),         # 3,0% < PD <= 8,0% a.a.
        ("D", 1.000, "Alto Risco / Rejeitar")  # PD > 8,0% a.a.
    ]
    RATING_ORDER = ["A", "B", "C", "D"]

    # Fator de risco setorial (penaliza ou melhora o crédito)
    SETORES_RISCO = {
        "Serviços Essenciais (energia, água, telecom)": -0.20,
        "Alimentos & Farma": -0.15,
        "Varejo Não-Duráveis": 0.00,
        "Varejo Duráveis / Moda": 0.20,
        "Construção Civil & Imobiliário": 0.30,
        "Transportes & Logística": 0.10,
        "Tecnologia / Startups": 0.30,
        "Setor Público / Concessões": -0.10,
        "Outros / Neutro": 0.00,
    }

    # Coeficientes do modelo Logit (hipotéticos)
    COEFICIENTES = {
        "INTERCEPT": 2.5,
        "LIQUIDEZ_CORRENTE": -0.8,
        "ENDIVIDAMENTO_GERAL": 1.5,
        "MARGEM_EBITDA": -1.2,
        "TEMPO_RELACIONAMENTO": -0.05,
        "INADIMPLENCIA_RECENTE": 2.0,
        "CONCENTRACAO_SACADO": 1.0,
        "FATOR_SETORIAL": 0.7,
    }

    # Políticas padrão de concentração (ajuste depois se quiser)
    LIMITE_MAX_PL = 0.25       # 25% do PL
    LIMITE_MAX_JUNIOR = 1.50   # 150% da Cota Júnior

    # -----------------------------------------------------------------
    # Funções auxiliares
    # -----------------------------------------------------------------
    def map_pd_to_rating(pd_anual: float):
        for codigo, limite, desc in RATING_CUTS:
            if pd_anual <= limite:
                label = f"{codigo} ({desc})"
                return codigo, desc, label
        return "D", "Alto Risco / Rejeitar", "D (Alto Risco / Rejeitar)"

    def aplica_override_rating(codigo_original: str, ajuste: str):
        idx = RATING_ORDER.index(codigo_original)

        if ajuste == "↑ +1 notch" and idx > 0:
            idx_final = idx - 1
        elif ajuste == "↓ -1 notch" and idx < len(RATING_ORDER) - 1:
            idx_final = idx + 1
        else:
            idx_final = idx

        codigo_final = RATING_ORDER[idx_final]
        houve_override = (codigo_final != codigo_original)
        return codigo_final, houve_override

    def calcular_rating(
        liquidez_corrente: float,
        endividamento_geral: float,
        margem_ebitda: float,
        tempo_relacionamento: int,
        inadimplencia_recente: bool,
        concentracao_sacado: float,
        fator_setorial: float,
    ):
        z = (
            COEFICIENTES["INTERCEPT"]
            + COEFICIENTES["LIQUIDEZ_CORRENTE"] * liquidez_corrente
            + COEFICIENTES["ENDIVIDAMENTO_GERAL"] * endividamento_geral
            + COEFICIENTES["MARGEM_EBITDA"] * margem_ebitda
            + COEFICIENTES["TEMPO_RELACIONAMENTO"] * tempo_relacionamento
            + COEFICIENTES["INADIMPLENCIA_RECENTE"] * (1 if inadimplencia_recente else 0)
            + COEFICIENTES["CONCENTRACAO_SACADO"] * concentracao_sacado
            + COEFICIENTES["FATOR_SETORIAL"] * fator_setorial
        )
        pd_anual = 1 / (1 + np.exp(-z))
        return z, pd_anual

    # =================================================================
    # 2. DASHBOARD STREAMLIT – RATING + PRICING + LIMITE
    # =================================================================
    def rating_dashboard():
        st.title("📊 FIDC Pricing & Rating Model v2.0")
        st.markdown(
            """
            Modelo de decisão de crédito com **rating**, **perda esperada (EL)**,
            **precificação da taxa de deságio** e **análise de limite de exposição**
            para o sacado.
            """
        )

        # -------------------------------------------------------------
        # INPUTS – BLOCO 1: RISCO DE CRÉDITO
        # -------------------------------------------------------------
        st.markdown("---")
        st.header("⚙️ Parâmetros do Sacado e da Exposição")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Indicadores Financeiros")
            liquidez_corrente = st.number_input(
                "1. Liquidez Corrente (Ativo Circ. / Passivo Circ.)",
                min_value=0.0,
                value=1.50,
                step=0.10,
                format="%.2f",
                help="Valor ideal > 1,0. Quanto maior, melhor."
            )
            endividamento_geral = st.number_input(
                "2. Endividamento Geral (Passivo Total / Ativo Total)",
                min_value=0.0,
                max_value=1.0,
                value=0.60,
                step=0.05,
                format="%.2f",
                help="Valor ideal < 0,7. Quanto menor, melhor."
            )
            margem_ebitda = st.number_input(
                "3. Margem EBITDA (EBITDA / Receita Líquida)",
                min_value=-1.0,
                max_value=1.0,
                value=0.15,
                step=0.01,
                format="%.2f",
                help="Margem de lucro operacional. Quanto maior, melhor."
            )

        with col2:
            st.subheader("Comportamento, Concentração e Setor")
            tempo_relacionamento = st.number_input(
                "4. Tempo de Relacionamento (meses)",
                min_value=0,
                value=36,
                step=6,
                help="Tempo de relacionamento com o cedente/fundo."
            )
            inadimplencia_recente = st.checkbox(
                "5. Inadimplência Recente (restrição/protesto últimos 12 meses)",
                value=False,
                help="Marque se houver qualquer registro de inadimplência recente."
            )
            concentracao_sacado_pct = st.number_input(
                "6. Concentração do Sacado na Carteira (% dos recebíveis)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=1.0,
                format="%.2f",
                help="Exposição deste sacado / carteira total de recebíveis do FIDC."
            )
            concentracao_sacado = concentracao_sacado_pct / 100.0

            setor_economico = st.selectbox(
                "7. Setor Econômico do Sacado",
                list(SETORES_RISCO.keys()),
                help="Cada setor tem um fator de risco pré-definido (penalização ou alívio)."
            )
            fator_setorial = SETORES_RISCO[setor_economico]

        # -------------------------------------------------------------
        # INPUTS – BLOCO 2: PRAZO, LGD, FUNDO E LIMITE DESEJADO
        # -------------------------------------------------------------
        st.markdown("---")
        st.header("📏 Parâmetros da Operação, do Fundo e Limite Desejado")

        c1, c2, c3 = st.columns(3)

        with c1:
            prazo_dias = st.number_input(
                "Prazo médio da carteira (dias úteis)",
                min_value=1,
                value=60,
                step=5,
                help="Prazo médio ponderado dos recebíveis deste sacado."
            )

        with c2:
            lgd_pct = st.number_input(
                "LGD – Loss Given Default (% da exposição)",
                min_value=0.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                format="%.2f",
                help="Percentual da exposição perdido em caso de default."
            )
            lgd = lgd_pct / 100.0

        with c3:
            custo_fundo_aa = st.number_input(
                "Custo de Captação do Fundo (% a.a.)",
                min_value=0.0,
                value=15.0,
                step=0.5,
                format="%.2f"
            ) / 100.0
            spread_min_am = st.number_input(
                "Spread Mínimo Desejado (% a.m.)",
                min_value=0.0,
                value=0.50,
                step=0.10,
                format="%.2f"
            ) / 100.0

        # Limite desejado em R$
        st.markdown("#### 💳 Limite de Exposição Desejado para o Sacado")
        c_lim = st.columns(1)[0]
        with c_lim:
            limite_desejado = st.number_input(
                "Limite desejado (R$)",
                min_value=0.0,
                value=5_000_000.0,
                step=250_000.0,
                format="%.2f",
                help="Limite total de crédito/exposição que você pretende aprovar para este sacado."
            )

        # -------------------------------------------------------------
        # INPUTS – BLOCO 3: DINÂMICA DE CAIXA / ANTECIPAÇÃO DE RECEBÍVEIS
        # -------------------------------------------------------------
        st.markdown("#### 💸 Dinâmica de Caixa e Necessidade de Antecipação de Recebíveis")

        c_nc1, c_nc2, c_nc3, c_nc4 = st.columns(4)

        with c_nc1:
            faturamento_mensal = st.number_input(
                "Faturamento bruto mensal (R$)",
                min_value=0.0,
                value=10_000_000.0,
                step=500_000.0,
                format="%.2f",
                help="Faturamento médio mensal da empresa/sacado."
            )

        with c_nc2:
            pmr_dias = st.number_input(
                "Prazo médio de recebimento (dias)",
                min_value=0,
                value=60,
                step=5,
                help="Dias corridos médios entre venda e recebimento."
            )

        with c_nc3:
            pmp_dias = st.number_input(
                "Prazo médio de pagamento a fornecedores (dias)",
                min_value=0,
                value=30,
                step=5,
                help="Dias corridos médios entre compra e pagamento."
            )

        with c_nc4:
            caixa_proprio = st.number_input(
                "Caixa livre disponível (R$)",
                min_value=0.0,
                value=2_000_000.0,
                step=250_000.0,
                format="%.2f",
                help="Caixa próprio que a empresa tem para financiar o giro."
            )

        # Cálculo da necessidade de antecipação
        if faturamento_mensal > 0:
            vendas_dia = faturamento_mensal / 30.0  # aprox. dias corridos
        else:
            vendas_dia = 0.0

        gap_dias = max(pmr_dias - pmp_dias, 0)  # se PMR <= PMP, não há gap de saída antes da entrada
        necessidade_caixa = vendas_dia * gap_dias
        necessidade_antecipacao = max(necessidade_caixa - caixa_proprio, 0.0)

        if faturamento_mensal > 0:
            dependencia_antecipacao = necessidade_antecipacao / faturamento_mensal
        else:
            dependencia_antecipacao = 0.0

        if necessidade_antecipacao > 0:
            cobertura_limite_necessidade = limite_desejado / necessidade_antecipacao
        else:
            cobertura_limite_necessidade = 0.0

        # -------------------------------------------------------------
        # CÁLCULO – RATING, PD, EL, TAXA E CONCENTRAÇÃO
        # -------------------------------------------------------------
        dias_uteis_ano = 252

        # 1) Score e PD anual
        z_score, pd_anual = calcular_rating(
            liquidez_corrente,
            endividamento_geral,
            margem_ebitda,
            tempo_relacionamento,
            inadimplencia_recente,
            concentracao_sacado,
            fator_setorial,
        )

        # 2) Rating inicial
        rating_cod_original, rating_desc, rating_label_original = map_pd_to_rating(pd_anual)

        # 3) PD no prazo da operação
        pd_periodo = 1 - (1 - pd_anual) ** (prazo_dias / dias_uteis_ano)

        # 4) Perda Esperada (EL) no período
        el_periodo = pd_periodo * lgd

        # 5) Custo de risco médio mensal aproximado
        taxa_risco_am = el_periodo * (dias_uteis_ano / prazo_dias) / 12.0

        # 6) Custo do fundo (a.m.) e taxa final
        custo_fundo_am = custo_fundo_aa / 12.0
        taxa_sugerida_am = custo_fundo_am + taxa_risco_am + spread_min_am

        # 7) Concentração do limite desejado
        if pl_total > 0:
            conc_pl = limite_desejado / pl_total
        else:
            conc_pl = 0.0

        if valor_junior > 0:
            conc_junior = limite_desejado / valor_junior
        else:
            conc_junior = 0.0

        # -------------------------------------------------------------
        # OVERRIDE DE RATING
        # -------------------------------------------------------------
        st.markdown("---")
        st.header("🧭 Ajuste de Julgamento (Override de Rating)")

        col_o1, col_o2 = st.columns([1, 2])

        with col_o1:
            ajuste_rating = st.selectbox(
                "Ajuste de julgamento",
                ["Sem ajuste", "↑ +1 notch", "↓ -1 notch"],
                help="Use para subir/baixar um notch em casos excepcionais."
            )

        with col_o2:
            justificativa_override = st.text_area(
                "Justificativa para override (se houver):",
                value="",
                height=80
            )

        rating_cod_final, houve_override = aplica_override_rating(
            rating_cod_original, ajuste_rating
        )

        desc_final = next(desc for code, _, desc in RATING_CUTS if code == rating_cod_final)
        rating_label_final = f"{rating_cod_final} ({desc_final})"

        # -------------------------------------------------------------
        # OUTPUTS – CARDS PRINCIPAIS
        # -------------------------------------------------------------
        st.markdown("---")

        col_rating, col_pd, col_lgd, col_taxa = st.columns(4)

        col_rating.metric(
            "Rating Final",
            rating_label_final,
            help=f"Rating do modelo (antes de override): {rating_label_original}."
        )

        col_pd.metric(
            "PD Anual Estimada",
            f"{pd_anual*100:.2f}%",
            help="Probabilidade de default em 12 meses estimada pelo modelo logístico."
        )

        col_lgd.metric(
            "LGD (Perda Dada a Inadimplência)",
            f"{lgd_pct:.2f}%",
            help="Percentual estimado de perda caso ocorra default."
        )

        taxa_base_am = custo_fundo_am + spread_min_am
        delta_pricing = (taxa_sugerida_am - taxa_base_am) * 100.0
        delta_msg = "Meta Atingida" if delta_pricing >= 0 else "Abaixo da Meta"

        col_taxa.metric(
            "Taxa Sugerida (a.m.)",
            f"{taxa_sugerida_am*100:.2f}%",
            delta=f"{delta_pricing:+.2f} p.p.",
            delta_color="normal" if delta_pricing >= 0 else "inverse",
            help="Taxa final combinando custo de captação, risco (EL) e spread FIDC."
        )

        # -------------------------------------------------------------
        # CARDS – LIMITE APROVADO / CONCENTRAÇÃO
        # -------------------------------------------------------------
        st.markdown("#### 📌 Limite de Exposição e Concentração no Fundo")

        lim1, lim2, lim3 = st.columns(3)

        lim1.metric(
            "Limite Desejado para o Sacado",
            format_brl(limite_desejado),
            help="Valor total de limite de crédito pretendido para este sacado."
        )

        delta_pl = (conc_pl - LIMITE_MAX_PL) * 100.0
        lim2.metric(
            "% do PL do Fundo",
            f"{conc_pl*100:.2f}%",
            delta=f"Política: {LIMITE_MAX_PL*100:.1f}% / Dif: {delta_pl:+.2f} p.p.",
            delta_color="inverse" if conc_pl > LIMITE_MAX_PL else "normal",
            help="Exposição deste sacado dividida pelo PL total do FIDC."
        )

        delta_jr = (conc_junior - LIMITE_MAX_JUNIOR) * 100.0
        lim3.metric(
            "% da Cota Júnior",
            f"{conc_junior*100:.2f}%",
            delta=f"Política: {LIMITE_MAX_JUNIOR*100:.1f}% / Dif: {delta_jr:+.2f} p.p.",
            delta_color="inverse" if conc_junior > LIMITE_MAX_JUNIOR else "normal",
            help="Limite do sacado em relação ao colchão de subordinação (Cota Júnior)."
        )

        if houve_override and ajuste_rating != "Sem ajuste" and justificativa_override.strip() == "":
            st.warning("⚠️ Override aplicado sem justificativa preenchida.")

        # -------------------------------------------------------------
        # CARDS – NECESSIDADE DE ANTECIPAÇÃO (DERIVADA DO CICLO DE CAIXA)
        # -------------------------------------------------------------
        st.markdown("#### 🔄 Gap de Caixa e Dependência de Antecipação")

        nc1, nc2, nc3, nc4 = st.columns(4)

        nc1.metric(
            "Necessidade de Caixa (Ciclo)",
            format_brl(necessidade_caixa),
            help="Vendas médias por dia × (PMR − PMP). Capital de giro necessário para financiar o ciclo."
        )

        nc2.metric(
            "Necessidade de Antecipação",
            format_brl(necessidade_antecipacao),
            help="Necessidade de caixa menos o caixa próprio disponível."
        )

        nc3.metric(
            "% Dependência de Antecipação",
            f"{dependencia_antecipacao*100:.2f}%",
            help="Necessidade de antecipação / faturamento mensal. Quanto maior, mais dependente de FIDC/antecipação."
        )

        nc4.metric(
            "Cobertura da Necessidade pelo Limite",
            "N/A" if necessidade_antecipacao == 0 else f"{cobertura_limite_necessidade*100:.2f}%",
            help="Quanto do gap de caixa (necessidade de antecipação) é coberto pelo limite desejado."
        )

        # -------------------------------------------------------------
        # COMPOSIÇÃO DA TAXA (WATERFALL) + PESO DAS VARIÁVEIS
        # -------------------------------------------------------------
        st.markdown("---")
        st.subheader("🧮 Composição da Taxa (Pricing) & Peso das Variáveis")

        col_wf, col_sens = st.columns(2)

        # Waterfall
        with col_wf:
            st.markdown("**Waterfall de Precificação (% a.m.)**")

            valores_wf = [
                custo_fundo_am * 100.0,
                taxa_risco_am * 100.0,
                spread_min_am * 100.0,
                taxa_sugerida_am * 100.0,
            ]

            fig_wf = go.Figure(
                go.Waterfall(
                    name="Taxa",
                    orientation="v",
                    measure=["relative", "relative", "relative", "total"],
                    x=["Custo Captação", "Custo Risco (PD·LGD)", "Spread FIDC", "Taxa Final"],
                    y=valores_wf,
                    text=[f"{v:.2f}%" for v in valores_wf],
                    textposition="outside",
                )
            )
            fig_wf.update_layout(
                showlegend=False,
                yaxis_title="% a.m.",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        # Sensibilidade
        with col_sens:
            st.markdown("**Sensibilidade do Modelo (Score Z)**")

            contrib = {
                "Liquidez": COEFICIENTES["LIQUIDEZ_CORRENTE"] * liquidez_corrente,
                "Endividamento": COEFICIENTES["ENDIVIDAMENTO_GERAL"] * endividamento_geral,
                "Margem EBITDA": COEFICIENTES["MARGEM_EBITDA"] * margem_ebitda,
                "Histórico (Tempo)": COEFICIENTES["TEMPO_RELACIONAMENTO"] * tempo_relacionamento,
                "Inadimplência": COEFICIENTES["INADIMPLENCIA_RECENTE"] * (1 if inadimplencia_recente else 0),
                "Concentração": COEFICIENTES["CONCENTRACAO_SACADO"] * concentracao_sacado,
                "Fator Setorial": COEFICIENTES["FATOR_SETORIAL"] * fator_setorial,
            }

            df_sens = pd.DataFrame(
                list(contrib.items()),
                columns=["Variável", "Impacto_Z"]
            )
            df_sens["Abs"] = df_sens["Impacto_Z"].abs()
            df_sens = df_sens.sort_values("Abs", ascending=True)

            cores = ["#e74c3c" if v > 0 else "#27ae60" for v in df_sens["Impacto_Z"]]

            fig_sens = go.Figure(
                go.Bar(
                    x=df_sens["Impacto_Z"],
                    y=df_sens["Variável"],
                    orientation="h",
                    marker=dict(color=cores),
                )
            )
            fig_sens.update_layout(
                xaxis_title="Impacto no Score Z",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_sens, use_container_width=True)

        # -------------------------------------------------------------
        # DETALHES DO MODELO – TABELA + CURVA PD x Z
        # -------------------------------------------------------------
        st.markdown("---")
        st.subheader("🔍 Detalhes do Modelo")

        contrib_full = {
            "Intercepto": COEFICIENTES["INTERCEPT"],
            "Liquidez Corrente": COEFICIENTES["LIQUIDEZ_CORRENTE"] * liquidez_corrente,
            "Endividamento Geral": COEFICIENTES["ENDIVIDAMENTO_GERAL"] * endividamento_geral,
            "Margem EBITDA": COEFICIENTES["MARGEM_EBITDA"] * margem_ebitda,
            "Tempo de Relacionamento": COEFICIENTES["TEMPO_RELACIONAMENTO"] * tempo_relacionamento,
            "Inadimplência Recente": COEFICIENTES["INADIMPLENCIA_RECENTE"] * (1 if inadimplencia_recente else 0),
            "Concentração do Sacado": COEFICIENTES["CONCENTRACAO_SACADO"] * concentracao_sacado,
            "Fator Setorial": COEFICIENTES["FATOR_SETORIAL"] * fator_setorial,
        }

        df_contrib = pd.DataFrame(
            list(contrib_full.items()),
            columns=["Variável", "Contribuição para o Score Z"]
        )
        df_contrib["Sinal"] = df_contrib["Contribuição para o Score Z"].apply(
            lambda x: "Aumenta Risco" if x > 0 else "Diminui Risco"
        )
        df_contrib["Abs"] = df_contrib["Contribuição para o Score Z"].abs()

        st.dataframe(
            df_contrib.sort_values("Abs", ascending=False).drop(columns=["Abs"]),

            hide_index=True,
            use_container_width=True,
        )

        st.metric(
            "Score Z (Logit)",
            f"{z_score:.4f}",
            help="Score linear do modelo. Quanto maior o Z, maior a PD estimada."
        )

        st.markdown("##### Curva de Probabilidade de Default (PD) x Score Z")

        z_range = np.linspace(-5, 5, 200)
        pd_range = 1 / (1 + np.exp(-z_range))

        fig_pd = go.Figure()
        fig_pd.add_trace(
            go.Scatter(
                x=z_range,
                y=pd_range,
                mode="lines",
                name="PD(z)",
            )
        )
        fig_pd.add_vline(
            x=z_score,
            line_width=2,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Score Z Atual: {z_score:.2f}",
            annotation_position="top left",
        )
        fig_pd.add_hline(
            y=pd_anual,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text=f"PD Anual: {pd_anual*100:.2f}%",
            annotation_position="bottom right",
        )
        fig_pd.update_layout(
            title="Curva Logística – Score Z x PD Anual",
            xaxis_title="Score Z (Logit)",
            yaxis_title="PD Anual",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_pd, use_container_width=True)

    # chama o dashboard
    rating_dashboard()
