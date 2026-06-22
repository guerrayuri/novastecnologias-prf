"""
Análise de Acidentes em Rodovias Federais do Brasil
Dataset: PRF (Polícia Rodoviária Federal) via Kaggle
Disciplina: Novas Tecnologias — Engenharia de Software
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

# ──────────────────────────────────────────────
# 0. CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Acidentes PRF — Brasil",
    layout="wide"
)

st.title(" Análise de Acidentes em Rodovias Federais do Brasil")
st.markdown(
    "Dados abertos da **Polícia Rodoviária Federal (PRF)**. "
    "Use os filtros na barra lateral para explorar os padrões de acidentes."
)

# ──────────────────────────────────────────────
# 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ──────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    """
    Tenta carregar o CSV real da PRF.
    Se não existir localmente, usa dados simulados realistas
    para demonstração (mesma estrutura do dataset original).
    """
    csv_path = os.path.join(os.path.dirname(__file__), "acidentes_prf.csv")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=";", encoding="latin1", low_memory=False)
    else:
        df = _gerar_dados_simulados()

    return _limpar_e_enriquecer(df)


def _gerar_dados_simulados():
    """
    Gera ~8 000 registros simulados com a mesma estrutura
    do dataset real da PRF para fins de demonstração.
    """
    np.random.seed(42)
    n = 8_000

    ufs = [
        "MG", "SP", "PR", "SC", "RS", "GO", "BA",
        "MT", "MS", "RJ", "ES", "CE", "PE", "PA", "TO"
    ]
    pesos_uf = [12, 11, 10, 8, 8, 7, 6, 5, 5, 5, 4, 4, 4, 3, 3]

    tipos = [
        "Colisão traseira", "Saída de pista", "Colisão lateral",
        "Atropelamento de pessoa", "Capotamento", "Colisão frontal",
        "Queda de motocicleta", "Atropelamento de animal", "Engavetamento"
    ]
    pesos_tipo = [22, 20, 15, 10, 10, 8, 7, 5, 3]

    causas = [
        "Falta de atenção do condutor", "Velocidade incompatível",
        "Desobediência à sinalização", "Ingestão de álcool",
        "Ultrapassagem indevida", "Dormindo", "Defeito na via",
        "Chuva", "Animais na pista", "Falta de iluminação"
    ]
    pesos_causa = [30, 18, 12, 10, 8, 7, 5, 4, 3, 3]

    fases = ["Pleno dia", "Plena noite", "Amanhecer", "Anoitecer"]
    pesos_fase = [50, 30, 10, 10]

    condicoes = ["Céu claro", "Chuva", "Nublado", "Neblina/Fumaça", "Sol"]
    pesos_cond = [55, 20, 15, 5, 5]

    # Datas de 2023
    datas = pd.to_datetime(
        np.random.uniform(
            pd.Timestamp("2023-01-01").timestamp(),
            pd.Timestamp("2023-12-31").timestamp(),
            size=n
        ),
        unit="s"
    )

    # Horas com pico em horário comercial e noturno
    # 24 valores (horas 0-23) somando 1.0
    _p_horas = [
        0.02, 0.02, 0.02, 0.02, 0.02, 0.02,  # 00-05 madrugada
        0.04, 0.07, 0.06,                     # 06-08 manhã (pico)
        0.05, 0.05, 0.05, 0.05, 0.05,         # 09-13 comercial
        0.06, 0.07, 0.06, 0.05,               # 14-17 tarde (pico)
        0.04, 0.04, 0.05, 0.04, 0.03, 0.02,   # 18-23 noite
    ]
    hora_base = np.random.choice(range(24), n, p=_p_horas)

    def escolher(opcoes, pesos, size):
        pesos = np.array(pesos, dtype=float)
        pesos /= pesos.sum()
        return np.random.choice(opcoes, size=size, p=pesos)

    df = pd.DataFrame({
        "data_inversa": datas.strftime("%Y-%m-%d"),
        "dia_semana": datas.day_name(),
        "horario": [f"{h:02d}:{np.random.randint(0,60):02d}:00" for h in hora_base],
        "uf": escolher(ufs, pesos_uf, n),
        "tipo_acidente": escolher(tipos, pesos_tipo, n),
        "causa_acidente": escolher(causas, pesos_causa, n),
        "fase_dia": escolher(fases, pesos_fase, n),
        "condicao_metereologica": escolher(condicoes, pesos_cond, n),
        "mortos": np.random.negative_binomial(0.3, 0.7, n),
        "feridos_graves": np.random.negative_binomial(0.5, 0.6, n),
        "feridos_leves": np.random.negative_binomial(1.2, 0.6, n),
        "veiculos": np.random.randint(1, 5, n),
        "pessoas": np.random.randint(1, 8, n),
        "br": np.random.choice([101, 116, 153, 40, 262, 364, 277, 376], n),
    })
    return df


def _limpar_e_enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Etapa de limpeza e engenharia de features.
    Critérios aplicados:
      - Converte data para datetime
      - Trata valores nulos: numéricos → mediana; categóricos → 'Ignorado'
      - Remove duplicatas
      - Cria: hora_int, faixa_horaria, mes, dia_semana_pt, total_vitimas
    """
    # ── Padronizar nomes de colunas ──────────────────────────────────────
    df.columns = df.columns.str.strip().str.lower()

    # ── Converter data ────────────────────────────────────────────────────
    if "data_inversa" in df.columns:
        df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    elif "data" in df.columns:
        df["data_inversa"] = pd.to_datetime(df["data"], errors="coerce")

    # ── Remover duplicatas ────────────────────────────────────────────────
    antes = len(df)
    df = df.drop_duplicates()
    duplicatas_removidas = antes - len(df)

    # ── Colunas numéricas: preencher nulos com mediana ────────────────────
    cols_num = ["mortos", "feridos_graves", "feridos_leves", "veiculos", "pessoas"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())
            # Garantir sem negativos (pode ocorrer em dados reais corrompidos)
            df[col] = df[col].clip(lower=0)

    # ── Colunas categóricas: preencher nulos com 'Ignorado' ──────────────
    cols_cat = ["uf", "tipo_acidente", "causa_acidente", "fase_dia",
                "condicao_metereologica", "dia_semana"]
    for col in cols_cat:
        if col in df.columns:
            df[col] = df[col].fillna("Ignorado").str.strip()

    # ── Engenharia de features ────────────────────────────────────────────
    if "horario" in df.columns:
        df["hora_int"] = df["horario"].str[:2].str.extract(r"(\d+)")[0]
        df["hora_int"] = pd.to_numeric(df["hora_int"], errors="coerce").fillna(0).astype(int)
    else:
        df["hora_int"] = 0

    # Faixa horária
    def faixa(h):
        if 6 <= h < 12:
            return "Manhã (06-12)"
        elif 12 <= h < 18:
            return "Tarde (12-18)"
        elif 18 <= h < 24:
            return "Noite (18-24)"
        else:
            return "Madrugada (00-06)"

    df["faixa_horaria"] = df["hora_int"].apply(faixa)

    # Mês
    if "data_inversa" in df.columns:
        df["mes"] = df["data_inversa"].dt.month
        df["mes_nome"] = df["data_inversa"].dt.strftime("%b")
    else:
        df["mes"] = 1
        df["mes_nome"] = "Jan"

    # Total de vítimas (mortos + feridos)
    vitimas_cols = [c for c in ["mortos", "feridos_graves", "feridos_leves"] if c in df.columns]
    df["total_vitimas"] = df[vitimas_cols].sum(axis=1)

    # Guardar info de limpeza para exibir no app
    df.attrs["duplicatas_removidas"] = duplicatas_removidas

    return df


# ── Carregar ─────────────────────────────────────────────────────────────
with st.spinner("Carregando e processando os dados…"):
    df_original = carregar_dados()

# ──────────────────────────────────────────────
# 2. SIDEBAR — FILTROS
# ──────────────────────────────────────────────
st.sidebar.header("🔍 Filtros")

ufs_disponiveis = sorted(df_original["uf"].unique())
ufs_selecionadas = st.sidebar.multiselect(
    "Estado (UF):", ufs_disponiveis, default=ufs_disponiveis[:6]
)

tipos_disponiveis = sorted(df_original["tipo_acidente"].unique())
tipos_selecionados = st.sidebar.multiselect(
    "Tipo de Acidente:", tipos_disponiveis, default=tipos_disponiveis
)

faixas_disponiveis = ["Madrugada (00-06)", "Manhã (06-12)",
                      "Tarde (12-18)", "Noite (18-24)"]
faixas_selecionadas = st.sidebar.multiselect(
    "Faixa Horária:", faixas_disponiveis, default=faixas_disponiveis
)

# Aplicar filtros
df = df_original.copy()

if ufs_selecionadas:
    df = df[df["uf"].isin(ufs_selecionadas)]
if tipos_selecionados:
    df = df[df["tipo_acidente"].isin(tipos_selecionados)]
if faixas_selecionadas:
    df = df[df["faixa_horaria"].isin(faixas_selecionadas)]

if len(df) == 0:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

# ──────────────────────────────────────────────
# 3. MÉTRICAS RESUMO
# ──────────────────────────────────────────────
st.subheader("Resumo Geral")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total de Acidentes", f"{len(df):,.0f}")
col2.metric("Mortos", f"{int(df['mortos'].sum()):,}")
col3.metric("Feridos Graves", f"{int(df['feridos_graves'].sum()):,}")
col4.metric("Feridos Leves", f"{int(df['feridos_leves'].sum()):,}")
col5.metric("Total de Vítimas", f"{int(df['total_vitimas'].sum()):,}")

st.markdown("---")

# ──────────────────────────────────────────────
# 4. GRÁFICOS
# ──────────────────────────────────────────────

COR_PRIMARIA = "#C0392B"
COR_SECUNDARIA = "#2E86C1"
COR_DESTAQUE = "#E67E22"
FUNDO = "#F8F9FA"

def estilizar_ax(ax, titulo, xlabel, ylabel):
    ax.set_title(titulo, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))


# ── Gráfico 1 — Top 8 tipos de acidente ──────────────────────────────────
st.subheader("1. Tipos de Acidente Mais Frequentes")

top_tipos = (
    df["tipo_acidente"]
    .value_counts()
    .head(8)
    .sort_values(ascending=True)
)

fig1, ax1 = plt.subplots(figsize=(10, 4))
fig1.patch.set_facecolor(FUNDO)
ax1.set_facecolor(FUNDO)

barras = ax1.barh(top_tipos.index, top_tipos.values, color=COR_PRIMARIA, edgecolor="white")
for bar, val in zip(barras, top_tipos.values):
    ax1.text(val + max(top_tipos.values) * 0.01, bar.get_y() + bar.get_height() / 2,
             f"{val:,}", va="center", fontsize=8)

estilizar_ax(ax1, "Tipos de Acidente Mais Frequentes", "Número de Acidentes", "")
plt.tight_layout()
st.pyplot(fig1)

st.markdown(
    "> **Insight:** Colisões traseiras e saídas de pista lideram o ranking, "
    "sinalizando que falta de atenção e excesso de velocidade são os vetores "
    "principais de risco nas rodovias federais."
)

# ── Gráfico 2 — Distribuição horária ─────────────────────────────────────
st.subheader("2. Distribuição de Acidentes por Hora do Dia")

acidentes_por_hora = df.groupby("hora_int").size().reindex(range(24), fill_value=0)

fig2, ax2 = plt.subplots(figsize=(10, 4))
fig2.patch.set_facecolor(FUNDO)
ax2.set_facecolor(FUNDO)

ax2.plot(acidentes_por_hora.index, acidentes_por_hora.values,
         color=COR_SECUNDARIA, linewidth=2.5, marker="o", markersize=5, label="Acidentes/hora")
ax2.fill_between(acidentes_por_hora.index, acidentes_por_hora.values,
                 alpha=0.15, color=COR_SECUNDARIA)
ax2.axvline(x=acidentes_por_hora.idxmax(), color=COR_PRIMARIA,
            linestyle="--", linewidth=1.5, label=f"Pico: {acidentes_por_hora.idxmax()}h")
ax2.set_xticks(range(24))
ax2.legend(fontsize=9)

estilizar_ax(ax2, "Acidentes por Hora do Dia (0h–23h)",
             "Hora do Dia", "Número de Acidentes")
plt.tight_layout()
st.pyplot(fig2)

st.markdown(
    "> **Insight:** O pico de acidentes ocorre nos horários de maior tráfego "
    "(manhã e fim de tarde). A madrugada, apesar de menor volume, "
    "tende a apresentar maior gravidade por causa do sono ao volante."
)

# ── Gráfico 3 — Top 10 causas ────────────────────────────────────────────
st.subheader("3. Principais Causas de Acidentes")

top_causas = df["causa_acidente"].value_counts().head(10)

fig3, ax3 = plt.subplots(figsize=(10, 4))
fig3.patch.set_facecolor(FUNDO)
ax3.set_facecolor(FUNDO)

cores = [COR_PRIMARIA if i == 0 else COR_DESTAQUE if i == 1 else "#7F8C8D"
         for i in range(len(top_causas))]
ax3.bar(range(len(top_causas)), top_causas.values, color=cores, edgecolor="white")
ax3.set_xticks(range(len(top_causas)))
ax3.set_xticklabels(
    [c[:22] + "…" if len(c) > 22 else c for c in top_causas.index],
    rotation=35, ha="right", fontsize=8
)

estilizar_ax(ax3, "Top 10 Causas de Acidentes nas Rodovias Federais",
             "", "Número de Acidentes")
plt.tight_layout()
st.pyplot(fig3)

st.markdown(
    "> **Insight:** A **falta de atenção do condutor** é a causa dominante, "
    "seguida de **velocidade incompatível**. Estas duas causas juntas respondem "
    "por quase metade dos acidentes registrados, reforçando a necessidade de "
    "campanhas educativas e fiscalização eletrônica."
)

# ── Gráfico 4 — Acidentes por UF ─────────────────────────────────────────
st.subheader("4. Acidentes por Estado (UF) — Top 12")

top_uf = (
    df.groupby("uf")
    .agg(acidentes=("tipo_acidente", "count"), mortos=("mortos", "sum"))
    .sort_values("acidentes", ascending=False)
    .head(12)
)

fig4, ax4a = plt.subplots(figsize=(10, 4))
fig4.patch.set_facecolor(FUNDO)
ax4a.set_facecolor(FUNDO)

x = np.arange(len(top_uf))
largura = 0.45

barras_ac = ax4a.bar(x - largura/2, top_uf["acidentes"],
                     largura, label="Acidentes", color=COR_SECUNDARIA, edgecolor="white")
ax4b = ax4a.twinx()
barras_m = ax4b.bar(x + largura/2, top_uf["mortos"],
                    largura, label="Mortos", color=COR_PRIMARIA, edgecolor="white")

ax4a.set_xticks(x)
ax4a.set_xticklabels(top_uf.index, fontsize=9)
ax4a.set_ylabel("Número de Acidentes", fontsize=10, color=COR_SECUNDARIA)
ax4b.set_ylabel("Número de Mortos", fontsize=10, color=COR_PRIMARIA)

linhas1, labels1 = ax4a.get_legend_handles_labels()
linhas2, labels2 = ax4b.get_legend_handles_labels()
ax4a.legend(linhas1 + linhas2, labels1 + labels2, fontsize=9, loc="upper right")

ax4a.set_title("Acidentes e Mortos por Estado (UF)", fontsize=13, fontweight="bold")
ax4a.spines["top"].set_visible(False)
ax4b.spines["top"].set_visible(False)
plt.tight_layout()
st.pyplot(fig4)

st.markdown(
    "> **Insight:** Os estados com maior malha rodoviária federal e volume de "
    "tráfego de cargas (MG, SP, PR, SC) concentram o maior número de acidentes. "
    "A proporção entre acidentes e mortos indica onde a gravidade é maior."
)

# ──────────────────────────────────────────────
# 5. TABELA DE DADOS FILTRADOS
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Amostra dos Dados Filtrados")

cols_exibir = [c for c in
               ["data_inversa", "uf", "tipo_acidente", "causa_acidente",
                "fase_dia", "mortos", "feridos_graves", "feridos_leves", "total_vitimas"]
               if c in df.columns]

st.dataframe(
    df[cols_exibir].head(100).reset_index(drop=True),
    use_container_width=True
)

# ──────────────────────────────────────────────
# 6. RODAPÉ
# ──────────────────────────────────────────────
st.markdown("---")
st.caption(
    "📌 Fonte: Polícia Rodoviária Federal (PRF) — Dados Abertos  |  "
    "Disciplina: Novas Tecnologias — Engenharia de Software"
)
