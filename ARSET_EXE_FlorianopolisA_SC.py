#-------------------------------------------------------------------------------
#ALGORITMO PARA EXTRAÇÃO E ANÁLISE DE SÉRIES TEMPORAIS DE LUZES NOTURNAS (NTL)
#-------------------------------------------------------------------------------

#Autor: Daniel Adami Dutra

#Aplicação: Análise de séries temporais de radiância de luzes noturnas no Município de Florianópolis- Estado de Santa Catarina- Brasil (junho/julho 2020)
#Produto de satélite Suomi: VIIRS Day/Night Band NASA(ex.: VNP46A2 Black Marble)
#Obs 1.: Adaptado do algoritmo disponível no webnar de (2020) ARSET - Introdução aos dados de luzes noturnas do "Black Marble" da NASA 
#Programa de Treinamento em Sensoriamento Remoto Aplicado da NASA (ARSET). https://www.earthdata.nasa.gov/learn/trainings/introduction-nasas-black-marble-night-lights-data .  
#Obs 2.:Aprimorado com o uso de inteligência artificial generativa ChatGPT da OpenAI

#Descrição geral
#---------------
#Este algoritmo processa arquivos HDF5 contendo dados de radiância de luzes
#noturnas (Nighttime Lights NTL) provenientes do sensor VIIRS. O script:

#1) Permite entrada de dados Latitude e Longitude, digitando valores via teclado(interface).
#2) Converte arquivos HDF5 em raster GeoTIFF temporário.
#3) Extrai valores de radiância para um ponto geográfico específico.
#4) Calcula dois tipos de amostragem espacial:
   #- Pixel único (1x1)
   #- Média de vizinhança (3x3)
#5) Converte datas julianas para datas do calendário.
#6) Gera gráfico da série temporal.
#7) Exibe tabela de valores.
#8) Exporta os resultados para um arquivo Excel.

#Bibliotecas necessárias
#-----------------------
#- os
#- numpy
#- datetime
#- statistics
#- matplotlib
#- GDAL
#- pandas
#- QInputDialog
#- urllib.request
#- json

#Saídas do algoritmo
#-------------------
#1) Gráfico da série temporal de NTL
#2) Tabela visual com valores da série temporal
#3) Arquivo Excel com os dados extraídos

#-------------------------------------------------------------------------------
# Importa Bibliotecas
#-------------------------------------------------------------------------------
# ============================================================
# ALGORITMO CIENTÍFICO – ANÁLISE DE LUZ NOTURNA VIIRS (NTL)
# Sensor: VIIRS Day/Night Band
# ============================================================

import os
import numpy as np
import datetime
import statistics as stat
import matplotlib.pyplot as plt
from osgeo import gdal
import pandas as pd
from qgis.PyQt.QtWidgets import QInputDialog
import urllib.request
import json


# ============================================================
# FUNÇÃO: Entrada de coordenadas
# ============================================================

def get_coordinates():

    lat, ok1 = QInputDialog.getDouble(
        None,
        "Entrada de Coordenadas",
        "Digite a Latitude:",
        decimals=6
    )

    lon, ok2 = QInputDialog.getDouble(
        None,
        "Entrada de Coordenadas",
        "Digite a Longitude:",
        decimals=6
    )

    if ok1 and ok2:
        return lat, lon
    else:
        raise Exception("Entrada cancelada pelo usuário.")


# ============================================================
# FUNÇÃO: Detectar cidade e bairro (OpenStreetMap)
# ============================================================

def get_location(lat, lon):

    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"

    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'VIIRS_NTL_Analysis'}
    )

    response = urllib.request.urlopen(req)

    data = json.loads(response.read().decode())

    address = data.get("address", {})

    city = address.get(
        "city",
        address.get(
            "town",
            address.get("village", "Desconhecida")
        )
    )

    suburb = address.get(
        "suburb",
        address.get(
            "neighbourhood",
            address.get("quarter", "")
        )
    )

    state = address.get("state", "")

    return city, suburb, state


# ============================================================
# FUNÇÃO: Plot da série temporal
# ============================================================

def plot_time_series(jd, dnb_value3, dnb_value1, city, suburb):

    plt.figure(figsize=(12,6))

    plt.plot(jd, dnb_value3, label="DNB 3x3", marker='o')
    plt.plot(jd, dnb_value1, label="DNB 1x1", marker='o')

    plt.xlabel("Data")
    plt.ylabel("Radiação NTL (W.m⁻².sr⁻¹)")

    titulo = f"Série Temporal de NTL - {city} ({suburb})"

    plt.title(titulo)

    plt.legend()
    plt.grid(True)

    plt.tight_layout()

    plt.savefig("Serie_Temporal_NTL.png", dpi=300)
    plt.savefig("Serie_Temporal_NTL.pdf")

    plt.show()

# ============================================================
# FUNÇÃO: Plotar tabela da série temporal (N páginas automáticas)
# ============================================================

def plot_table(df, city, suburb, state):

    # Renomear colunas
    df_plot = df.copy()

    df_plot.columns = ["Data", "DNB 3 x 3 (W.m⁻².sr⁻¹)", "DNB 1 x 1 (W.m⁻².sr⁻¹)"]

    # Converter valores para 3 casas decimais
    df_plot["DNB 3 x 3 (W.m⁻².sr⁻¹)"] = df_plot["DNB 3 x 3 (W.m⁻².sr⁻¹)"].apply(
        lambda x: f"{x:.3f}" if pd.notnull(x) else ""
    )

    df_plot["DNB 1 x 1 (W.m⁻².sr⁻¹)"] = df_plot["DNB 1 x 1 (W.m⁻².sr⁻¹)"].apply(
        lambda x: f"{x:.3f}" if pd.notnull(x) else ""
    )

    # Converter data para string
    df_plot["Data"] = df_plot["Data"].astype(str)

    # --------------------------------------------------------
    # Definir número máximo de linhas por página
    # --------------------------------------------------------

    linhas_por_pagina = 25

    total_linhas = len(df_plot)

    total_paginas = int(np.ceil(total_linhas / linhas_por_pagina))

    # --------------------------------------------------------
    # Criar páginas automaticamente
    # --------------------------------------------------------

    for i in range(total_paginas):

        inicio = i * linhas_por_pagina
        fim = inicio + linhas_por_pagina

        pagina = df_plot.iloc[inicio:fim]

        fig, ax = plt.subplots(figsize=(10,8))

        ax.axis('off')

        titulo = f"Tabela da Série Temporal de NTL\n{suburb}, {city}/{state}"

        plt.title(titulo, fontsize=14, weight='bold', pad=20)

        tabela = ax.table(
            cellText=pagina.values,
            colLabels=pagina.columns,
            cellLoc='center',
            loc='center'
        )

        tabela.auto_set_font_size(False)
        tabela.set_fontsize(10)
        tabela.scale(1.2,1.3)

        # ----------------------------------------------------
        # Numeração automática das páginas
        # ----------------------------------------------------

        if total_paginas == 1:
            texto_pagina = "Página 1/1"
        else:
            texto_pagina = f"Página {i+1}/{total_paginas}"

        plt.figtext(
            0.5, 0.02,
            texto_pagina,
            ha="center",
            fontsize=10
        )

        # Salvar figura
        plt.savefig(
            f"Tabela_Serie_Temporal_NTL_pag{i+1}.png",
            dpi=300,
            bbox_inches='tight'
        )

        plt.show()

# ============================================================
# FUNÇÃO: Converter data juliana
# ============================================================

def convert_julian_to_date(julian_day):

    return datetime.datetime.strptime(julian_day, '%y%j').date()


# ============================================================
# FUNÇÃO: Extrair valor do raster
# ============================================================

def get_raster_data(input_raster, lat, lon, window):

    raster = gdal.Open(input_raster)

    if raster is None:
        print("Erro ao abrir:", input_raster)
        return None

    band = raster.GetRasterBand(1)

    transform = raster.GetGeoTransform()

    x_origin, pixel_width, _, y_origin, _, pixel_height = transform

    pixel_height = abs(pixel_height)

    col = int((lon - x_origin) / pixel_width)
    row = int((y_origin - lat) / pixel_height)

    data = band.ReadAsArray()

    if window == 3:

        indices = [(i,j) for i in [-1,0,1] for j in [-1,0,1]]

        values = [
            data[row+i, col+j]
            for i,j in indices
            if 0 <= row+i < data.shape[0] and 0 <= col+j < data.shape[1]
        ]

        return stat.mean(values) if values else None

    else:

        if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
            return data[row,col]
        else:
            return None


# ============================================================
# FUNÇÃO: Processar HDF5
# ============================================================

def process_hd5(input_hd5, layer, output_folder, lat, lon, window):

    hdflayer = gdal.Open(input_hd5)

    subhdflayer = hdflayer.GetSubDatasets()[layer][0]

    rlayer = gdal.Open(subhdflayer)

    output_raster = os.path.join(
        output_folder,
        os.path.basename(input_hd5).replace(".h5",".tif")
    )

    gdal.Translate(output_raster, rlayer)

    value = get_raster_data(output_raster, lat, lon, window)

    os.remove(output_raster)

    return value


# ============================================================
# CONFIGURAÇÃO DOS DIRETÓRIOS
# ============================================================

input_folder = "C:/Users/Clima/Downloads/LAACS/Florianopolis SC/Data_FL7"
output_folder = "C:/Users/Clima/Downloads/LAACS/Output/"

os.chdir(input_folder)


# ============================================================
# ENTRADA DE COORDENADAS
# ============================================================

lat, lon = get_coordinates()

print("Latitude:", lat)
print("Longitude:", lon)


# ============================================================
# IDENTIFICAR LOCALIZAÇÃO
# ============================================================

city, suburb, state = get_location(lat, lon)

print("Cidade:", city)
print("Bairro:", suburb)
print("Estado:", state)


# ============================================================
# PROCESSAMENTO DOS DADOS
# ============================================================

raster_files = sorted([f for f in os.listdir(input_folder) if f.endswith(".h5")])

dnb_value1 = []
dnb_value3 = []
jd = []

for file in raster_files:

    year, julian_day = file[11:13], file[13:16]

    date_of_year = convert_julian_to_date(year + julian_day)

    jd.append(date_of_year)

    v3 = process_hd5(file, 2, output_folder, lat, lon, 3)
    v1 = process_hd5(file, 2, output_folder, lat, lon, 1)

    if v3 is not None:
        v3 = v3 / 10

    if v1 is not None:
        v1 = v1 / 10

    dnb_value3.append(v3)
    dnb_value1.append(v1)


# ============================================================
# TABELA FINAL
# ============================================================

df = pd.DataFrame({
    "Data": jd,
    "DNB_3x3": dnb_value3,
    "DNB_1x1": dnb_value1
})

# Arredondar valores para 3 casas decimais
df["DNB_3x3"] = df["DNB_3x3"].round(3)
df["DNB_1x1"] = df["DNB_1x1"].round(3)

# Converter data para formato dia-mês-ano
df["Data"] = pd.to_datetime(df["Data"]).dt.strftime("%d-%m-%Y")

print("\nTabela de resultados:\n")

print(df)


# ============================================================
# EXPORTAR PARA EXCEL
# ============================================================

excel_file = f"NTL_{city}_{suburb}.xlsx"

df.to_excel(excel_file, index=False)


# ============================================================
# GERAR GRÁFICO
# ============================================================

plot_time_series(jd, dnb_value3, dnb_value1, city, suburb)


# ============================================================
# GERAR TABELA GRÁFICA
# ============================================================

plot_table(df, city, suburb, state)