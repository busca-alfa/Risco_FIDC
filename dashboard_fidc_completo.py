import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go



st.set_page_config(
    page_title="FIDC - Estrutura de Cotas",
    layout="wide"
)

# Ajuste visual nos cards de métricas
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] > label {
        font-size: 0.85rem;
        font-weight: 600;
    }
    div[data-testid="stMetric"] > div {
        font-size: 1.4rem;
        font-weight: 700;
    }
    /* Cards com bordas e sombras */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Títulos de seções */
    .section-header {
        background: linear-gradient(90deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏦 FIDC - Estrutura de Cotas e P&L Diário")
st.markdown(
    """
    Modelo econômico-financeiro para analisar a estrutura de cotas de um FIDC, 
    o custo diário das classes, o retorno residual da Cota Júnior, a PDD e o colchão de subordinação.
    """
)

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
notas_usuario = st.sidebar.text_area(
    "Bloco de notas (melhorias / ideias para o modelo)",
    ""
)
# (não entra em nenhum cálculo, é só para você não esquecer)

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
    value=20_000_000.0,
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
    value=float(100 * valor_junior / pl_total) if pl_total > 0 else 20.0,
    step=1.0,
    format="%.2f"
)
sub_min = sub_min_pct / 100.0

st.sidebar.markdown("---")

# Taxas de mercado e carteira
cdi_aa_pct = st.sidebar.number_input(
    "CDI (% a.a.)",
    min_value=0.0,
    value=10.0,
    step=0.25,
    format="%.2f"
)
cdi_aa = cdi_aa_pct / 100.0
cdi_diario = anual_to_diario(cdi_aa)
cdi_am = (1 + cdi_aa) ** (1/12) - 1

taxa_carteira_am_pct = st.sidebar.number_input(
    "Taxa da carteira (% a.m. sobre recebíveis)",
    min_value=0.0,
    value=2.5,
    step=0.1,
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
    value=1.0,
    step=0.25,
    format="%.2f"
)
spread_mezz_aa_pct = st.sidebar.number_input(
    "Spread da Cota Mezzanino (% a.a. sobre CDI)",
    min_value=0.0,
    value=2.5,
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
    value=0.5,
    step=0.10,
    format="%.2f"
)
taxa_gestao_aa_pct = st.sidebar.number_input(
    "Taxa de Gestão (% a.a. sobre PL)",
    min_value=0.0,
    value=1.0,
    step=0.10,
    format="%.2f"
)
taxa_adm_aa = taxa_adm_aa_pct / 100.0
taxa_gestao_aa = taxa_gestao_aa_pct / 100.0

taxa_adm_diaria = anual_to_diario(taxa_adm_aa)
taxa_gestao_diaria = anual_to_diario(taxa_gestao_aa)

outros_custos_mensais = st.sidebar.number_input(
    "Outros custos fixos (R$ / mês)",
    min_value=0.0,
    value=0.0,
    step=1_000.0,
    format="%.2f"
)
# Aproximação: 12 meses ~ 252 dias úteis
custo_outros_dia = outros_custos_mensais * 12.0 / 252.0

# Outras receitas mensais (ex.: rebate, serviços, consultoria)
outros_receitas_mensais = st.sidebar.number_input(
    "Outras receitas (R$ / mês)",
    min_value=0.0,
    value=0.0,
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
valor_caixa = pl_total - valor_recebiveis

# Receitas
receita_carteira_dia = valor_recebiveis * taxa_carteira_diaria
receita_caixa_dia    = valor_caixa      * cdi_diario
receita_financeira_dia = receita_carteira_dia + receita_caixa_dia
receita_total_dia      = receita_financeira_dia + receita_outros_dia

# Custos das cotas
custo_senior_dia = valor_senior * taxa_senior_diaria
custo_mezz_dia   = valor_mezz   * taxa_mezz_diaria

# Taxas
custo_adm_dia    = pl_total * taxa_adm_diaria
custo_gestao_dia = pl_total * taxa_gestao_diaria

prov_rates = np.array([
    prov_0_30, prov_31_60, prov_61_90, prov_91_120, prov_121_150,
    prov_151_180, prov_181_240, prov_241_300, prov_300p
]) / 100.0

taxa_perda_esperada = float(np.sum(buckets_pct_norm * prov_rates))
pdd_base = valor_recebiveis * taxa_perda_esperada
pdd_dia = pdd_base / 252.0 if incluir_pdd else 0.0

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

# --- RETORNOS DA COTA JÚNIOR (todos coerentes com o Waterfall) ---

resultado_junior_dia = resultado_liquido_dia

# Retorno diário (simples)
retorno_diario_junior = (
    resultado_junior_dia / valor_junior if valor_junior > 0 else 0.0
)

# Retorno mensal projetado (21 dias úteis)
retorno_mensal_junior = (
    (resultado_junior_dia * 21) / valor_junior if valor_junior > 0 else 0.0
)

# Retorno anual simples (coerente com o gráfico Waterfall!)
retorno_anualizado_junior = (
    (resultado_junior_dia * 252) / valor_junior if valor_junior > 0 else 0.0
)


retorno_diario_senior = taxa_senior_diaria
retorno_mensal_senior = retorno_diario_senior * 21
retorno_anualizado_senior = retorno_diario_senior * 252

retorno_diario_mezz = taxa_mezz_diaria
retorno_mensal_mezz = retorno_diario_mezz * 21
retorno_anualizado_mezz = retorno_diario_mezz * 252


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

# PDD (anual) – cenário base (sem stress da aba 5)
pdd_ano = pdd_dia * dias_uteis_ano

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
tab_estrutura, tab_risco, tab_alvo, tab_dre, tab_pdd_stress = st.tabs(
    [
        "📊 Estrutura & P&L",
        "🧨 Risco, PDD & Subordinação",
        "🎯 Taxa alvo da Cota Júnior",
        "📑 DRE Projetado",
        "🧪 Capacidade de Absorção de Perdas"
    ]
)

# -------------------------------------------------------------------
# ABA 1 – ESTRUTURA & P&L
# -------------------------------------------------------------------
with tab_estrutura:
    st.markdown('<div class="section-header">🏗️ Estrutura de Capital</div>', unsafe_allow_html=True)

    # 1. Preparar os dados na ordem correta (Sênior -> Mezz -> Júnior)
    # A Sênior tem prioridade, então fica no topo. A Júnior é o alicerce, fica na base.
    
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
                fill_color='#2c3e50', # Azul escuro corporativo
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
                fill_color=[df_struct.Color], # Cores de fundo condicionais (Sênior safe, Jr risk)
                align='left',
                font=dict(color='black', size=13),
                height=30
            )
        )])
        
        fig_table.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=160
        )
        st.plotly_chart(fig_table, use_container_width=True)

    with c_viz:
        # Gráfico de Pilha (Stacked Bar) para ver o "Colchão" visualmente
        fig_stack = go.Figure()
        
        # Adicionamos na ordem inversa para empilhar visualmente: Jr em baixo, Sênior em cima
        # Júnior (Base)
        fig_stack.add_trace(go.Bar(
            name='Júnior', x=['FIDC'], y=[valor_junior], 
            marker_color='#e74c3c', text=f"{df_struct.iloc[2]['Perc']*100:.0f}%", textposition='auto'
        ))
        # Mezzanino (Meio)
        fig_stack.add_trace(go.Bar(
            name='Mezzanino', x=['FIDC'], y=[valor_mezz], 
            marker_color='#f1c40f', text=f"{df_struct.iloc[1]['Perc']*100:.0f}%", textposition='auto'
        ))
        # Sênior (Topo)
        fig_stack.add_trace(go.Bar(
            name='Sênior', x=['FIDC'], y=[valor_senior], 
            marker_color='#27ae60', text=f"{df_struct.iloc[0]['Perc']*100:.0f}%", textposition='auto'
        ))

        # LINHA TRACEJADA DO MÍNIMO DE SUBORDINAÇÃO
        subordinacao_minima_valor = pl_total * sub_min
        fig_stack.add_shape(
            type="line",
            x0=-0.4, x1=0.4,
            y0=subordinacao_minima_valor, y1=subordinacao_minima_valor,
            line=dict(color="white", width=2, dash="dash")
        )
        
        # Legenda abaixo do gráfico
        fig_stack.add_annotation(
            x=0.5, y=-0.12,               # abaixo da barra
            xref="paper", yref="paper",   # ref. relativa ao container
            text=f"Mín. Subordinação ({sub_min_pct:.1f}%)",
            showarrow=False,
            font=dict(size=12, color="red"),
            align="center"
        )


        fig_stack.update_layout(
            barmode='stack',
            title={
                'text': "Subordinação Visual",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            showlegend=True,
            margin=dict(l=20, r=20, t=50, b=20),
            height=280,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor='center')
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-header">💰 Informações Financeiras</div>', unsafe_allow_html=True)

    # Regra de enquadramento: mínimo 67% do PL em recebíveis
    min_recebiveis_regra = pl_total * 0.67
    
    # 1. Taxa média BRUTA do PL (a.m.):
    #    Ponderação: % Recebíveis * Taxa Carteira + % Caixa * Taxa CDI
    taxa_media_pl_am = pct_recebiveis * taxa_carteira_am + (1 - pct_recebiveis) * cdi_am
    
    # 2. Impacto da PDD no PL (a.m.):
    #    Transformamos o custo diário da PDD em custo mensal (x21) e dividimos pelo PL
    impacto_pdd_pl_am = (pdd_dia * 21) / pl_total if pl_total > 0 else 0.0
    
    # 3. Taxa média LÍQUIDA de PDD (a.m.):
    taxa_media_pl_am_liq = taxa_media_pl_am - impacto_pdd_pl_am
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Situação atual
    col1.metric(
        "Alocação em Recebíveis",
        format_brl(valor_recebiveis),
        f"{pct_recebiveis*100:.0f}% do PL"
    )
    col2.metric(
        "Caixa (a CDI)",
        format_brl(valor_caixa),
        f"{(1 - pct_recebiveis)*100:.0f}% do PL"
    )
    
    # Regra de 67% em recebíveis
    col3.metric(
        "Mínimo em Recebíveis",
        format_brl(min_recebiveis_regra),
        "67% do PL",
        delta_color="inverse" 
    )

    # Taxa média ponderada do PL (ao mês) com visão Líquida no Delta
    col4.metric(
        "Taxa média do PL (a.m.)",
        f"{taxa_media_pl_am*100:.2f}%",
        delta=f"Líq. de PDD: {taxa_media_pl_am_liq*100:.2f}%", # AQUI ESTÁ A MUDANÇA
        delta_color="off", # 'off' deixa cinza (neutro), ou use 'normal' para verde/vermelho
        help="A taxa principal é bruta. O valor menor abaixo já desconta o custo da PDD mensal."
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
    
    
    # Retornos mensais projetados a partir do anual (equivalência em 12 meses)
    retorno_mensal_junior  = (1 + retorno_anualizado_junior) ** (1/12) - 1
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
    

    # ---------------------------------------------------------------
    # NOVA SEÇÃO: GRÁFICOS DE RETORNO / PDD / WATERFALL
    # ---------------------------------------------------------------
    st.markdown("---")
   # ---------------------------------------------------------------
    # 2) PDD simulada vs limite de perda (mini-stress regulatório)
    # ---------------------------------------------------------------
    st.markdown(
        '<div class="section-header">🧨 PDD Simulada vs Limite de Subordinação</div>',
        unsafe_allow_html=True,
    )

    if pdd_base <= 0 or valor_recebiveis <= 0 or perda_lim_sub <= 0:
        st.info(
            "A PDD base, o saldo de recebíveis ou o limite de perda estão zerados. "
            "Ajuste os parâmetros para visualizar o gráfico de stress."
        )
    else:
        # multiplicador máximo: 0 até ~1.5x o multiplicador de ruptura, com mínimo 2x
        mult_ruptura_base = perda_lim_sub / pdd_base if pdd_base > 0 else 0
        max_mult = max(2.0, mult_ruptura_base * 1.5)

        mult_grid = np.linspace(0.0, max_mult, 60)
        perdas_sim = mult_grid * pdd_base
        perdas_pct = (perdas_sim / valor_recebiveis) * 100.0

        limite_pct = perda_lim_sub_pct_recebiveis * 100.0

        fig_pdd = go.Figure()
        fig_pdd.add_trace(
            go.Scatter(
                x=mult_grid,
                y=perdas_pct,
                mode="lines",
                name="PDD simulada (% dos recebíveis)",
                line=dict(width=3),
            )
        )
        fig_pdd.add_trace(
            go.Scatter(
                x=[0, max_mult],
                y=[limite_pct, limite_pct],
                mode="lines",
                name="Limite de perda (subordinação mínima)",
                line=dict(dash="dash", width=2),
            )
        )

        # marcador de ruptura, se estiver no range
        if 0 <= mult_ruptura_base <= max_mult:
            fig_pdd.add_trace(
                go.Scatter(
                    x=[mult_ruptura_base],
                    y=[limite_pct],
                    mode="markers+text",
                    name="Ponto de ruptura",
                    text=[f"m* = {mult_ruptura_base:.2f}x"],
                    textposition="bottom center",
                    marker=dict(size=10, symbol="x"),
                )
            )

        fig_pdd.update_layout(
            xaxis_title="Multiplicador sobre a PDD Base",
            yaxis_title="Perda acumulada (% dos recebíveis)",
            height=350,
            margin=dict(l=20, r=20, t=40, b=40),
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_pdd, use_container_width=True)

    # -----------------------------
    # WATERFALL - Escolha Dia ou Ano
    # -----------------------------
    st.markdown("---")
    st.markdown(
        '<div class="section-header">📊 Análise Gráfica: Waterfall do Resultado</div>',
        unsafe_allow_html=True,
    )
    
    
    modo_wf = st.radio(
        "Visualizar Waterfall por:",
        ["Diário", "Anual"],
        horizontal=True
    )
    
    fator = 1 if modo_wf == "Diário" else 252
    
    # Ajustar valores conforme o período
    rec_carteira = receita_carteira_dia * fator
    rec_caixa = receita_caixa_dia * fator
    rec_outros = receita_outros_dia * fator
    c_senior = custo_senior_dia * fator
    c_mezz = custo_mezz_dia * fator
    c_adm = custo_adm_dia * fator
    c_gest = custo_gestao_dia * fator
    pdd_v = pdd_dia * fator
    c_outros_v = custo_outros_dia * fator
    
    resultado_final = (
        rec_carteira + rec_caixa + rec_outros
        - c_senior - c_mezz - c_adm - c_gest - pdd_v - c_outros_v
    )
    
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
        "Resultado Final"
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
        "total"
    ]
    
    fig_wf = go.Figure(go.Waterfall(
        name="waterfall",
        orientation="v",
        measure=measures_wf,
        x=labels_wf,
        textposition="outside",
        y=values_wf,
        connector={"line": {"color": "rgb(63,63,63)"}}
    ))
    
    fig_wf = go.Figure(go.Waterfall(
        name="waterfall",
        orientation="v",
        measure=measures_wf,
        x=labels_wf,
        y=values_wf,
        text=[format_brl(v) for v in values_wf],   # <<< AQUI: textos dos valores
        textposition="outside",                    # mostra os textos para fora das barras
        connector={"line": {"color": "rgb(63,63,63)"}}
    ))
    
    fig_wf.update_layout(
        margin=dict(l=40, r=40, t=90, b=40),  # aumenta margem superior
        yaxis=dict(automargin=True)
    )
    
        
    st.plotly_chart(fig_wf, use_container_width=True)


# -------------------------------------------------------------------
# ABA 2 – RISCO, PDD & SUBORDINAÇÃO (cenário base)
# -------------------------------------------------------------------
with tab_risco:
    st.markdown("### Painel do Risco – PDD & Subordinação")

    # ---- KPIs principais do risco ----
    folga_limite = perda_lim_sub - pdd_base
    folga_pct = folga_limite / perda_lim_sub * 100 if perda_lim_sub > 0 else 0.0
    cobertura_jr_x = valor_junior / pdd_base if pdd_base > 0 else np.inf

    cR1, cR2, cR3, cR4 = st.columns(4)
    cR1.metric(
        "PDD Base (estoque)",
        format_brl(pdd_base),
        delta=f"{taxa_perda_esperada*100:.2f}% dos recebíveis",
        delta_color="off",
        help="PDD esperada aplicada sobre a carteira atual (bucketizada)."
    )
    cR2.metric(
        "Limite por Subordinação",
        format_brl(perda_lim_sub),
        delta=f"{perda_lim_sub_pct_recebiveis*100:.2f}% dos recebíveis",
        delta_color="off",
        help="Perda máxima antes de violar o índice mínimo de subordinação informado."
    )
    cR3.metric(
        "Folga vs Limite",
        format_brl(folga_limite),
        delta=f"{folga_pct:.1f}% de folga" if perda_lim_sub > 0 else "N/A",
        delta_color="normal" if folga_limite >= 0 else "inverse",
        help="Se negativo, já há desenquadramento em relação ao limite de perda."
    )
    cR4.metric(
        "Cobertura Júnior vs PDD",
        f"{cobertura_jr_x:.1f}x" if np.isfinite(cobertura_jr_x) else "∞",
        delta=f"PL Jr: {format_brl(valor_junior)}",
        delta_color="off",
        help="Quantas vezes o PL Júnior cobre a PDD base."
    )

    st.markdown("---")
    st.markdown("#### Distribuição de PDD por faixa de atraso")

    buckets = [
        "0–30", "31–60", "61–90", "91–120", "121–150",
        "151–180", "181–240", "241–300", ">300"
    ]
    pct_vec   = np.array([
        pct_0_30, pct_31_60, pct_61_90, pct_91_120, pct_121_150,
        pct_151_180, pct_181_240, pct_241_300, pct_300p
    ])
    prov_vec  = np.array([
        prov_0_30, prov_31_60, prov_61_90, prov_91_120, prov_121_150,
        prov_151_180, prov_181_240, prov_241_300, prov_300p
    ])

    pct_norm = pct_vec / pct_vec.sum() if pct_vec.sum() > 0 else np.zeros_like(pct_vec)
    perda_base_bucket = valor_recebiveis * pct_norm * (prov_vec / 100.0)

    df_pdd = pd.DataFrame({
        "Faixa (dias)": buckets,
        "% carteira (input)": pct_vec,
        "% carteira (normalizada)": pct_norm * 100,
        "Provisão % (input)": prov_vec,
        "Perda esperada (R$)": perda_base_bucket
    })

    col_tbl, col_chart = st.columns([1.3, 1])
    with col_tbl:
        st.dataframe(
            df_pdd.style.format({
                "% carteira (input)": "{:.1f}",
                "% carteira (normalizada)": "{:.1f}",
                "Provisão % (input)": "{:.1f}",
                "Perda esperada (R$)": "R$ {:,.2f}".format,
            }),
            use_container_width=True,
            height=260
        )
    with col_chart:
        fig_buckets = go.Figure()
        fig_buckets.add_trace(
            go.Bar(
                x=df_pdd["Perda esperada (R$)"],
                y=df_pdd["Faixa (dias)"],
                orientation="h",
                marker_color="#e67e22",
                text=[format_brl(v) for v in df_pdd["Perda esperada (R$)"]],
                textposition="outside",
                name="Perda esperada"
            )
        )
        fig_buckets.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            height=260,
            showlegend=False,
            xaxis_title="Perda esperada (R$)"
        )
        st.plotly_chart(fig_buckets, use_container_width=True)

    st.markdown("---")
    st.markdown("#### PDD Base x Limite de Subordinação")

    # Barra tipo bullet: PDD base + folga até o limite
    barra_folga = max(perda_lim_sub - pdd_base, 0)
    fig_limit = go.Figure()
    fig_limit.add_trace(go.Bar(
        y=["Exposição a perda"],
        x=[pdd_base],
        orientation="h",
        name="PDD Base",
        marker_color="#c0392b",
        text=[format_brl(pdd_base)],
        textposition="inside"
    ))
    fig_limit.add_trace(go.Bar(
        y=["Exposição a perda"],
        x=[barra_folga],
        orientation="h",
        name="Folga até limite",
        marker_color="#27ae60",
        text=[format_brl(barra_folga)],
        textposition="inside"
    ))
    fig_limit.add_shape(
        type="line",
        x0=perda_lim_sub, x1=perda_lim_sub,
        y0=-0.5, y1=0.5,
        line=dict(color="black", dash="dash", width=2)
    )
    fig_limit.update_layout(
        barmode="stack",
        height=180,
        margin=dict(l=30, r=30, t=20, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        xaxis_title="R$",
    )
    st.plotly_chart(fig_limit, use_container_width=True)

    # Alertas / mensagens resumidas
    impacto_junior = valor_junior - pdd_base
    if folga_limite < 0:
        st.error("⚠️ PDD base ultrapassa o limite de perda pela subordinação mínima. Recompor subordinação ou reduzir risco.")
    elif impacto_junior < 0:
        st.warning("⚠️ A PDD base consome todo o colchão da Cota Júnior.")
    else:
        st.success("✅ PDD base abaixo do limite de perda e preservando o colchão da Cota Júnior.")

    st.markdown("---")
    st.markdown("#### Simulação dinâmica: perda x índice de subordinação")

    if pl_total <= 0:
        st.info("Informe um PL total maior que zero para simular a subordinação.")
    else:
        perda_ref = pdd_base if pdd_base > 0 else valor_junior * 0.2
        perda_max = max(perda_ref * 2, valor_junior * 1.2, pl_total * 0.3, 1_000.0)
        perda_sim = st.slider(
            "Perda simulada (R$)",
            min_value=0.0,
            max_value=float(perda_max),
            value=float(min(perda_ref, perda_max)),
            step=float(max(perda_max / 100, 100.0)),
            help="Escolha um valor de perda e veja o índice Júnior/PL após o choque."
        )

        # Curva de subordinação ao longo de perdas
        perdas_grid = np.linspace(0, perda_max, 60)
        sub_grid = []
        for perda in perdas_grid:
            pl_sim = max(pl_total - perda, 1e-9)
            jr_sim = max(valor_junior - perda, 0.0)
            sub_grid.append(jr_sim / pl_sim * 100)

        pl_sim_sel = max(pl_total - perda_sim, 1e-9)
        jr_sim_sel = max(valor_junior - perda_sim, 0.0)
        sub_sel = jr_sim_sel / pl_sim_sel * 100

        fig_sub = go.Figure()
        fig_sub.add_trace(go.Scatter(
            x=perdas_grid,
            y=sub_grid,
            mode="lines",
            name="Subordinação simulada (Jr / PL)",
            line=dict(width=3, color="#1f77b4")
        ))
        fig_sub.add_trace(go.Scatter(
            x=[perda_sim],
            y=[sub_sel],
            mode="markers+text",
            name="Perda escolhida",
            marker=dict(size=10, color="#d62728", symbol="diamond"),
            text=[f"{sub_sel:.2f}%"],
            textposition="top center"
        ))
        fig_sub.add_hline(
            y=sub_min_pct,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Subordinação mínima: {sub_min_pct:.1f}%",
            annotation_position="bottom right"
        )
        fig_sub.update_layout(
            height=320,
            xaxis_title="Perda (R$)",
            yaxis_title="Índice Júnior / PL (%)",
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_sub, use_container_width=True)

        col_sim1, col_sim2, col_sim3 = st.columns(3)
        col_sim1.metric("Perda simulada", format_brl(perda_sim))
        col_sim2.metric("PL pós-perda", format_brl(pl_sim_sel))
        col_sim3.metric("Subordinação pós-perda", f"{sub_sel:.2f}%")

# -------------------------------------------------------------------
# -------------------------------------------------------------------
# ABA 3 – ANÁLISE DE SENSIBILIDADE E SIMULAÇÃO (VERSÃO ROBUSTA)
# -------------------------------------------------------------------
with tab_alvo:
    st.markdown('<div class="section-header">🎯 Análise de Sensibilidade e Simulação</div>', unsafe_allow_html=True)
    
    # Criar sub-tabs para organizar as análises
    subtab_sim_taxa, subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "🚀 Simulador de Taxa",
        "📊 Sensibilidade de Taxa",
        "🔥 Simulador de Cenários",
        "⚖️ Break-even Analysis",
        "🌡️ Heatmap de Risco"
    ])
    
    # ============================================================
    # SUB-ABA 0: SIMULADOR DE TAXA (juros + taxas + PDD)
    # ============================================================
    with subtab_sim_taxa:
        st.markdown("### Simulador de Taxa do Empréstimo (com TAC, mora/multa e PDD)")
        st.caption("Calcule a taxa efetiva do crédito considerando juros, TAC, atraso, multa e probabilidade de PDD.")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            ticket = st.number_input("Ticket (principal)", min_value=1_000.0, value=1_000_000.0, step=50_000.0, format="%.2f")
            preco_compra = st.number_input("Preço de compra (R$)", min_value=0.0, value=ticket, step=50_000.0, format="%.2f")
            prazo_dias = st.number_input("Prazo (dias)", min_value=1, value=360, step=30)
            taxa_juros_am = st.number_input("Juros a.m. (%)", min_value=0.0, value=float(taxa_carteira_am_pct), step=0.25, format="%.2f") / 100.0
        with col_b:
            tac_val = st.number_input("TAC (R$, upfront)", min_value=0.0, value=20_000.0, step=5_000.0, format="%.2f")
            mora_pct = st.number_input("Mora (% a.m. sobre inadimplente)", min_value=0.0, value=1.0, step=0.1, format="%.2f") / 100.0
            multa_pct = st.number_input("Multa (% flat na perda)", min_value=0.0, value=2.0, step=0.1, format="%.2f") / 100.0
        with col_c:
            prob_pdd_pct = st.number_input("Probabilidade de PDD (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, format="%.2f")
            dias_atraso = st.number_input("Dias de atraso (para mora)", min_value=0, value=0, step=1)

        prob_pdd = prob_pdd_pct / 100.0

        # Juros proporcionais ao prazo (base 30 dias corridos por mês) sobre todo o principal
        taxa_juros_dia = (1 + taxa_juros_am) ** (1/30) - 1
        juros_total = ticket * (((1 + taxa_juros_dia) ** prazo_dias) - 1)

        # Penalidades: multa flat sobre o principal + mora proporcional aos dias de atraso sobre o principal
        mora_dia = mora_pct / 30.0
        multa_val = ticket * multa_pct
        mora_val = ticket * mora_dia * dias_atraso
        penalidade = multa_val + mora_val

        # Fluxos: saída inicial + entrada única no vencimento (principal + juros + penalidades)
        cfs = [-preco_compra + tac_val]
        recebimento_final = ticket + juros_total + penalidade
        cfs.append(recebimento_final)

        def calc_irr(vals):
            arr = np.array(vals, dtype=float)
            # precisa de pelo menos um fluxo positivo e um negativo
            if not (np.any(arr > 0) and np.any(arr < 0)):
                return np.nan
            # 1) Tenta numpy_financial, se existir
            try:
                import numpy_financial as npf  # type: ignore
                return float(npf.irr(arr))
            except Exception:
                pass
            # 2) Tenta np.irr (deprecated/ausente em numpy>=2)
            irr_attr = getattr(np, "irr", None)
            if irr_attr is not None:
                try:
                    return float(irr_attr(arr))
                except Exception:
                    pass
            # 3) Newton-Raphson simples como fallback
            r = 0.1
            for _ in range(100):
                denom = (1 + r) ** np.arange(len(arr))
                f = np.sum(arr / denom)
                df = np.sum(-np.arange(len(arr)) * arr / ((1 + r) ** (np.arange(len(arr)) + 1)))
                if df == 0:
                    break
                r_new = r - f / df
                if not np.isfinite(r_new):
                    break
                if abs(r_new - r) < 1e-8:
                    return r_new
                r = r_new
            return np.nan

        # TIR bruta: extrai taxa diária dos dois fluxos e converte para mês (30d) e ano (365d)
        irr_d = np.nan
        if recebimento_final > 0 and (-cfs[0]) > 0:
            irr_d = (recebimento_final / (-cfs[0])) ** (1 / prazo_dias) - 1
        irr_valid = irr_d is not None and not np.isnan(irr_d)
        irr_m = (1 + irr_d) ** 30 - 1 if irr_valid else np.nan
        irr_a = (1 + irr_d) ** 365 - 1 if irr_valid else np.nan

        # TIR líquida: aplica PDD como redutor percentual da TIR (LGD)
        pdd_esperada = ticket * prob_pdd
        irr_m_liq = irr_m * (1 - prob_pdd) if irr_valid else np.nan
        irr_liq_valid = irr_m_liq is not None and not np.isnan(irr_m_liq)
        irr_a_liq = (1 + irr_m_liq) ** 12 - 1 if irr_liq_valid else np.nan
        retorno_periodo = (recebimento_final / (-cfs[0])) - 1 if irr_valid else np.nan
        retorno_periodo_liq = retorno_periodo * (1 - prob_pdd) if irr_valid else np.nan

        col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
        col_k1.metric("Retorno do período (bruto)", f"{retorno_periodo*100:.2f}%" if irr_valid else "N/A")
        col_k2.metric("Retorno do período (líquido PDD)", f"{retorno_periodo_liq*100:.2f}%" if irr_liq_valid else "N/A")
        col_k3.metric("TIR mensal (bruta)", f"{irr_m*100:.2f}%" if irr_valid else "N/A")
        col_k4.metric("TIR mensal líquida (após PDD)", f"{irr_m_liq*100:.2f}%" if irr_liq_valid else "N/A")
        col_k5.metric("TIR anualizada líquida", f"{irr_a_liq*100:.2f}%" if irr_liq_valid else "N/A")

        # Pequena visão dos fluxos e total a receber
        total_inflow = recebimento_final + tac_val
        st.markdown("##### Resumo dos fluxos")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Total a receber (R$)", format_brl(total_inflow))
            st.metric("Receita de juros total (R$)", format_brl(juros_total))
        with col_f2:
            st.metric("Penalidades esperadas (R$)", format_brl(penalidade))
            st.metric("TAC (R$)", format_brl(tac_val))
            st.metric("PDD esperada (R$)", format_brl(pdd_esperada))

        with st.expander("Hipóteses do simulador"):
            st.markdown(
                """
                - Operação bullet simples: juros mensais sobre o saldo total, principal no vencimento.
                - TAC recebida upfront, somada ao fluxo inicial.
                - PDD é apenas informativa para penalidades; não reduz a base de juros nem o principal performing.
                - Mora e multa são percentuais mensais aplicados sobre a fração inadimplente.
                - Ajuste os campos para refletir políticas específicas (ex.: parcelas iguais, amortizações, outros encargos).
                """
            )
    
    # ============================================================
    # SUB-ABA 1: SENSIBILIDADE DE TAXA DA CARTEIRA
    # ============================================================
    with subtab1:
        st.markdown("### Análise de Sensibilidade: Taxa da Carteira vs Retorno da Júnior")
        st.caption("Veja como variações na taxa da carteira impactam o retorno da Cota Júnior")
        
        col_s1, col_s2 = st.columns([2, 1])
        
        with col_s2:
            st.markdown("**Parâmetros da Simulação:**")
            
            # Range de variação da taxa
            taxa_min_sim = st.number_input(
                "Taxa mínima (% a.m.)",
                min_value=0.0,
                max_value=10.0,
                value=max(0.5, taxa_carteira_am_pct - 1.5),
                step=0.1,
                format="%.2f"
            )
            taxa_max_sim = st.number_input(
                "Taxa máxima (% a.m.)",
                min_value=0.0,
                max_value=10.0,
                value=taxa_carteira_am_pct + 1.5,
                step=0.1,
                format="%.2f"
            )
            
            # Checkbox para incluir PDD variável
            pdd_variavel = st.checkbox(
                "Simular PDD variável (aumenta com inadimplência)",
                value=False
            )
            
            if pdd_variavel:
                fator_pdd = st.slider(
                    "Fator de aumento da PDD (%)",
                    min_value=0,
                    max_value=200,
                    value=100,
                    step=10
                ) / 100.0
            else:
                fator_pdd = 1.0
        
        with col_s1:
            # Gerar curva de sensibilidade
            n_pontos = 50
            taxas_sim = np.linspace(taxa_min_sim/100, taxa_max_sim/100, n_pontos)
            retornos_junior_sim = []
            resultado_liquido_sim = []
            pdd_sim_values = []
            
            for taxa_sim_am in taxas_sim:
                taxa_sim_diaria = mensal_to_diario(taxa_sim_am)
                receita_cart_sim = valor_recebiveis * taxa_sim_diaria
                receita_total_sim = receita_cart_sim + receita_caixa_dia + receita_outros_dia
                
                # PDD ajustada se variável
                pdd_sim = pdd_dia * fator_pdd
                pdd_sim_values.append(pdd_sim * 252)
                
                resultado_sim = (
                    receita_total_sim
                    - custo_senior_dia
                    - custo_mezz_dia
                    - custo_adm_dia
                    - custo_gestao_dia
                    - pdd_sim
                    - custo_outros_dia
                )
                
                resultado_liquido_sim.append(resultado_sim * 252)  # Anualizado
                
                ret_diario_sim = resultado_sim / valor_junior if valor_junior > 0 else 0
                ret_anual_sim = (1 + ret_diario_sim) ** 252 - 1
                retornos_junior_sim.append(ret_anual_sim * 100)
            
            # Criar gráfico
            fig_sens = go.Figure()
            
            # Linha principal de retorno
            fig_sens.add_trace(go.Scatter(
                x=taxas_sim * 100,
                y=retornos_junior_sim,
                mode='lines',
                name='Retorno Júnior',
                line=dict(color='#3498db', width=3),
                hovertemplate='Taxa: %{x:.2f}% a.m.<br>Retorno: %{y:.2f}% a.a.<extra></extra>'
            ))
            
            # Marcar ponto atual
            idx_atual = np.argmin(np.abs(taxas_sim - taxa_carteira_am))
            fig_sens.add_trace(go.Scatter(
                x=[taxa_carteira_am_pct],
                y=[retornos_junior_sim[idx_atual]],
                mode='markers+text',
                name='Cenário Atual',
                marker=dict(size=15, color='red', symbol='star'),
                text=['ATUAL'],
                textposition='top center',
                hovertemplate='<b>Cenário Atual</b><br>Taxa: %{x:.2f}% a.m.<br>Retorno: %{y:.2f}% a.a.<extra></extra>'
            ))
            
            # Linha de break-even (retorno = 0)
            fig_sens.add_hline(
                y=0,
                line_dash="dash",
                line_color="red",
                annotation_text="Break-even (Retorno = 0%)",
                annotation_position="right"
            )
            
            fig_sens.update_layout(
                title={
                    'text': 'Sensibilidade: Taxa da Carteira × Retorno da Cota Júnior',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Taxa da Carteira (% a.m.)',
                yaxis_title='Retorno Anualizado da Júnior (% a.a.)',
                height=450,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_sens, use_container_width=True)
        
        # Métricas de insights
        st.markdown("---")
        st.markdown("**💡 Insights da Análise:**")
        
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        
        # Taxa de break-even
        idx_breakeven = np.argmin(np.abs(np.array(retornos_junior_sim)))
        taxa_breakeven = taxas_sim[idx_breakeven] * 100
        
        col_i1.metric(
            "Taxa de Break-even",
            f"{taxa_breakeven:.2f}% a.m.",
            delta=f"{taxa_breakeven - taxa_carteira_am_pct:.2f} p.p.",
            delta_color="inverse"
        )
        
        # Elasticidade (variação % retorno / variação % taxa)
        if len(retornos_junior_sim) > 1:
            delta_ret = retornos_junior_sim[-1] - retornos_junior_sim[0]
            delta_taxa = (taxas_sim[-1] - taxas_sim[0]) * 100
            elasticidade = delta_ret / delta_taxa if delta_taxa != 0 else 0
        else:
            elasticidade = 0
        
        col_i2.metric(
            "Elasticidade",
            f"{elasticidade:.2f}",
            help="Variação % no retorno para cada 1 p.p. de variação na taxa"
        )
        
        # Retorno máximo e mínimo
        ret_max = max(retornos_junior_sim)
        ret_min = min(retornos_junior_sim)
        
        col_i3.metric(
            "Retorno Máximo",
            f"{ret_max:.2f}% a.a.",
            delta=f"Taxa: {taxa_max_sim:.2f}% a.m.",
            delta_color="off"
        )
        
        col_i4.metric(
            "Retorno Mínimo",
            f"{ret_min:.2f}% a.a.",
            delta=f"Taxa: {taxa_min_sim:.2f}% a.m.",
            delta_color="off"
        )
    
    # ============================================================
    # SUB-ABA 2: SIMULADOR DE CENÁRIOS MÚLTIPLOS
    # ============================================================
    with subtab2:
        st.markdown("### Simulador de Cenários Múltiplos")
        st.caption("Compare diferentes combinações de parâmetros e veja o impacto no resultado do fundo")
        
        st.markdown("**Configure até 3 cenários para comparação:**")
        
        # Criar 3 colunas para 3 cenários
        col_c1, col_c2, col_c3 = st.columns(3)
        
        cenarios = []
        
        for idx, col in enumerate([col_c1, col_c2, col_c3], 1):
            with col:
                st.markdown(f"**Cenário {idx}**")
                
                if idx == 1:
                    # Cenário 1 = Base (valores atuais)
                    nome_cenario = st.text_input(f"Nome do cenário {idx}", value="Base (Atual)", key=f"nome_{idx}")
                    taxa_c = taxa_carteira_am_pct
                    pdd_mult_c = 1.0
                    spread_s_c = spread_senior_aa_pct
                    spread_m_c = spread_mezz_aa_pct
                    
                    st.metric("Taxa Carteira", f"{taxa_c:.2f}% a.m.")
                    st.metric("PDD Multiplicador", f"{pdd_mult_c:.1f}x")
                    st.metric("Spread Sênior", f"{spread_s_c:.2f}% a.a.")
                    st.metric("Spread Mezz", f"{spread_m_c:.2f}% a.a.")
                else:
                    nome_cenario = st.text_input(f"Nome do cenário {idx}", value=f"Cenário {idx}", key=f"nome_{idx}")
                    
                    taxa_c = st.number_input(
                        f"Taxa Carteira (% a.m.)",
                        min_value=0.0,
                        max_value=10.0,
                        value=taxa_carteira_am_pct,
                        step=0.1,
                        format="%.2f",
                        key=f"taxa_{idx}"
                    )
                    
                    pdd_mult_c = st.number_input(
                        f"Multiplicador PDD",
                        min_value=0.0,
                        max_value=5.0,
                        value=1.0,
                        step=0.1,
                        format="%.1f",
                        key=f"pdd_{idx}"
                    )
                    
                    spread_s_c = st.number_input(
                        f"Spread Sênior (% a.a.)",
                        min_value=0.0,
                        max_value=10.0,
                        value=spread_senior_aa_pct,
                        step=0.25,
                        format="%.2f",
                        key=f"spread_s_{idx}"
                    )
                    
                    spread_m_c = st.number_input(
                        f"Spread Mezz (% a.a.)",
                        min_value=0.0,
                        max_value=10.0,
                        value=spread_mezz_aa_pct,
                        step=0.25,
                        format="%.2f",
                        key=f"spread_m_{idx}"
                    )
                
                cenarios.append({
                    'nome': nome_cenario,
                    'taxa_carteira_am': taxa_c / 100,
                    'pdd_mult': pdd_mult_c,
                    'spread_senior_aa': spread_s_c / 100,
                    'spread_mezz_aa': spread_m_c / 100
                })
        
        # Calcular resultados para cada cenário
        st.markdown("---")
        st.markdown("**📊 Comparação de Resultados:**")
        
        resultados_cenarios = []
        
        for cen in cenarios:
            # Recalcular com parâmetros do cenário
            taxa_cart_diaria_c = mensal_to_diario(cen['taxa_carteira_am'])
            receita_cart_c = valor_recebiveis * taxa_cart_diaria_c
            receita_total_c = receita_cart_c + receita_caixa_dia + receita_outros_dia
            
            taxa_senior_aa_c = cdi_aa + cen['spread_senior_aa']
            taxa_mezz_aa_c = cdi_aa + cen['spread_mezz_aa']
            taxa_senior_diaria_c = anual_to_diario(taxa_senior_aa_c)
            taxa_mezz_diaria_c = anual_to_diario(taxa_mezz_aa_c)
            
            custo_senior_c = valor_senior * taxa_senior_diaria_c
            custo_mezz_c = valor_mezz * taxa_mezz_diaria_c
            
            pdd_c = pdd_dia * cen['pdd_mult']
            
            resultado_liquido_c = (
                receita_total_c
                - custo_senior_c
                - custo_mezz_c
                - custo_adm_dia
                - custo_gestao_dia
                - pdd_c
                - custo_outros_dia
            )
            
            resultado_junior_c = resultado_liquido_c
            ret_diario_junior_c = resultado_junior_c / valor_junior if valor_junior > 0 else 0
            ret_anual_junior_c = (1 + ret_diario_junior_c) ** 252 - 1
            
            resultados_cenarios.append({
                'Cenário': cen['nome'],
                'Receita Total (dia)': receita_total_c,
                'Custo Sênior (dia)': custo_senior_c,
                'Custo Mezz (dia)': custo_mezz_c,
                'PDD (dia)': pdd_c,
                'Resultado Júnior (dia)': resultado_junior_c,
                'Retorno Júnior (% a.a.)': ret_anual_junior_c * 100,
                'Resultado Anual Júnior': resultado_junior_c * 252
            })
        
        # Criar DataFrame
        df_cenarios = pd.DataFrame(resultados_cenarios)
        
        # Gráfico de barras comparativo
        fig_comp = go.Figure()
        
        fig_comp.add_trace(go.Bar(
            name='Receita Total',
            x=df_cenarios['Cenário'],
            y=df_cenarios['Receita Total (dia)'],
            marker_color='#2ecc71'
        ))
        
        fig_comp.add_trace(go.Bar(
            name='Custo Sênior',
            x=df_cenarios['Cenário'],
            y=df_cenarios['Custo Sênior (dia)'],
            marker_color='#e74c3c'
        ))
        
        fig_comp.add_trace(go.Bar(
            name='Custo Mezz',
            x=df_cenarios['Cenário'],
            y=df_cenarios['Custo Mezz (dia)'],
            marker_color='#f39c12'
        ))
        
        fig_comp.add_trace(go.Bar(
            name='PDD',
            x=df_cenarios['Cenário'],
            y=df_cenarios['PDD (dia)'],
            marker_color='#95a5a6'
        ))
        
        fig_comp.update_layout(
            title={
                'text': 'Comparação de Receitas e Custos por Cenário (Diário)',
                'x': 0.5,
                'xanchor': 'center'
            },
            barmode='group',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Gráfico de retorno da Júnior
        fig_ret = go.Figure()
        
        colors = ['#3498db' if i == 0 else '#95a5a6' for i in range(len(df_cenarios))]
        
        fig_ret.add_trace(go.Bar(
            x=df_cenarios['Cenário'],
            y=df_cenarios['Retorno Júnior (% a.a.)'],
            marker_color=colors,
            text=[f"{v:.2f}%" for v in df_cenarios['Retorno Júnior (% a.a.)']],
            textposition='outside'
        ))
        
        fig_ret.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Break-even"
        )
        
        fig_ret.update_layout(
            title={
                'text': 'Retorno Anualizado da Cota Júnior por Cenário',
                'x': 0.5,
                'xanchor': 'center'
            },
            yaxis_title='Retorno (% a.a.)',
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig_ret, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("**📋 Tabela Detalhada:**")
        
        df_display = df_cenarios.copy()
        df_display['Receita Total (dia)'] = df_display['Receita Total (dia)'].apply(format_brl)
        df_display['Custo Sênior (dia)'] = df_display['Custo Sênior (dia)'].apply(format_brl)
        df_display['Custo Mezz (dia)'] = df_display['Custo Mezz (dia)'].apply(format_brl)
        df_display['PDD (dia)'] = df_display['PDD (dia)'].apply(format_brl)
        df_display['Resultado Júnior (dia)'] = df_display['Resultado Júnior (dia)'].apply(format_brl)
        df_display['Resultado Anual Júnior'] = df_display['Resultado Anual Júnior'].apply(format_brl)
        df_display['Retorno Júnior (% a.a.)'] = df_display['Retorno Júnior (% a.a.)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # ============================================================
    # SUB-ABA 3: ANÁLISE DE BREAK-EVEN
    # ============================================================
    with subtab3:
        st.markdown("### Análise de Break-even: Taxa Mínima por Nível de PDD")
        st.caption("Descubra qual a taxa mínima da carteira necessária para diferentes níveis de inadimplência")
        
        col_b1, col_b2 = st.columns([2, 1])
        
        with col_b2:
            st.markdown("**Parâmetros:**")
            
            retorno_alvo_breakeven = st.number_input(
                "Retorno alvo da Júnior (% a.a.)",
                min_value=-50.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                help="0% = break-even (não ganha nem perde)"
            )
            
            pdd_max_analise = st.slider(
                "PDD máxima para análise (multiplicador)",
                min_value=0.5,
                max_value=5.0,
                value=3.0,
                step=0.1
            )
        
        with col_b1:
            # Calcular taxa mínima para diferentes níveis de PDD
            n_pontos_pdd = 30
            pdd_mults = np.linspace(0.5, pdd_max_analise, n_pontos_pdd)
            taxas_minimas = []
            
            ret_alvo_diario = anual_to_diario(retorno_alvo_breakeven / 100)
            resultado_alvo_dia = ret_alvo_diario * valor_junior
            
            for pdd_mult in pdd_mults:
                pdd_sim = pdd_dia * pdd_mult
                
                # Resultado alvo = Receita total - Custos
                # Receita total = Receita carteira + Receita caixa + Outras
                # Receita carteira = valor_recebiveis * taxa_diaria
                # Resolver para taxa_diaria
                
                custos_totais = (
                    custo_senior_dia +
                    custo_mezz_dia +
                    custo_adm_dia +
                    custo_gestao_dia +
                    pdd_sim +
                    custo_outros_dia
                )
                
                receita_necessaria = resultado_alvo_dia + custos_totais
                receita_carteira_necessaria = receita_necessaria - receita_caixa_dia - receita_outros_dia
                
                if valor_recebiveis > 0:
                    taxa_diaria_necessaria = receita_carteira_necessaria / valor_recebiveis
                    # Converter para mensal
                    taxa_aa_necessaria = (1 + taxa_diaria_necessaria) ** 252 - 1
                    taxa_am_necessaria = (1 + taxa_aa_necessaria) ** (1/12) - 1
                    taxas_minimas.append(taxa_am_necessaria * 100)
                else:
                    taxas_minimas.append(0)
            
            # Criar gráfico
            fig_breakeven = go.Figure()
            
            fig_breakeven.add_trace(go.Scatter(
                x=pdd_mults,
                y=taxas_minimas,
                mode='lines',
                name='Taxa Mínima',
                line=dict(color='#e74c3c', width=3),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.1)',
                hovertemplate='PDD: %{x:.2f}x<br>Taxa Mín: %{y:.2f}% a.m.<extra></extra>'
            ))
            
            # Marcar ponto atual
            idx_atual_pdd = np.argmin(np.abs(pdd_mults - 1.0))
            fig_breakeven.add_trace(go.Scatter(
                x=[1.0],
                y=[taxas_minimas[idx_atual_pdd]],
                mode='markers+text',
                name='PDD Atual',
                marker=dict(size=15, color='blue', symbol='diamond'),
                text=['ATUAL'],
                textposition='top center'
            ))
            
            # Linha da taxa atual
            fig_breakeven.add_hline(
                y=taxa_carteira_am_pct,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Taxa Atual ({taxa_carteira_am_pct:.2f}% a.m.)",
                annotation_position="right"
            )
            
            fig_breakeven.update_layout(
                title={
                    'text': f'Taxa Mínima da Carteira para Retorno de {retorno_alvo_breakeven:.1f}% a.a.',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Multiplicador de PDD (1.0 = Base)',
                yaxis_title='Taxa Mínima da Carteira (% a.m.)',
                height=450,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_breakeven, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.markdown("**💡 Análise de Margem de Segurança:**")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # Taxa mínima para PDD atual
        taxa_min_atual = taxas_minimas[idx_atual_pdd]
        margem_taxa = taxa_carteira_am_pct - taxa_min_atual
        
        col_m1.metric(
            "Taxa Mínima (PDD Atual)",
            f"{taxa_min_atual:.2f}% a.m.",
            delta=f"Margem: {margem_taxa:.2f} p.p.",
            delta_color="normal" if margem_taxa > 0 else "inverse"
        )
        
        # PDD máxima suportável com taxa atual
        if taxa_carteira_am_pct >= min(taxas_minimas):
            idx_pdd_max = np.argmin(np.abs(np.array(taxas_minimas) - taxa_carteira_am_pct))
            pdd_max_suportavel = pdd_mults[idx_pdd_max]
        else:
            pdd_max_suportavel = 0
        
        col_m2.metric(
            "PDD Máxima Suportável",
            f"{pdd_max_suportavel:.2f}x",
            delta=f"{(pdd_max_suportavel - 1.0):.2f}x acima da base",
            delta_color="normal" if pdd_max_suportavel > 1 else "inverse"
        )
        
        # Elasticidade
        if len(taxas_minimas) > 1:
            delta_taxa_be = taxas_minimas[-1] - taxas_minimas[0]
            delta_pdd_be = pdd_mults[-1] - pdd_mults[0]
            elasticidade_be = delta_taxa_be / delta_pdd_be if delta_pdd_be != 0 else 0
        else:
            elasticidade_be = 0
        
        col_m3.metric(
            "Sensibilidade Taxa/PDD",
            f"{elasticidade_be:.2f} p.p./x",
            help="Aumento na taxa (p.p.) necessário para cada 1x de aumento na PDD"
        )
    
    # ============================================================
    # SUB-ABA 4: HEATMAP DE SENSIBILIDADE
    # ============================================================
    with subtab4:
        st.markdown("### Heatmap de Sensibilidade: Taxa × PDD")
        st.caption("Visualização 2D do retorno da Júnior para diferentes combinações de taxa da carteira e PDD")
        
        col_h1, col_h2 = st.columns([3, 1])
        
        with col_h2:
            st.markdown("**Parâmetros do Heatmap:**")
            
            n_pontos_taxa_heat = st.slider(
                "Resolução (Taxa)",
                min_value=10,
                max_value=30,
                value=20,
                step=5
            )
            
            n_pontos_pdd_heat = st.slider(
                "Resolução (PDD)",
                min_value=10,
                max_value=30,
                value=20,
                step=5
            )
            
            taxa_min_heat = st.number_input(
                "Taxa mín (% a.m.)",
                min_value=0.0,
                value=max(0.5, taxa_carteira_am_pct - 1.0),
                step=0.1,
                format="%.2f"
            )
            
            taxa_max_heat = st.number_input(
                "Taxa máx (% a.m.)",
                min_value=0.0,
                value=taxa_carteira_am_pct + 1.0,
                step=0.1,
                format="%.2f"
            )
            
            pdd_min_heat = st.slider(
                "PDD mín (multiplicador)",
                min_value=0.0,
                max_value=2.0,
                value=0.5,
                step=0.1
            )
            
            pdd_max_heat = st.slider(
                "PDD máx (multiplicador)",
                min_value=0.0,
                max_value=5.0,
                value=2.5,
                step=0.1
            )
        
        with col_h1:
            # Gerar grid de valores
            taxas_heat = np.linspace(taxa_min_heat/100, taxa_max_heat/100, n_pontos_taxa_heat)
            pdd_mults_heat = np.linspace(pdd_min_heat, pdd_max_heat, n_pontos_pdd_heat)
            
            retornos_heat = np.zeros((n_pontos_pdd_heat, n_pontos_taxa_heat))
            
            for i, pdd_mult_h in enumerate(pdd_mults_heat):
                for j, taxa_h_am in enumerate(taxas_heat):
                    taxa_h_diaria = mensal_to_diario(taxa_h_am)
                    receita_cart_h = valor_recebiveis * taxa_h_diaria
                    receita_total_h = receita_cart_h + receita_caixa_dia + receita_outros_dia
                    
                    pdd_h = pdd_dia * pdd_mult_h
                    
                    resultado_h = (
                        receita_total_h
                        - custo_senior_dia
                        - custo_mezz_dia
                        - custo_adm_dia
                        - custo_gestao_dia
                        - pdd_h
                        - custo_outros_dia
                    )
                    
                    ret_diario_h = resultado_h / valor_junior if valor_junior > 0 else 0
                    ret_anual_h = (1 + ret_diario_h) ** 252 - 1
                    retornos_heat[i, j] = ret_anual_h * 100
            
            # Criar heatmap
            fig_heat = go.Figure(data=go.Heatmap(
                z=retornos_heat,
                x=taxas_heat * 100,
                y=pdd_mults_heat,
                colorscale='RdYlGn',
                zmid=0,
                colorbar=dict(title="Retorno<br>Júnior<br>(% a.a.)"),
                hovertemplate='Taxa: %{x:.2f}% a.m.<br>PDD: %{y:.2f}x<br>Retorno: %{z:.2f}% a.a.<extra></extra>'
            ))
            
            # Marcar ponto atual
            fig_heat.add_trace(go.Scatter(
                x=[taxa_carteira_am_pct],
                y=[1.0],
                mode='markers+text',
                marker=dict(size=15, color='white', symbol='star', line=dict(color='black', width=2)),
                text=['ATUAL'],
                textposition='top center',
                textfont=dict(color='white', size=12),
                name='Cenário Atual',
                showlegend=False
            ))
            
            fig_heat.update_layout(
                title={
                    'text': 'Heatmap: Retorno da Júnior (Taxa × PDD)',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Taxa da Carteira (% a.m.)',
                yaxis_title='Multiplicador de PDD',
                height=500
            )
            
            st.plotly_chart(fig_heat, use_container_width=True)
        
        # Tabela de cenários críticos
        st.markdown("---")
        st.markdown("**🎯 Cenários Críticos Identificados:**")
        
        col_cr1, col_cr2, col_cr3 = st.columns(3)
        
        # Melhor cenário
        idx_melhor = np.unravel_index(np.argmax(retornos_heat), retornos_heat.shape)
        melhor_ret = retornos_heat[idx_melhor]
        melhor_taxa = taxas_heat[idx_melhor[1]] * 100
        melhor_pdd = pdd_mults_heat[idx_melhor[0]]
        
        col_cr1.markdown("**🟢 Melhor Cenário**")
        col_cr1.metric("Retorno", f"{melhor_ret:.2f}% a.a.")
        col_cr1.caption(f"Taxa: {melhor_taxa:.2f}% a.m. | PDD: {melhor_pdd:.2f}x")
        
        # Pior cenário
        idx_pior = np.unravel_index(np.argmin(retornos_heat), retornos_heat.shape)
        pior_ret = retornos_heat[idx_pior]
        pior_taxa = taxas_heat[idx_pior[1]] * 100
        pior_pdd = pdd_mults_heat[idx_pior[0]]
        
        col_cr2.markdown("**🔴 Pior Cenário**")
        col_cr2.metric("Retorno", f"{pior_ret:.2f}% a.a.")
        col_cr2.caption(f"Taxa: {pior_taxa:.2f}% a.m. | PDD: {pior_pdd:.2f}x")
        
        # Cenário atual
        idx_taxa_atual = np.argmin(np.abs(taxas_heat - taxa_carteira_am))
        idx_pdd_atual = np.argmin(np.abs(pdd_mults_heat - 1.0))
        atual_ret = retornos_heat[idx_pdd_atual, idx_taxa_atual]
        
        col_cr3.markdown("**⭐ Cenário Atual**")
        col_cr3.metric("Retorno", f"{atual_ret:.2f}% a.a.")
        col_cr3.caption(f"Taxa: {taxa_carteira_am_pct:.2f}% a.m. | PDD: 1.00x")

# -------------------------------------------------------------------
# ABA 4 – DRE PROJETADO (MÊS A MÊS POR 1 ANO)
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
    base_outras_receitas_mes = receita_outros_dia * (252 / 12)  # aprox. = outros_receitas_mensais
    base_outros_custos_mes = custo_outros_dia * (252 / 12)      # aprox. = outros_custos_mensais

    df_param_base = pd.DataFrame({
        "Mês": meses,
        "Taxa carteira (% a.m.)": [base_taxa_carteira] * 12,
        "% PL em recebíveis": [base_pct_recebiveis] * 12,
        "Outras receitas (R$/mês)": [base_outras_receitas_mes] * 12,
        "Outros custos (R$/mês)": [base_outros_custos_mes] * 12,
        "PDD manual (R$/mês)": [0.0] * 12,
        # Movimento líquido: + = aporte, - = resgate
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
    dias_uteis_mes = dias_uteis_ano / meses_ano  # ~21 dias úteis/mês

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

        # PDD aproximada mensal: % de perda esperada sobre recebíveis no ano,
        # rateado em 12 meses. Soma valor manual informado.
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

        # Todo o resultado residual é da Cota Júnior
        resultado_junior_mes = resultado_fundo_mes

        # ----- PL FINAL DO MÊS -----
        # Sênior e Mezz recebem juros; acumula o saldo já com o custo do mês.
        pl_mezz_final   = pl_mezz_mov + custo_mezz_mes
        pl_senior_final = pl_senior_mov + custo_senior_mes
        pl_junior_final = pl_junior_mov + resultado_junior_mes
        # Total mostrado na visão gráfica reflete apenas Sênior + Mezz (saldo + juros)
        pl_total_final  = pl_mezz_final + pl_senior_final

        # Retorno da Júnior no mês (% sobre PL após movimentos)
        base_retorno_jr = pl_junior_mov if pl_junior_mov != 0 else 1.0
        retorno_jr_mes_pct = resultado_junior_mes / base_retorno_jr

        # Guardar linha da DRE
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
            "PL Final Júnior (R$)": pl_junior_final,
            "Retorno Júnior no mês (%)": retorno_jr_mes_pct * 100,
        })

        # Atualizar PL para o próximo mês
        pl_junior = pl_junior_final
        pl_mezz   = pl_mezz_final
        pl_senior = pl_senior_final

    # ---------------------------
    # TABELA FINAL DA DRE MENSAL
    # ---------------------------
    df_dre_mensal = pd.DataFrame(linhas_dre_mensal)

    st.markdown("#### DRE mês a mês (12 meses)")

    df_dre_show = df_dre_mensal.copy()

    # Formatação numérica
    for col in df_dre_show.columns:
        if col == "Mês":
            continue
        if "Retorno" in col and "(%)" in col:
            df_dre_show[col] = df_dre_show[col].apply(lambda x: f"{x:,.2f} %")
        else:
            df_dre_show[col] = df_dre_show[col].apply(format_brl)

    st.dataframe(df_dre_show, use_container_width=True, height=500)

    # ---------------------------
    # EXPORTAR PARÂMETROS + DRE PARA EXCEL
    # ---------------------------
    st.markdown("#### 📥 Exportar para Excel")

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_param.to_excel(writer, index=False, sheet_name="Parametros_12m")
        df_dre_mensal.to_excel(writer, index=False, sheet_name="DRE_12m")
    buffer.seek(0)

    st.download_button(
        label="Baixar Excel (Parâmetros + DRE 12m)",
        data=buffer,
        file_name="fidc_dre_12m.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ---------------------------
    # GRÁFICOS RESUMO (incluindo PDD)
    # ---------------------------
    st.markdown("---")
    st.markdown("#### Visão gráfica")

    col_g1, col_g2 = st.columns(2)

    # 1) Evolução do PL + PDD
    with col_g1:
        st.markdown("**Evolução do PL Final (Total e Júnior) + PDD mensal**")
        fig_pl = go.Figure()

        fig_pl.add_trace(go.Scatter(
            x=df_dre_mensal["Mês"],
            y=df_dre_mensal["PL Final (R$)"],
            mode="lines+markers",
            name="PL Final Total",
            yaxis="y1"
        ))
        fig_pl.add_trace(go.Scatter(
            x=df_dre_mensal["Mês"],
            y=df_dre_mensal["PL Final Júnior (R$)"],
            mode="lines+markers",
            name="PL Final Júnior",
            yaxis="y1"
        ))
        # PDD em eixo secundário
        fig_pl.add_trace(go.Bar(
            x=df_dre_mensal["Mês"],
            y=df_dre_mensal["PDD (R$)"],
            name="PDD do mês (R$)",
            opacity=0.4,
            yaxis="y2"
        ))

        fig_pl.update_layout(
            height=380,
            xaxis=dict(title="Mês"),
            yaxis=dict(title="PL (R$)", side="left"),
            yaxis2=dict(
                title="PDD (R$)",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            barmode="overlay",
            margin=dict(l=50, r=50, t=40, b=40)
        )
        st.plotly_chart(fig_pl, use_container_width=True)

    # 2) Retorno da Júnior + PDD em % do PL Júnior
    with col_g2:
        st.markdown("**Retorno da Cota Júnior e peso da PDD**")

        # PDD como % do PL Júnior após movimentos
        pdd_pct_sobre_junior = []
        for i, row in df_dre_mensal.iterrows():
            base_j = row["PL Final Júnior (R$)"] - row["Resultado Cota Júnior (R$)"]  # aprox base = PL após movimentos
            if base_j != 0:
                pdd_pct_sobre_junior.append(row["PDD (R$)"] / base_j * 100)
            else:
                pdd_pct_sobre_junior.append(0.0)

        fig_ret = go.Figure()

        fig_ret.add_trace(go.Bar(
            x=df_dre_mensal["Mês"],
            y=df_dre_mensal["Retorno Júnior no mês (%)"],
            name="Retorno Júnior (%)",
            text=[f"{v:,.2f}%" for v in df_dre_mensal["Retorno Júnior no mês (%)"]],
            textposition="outside",
            yaxis="y1"
        ))

        fig_ret.add_trace(go.Scatter(
            x=df_dre_mensal["Mês"],
            y=pdd_pct_sobre_junior,
            mode="lines+markers",
            name="PDD / PL Júnior (%)",
            yaxis="y2"
        ))

        fig_ret.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            yref="y1"
        )

        fig_ret.update_layout(
            height=380,
            xaxis_title="Mês",
            yaxis=dict(title="Retorno Júnior no mês (%)", side="left"),
            yaxis2=dict(
                title="PDD / PL Júnior (%)",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            margin=dict(l=50, r=50, t=40, b=40)
        )
        st.plotly_chart(fig_ret, use_container_width=True)


    
# -------------------------------------------------------------------
# ABA 5 – CAPACIDADE DE ABSORÇÃO (Visualização Corrigida - Ponto 1.0x Fixo)
# -------------------------------------------------------------------
with tab_pdd_stress:
    st.subheader("🧪 Stress Test: Capacidade de Absorção de Perdas")
    
    # --- VALIDAÇÕES E CÁLCULOS ESTRUTURAIS ---
    if pl_total <= 0 or valor_junior <= 0:
        st.error("O PL e a Cota Júnior precisam ser maiores que zero para calcular o stress.")
    elif pdd_base <= 0:
        st.warning("A PDD Base é zero. Ajuste as provisões (%) na barra lateral para ver o efeito do stress.")
    else:
        # 1. CÁLCULO DO PONTO DE RUPTURA
        if sub_min >= 1.0:
            limite_perda_enquadramento = 0.0
        else:
            numerador = valor_junior - (sub_min * pl_total)
            denominador = 1 - sub_min
            limite_perda_enquadramento = max(0.0, numerador / denominador) if denominador != 0 else 0.0
            
            if limite_perda_enquadramento > valor_junior:
                limite_perda_enquadramento = valor_junior

        # 2. CÁLCULOS DO CENÁRIO ATUAL
        margem_seguranca_atual = limite_perda_enquadramento - pdd_base
        mult_ruptura = limite_perda_enquadramento / pdd_base if pdd_base > 0 else 0
        pdd_pct_recebiveis_atual = taxa_perda_esperada * 100 

        # --- SEÇÃO 1: FOTOGRAFIA ATUAL ---
        st.markdown("### 📸 Cenário Atual (Baseado nos parâmetros da Sidebar)")
        col_real1, col_real2, col_real3, col_real4 = st.columns(4)
        
        with col_real1:
            st.metric("PDD Atual (Esperada)", format_brl(pdd_base), delta=f"{pdd_pct_recebiveis_atual:.2f}% da Carteira", delta_color="off")
        with col_real2:
            st.metric("Capacidade Máxima de Perda", format_brl(limite_perda_enquadramento), help="Teto máximo de PDD.")
        with col_real3:
            cor_margem = "normal" if margem_seguranca_atual > 0 else "inverse"
            st.metric("Margem de Segurança (R$)", format_brl(margem_seguranca_atual), delta="Dinheiro 'livre' no colchão", delta_color=cor_margem)
        with col_real4:
            st.metric("Multiplicador de Ruptura", f"{mult_ruptura:.2f}x", help="Se < 1.0x, o fundo já está desenquadrado hoje.")

        st.divider()

        # --- SEÇÃO 2: SIMULAÇÃO ---
        st.markdown("### 🕹️ Simulação de Stress")
        c_sim_input, c_sim_kpi = st.columns([1, 2])
        
        with c_sim_input:
            st.markdown("**Calibre o nível de estresse:**")
            # Ajuste dinâmico do máximo do slider para sempre caber o 1.0 e a ruptura
            max_slider = max(5.0, mult_ruptura * 1.5)
            user_mult = st.slider("Multiplicar PDD Atual por:", min_value=0.0, max_value=max_slider, value=1.0, step=0.1)
            
        perda_simulada = pdd_base * user_mult
        margem_restante_simulada = limite_perda_enquadramento - perda_simulada
        
        jr_sim = max(0, valor_junior - perda_simulada)
        pl_sim = max(0, pl_total - perda_simulada)
        sub_sim_pct = (jr_sim / pl_sim * 100) if pl_sim > 0 else 0.0
        
        with c_sim_kpi:
            k1, k2, k3 = st.columns(3)
            if perda_simulada > limite_perda_enquadramento:
                lbl_delta = "🚨 DESENQUADRADO"
                cor_delta_sim = "inverse"
            else:
                lbl_delta = "✅ ENQUADRADO"
                cor_delta_sim = "normal"

            k1.metric("Nova PDD Simulada", format_brl(perda_simulada), delta=f"{user_mult:.1f}x da base", delta_color="off")
            k2.metric("Subordinação Resultante", f"{sub_sim_pct:.2f}%", delta=f"Mínimo: {sub_min_pct:.2f}%", delta_color="off")
            k3.metric("Margem Restante (Simulada)", format_brl(margem_restante_simulada), delta=lbl_delta, delta_color=cor_delta_sim)

        # --- SEÇÃO 3: GRÁFICO ---
        max_x_graph = max(user_mult * 1.2, mult_ruptura * 1.3, 2.0) # Garante que o 1.0 apareça
        x_vals = np.linspace(0, max_x_graph, 100)
        y_vals = []
        
        # Calcular y para x=1.0 (HOJE)
        loss_today = pdd_base * 1.0
        j_today = max(0, valor_junior - loss_today)
        pl_today = max(0, pl_total - loss_today)
        sub_today_pct = (j_today / pl_today * 100) if pl_today > 0 else 0.0

        for m in x_vals:
            p_loss = pdd_base * m
            j_ = max(0, valor_junior - p_loss)
            pl_ = max(0, pl_total - p_loss)
            y_vals.append((j_ / pl_ * 100) if pl_ > 0 else 0.0)
        
        fig = go.Figure()
        
        # 1. Curva Azul
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='Índice de Subordinação', line=dict(color='#2980b9', width=3)))
        
        # 2. Linha Vermelha (Piso)
        fig.add_trace(go.Scatter(x=[0, max_x_graph], y=[sub_min_pct, sub_min_pct], mode='lines', name='Mínimo Regulatório', line=dict(color='#c0392b', dash='dash')))
        
        # 3. Ponto de Ruptura (X Vermelho)
        if mult_ruptura <= max_x_graph:
            fig.add_trace(go.Scatter(
                x=[mult_ruptura], y=[sub_min_pct], mode='markers', name='Ponto de Ruptura',
                marker=dict(symbol='x', size=12, color='red'),
                hoverinfo='text', text=[f"Ruptura: {mult_ruptura:.2f}x"]
            ))
            fig.add_vline(x=mult_ruptura, line_width=1, line_dash="dot", line_color="gray", opacity=0.5)

        # 4. Ponto HOJE (1.0x) - NOVO!
        fig.add_trace(go.Scatter(
            x=[1.0], y=[sub_today_pct], mode='markers+text', 
            name='HOJE (Realidade)',
            text=["HOJE (1.0x)"], textposition="bottom center",
            marker=dict(size=10, color='black', symbol='square')
        ))

        # 5. Ponto Simulado (Bolinha Roxa)
        fig.add_trace(go.Scatter(
            x=[user_mult], y=[sub_sim_pct], mode='markers+text', 
            name='SIMULAÇÃO',
            text=[f"Simulado ({user_mult}x)"], textposition="top center",
            marker=dict(size=15, color='#8e44ad', line=dict(width=2, color='white'))
        ))

        fig.update_layout(
            title={'text': "Dinâmica de Enquadramento", 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
            xaxis_title="Multiplicador sobre a PDD Base",
            yaxis_title="Índice de Subordinação (%)",
            height=450,
            margin=dict(l=20, r=20, t=80, b=20),
            legend=dict(orientation="h", y=1.02, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
