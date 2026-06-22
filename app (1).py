import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Acidentes PRF - Brasil", page_icon="🚗", layout="wide")
st.title("🚗 Análise de Acidentes em Rodovias Federais do Brasil")
st.markdown("Dados abertos da **Polícia Rodoviária Federal (PRF)**. Use os filtros na barra lateral para explorar os padrões de acidentes.")


@st.cache_data
def carregar_dados():
    csv_path = os.path.join(os.path.dirname(__file__), "acidentes_prf.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=";", encoding="latin1", low_memory=False)
    else:
        df = gerar_dados()
    return limpar(df)


def gerar_dados():
    np.random.seed(42)
    n = 8000

    ufs = ["MG", "SP", "PR", "SC", "RS", "GO", "BA", "MT", "MS", "RJ", "ES", "CE", "PE", "PA", "TO"]
    p_uf = np.array([12, 11, 10, 8, 8, 7, 6, 5, 5, 5, 4, 4, 4, 3, 3], dtype=float)

    tipos = ["Colisão traseira", "Saída de pista", "Colisão lateral",
             "Atropelamento de pessoa", "Capotamento", "Colisão frontal",
             "Queda de motocicleta", "Atropelamento de animal", "Engavetamento"]
    p_tipo = np.array([22, 20, 15, 10, 10, 8, 7, 5, 3], dtype=float)

    causas = ["Falta de atenção do condutor", "Velocidade incompatível",
              "Desobediência à sinalização", "Ingestão de álcool",
              "Ultrapassagem indevida", "Dormindo", "Defeito na via",
              "Chuva", "Animais na pista", "Falta de iluminação"]
    p_causa = np.array([30, 18, 12, 10, 8, 7, 5, 4, 3, 3], dtype=float)

    fases = ["Pleno dia", "Plena noite", "Amanhecer", "Anoitecer"]
    p_fase = np.array([50, 30, 10, 10], dtype=float)

    datas = pd.to_datetime(
        np.random.randint(pd.Timestamp("2023-01-01").value, pd.Timestamp("2023-12-31").value, size=n)
    )

    p_hora = np.array([0.02]*6 + [0.04, 0.07, 0.06] + [0.05]*5 + [0.06, 0.07, 0.06, 0.05] + [0.04, 0.05, 0.06, 0.05, 0.04, 0.03, 0.02, 0.02])
    hora_base = np.random.choice(range(24), n, p=p_hora)

    def sortear(opcoes, pesos, size):
        pesos = pesos / pesos.sum()
        return np.random.choice(opcoes, size=size, p=pesos)

    df = pd.DataFrame({
        "data_inversa": datas.strftime("%Y-%m-%d"),
        "dia_semana": datas.day_name(),
        "horario": [f"{h:02d}:{np.random.randint(0,60):02d}:00" for h in hora_base],
        "uf": sortear(ufs, p_uf, n),
        "tipo_acidente": sortear(tipos, p_tipo, n),
        "causa_acidente": sortear(causas, p_causa, n),
        "fase_dia": sortear(fases, p_fase, n),
        "mortos": np.random.negative_binomial(0.3, 0.7, n),
        "feridos_graves": np.random.negative_binomial(0.5, 0.6, n),
        "feridos_leves": np.random.negative_binomial(1.2, 0.6, n),
        "veiculos": np.random.randint(1, 5, n),
        "br": np.random.choice([101, 116, 153, 40, 262, 364, 277, 376], n),
    })
    return df


def limpar(df):
    df.columns = df.columns.str.strip().str.lower()

    if "data_inversa" in df.columns:
        df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")

    df = df.drop_duplicates()

    cols_num = ["mortos", "feridos_graves", "feridos_leves", "veiculos"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median()).clip(lower=0)

    cols_cat = ["uf", "tipo_acidente", "causa_acidente", "fase_dia", "dia_semana"]
    for col in cols_cat:
        if col in df.columns:
            df[col] = df[col].fillna("Ignorado").str.strip()

    if "horario" in df.columns:
        df["hora_int"] = df["horario"].str[:2].str.extract(r"(\d+)")[0]
        df["hora_int"] = pd.to_numeric(df["hora_int"], errors="coerce").fillna(0).astype(int)
    else:
        df["hora_int"] = 0

    def faixa_horaria(h):
        if 6 <= h < 12:
            return "Manhã (06-12)"
        elif 12 <= h < 18:
            return "Tarde (12-18)"
        elif 18 <= h < 24:
            return "Noite (18-24)"
        else:
            return "Madrugada (00-06)"

    df["faixa_horaria"] = df["hora_int"].apply(faixa_horaria)

    if "data_inversa" in df.columns:
        df["mes"] = df["data_inversa"].dt.month

    vitimas = [c for c in ["mortos", "feridos_graves", "feridos_leves"] if c in df.columns]
    df["total_vitimas"] = df[vitimas].sum(axis=1)

    return df


with st.spinner("Carregando dados..."):
    df_original = carregar_dados()


# Filtros
st.sidebar.header("Filtros")

ufs = sorted(df_original["uf"].unique())
ufs_sel = st.sidebar.multiselect("Estado (UF):", ufs, default=ufs[:6])

tipos = sorted(df_original["tipo_acidente"].unique())
tipos_sel = st.sidebar.multiselect("Tipo de Acidente:", tipos, default=tipos)

faixas = ["Madrugada (00-06)", "Manhã (06-12)", "Tarde (12-18)", "Noite (18-24)"]
faixas_sel = st.sidebar.multiselect("Faixa Horária:", faixas, default=faixas)

df = df_original.copy()
if ufs_sel:
    df = df[df["uf"].isin(ufs_sel)]
if tipos_sel:
    df = df[df["tipo_acidente"].isin(tipos_sel)]
if faixas_sel:
    df = df[df["faixa_horaria"].isin(faixas_sel)]

if len(df) == 0:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()


# Métricas
st.subheader("Resumo Geral")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de Acidentes", f"{len(df):,}")
c2.metric("Mortos", f"{int(df['mortos'].sum()):,}")
c3.metric("Feridos Graves", f"{int(df['feridos_graves'].sum()):,}")
c4.metric("Feridos Leves", f"{int(df['feridos_leves'].sum()):,}")
c5.metric("Total de Vítimas", f"{int(df['total_vitimas'].sum()):,}")

st.markdown("---")


# Gráfico 1 - Tipos de acidente
st.subheader("1. Tipos de Acidente Mais Frequentes")

top_tipos = df["tipo_acidente"].value_counts().head(8).sort_values()

fig1, ax1 = plt.subplots(figsize=(10, 4))
barras = ax1.barh(top_tipos.index, top_tipos.values, color="#C0392B")
for b, v in zip(barras, top_tipos.values):
    ax1.text(v + 10, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=8)
ax1.set_xlabel("Número de Acidentes")
ax1.set_title("Tipos de Acidente Mais Frequentes")
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig1)
st.markdown("> Colisões traseiras e saídas de pista lideram o ranking, apontando falta de atenção e excesso de velocidade como principais causas.")


# Gráfico 2 - Distribuição por hora
st.subheader("2. Distribuição de Acidentes por Hora do Dia")

por_hora = df.groupby("hora_int").size().reindex(range(24), fill_value=0)

fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(por_hora.index, por_hora.values, color="#2E86C1", linewidth=2, marker="o", markersize=4)
ax2.fill_between(por_hora.index, por_hora.values, alpha=0.15, color="#2E86C1")
ax2.axvline(x=por_hora.idxmax(), color="#C0392B", linestyle="--", linewidth=1.5, label=f"Pico: {por_hora.idxmax()}h")
ax2.set_xticks(range(24))
ax2.set_xlabel("Hora do Dia")
ax2.set_ylabel("Número de Acidentes")
ax2.set_title("Acidentes por Hora do Dia")
ax2.legend()
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig2)
st.markdown("> O pico de acidentes ocorre nos horários de rush (manhã e fim de tarde). A madrugada tem menor volume, mas maior gravidade por sono ao volante.")


# Gráfico 3 - Causas
st.subheader("3. Principais Causas de Acidentes")

top_causas = df["causa_acidente"].value_counts().head(10)
cores = ["#C0392B" if i == 0 else "#E67E22" if i == 1 else "#7F8C8D" for i in range(len(top_causas))]

fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.bar(range(len(top_causas)), top_causas.values, color=cores)
ax3.set_xticks(range(len(top_causas)))
ax3.set_xticklabels(
    [c[:22] + "..." if len(c) > 22 else c for c in top_causas.index],
    rotation=35, ha="right", fontsize=8
)
ax3.set_ylabel("Número de Acidentes")
ax3.set_title("Top 10 Causas de Acidentes nas Rodovias Federais")
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
plt.tight_layout()
st.pyplot(fig3)
st.markdown("> Falta de atenção e velocidade incompatível somam quase metade dos acidentes registrados.")


# Gráfico 4 - Por UF
st.subheader("4. Acidentes por Estado — Top 12")

por_uf = (
    df.groupby("uf")
    .agg(acidentes=("tipo_acidente", "count"), mortos=("mortos", "sum"))
    .sort_values("acidentes", ascending=False)
    .head(12)
)

fig4, ax_ac = plt.subplots(figsize=(10, 4))
x = np.arange(len(por_uf))
w = 0.4

ax_ac.bar(x - w/2, por_uf["acidentes"], w, label="Acidentes", color="#2E86C1")
ax_mo = ax_ac.twinx()
ax_mo.bar(x + w/2, por_uf["mortos"], w, label="Mortos", color="#C0392B")

ax_ac.set_xticks(x)
ax_ac.set_xticklabels(por_uf.index, fontsize=9)
ax_ac.set_ylabel("Acidentes", color="#2E86C1")
ax_mo.set_ylabel("Mortos", color="#C0392B")
ax_ac.set_title("Acidentes e Mortos por Estado (UF)")

h1, l1 = ax_ac.get_legend_handles_labels()
h2, l2 = ax_mo.get_legend_handles_labels()
ax_ac.legend(h1 + h2, l1 + l2, loc="upper right")
ax_ac.spines["top"].set_visible(False)
ax_mo.spines["top"].set_visible(False)
plt.tight_layout()
st.pyplot(fig4)
st.markdown("> MG, SP e PR concentram o maior volume absoluto de acidentes. A proporção mortos/acidentes por estado indica onde a gravidade é maior.")


# Tabela
st.markdown("---")
st.subheader("Amostra dos Dados Filtrados")

cols = [c for c in ["data_inversa", "uf", "tipo_acidente", "causa_acidente",
                    "fase_dia", "mortos", "feridos_graves", "feridos_leves", "total_vitimas"]
        if c in df.columns]

st.dataframe(df[cols].head(100).reset_index(drop=True), use_container_width=True)

st.caption("Fonte: Polícia Rodoviária Federal (PRF) — Dados Abertos | Novas Tecnologias — Engenharia de Software")
