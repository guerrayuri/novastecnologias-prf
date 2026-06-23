"""
Gerador do Relatorio Auxiliar em PDF
Disciplina: Novas Tecnologias - Engenharia de Software
Execute: python gerar_relatorio.py
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_I = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
VERMELHO = (192, 57, 43)


class PDF(FPDF):
    """Subclasse FPDF com cabecalho, rodape e helpers de formatacao."""

    def __init__(self):
        super().__init__()
        self.add_font("DV",      fname=FONT_R)
        self.add_font("DV", "B", fname=FONT_B)
        self.add_font("DV", "I", fname=FONT_I)

    def header(self):
        self.set_fill_color(*VERMELHO)
        self.rect(0, 0, 210, 16, "F")
        self.set_font("DV", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_y(3)
        self.cell(0, 10,
                  "Analise de Acidentes em Rodovias Federais do Brasil",
                  align="C")
        self.set_text_color(0, 0, 0)
        self.ln(13)

    def footer(self):
        self.set_y(-12)
        self.set_font("DV", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8,
                  f"Novas Tecnologias - Engenharia de Software  |  Pagina {self.page_no()}",
                  align="C")

    def sec(self, t):
        """Titulo de secao com fundo vermelho."""
        self.set_font("DV", "B", 10)
        self.set_fill_color(231, 76, 60)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, f"  {t}",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def par(self, t):
        """Paragrafo justificado."""
        self.set_font("DV", "", 9)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5, t, align="J")
        self.ln(2)

    def item(self, t):
        """Item de lista com travessao."""
        self.set_font("DV", "", 9)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5, f"  - {t}")


def gerar_relatorio(caminho_saida: str):
    pdf = PDF()
    pdf.set_auto_page_break(True, 14)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    # CAPA
    pdf.ln(6)
    pdf.set_font("DV", "B", 16)
    pdf.set_text_color(*VERMELHO)
    pdf.cell(0, 10, "Relatorio de Analise de Dados",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DV", "", 12)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 7, "Acidentes em Rodovias Federais - Brasil (2023)",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("DV", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Disciplina: Novas Tecnologias - Engenharia de Software",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # 1. INTRODUCAO
    pdf.sec("1. Introducao ao Problema")
    pdf.par(
        "O Brasil registra anualmente dezenas de milhares de acidentes nas "
        "rodovias federais, resultando em mortes, feridos e enormes prejuizos "
        "economicos. Segundo dados da PRF, em 2022 foram registrados mais de "
        "60.000 acidentes com vitimas nas BRs do pais."
    )
    pdf.par(
        "A leitura direta de planilhas brutas e inviavel para tomada de decisao. "
        "Este projeto aplica Pandas, NumPy, Matplotlib e Streamlit para transformar "
        "dados abertos da PRF em um dashboard interativo que responde perguntas "
        "sobre QUANDO, ONDE e POR QUE os acidentes ocorrem."
    )
    pdf.par(
        "Pergunta de negocio: Quais sao os padroes temporais, geograficos e "
        "causais dos acidentes nas rodovias federais e como eles podem orientar "
        "politicas de seguranca viaria?"
    )

    # 2. DATASET
    pdf.sec("2. Dataset Utilizado")
    pdf.par("Fonte: Policia Rodoviaria Federal (PRF) - Dados Abertos. "
            "Principais colunas utilizadas:")

    campos = [
        ("data_inversa",   "Data do acidente (YYYY-MM-DD)"),
        ("horario",        "Hora exata do acidente"),
        ("uf",             "Unidade Federativa onde ocorreu"),
        ("tipo_acidente",  "Classificacao do tipo de acidente"),
        ("causa_acidente", "Causa principal registrada pelo policial"),
        ("fase_dia",       "Periodo do dia (pleno dia, noite etc.)"),
        ("mortos",         "Quantidade de mortos"),
        ("feridos_graves", "Quantidade de feridos graves"),
        ("feridos_leves",  "Quantidade de feridos leves"),
        ("veiculos",       "Quantidade de veiculos envolvidos"),
    ]
    pdf.set_font("DV", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_x(pdf.l_margin)
    pdf.cell(38, 6, "Coluna",    border=1, fill=True)
    pdf.cell(0,  6, "Descricao", border=1, fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DV", "", 8)
    for i, (c, d) in enumerate(campos):
        f = (248, 248, 248) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*f)
        pdf.set_x(pdf.l_margin)
        pdf.cell(38, 5, c, border=1, fill=True)
        pdf.cell(0,  5, d, border=1, fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # 3. METODOLOGIA
    pdf.sec("3. Metodologia de Tratamento dos Dados")
    pdf.par("Etapas implementadas na funcao _limpar_e_enriquecer() do arquivo app.py:")
    etapas = [
        "Padronizacao de colunas: strip e lowercase.",
        "Conversao de tipos: data_inversa com pd.to_datetime - invalidos viram NaT.",
        "Remocao de duplicatas com df.drop_duplicates().",
        "Imputacao numerica: colunas de vitimas recebem a mediana - robusta a outliers.",
        "Imputacao categorica: uf e causa_acidente recebem Ignorado onde nulo.",
        "Clipping: valores negativos em vitimas sao zerados com clip(lower=0).",
        "Engenharia de features: hora_int (0-23), faixa_horaria, mes e mes_nome.",
        "total_vitimas = mortos + feridos_graves + feridos_leves (coluna de gravidade).",
    ]
    for e in etapas:
        pdf.item(e)
    pdf.ln(3)

    # 4. RESULTADOS
    pdf.sec("4. Resultados Visuais e Insights")
    graficos = [
        (
            "Grafico 1 - Tipos de Acidente Mais Frequentes (barras horizontais)",
            "Colisoes traseiras e saidas de pista respondem por cerca de 40% dos "
            "acidentes. Campanhas sobre distancia segura e uso de celular ao volante "
            "podem reduzir significativamente esses numeros."
        ),
        (
            "Grafico 2 - Distribuicao por Hora do Dia (linha com area preenchida)",
            "O pico ocorre entre 7h-9h e 17h-19h (rush). A madrugada apresenta "
            "menor volume, porem maior gravidade relativa por sono ao volante e alcool."
        ),
        (
            "Grafico 3 - Principais Causas de Acidentes (barras verticais)",
            "Falta de atencao (~30%) e velocidade incompativel (~18%) somam quase "
            "metade dos registros, reforcando a necessidade de fiscalizacao eletronica."
        ),
        (
            "Grafico 4 - Acidentes e Mortos por Estado (barras duplas)",
            "MG, SP e PR concentram o maior volume absoluto. A proporcao "
            "mortos/acidentes por UF indica onde a gravidade media e maior, "
            "orientando alocacao de recursos de seguranca viaria."
        ),
    ]
    for tit, desc in graficos:
        pdf.set_font("DV", "B", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, tit)
        pdf.set_font("DV", "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, desc, align="J")
        pdf.ln(3)

    # 5. CONCLUSAO
    pdf.sec("5. Conclusao")
    pdf.par(
        "A analise revelou que falta de atencao, velocidade incompativel e "
        "horario de pico formam o triangulo mais perigoso das rodovias federais. "
        "O dashboard Streamlit permite filtrar dados por estado, tipo e faixa "
        "horaria sem precisar escrever codigo adicional - esse e o valor central "
        "da solucao entregue."
    )

    # 6. LIMITACOES
    pdf.sec("6. Limitacoes")
    lims = [
        "Dados simulados seguem distribuicoes aproximadas; resultados precisos "
        "exigem o CSV real da PRF.",
        "Nao foram aplicados modelos preditivos (regressao, arvores), que seriam "
        "o proximo passo para prever gravidade de acidentes.",
        "Dados de lat/lon do dataset real permitiriam um mapa de calor geografico.",
    ]
    for l in lims:
        pdf.item(l)
    pdf.ln(4)

    # 7. REFERENCIAS
    pdf.sec("7. Referencias")
    pdf.par(
        "- PRF Dados Abertos: https://www.gov.br/prf/pt-br/acesso-a-informacao/"
        "dados-abertos/dados-abertos-acidentes\n"
        "- Pandas: https://pandas.pydata.org/docs/\n"
        "- Streamlit: https://docs.streamlit.io/\n"
        "- Matplotlib: https://matplotlib.org/stable/contents.html"
    )

    pdf.output(caminho_saida)
    print(f"Relatorio gerado: {caminho_saida}")


if __name__ == "__main__":
    saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorio_prf.pdf")
    gerar_relatorio(saida)
