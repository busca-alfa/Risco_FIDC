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
    # SUB-ABA 0: SIMULADOR DE TAXA (VERSÃO CORRIGIDA)
    # ============================================================
    with subtab_sim_taxa:
        st.markdown("### 💰 Simulador de Taxa do Empréstimo")
        st.caption("Calcule a taxa efetiva considerando deságio (calculado pela taxa), TAC, mora/multa e PDD como redutor de rentabilidade")
        
        # ========== SEÇÃO 1: PARÂMETROS DE ENTRADA ==========
        st.markdown('<div class="section-header">📋 Parâmetros da Operação</div>', unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown("**Estrutura do Crédito:**")
            ticket = st.number_input(
                "Valor de Face (R$)", 
                min_value=1_000.0, 
                value=1_000_000.0, 
                step=50_000.0, 
                format="%.2f",
                help="Valor que o cliente pagará no vencimento"
            )
            taxa_juros_am = st.number_input(
                "Taxa de Juros (% a.m.)", 
                min_value=0.0, 
                value=float(taxa_carteira_am_pct), 
                step=0.25, 
                format="%.2f",
                help="Taxa que define o deságio na compra"
            ) / 100.0
            prazo_dias = st.number_input(
                "Prazo (dias)", 
                min_value=1, 
                value=360, 
                step=30
            )
        
        with col_b:
            st.markdown("**Taxas e Encargos:**")
            tac_val = st.number_input(
                "Outras Taxas (R$)", 
                min_value=0.0, 
                value=20_000.0, 
                step=5_000.0, 
                format="%.2f",
                help="Descontada do desembolso (cliente recebe menos)"
            )
            mora_pct = st.number_input(
                "Mora (% a.m.)", 
                min_value=0.0, 
                value=1.0, 
                step=0.1, 
                format="%.2f",
                help="Juros de mora sobre o valor de face"
            ) / 100.0
            multa_pct = st.number_input(
                "Multa (% flat)", 
                min_value=0.0, 
                value=2.0, 
                step=0.1, 
                format="%.2f",
                help="Multa sobre o valor de face em caso de atraso"
            ) / 100.0
        
        with col_c:
            st.markdown("**Risco e Inadimplência:**")
            prob_pdd_pct = st.number_input(
                "PDD - Probabilidade de Default (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=5.0, 
                step=0.5, 
                format="%.2f",
                help="Reduz a taxa efetiva (não é perda de valor)"
            )
            dias_atraso = st.number_input(
                "Dias de Atraso Médio", 
                min_value=0, 
                value=0, 
                step=5,
                help="Para cálculo de mora"
            )
        
        prob_pdd = prob_pdd_pct / 100.0
        
        # ========== CÁLCULOS ==========
        
        # 1. DESÁGIO: Calculado pela taxa de juros (VPL)
        # Fórmula simplificada: Deságio = Valor de Face × (1 - 1/(1+taxa)^períodos)
        prazo_meses = prazo_dias / 30.0
        if taxa_juros_am > 0:
            fator_desconto = 1 / ((1 + taxa_juros_am) ** prazo_meses)
            desagio_valor = ticket * (1 - fator_desconto)
        else:
            desagio_valor = 0
        
        desagio_pct = (desagio_valor / ticket * 100) if ticket > 0 else 0
        
        # 2. PREÇO DE COMPRA (sem TAC)
        preco_compra = ticket - desagio_valor
        
        # 3. DESEMBOLSO LÍQUIDO (o que o cliente recebe)
        desembolso_liquido = preco_compra - tac_val
        
        # 4. JUROS TOTAIS (sobre o valor de face)
        taxa_juros_dia = (1 + taxa_juros_am) ** (1/30) - 1
        juros_total = ticket * (((1 + taxa_juros_dia) ** prazo_dias) - 1)
        
        # 5. PENALIDADES (se houver atraso)
        mora_dia = mora_pct / 30.0
        multa_val = ticket * multa_pct if dias_atraso > 0 else 0
        mora_val = ticket * mora_dia * dias_atraso
        penalidade_total = multa_val + mora_val
        
        # 6. RECEBIMENTO NO VENCIMENTO
        recebimento_final = ticket + penalidade_total
        # Nota: juros já estão embutidos no valor de face (por isso o deságio)
        
        # 7. TIR BRUTA (sem considerar PDD)
        if recebimento_final > 0 and desembolso_liquido > 0:
            irr_d_bruto = (recebimento_final / desembolso_liquido) ** (1 / prazo_dias) - 1
            irr_m_bruto = (1 + irr_d_bruto) ** 30 - 1
            irr_a_bruto = (1 + irr_d_bruto) ** 365 - 1
            retorno_periodo_bruto = (recebimento_final / desembolso_liquido) - 1
            irr_valid = True
        else:
            irr_d_bruto = irr_m_bruto = irr_a_bruto = retorno_periodo_bruto = np.nan
            irr_valid = False
        
        # 8. TIR LÍQUIDA: PDD reduz a taxa (não o valor)
        # Fórmula: TIR Líquida = TIR Bruta × (1 - PDD%)
        if irr_valid:
            irr_m_liquido = irr_m_bruto * (1 - prob_pdd)
            irr_a_liquido = (1 + irr_m_liquido) ** 12 - 1
            retorno_periodo_liquido = retorno_periodo_bruto * (1 - prob_pdd)
            irr_liq_valid = True
        else:
            irr_m_liquido = irr_a_liquido = retorno_periodo_liquido = np.nan
            irr_liq_valid = False
        
        # 9. RECEITAS E LUCROS
        receita_total_bruta = recebimento_final - desembolso_liquido
        
        # PDD esperada (apenas para informação, não afeta fluxo de caixa)
        pdd_esperada_valor = receita_total_bruta * prob_pdd
        receita_total_liquida = receita_total_bruta - pdd_esperada_valor
        
        # 10. IMPACTO DA TAC NA TIR
        # Calcular TIR sem TAC para comparação
        desembolso_sem_tac = preco_compra
        if recebimento_final > 0 and desembolso_sem_tac > 0:
            irr_d_sem_tac = (recebimento_final / desembolso_sem_tac) ** (1 / prazo_dias) - 1
            irr_m_sem_tac = (1 + irr_d_sem_tac) ** 30 - 1
            irr_m_sem_tac_liq = irr_m_sem_tac * (1 - prob_pdd)
            impacto_tac = (irr_m_bruto - irr_m_sem_tac) * 100  # em p.p.
        else:
            irr_m_sem_tac_liq = np.nan
            impacto_tac = 0
        
        # ========== SEÇÃO 2: RESULTADOS PRINCIPAIS ==========
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Resultados da Simulação</div>', unsafe_allow_html=True)
        
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        
        col_r1.metric(
            "Deságio Calculado",
            f"{desagio_pct:.2f}%",
            delta=format_brl(desagio_valor),
            delta_color="off",
            help="Calculado pela taxa de juros"
        )
        
        col_r2.metric(
            "Desembolso Líquido",
            format_brl(desembolso_liquido),
            delta=f"TAC: {format_brl(tac_val)}",
            delta_color="inverse",
            help="O que o cliente efetivamente recebe"
        )
        
        col_r3.metric(
            "TIR Mensal Bruta",
            f"{irr_m_bruto*100:.2f}%" if irr_valid else "N/A",
            help="Sem considerar PDD"
        )
        
        col_r4.metric(
            "TIR Mensal Líquida",
            f"{irr_m_liquido*100:.2f}%" if irr_liq_valid else "N/A",
            delta=f"-{(irr_m_bruto - irr_m_liquido)*100:.2f} p.p." if irr_liq_valid else "",
            delta_color="inverse",
            help="Após aplicar PDD como redutor"
        )
        
        col_r5.metric(
            "TIR Anual Líquida",
            f"{irr_a_liquido*100:.2f}%" if irr_liq_valid else "N/A",
            help="Taxa anualizada (12 meses)"
        )
        
        # Métricas adicionais
        st.markdown("---")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        col_m1.metric(
            "Retorno do Período",
            f"{retorno_periodo_liquido*100:.2f}%" if irr_valid else "N/A",
            help=f"Retorno total em {prazo_dias} dias"
        )
        
        col_m2.metric(
            "Impacto da TAC",
            f"+{impacto_tac:.2f} p.p." if impacto_tac > 0 else f"{impacto_tac:.2f} p.p.",
            delta=f"TIR sem TAC: {irr_m_sem_tac_liq*100:.2f}%" if not np.isnan(irr_m_sem_tac_liq) else "",
            delta_color="off",
            help="Quanto a TAC aumenta a TIR"
        )
        
        col_m3.metric(
            "Receita Total Bruta",
            format_brl(receita_total_bruta),
            help="Sem considerar PDD"
        )
        
        col_m4.metric(
            "Receita Líquida (c/ PDD)",
            format_brl(receita_total_liquida),
            delta=f"PDD: {format_brl(pdd_esperada_valor)}",
            delta_color="inverse",
            help="Após provisão para PDD"
        )
        
        # ========== SEÇÃO 4: COMPOSIÇÃO DAS RECEITAS (PIZZA) ==========
        st.markdown("---")
        st.markdown('<div class="section-header">🥧 Composição das Receitas</div>', unsafe_allow_html=True)

        col_p1, col_p2 = st.columns([1.5, 1])

        with col_p1:
            # Componentes de receita
            receitas_componentes = {
                'Deságio': desagio_valor,
                'TAC': tac_val,
                'Mora': mora_val,
                'Multa': multa_val
            }
            
            # Filtrar componentes com valor > 0
            receitas_filtradas = {k: v for k, v in receitas_componentes.items() if v > 0}
            
            if receitas_filtradas:
                fig_pizza = go.Figure(data=[go.Pie(
                    labels=list(receitas_filtradas.keys()),
                    values=list(receitas_filtradas.values()),
                    hole=0.4,
                    marker=dict(colors=['#2ecc71', '#f39c12', '#9b59b6', '#e74c3c']),
                    textinfo='label+percent',
                    textposition='outside',
                    hovertemplate='''<b>%{label}</b>  
                    Valor: %{value:,.2f}  
                    %{percent}<extra></extra>'''
                )])
                
                total_receitas = sum(receitas_filtradas.values())
                
                fig_pizza.update_layout(
                    title={
                        'text': f'Total de Receitas: {format_brl(total_receitas)}',
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'size': 16}
                    },
                    height=500,  # ← AUMENTADO
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5)
                )
                
                st.plotly_chart(fig_pizza, use_container_width=True)
            else:
                st.info("Sem componentes de receita para exibir")

        with col_p2:
            st.markdown("**📊 Detalhamento Percentual:**")
            
            total_receitas = sum(receitas_componentes.values())
            
            if total_receitas > 0:
                for componente, valor in receitas_componentes.items():
                    if valor > 0:
                        pct_total = (valor / total_receitas * 100)
                        pct_invest = (valor / desembolso_liquido * 100)
                        
                        st.markdown(f"**{componente}:**")
                        st.caption(f"{format_brl(valor)} ({pct_total:.1f}% do total | {pct_invest:.2f}% do investimento)")
                
                # ← REMOVIDO: Cards de Total de Receitas e Margem Bruta
            else:
                st.info("Sem receitas para exibir")

        
        # ========== SEÇÃO 5: COMPARAÇÃO DE CENÁRIOS DE PAGAMENTO ==========
        st.markdown("---")
        st.markdown('<div class="section-header">🎯 Comparação de Cenários de Pagamento</div>', unsafe_allow_html=True)
        
        st.caption("Análise de diferentes situações de pagamento e seu impacto na rentabilidade")
        
        # Definir cenários
        cenarios_pagamento = [
            {
                'nome': '✅ Pagamento no Prazo',
                'dias_atraso': 0,
                'prob_pdd': 0.0,
                'descricao': 'Cliente paga no vencimento'
            },
            {
                'nome': '⏰ Atraso de 1 dia',
                'dias_atraso': 1,
                'descricao': 'Atraso mínimo'
            },
            {
                'nome': '⏰ Atraso de 5 dias',
                'dias_atraso': 5,
                'descricao': 'Atraso pontual'
            },
            {
                'nome': '⏰ Atraso de 10 dias',
                'dias_atraso': 10,
                'descricao': 'Atraso moderado'
            },

            {
                'nome': '⏰ Atraso de 30 dias',
                'dias_atraso': 30,
                'descricao': 'Atraso preocupante'
            },

            {
                'nome': '⏰ Atraso de 60 dias',
                'dias_atraso': 60,
                'prob_pdd': prob_pdd * 0.3,
                'descricao': 'Atraso com provisão de PDD'
            },
        ]
        
        resultados_cenarios = []

        for cen in cenarios_pagamento:
            # Recalcular penalidades
            mora_val_cen = ticket * mora_dia * cen['dias_atraso']
            multa_val_cen = ticket * multa_pct if cen['dias_atraso'] > 0 else 0
            penalidade_cen = multa_val_cen + mora_val_cen
            
            recebimento_cen = ticket + penalidade_cen
            
            # Pegar PDD do cenário (0.0 se não definido)
            pdd_cenario = cen.get('prob_pdd', 0.0)
            
            # Calcular TIR
            if recebimento_cen > 0 and desembolso_liquido > 0:
                irr_d_cen = (recebimento_cen / desembolso_liquido) ** (1 / prazo_dias) - 1
                irr_m_cen = (1 + irr_d_cen) ** 30 - 1
                irr_m_liq_cen = irr_m_cen * (1 - pdd_cenario)
                irr_a_liq_cen = (1 + irr_m_liq_cen) ** 12 - 1
                
                receita_bruta_cen = recebimento_cen - desembolso_liquido
                pdd_esperada_cen = receita_bruta_cen * pdd_cenario
                receita_liq_cen = receita_bruta_cen - pdd_esperada_cen
            else:
                irr_m_liq_cen = irr_a_liq_cen = 0
                penalidade_cen = pdd_esperada_cen = receita_liq_cen = 0
            
            resultados_cenarios.append({
                'Cenário': cen['nome'],
                'Descrição': cen['descricao'],
                'TIR Mensal (%)': f"{irr_m_liq_cen*100:.2f}",
                'TIR Anual (%)': f"{irr_a_liq_cen*100:.2f}",
                'Penalidades (R$)': format_brl(penalidade_cen),
                'PDD Esperada (R$)': format_brl(pdd_esperada_cen),
                'Receita Líquida (R$)': format_brl(receita_liq_cen)
            })

        # Criar DataFrame
        df_cenarios = pd.DataFrame(resultados_cenarios)

        # Exibir tabela
        st.dataframe(
            df_cenarios,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cenário": st.column_config.TextColumn("Cenário", width="medium"),
                "Descrição": st.column_config.TextColumn("Descrição", width="medium"),
                "TIR Mensal (%)": st.column_config.TextColumn("TIR Mensal (%)", width="small"),
                "TIR Anual (%)": st.column_config.TextColumn("TIR Anual (%)", width="small"),
                "Penalidades (R$)": st.column_config.TextColumn("Penalidades", width="medium"),
                "PDD Esperada (R$)": st.column_config.TextColumn("PDD Esperada", width="medium"),
                "Receita Líquida (R$)": st.column_config.TextColumn("Receita Líquida", width="medium")
            }
        )

        
            
        # ========== SEÇÃO 6: HIPÓTESES E OBSERVAÇÕES ==========
        with st.expander("📖 Hipóteses e Metodologia do Simulador"):
            st.markdown(
                """
                ### Premissas do Modelo:
                
                **Estrutura da Operação:**
                - Operação **bullet** (pagamento único no vencimento)
                - Cliente recebe: `Valor de Face - Deságio - TAC`
                - Cliente paga no vencimento: `Valor de Face` (+ penalidades se atrasar)
                
                **Deságio (Calculado pela Taxa):**
                - Fórmula: `Deságio = Valor de Face × (1 - 1/(1+taxa)^períodos)`
                - Representa o ganho financeiro do FIDC pela antecipação
                - Quanto maior a taxa, maior o deságio
                
                **TAC (Taxa de Abertura de Crédito):**
                - Descontada do desembolso (cliente recebe menos)
                - Aumenta a TIR do FIDC sem aumentar o risco
                - Analisada separadamente para avaliar seu impacto
                
                **Penalidades (Mora e Multa):**
                - **Multa**: 2% flat sobre o valor de face (aplicada uma vez)
                - **Mora**: 1% a.m. sobre o valor de face × (dias de atraso / 30)
                - Aplicadas apenas em caso de atraso
                - Aumentam o retorno mas indicam risco maior
                
                **PDD (Provisão para Devedores Duvidosos):**
                - Atua como **redutor da taxa efetiva**, NÃO como perda de principal
                - Fórmula: `TIR Líquida = TIR Bruta × (1 - PDD%)`
                - Exemplo: TIR Bruta 5% a.m. com PDD 10% → TIR Líquida = 4,5% a.m.
                - Reflete a expectativa de perda na carteira
                
                **Cálculo da TIR:**
                - **TIR Bruta**: Baseada apenas nos fluxos de caixa (desembolso vs recebimento)
                - **TIR Líquida**: Aplica o fator de redução do PDD
                - Conversões: Diária → Mensal (30 dias) → Anual (12 meses)
                
                ### Observações Importantes:
                
                - O modelo assume que a operação é **performing** até o vencimento
                - PDD é tratada como **expectativa de perda**, não perda realizada
                - Mora e multa são aplicadas sobre o **valor de face total**
                - Quanto maior o atraso, maior a penalidade mas também maior o risco (PDD)
                - TAC é uma receita imediata que melhora a TIR sem aumentar exposição
                - Ajuste os parâmetros conforme políticas específicas do FIDC
                
                ### Interpretação dos Cenários:
                
                - **Pagamento no Prazo**: Cenário ideal, sem risco adicional
                - **Atrasos**: Maior retorno mas maior risco (PDD parcial)
                - **Default**: Perda total da rentabilidade (PDD 100%)
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
    # SUB-ABA 2: SIMULADOR COMPLETO DO FUNDO (CORRIGIDO)
    # ============================================================
    with subtab2:
        st.markdown("### 🎛️ Simulador Completo do Fundo")
        st.caption("Ajuste qualquer variável do fundo e veja o impacto em tempo real na rentabilidade da Cota Júnior")
        
        # --- DEFINE VARIÁVEL DE BASE ---
        pct_caixa_aplicado_atual = 1.0 # Assume 100% aplicado no cenário atual
        
        # ========== SEÇÃO 1: PAINEL DE CONTROLE ==========
        st.markdown('<div class="section-header">⚙️ Painel de Controle - Ajuste as Variáveis</div>', unsafe_allow_html=True)
        
        # Organizar em 3 colunas
        col_sim1, col_sim2, col_sim3 = st.columns(3)
        
        pct_caixa = 1 - pct_recebiveis
        valor_caixa = pl_total * pct_caixa

        with col_sim1:
            st.markdown("**💰 Receitas:**")
            
            taxa_cart_sim = st.number_input(
                "Taxa da Carteira (% a.m.)",
                min_value=0.0,
                max_value=10.0,
                value=float(taxa_carteira_am_pct),
                step=0.1,
                format="%.2f",
                key="sim_taxa_cart",
                help="Taxa de juros dos recebíveis"
            ) / 100
            
            pct_caixa_aplicado_sim = st.slider(
                "% do Caixa Aplicado",
                min_value=0.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                format="%.0f%%",
                key="sim_pct_caixa",
                help="Percentual do caixa aplicado em CDI"
            ) / 100
            
            taxa_caixa_aa_sim = st.number_input(
                "Taxa do Caixa (% a.a.)",
                min_value=0.0,
                max_value=20.0,
                value=float(cdi_aa * 100),
                step=0.5,
                format="%.2f",
                key="sim_taxa_caixa"
            ) / 100
        
        with col_sim2:
            st.markdown("**💸 Custos das Cotas:**")
            
            spread_senior_sim = st.number_input(
                "Spread Sênior (% a.a.)",
                min_value=0.0,
                max_value=10.0,
                value=float(spread_senior_aa_pct),
                step=0.25,
                format="%.2f",
                key="sim_spread_senior",
                help="Spread sobre CDI para cota sênior"
            ) / 100
            
            spread_mezz_sim = st.number_input(
                "Spread Mezzanino (% a.a.)",
                min_value=0.0,
                max_value=10.0,
                value=float(spread_mezz_aa_pct),
                step=0.25,
                format="%.2f",
                key="sim_spread_mezz",
                help="Spread sobre CDI para cota mezzanino"
            ) / 100
            
            taxa_adm_aa_sim = st.number_input(
                "Taxa de Administração (% a.a.)",
                min_value=0.0,
                max_value=5.0,
                value=float(taxa_adm_aa_pct),
                step=0.1,
                format="%.2f",
                key="sim_taxa_adm"
            ) / 100
            
            taxa_gestao_aa_sim = st.number_input(
                "Taxa de Gestão (% a.a.)",
                min_value=0.0,
                max_value=5.0,
                value=float(taxa_gestao_aa_pct),
                step=0.1,
                format="%.2f",
                key="sim_taxa_gestao"
            ) / 100
        
        with col_sim3:
            st.markdown("**⚠️ Riscos:**")
            
            pdd_mult_sim = st.slider(
                "Multiplicador de PDD",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.1,
                format="%.1f",
                key="sim_pdd_mult",
                help="1.0 = PDD atual | 2.0 = dobro do PDD"
            )
            
            st.markdown("**📊 Estrutura de Capital:**")
            st.caption(f"Sênior: {format_brl(valor_senior)} ({(valor_senior/pl_total*100):.1f}%)")
            st.caption(f"Mezzanino: {format_brl(valor_mezz)} ({(valor_mezz/pl_total*100):.1f}%)")
            st.caption(f"Júnior: {format_brl(valor_junior)} ({(valor_junior/pl_total*100):.1f}%)")
            st.caption(f"PL Total: {format_brl(pl_total)}")
        
        # ========== CÁLCULOS DO CENÁRIO SIMULADO (CORRIGIDOS) ==========
        
        # Receitas
        # Aplica % de caixa aplicado sobre o valor do caixa
        valor_caixa_aplicado_sim = valor_caixa * pct_caixa_aplicado_sim
        
        taxa_cart_diaria_sim = mensal_to_diario(taxa_cart_sim)
        taxa_caixa_diaria_sim = anual_to_diario(taxa_caixa_aa_sim)
        
        receita_cart_sim = valor_recebiveis * taxa_cart_diaria_sim
        # CORREÇÃO: Receita caixa considera apenas a parte aplicada
        receita_caixa_sim = valor_caixa_aplicado_sim * taxa_caixa_diaria_sim
        receita_total_sim = receita_cart_sim + receita_caixa_sim + receita_outros_dia
        
        # Custos
        taxa_senior_aa_sim = cdi_aa + spread_senior_sim
        taxa_mezz_aa_sim = cdi_aa + spread_mezz_sim
        
        taxa_senior_diaria_sim = anual_to_diario(taxa_senior_aa_sim)
        taxa_mezz_diaria_sim = anual_to_diario(taxa_mezz_aa_sim)
        
        custo_senior_sim = valor_senior * taxa_senior_diaria_sim
        custo_mezz_sim = valor_mezz * taxa_mezz_diaria_sim
        
        custo_adm_sim = pl_total * anual_to_diario(taxa_adm_aa_sim)
        custo_gestao_sim = pl_total * anual_to_diario(taxa_gestao_aa_sim)
        
        pdd_sim = pdd_dia * pdd_mult_sim
        
        # Resultado Líquido Diário
        resultado_liquido_sim = (
            receita_total_sim
            - custo_senior_sim
            - custo_mezz_sim
            - custo_adm_sim
            - custo_gestao_sim
            - pdd_sim
            - custo_outros_dia
        )
        
        resultado_junior_sim = resultado_liquido_sim
        ret_diario_junior_sim = resultado_junior_sim / valor_junior if valor_junior > 0 else 0
        
        # CORREÇÃO MATEMÁTICA: Usar Juros Simples (* 252) para consistência
        # Se usarmos exponencial aqui e linear lá em cima, dá diferença.
        # Vamos padronizar com a lógica que você usa no Waterfall (Linear para visualização rápida).
        retorno_anualizado_junior_sim = ret_diario_junior_sim * 252 
        retorno_mensal_junior_sim = ret_diario_junior_sim * 21
        
        # ========== SEÇÃO 2: RESULTADOS DA SIMULAÇÃO ==========
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Resultados da Simulação</div>', unsafe_allow_html=True)
        
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        
        # Calcular variações
        delta_receita = receita_total_sim - receita_total_dia
        delta_custo_total_sim = (custo_senior_sim + custo_mezz_sim + custo_adm_sim + custo_gestao_sim + pdd_sim + custo_outros_dia)
        delta_custo_total_atual = (custo_senior_dia + custo_mezz_dia + custo_adm_dia + custo_gestao_dia + pdd_dia + custo_outros_dia)
        delta_custo = delta_custo_total_sim - delta_custo_total_atual
        delta_resultado = resultado_junior_sim - resultado_junior_dia
        
        # Delta do retorno (p.p.)
        delta_ret_anual = (retorno_anualizado_junior_sim - retorno_anualizado_junior) * 100
        
        col_r1.metric("Receita Total (dia)", format_brl(receita_total_sim), delta=format_brl(delta_receita), delta_color="normal")
        col_r2.metric("Custos Totais (dia)", format_brl(delta_custo_total_sim), delta=format_brl(delta_custo), delta_color="inverse")
        col_r3.metric("Resultado Júnior (dia)", format_brl(resultado_junior_sim), delta=format_brl(delta_resultado), delta_color="normal")
        col_r4.metric("Retorno Júnior (% a.m.)", f"{retorno_mensal_junior_sim*100:.2f}%", delta=f"{(retorno_mensal_junior_sim - retorno_mensal_junior)*100:.2f} p.p.", delta_color="normal")
        col_r5.metric("Retorno Júnior (% a.a.)", f"{retorno_anualizado_junior_sim*100:.2f}%", delta=f"{delta_ret_anual:.2f} p.p.", delta_color="normal")
        
        # ========== SEÇÃO 3: COMPARAÇÃO CENÁRIO ATUAL VS SIMULADO ==========
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Comparação: Atual vs Simulado</div>', unsafe_allow_html=True)
        
        # Criar DataFrame comparativo
        df_comparacao = pd.DataFrame({
            'Métrica': [
                'Taxa da Carteira (% a.m.)', '% Caixa Aplicado', 'Spread Sênior (% a.a.)', 'Spread Mezzanino (% a.a.)', 'Multiplicador PDD',
                'Receita Total (dia)', 'Custo Sênior (dia)', 'Custo Mezzanino (dia)', 'PDD (dia)', 'Resultado Júnior (dia)', 'Retorno Júnior (% a.a.)'
            ],
            'Cenário Atual': [
                f"{taxa_carteira_am_pct:.2f}%", f"{pct_caixa_aplicado_atual*100:.0f}%", f"{spread_senior_aa_pct:.2f}%", f"{spread_mezz_aa_pct:.2f}%", "1.0x",
                format_brl(receita_total_dia), format_brl(custo_senior_dia), format_brl(custo_mezz_dia), format_brl(pdd_dia), format_brl(resultado_junior_dia), f"{retorno_anualizado_junior*100:.2f}%"
            ],
            'Cenário Simulado': [
                f"{taxa_cart_sim*100:.2f}%", f"{pct_caixa_aplicado_sim*100:.0f}%", f"{spread_senior_sim*100:.2f}%", f"{spread_mezz_sim*100:.2f}%", f"{pdd_mult_sim:.1f}x",
                format_brl(receita_total_sim), format_brl(custo_senior_sim), format_brl(custo_mezz_sim), format_brl(pdd_sim), format_brl(resultado_junior_sim), f"{retorno_anualizado_junior_sim*100:.2f}%"
            ],
            'Variação': [
                f"{(taxa_cart_sim - taxa_carteira_am_pct/100)*100:.2f} p.p.", f"{(pct_caixa_aplicado_sim - pct_caixa_aplicado_atual)*100:.0f} p.p.",
                f"{(spread_senior_sim - spread_senior_aa_pct/100)*100:.2f} p.p.", f"{(spread_mezz_sim - spread_mezz_aa_pct/100)*100:.2f} p.p.", f"{pdd_mult_sim - 1.0:+.1f}x",
                format_brl(delta_receita), format_brl(custo_senior_sim - custo_senior_dia), format_brl(custo_mezz_sim - custo_mezz_dia),
                format_brl(pdd_sim - pdd_dia), format_brl(delta_resultado), f"{delta_ret_anual:+.2f} p.p."
            ]
        })
        
        st.dataframe(
            df_comparacao,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Métrica": st.column_config.TextColumn("Métrica", width="medium"),
                "Cenário Atual": st.column_config.TextColumn("Cenário Atual", width="medium"),
                "Cenário Simulado": st.column_config.TextColumn("Cenário Simulado", width="medium"),
                "Variação": st.column_config.TextColumn("Variação", width="small")
            }
        )
        
        # ========== SEÇÃO 4: ANÁLISE DE SENSIBILIDADE - TAXA DA CARTEIRA ==========
        st.markdown("---")
        st.markdown('<div class="section-header">📈 Análise de Sensibilidade: Taxa da Carteira</div>', unsafe_allow_html=True)
        
        st.caption("Veja como variações na taxa da carteira impactam o retorno da Cota Júnior")
        
        # Gerar range de taxas
        taxa_min = max(0, taxa_carteira_am_pct/100 - 0.02)  # -2 p.p.
        taxa_max = taxa_carteira_am_pct/100 + 0.02  # +2 p.p.
        taxas_range = np.linspace(taxa_min, taxa_max, 50)
        
        retornos_taxa = []
        
        for taxa_test in taxas_range:
            taxa_diaria_test = mensal_to_diario(taxa_test)
            receita_cart_test = valor_recebiveis * taxa_diaria_test
            receita_total_test = receita_cart_test + receita_caixa_sim + receita_outros_dia
            
            resultado_test = (
                receita_total_test
                - custo_senior_sim
                - custo_mezz_sim
                - custo_adm_sim
                - custo_gestao_sim
                - pdd_sim
                - custo_outros_dia
            )
            
            ret_diario_test = resultado_test / valor_junior if valor_junior > 0 else 0
            ret_anual_test = (1 + ret_diario_test) ** 252 - 1
            
            retornos_taxa.append(ret_anual_test * 100)
        
        # Criar gráfico
        fig_sens_taxa = go.Figure()
        
        fig_sens_taxa.add_trace(go.Scatter(
            x=taxas_range * 100,
            y=retornos_taxa,
            mode='lines',
            name='Retorno Júnior',
            line=dict(color='#3498db', width=3),
            hovertemplate='Taxa: %{x:.2f}% a.m.<br>Retorno: %{y:.2f}% a.a.<extra></extra>'
        ))
        
        # Marcar cenário simulado
        fig_sens_taxa.add_trace(go.Scatter(
            x=[taxa_cart_sim * 100],
            y=[retorno_anualizado_junior_sim * 100],
            mode='markers',
            name='Cenário Simulado',
            marker=dict(color='red', size=12, symbol='star'),
            hovertemplate='<b>Cenário Simulado</b><br>Taxa: %{x:.2f}% a.m.<br>Retorno: %{y:.2f}% a.a.<extra></extra>'
        ))
        
        # Linha de break-even
        fig_sens_taxa.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Break-even (0%)",
            annotation_position="right"
        )
        
        fig_sens_taxa.update_layout(
            title={
                'text': 'Sensibilidade: Taxa da Carteira vs Retorno da Júnior',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            xaxis_title='Taxa da Carteira (% a.m.)',
            yaxis_title='Retorno Júnior (% a.a.)',
            height=400,
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig_sens_taxa, use_container_width=True)
        
        # Métricas de sensibilidade
        col_sens1, col_sens2, col_sens3 = st.columns(3)
        
        # Calcular elasticidade (variação % retorno / variação % taxa)
        if len(retornos_taxa) > 1:
            delta_ret = retornos_taxa[-1] - retornos_taxa[0]
            delta_taxa = (taxas_range[-1] - taxas_range[0]) * 100
            elasticidade = delta_ret / delta_taxa if delta_taxa != 0 else 0
        else:
            elasticidade = 0
        
        col_sens1.metric(
            "Elasticidade",
            f"{elasticidade:.2f}",
            help="Variação do retorno (p.p.) para cada 1 p.p. de variação na taxa"
        )
        
        col_sens2.metric(
            "Retorno Mínimo",
            f"{min(retornos_taxa):.2f}%",
            help=f"Com taxa de {taxa_min*100:.2f}% a.m."
        )
        
        col_sens3.metric(
            "Retorno Máximo",
            f"{max(retornos_taxa):.2f}%",
            help=f"Com taxa de {taxa_max*100:.2f}% a.m."
        )
        
        # ========== SEÇÃO 5: ANÁLISE DE SENSIBILIDADE - % CAIXA APLICADO ==========
        st.markdown("---")
        st.markdown('<div class="section-header">💰 Análise de Sensibilidade: % Caixa Aplicado</div>', unsafe_allow_html=True)
        
        st.caption("Veja como variações no percentual de caixa aplicado impactam o retorno da Cota Júnior")
        
        # Gerar range de % caixa
        pct_caixa_range = np.linspace(0, 1, 50)
        
        retornos_caixa = []
        
        for pct_test in pct_caixa_range:
            valor_caixa_aplicado_test = valor_caixa * pct_test
            receita_caixa_test = valor_caixa_aplicado_test * taxa_caixa_diaria_sim
            receita_total_test = receita_cart_sim + receita_caixa_test + receita_outros_dia
            
            resultado_test = (
                receita_total_test
                - custo_senior_sim
                - custo_mezz_sim
                - custo_adm_sim
                - custo_gestao_sim
                - pdd_sim
                - custo_outros_dia
            )
            
            ret_diario_test = resultado_test / valor_junior if valor_junior > 0 else 0
            ret_anual_test = (1 + ret_diario_test) ** 252 - 1
            
            retornos_caixa.append(ret_anual_test * 100)
        
        # Criar gráfico
        fig_sens_caixa = go.Figure()
        
        fig_sens_caixa.add_trace(go.Scatter(
            x=pct_caixa_range * 100,
            y=retornos_caixa,
            mode='lines',
            name='Retorno Júnior',
            line=dict(color='#2ecc71', width=3),
            hovertemplate='% Caixa: %{x:.0f}%<br>Retorno: %{y:.2f}% a.a.<extra></extra>'
        ))
        
        # Marcar cenário simulado
        fig_sens_caixa.add_trace(go.Scatter(
            x=[pct_caixa_aplicado_sim * 100],
            y=[retorno_anualizado_junior_sim * 100],
            mode='markers',
            name='Cenário Simulado',
            marker=dict(color='red', size=12, symbol='star'),
            hovertemplate='<b>Cenário Simulado</b><br>% Caixa: %{x:.0f}%<br>Retorno: %{y:.2f}% a.a.<extra></extra>'
        ))
        
        # Linha de break-even
        fig_sens_caixa.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Break-even (0%)",
            annotation_position="right"
        )
        
        fig_sens_caixa.update_layout(
            title={
                'text': 'Sensibilidade: % Caixa Aplicado vs Retorno da Júnior',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            xaxis_title='% do Caixa Aplicado',
            yaxis_title='Retorno Júnior (% a.a.)',
            height=400,
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig_sens_caixa, use_container_width=True)
        
        # Métricas de sensibilidade
        col_sens_c1, col_sens_c2, col_sens_c3 = st.columns(3)
        
        # Calcular impacto de aplicar 100% vs 0%
        impacto_total = retornos_caixa[-1] - retornos_caixa[0]
        
        col_sens_c1.metric(
            "Impacto Total",
            f"{impacto_total:.2f} p.p.",
            help="Diferença entre aplicar 100% e 0% do caixa"
        )
        
        col_sens_c2.metric(
            "Retorno com 0% Aplicado",
            f"{retornos_caixa[0]:.2f}%",
            help="Retorno se não aplicar nada do caixa"
        )
        
        col_sens_c3.metric(
            "Retorno com 100% Aplicado",
            f"{retornos_caixa[-1]:.2f}%",
            help="Retorno se aplicar todo o caixa"
        )
        
        # ========== INSIGHTS E RECOMENDAÇÕES ==========
        st.markdown("---")
        st.markdown('<div class="section-header">💡 Insights e Recomendações</div>', unsafe_allow_html=True)
        
        col_ins1, col_ins2 = st.columns(2)
        
        with col_ins1:
            st.markdown("**🎯 Principais Alavancas de Rentabilidade:**")
            
            # Calcular impacto de cada variável
            impactos = {
                'Taxa da Carteira': abs(elasticidade),
                '% Caixa Aplicado': abs(impacto_total / 100),
                'Spread Sênior': abs((custo_senior_sim - custo_senior_dia) / resultado_junior_dia * 100) if resultado_junior_dia != 0 else 0,
                'Spread Mezzanino': abs((custo_mezz_sim - custo_mezz_dia) / resultado_junior_dia * 100) if resultado_junior_dia != 0 else 0
            }
            
            # Ordenar por impacto
            impactos_ordenados = sorted(impactos.items(), key=lambda x: x[1], reverse=True)
            
            for i, (variavel, impacto) in enumerate(impactos_ordenados, 1):
                st.caption(f"{i}. **{variavel}** - Impacto: {impacto:.2f}")
        
        with col_ins2:
            st.markdown("**⚠️ Alertas:**")
            
            # Gerar alertas baseados na simulação
            if retorno_anualizado_junior_sim < 0:
                st.warning("⚠️ Retorno da Júnior negativo no cenário simulado")
            
            if pdd_mult_sim > 2.0:
                st.warning("⚠️ PDD muito elevado (>2x) - risco alto")
            
            if pct_caixa_aplicado_sim < 0.5:
                st.info("💡 Considere aumentar % de caixa aplicado para melhorar rentabilidade")
            
            if delta_ret_anual > 5:
                st.success(f"✅ Melhoria de {delta_ret_anual:.2f} p.p. no retorno da Júnior!")
            elif delta_ret_anual < -5:
                st.error(f"❌ Piora de {abs(delta_ret_anual):.2f} p.p. no retorno da Júnior")
    
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
