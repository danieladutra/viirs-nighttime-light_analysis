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

#1) Converte arquivos HDF5 em raster GeoTIFF temporário.
#2) Extrai valores de radiância para um ponto geográfico específico.
#3) Calcula dois tipos de amostragem espacial:
   #- Pixel único (1x1)
   #- Média de vizinhança (3x3)
#4) Converte datas julianas para datas do calendário.
#5) Gera gráfico da série temporal.
#6) Exibe tabela de valores.
#7) Exporta os resultados para um arquivo Excel.

#Bibliotecas necessárias
#-----------------------
#- os
#- numpy
#- datetime
#- statistics
#- matplotlib
#- GDAL
#- pandas

#Saídas do algoritmo
#-------------------
#1) Gráfico da série temporal de NTL
#2) Tabela visual com valores da série temporal
#3) Arquivo Excel com os dados extraídos

#-------------------------------------------------------------------------------
# Importa Bibliotecas
#-------------------------------------------------------------------------------
import os
import numpy as np
import datetime
import statistics as stat
import matplotlib.pyplot as plt
from osgeo import gdal
import pandas as pd


# ---------------------------------------------------------------------------
# FUNÇÃO: plot_time_series
# ---------------------------------------------------------------------------
# Objetivo:
# Gerar o gráfico da série temporal de radiância NTL e também
# apresentar uma tabela com os valores calculados.
#
# Parâmetros:
# jd           -> lista de datas
# dnb_value3   -> valores médios em janela 3x3
# dnb_value1   -> valores em pixel único (1x1)
# ---------------------------------------------------------------------------


def plot_time_series(jd, dnb_value3, dnb_value1):
    
    # Criação da figura principal do gráfico
    plt.figure(figsize=(12, 6))
    
    # Plotagem das séries temporais
    plt.plot(jd, dnb_value3, label="DNB_3x3", linestyle='solid', marker='o')
    plt.plot(jd, dnb_value1, label="DNB_1x1", linestyle='solid', marker='o')
    
    # Rótulos dos eixos
    plt.xlabel('Data')
    plt.ylabel('Radiação NTL (W.m⁻².sr⁻¹)')
    
    # Títulos possíveis do gráfico (descomentar conforme o bairro analisado)
    plt.title('Série Temporal de NTL - Florianpolis, SC (B. Daniela)')
    #plt.title('Série Temporal de NTL - Florianópolis, SC (B. Armação do Pântano do Sul)')
    #plt.title('Série Temporal de NTL - Florianópolis, SC (B. Barra da Lagoa)') 
    #plt.title('Série Temporal de NTL - Florianópolis, SC (B. São João do Rio Vermelho)')
    #plt.title('Série Temporal de NTL - Florianópolis, SC (Canasvieiras)') 
    #plt.title('Série Temporal de NTL - Florianópolis, SC (Canto da Lagoa)')
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.show()
    
    # -----------------------------------------------------------------------
    # Criação de uma tabela com os valores da série temporal
    # -----------------------------------------------------------------------

    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.axis('tight')
    ax.axis('off')
    
    
    col_labels = ['Data', 'DNB_3x3', 'DNB_1x1']
    
    # Conversão das datas para string
    jd_str = [date.strftime('%Y-%m-%d') for date in jd]
    
    # Montagem das linhas da tabela
    rows = [[date, f"{v3:.3f}", f"{v1:.3f}"] for date, v3, v1 in zip(jd_str, dnb_value3, dnb_value1)]
    
    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
        colColours=['#f0f0f0']*3
     )
    
    # Títulos possíveis da tabela (descomentar conforme o bairro analisado)
    plt.title('Tabela de Valores da Série Temporal Florianópolis SC (B. Daniela)')
    #plt.title('Tabela de Valores da Série Temporal Florianópolis SC (B. Armação do Pântano do Sul)')
    #plt.title('Tabela de Valores da Série Temporal Florianópolis SC (B. Barra da Lagoa)')
    #plt.title('Tabela de Valores da Série Temporal Florianópolis SC (B. São João do Rio Vermelho)')
    #plt.title('Tabela de Valores da Série Temporal Florianópolis SC (B. Canasvieiras)')
    #plt.title('Tabela de Valores da Série Temporal Florianópolis SC (B. Canto da Lagoa)')
    
    plt.show()


# ---------------------------------------------------------------------------
# FUNÇÃO: convert_julian_to_date
# ---------------------------------------------------------------------------
# Objetivo:
# Converter data juliana (YYDDD) para data do calendário.
#
# Exemplo:
# 23045 → 14/02/2023
# ---------------------------------------------------------------------------

def convert_julian_to_date(julian_day):
    return datetime.datetime.strptime(julian_day, '%y%j').date()

# ---------------------------------------------------------------------------
# FUNÇÃO: get_raster_data
# ---------------------------------------------------------------------------
# Objetivo:
# Extrair valores de radiância em um pixel ou em uma janela 3x3.
#
# Parâmetros:
# input_raster -> arquivo raster temporário
# lat          -> latitude do ponto
# lon          -> longitude do ponto
# window       -> tamanho da janela (1 ou 3)
# ---------------------------------------------------------------------------

def get_raster_data(input_raster, lat, lon, window):
    raster = gdal.Open(input_raster, gdal.GA_ReadOnly)
    
    if raster is None:
        print("Erro ao abrir imagem:", input_raster)
        return None
    
    band = raster.GetRasterBand(1)
    
    transform = raster.GetGeoTransform()
    
    x_origin, pixel_width, _, y_origin, _, pixel_height = transform
    
    pixel_height = abs(pixel_height)
    
    # Conversão de coordenadas geográficas para índice de pixel
    col = int((lon - x_origin) / pixel_width)
    row = int((y_origin - lat) / pixel_height)
    
    data = band.ReadAsArray()
    
    # Cálculo da média em janela 3x3
    
    if window == 3:
        indices = [(i, j) for i in [-1, 0, 1] for j in [-1, 0, 1]]

        values = [
            data[row + i, col + j]
            for i, j in indices
            if 0 <= row + i < data.shape[0] and 0 <= col + j < data.shape[1]
        ]

        return float(format(stat.mean(values), '.2f')) if values else None

    # Valor de pixel único
    else:

        return float(data[row, col]) if 0 <= row < data.shape[0] and 0 <= col < data.shape[1] else None

        
# ---------------------------------------------------------------------------
# FUNÇÃO: process_hd5
# ---------------------------------------------------------------------------
# Objetivo:
# Converter um arquivo HDF5 para GeoTIFF temporário e extrair valores
# de radiância NTL.
#
# Parâmetros:
# input_hd5     -> arquivo HDF5
# layer         -> índice da subcamada
# output_folder -> pasta temporária
# lat, lon      -> coordenadas do ponto
# window        -> tamanho da janela de amostragem
# ---------------------------------------------------------------------------

def process_hd5(input_hd5, layer, output_folder, lat, lon, window):
    
    hdflayer = gdal.Open(input_hd5, gdal.GA_ReadOnly)
    
    subhdflayer = hdflayer.GetSubDatasets()[layer][0]
    
    rlayer = gdal.Open(subhdflayer, gdal.GA_ReadOnly)
    
    output_raster = os.path.join(
        output_folder,
        os.path.basename(input_hd5).replace('.h5', '.tif')
    )
    
    # Conversão para GeoTIFF
    gdal.Translate(
        output_raster,
        rlayer,
        options=gdal.TranslateOptions(format='GTiff')
    )
    
    # Extração do valor do pixel
    value = get_raster_data(output_raster, lat, lon, window)
    
    # Remoção do raster temporário
    os.remove(output_raster)
    
    return value


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DE DIRETÓRIOS
# ---------------------------------------------------------------------------

input_folder = "C:/Users/Clima/Downloads/LAACS/Florianopolis SC/Data_FL7"
output_folder = "C:/Users/Clima/Downloads/LAACS/Output/"

os.chdir(input_folder)

# --------------------------------------------------------------------------------
# DEFINIÇÃO DAS COORDENADAS DE INTERESSE (descomentar conforme o bairro analisado)
# --------------------------------------------------------------------------------

lat, lon = -27.4507, -48.5201  # B. Daniela
# lat, lon = -27.7542, -48.5041  # B. Armação do Pântano do Sul
# lat, lon = -27.5999, -48.4325  # B. Barra da Lagoa
# lat, lon = -27.4840, -48.4049  # B. São João do Rio Vermelho
# lat, lon = -27.4886, -48.4694  # Canasvieiras         
# lat, lon = -27.6205, -48.4823  # Canto da Lagoa

# ---------------------------------------------------------------------------
# LISTAGEM DOS ARQUIVOS HDF5
# ---------------------------------------------------------------------------

raster_files = sorted(os.listdir(input_folder))

# Inicialização das listas da série temporal
dnb_value1, dnb_value3, jd = [], [], []

# ---------------------------------------------------------------------------
# PROCESSAMENTO DOS ARQUIVOS
# ---------------------------------------------------------------------------

for file in raster_files:

    if not file.endswith(".h5"):
        continue

    try:
        year, julian_day = file[11:13], file[13:16]

        if not (year.isdigit() and julian_day.isdigit()):
            print("Arquivo ignorado:", file)
            continue

        date_of_year = convert_julian_to_date(year + julian_day)
        jd.append(date_of_year)

        dnb_value3.append(process_hd5(file, 2, output_folder, lat, lon, 3) / 10)
        dnb_value1.append(process_hd5(file, 2, output_folder, lat, lon, 1) / 10)

    except Exception as e:
        print("Erro ao processar:", file, e)

# ---------------------------------------------------------------------------
# GERAÇÃO DO GRÁFICO
# ---------------------------------------------------------------------------

plot_time_series(jd, dnb_value3, dnb_value1)

print (jd, dnb_value3, dnb_value1)

# ---------------------------------------------------------------------------
# CRIAÇÃO DO DATAFRAME
# ---------------------------------------------------------------------------

df = pd.DataFrame({
    "Data": jd,
    "DNB_3x3": dnb_value3,
    "DNB_1x1": dnb_value1
})

# Impressão da tabela no terminal
print(df)

# ---------------------------------------------------------------------------
# EXPORTAÇÃO PARA EXCEL (descomentar conforme o bairro analisado)
# ---------------------------------------------------------------------------

excel_file = os.path.join(output_folder, "Serie_Temporal_NTL_Florianópolis_SC_Bairro Daniela.xlsx")
#excel_file = os.path.join(output_folder, "Serie_Temporal_NTL_Florianópolis_SC_Bairro Armação do Pântano do Sul.xlsx")
#excel_file = os.path.join(output_folder, "Serie_Temporal_NTL_Florianópolis_SC_Bairro Barra da Lagoa.xlsx")
#excel_file = os.path.join(output_folder, "Serie_Temporal_NTL_Florianópolis_SC_Bairro São João do Rio Vermelho.xlsx")
#excel_file = os.path.join(output_folder, "Serie_Temporal_NTL_Florianópolis_SC_Bairro Canasvieiras.xlsx")
#excel_file = os.path.join(output_folder, "Serie_Temporal_NTL_Florianópolis_SC_Bairro Canto da Lagoa.xlsx")

df.to_excel(excel_file, index=False)

print("Arquivo Excel salvo em:", excel_file)