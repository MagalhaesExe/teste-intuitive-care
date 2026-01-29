import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

URL_DIRETORIO = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
CADASTRO_LOCAL = "data/raw/cadastro_operadoras.csv"

def buscar_e_baixar_csv():
    if not os.path.exists("data/raw"): os.makedirs("data/raw")
    
    try:
        logger.info(f"Acessando diretório da ANS: {URL_DIRETORIO}")
        response = requests.get(URL_DIRETORIO)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura por links que terminam com .csv
        link_csv = None
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.csv'):
                link_csv = href
                break
        
        if not link_csv:
            raise Exception("Nenhum arquivo CSV encontrado no diretório.")

        # Constrói a URL completa de download
        url_download = URL_DIRETORIO + link_csv
        logger.info(f"Arquivo encontrado: {link_csv}. Iniciando download...")
        
        res_file = requests.get(url_download)
        with open(CADASTRO_LOCAL, 'wb') as f:
            f.write(res_file.content)
            
        logger.info("Download do cadastro concluído com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao buscar/baixar o cadastro: {e}")
        return False
    
def enrich_data():
    if not os.path.exists(CADASTRO_LOCAL):
        if not buscar_e_baixar_csv(): return

    # 1. Carregar dados financeiros
    df_fin = pd.read_csv("data/processed/consolidado_despesas.csv", dtype={'CNPJ': str})
    
    # 2. Carregar dados cadastrais
    try:
        df_cad = pd.read_csv(CADASTRO_LOCAL, sep=';', encoding='latin-1', dtype={'CNPJ': str})
        if len(df_cad.columns) < 2:
            df_cad = pd.read_csv(CADASTRO_LOCAL, sep=',', encoding='latin-1', dtype={'CNPJ': str})
    except Exception as e:
        logger.error(f"Erro ao ler CSV de cadastro: {e}")
        return

    logger.info(f"Colunas encontradas no cadastro: {df_cad.columns.tolist()}")

    # --- MAPEAMENTO INTELIGENTE DE COLUNAS ---
    # Note que renomeamos o CNPJ do cadastro para 'CNPJ_CADASTRO' para evitar conflito no merge
    mapeamento = {}
    colunas_procuradas = {
        'CNPJ_CADASTRO': ['CNPJ', 'cnpj'], 
        'RegistroANS': ['REGISTRO_OPERADORA', 'Registro_ANS', 'Registro ANS', 'Reg_ANS'],
        'Modalidade': ['Modalidade', 'MODALIDADE'],
        'UF': ['UF', 'Uf', 'Estado']
    }

    for alvo, aliases in colunas_procuradas.items():
        for alias in aliases:
            if alias in df_cad.columns:
                mapeamento[alias] = alvo
                break

    if len(mapeamento) < 4:
        logger.error(f"Colunas faltantes. Encontradas: {list(mapeamento.keys())}")
        return

    df_cad = df_cad[list(mapeamento.keys())].rename(columns=mapeamento)
    df_cad = df_cad.drop_duplicates(subset=['RegistroANS'], keep='first')
    
    # --- PADRONIZAÇÃO E JOIN ---
    logger.info("Padronizando tipos e realizando Join...")
    df_fin['CNPJ'] = df_fin['CNPJ'].astype(str).str.strip()
    df_cad['RegistroANS'] = df_cad['RegistroANS'].astype(str).str.strip()

    df_final = pd.merge(
        df_fin, 
        df_cad, 
        left_on='CNPJ',      # Registro ANS que está no arquivo de despesas
        right_on='RegistroANS', 
        how='left'
    )

    # --- PÓS-PROCESSAMENTO ---
    # Criamos a coluna final de CNPJ usando o valor real do cadastro
    df_final['CNPJ_Final'] = df_final['CNPJ_CADASTRO'].fillna(df_final['CNPJ'])
    
    # Selecionamos as 8 colunas finais conforme o desafio
    colunas_finais = [
        'CNPJ_Final', 'RazaoSocial', 'Trimestre', 'Ano', 
        'ValorDespesas', 'RegistroANS', 'Modalidade', 'UF'
    ]
    
    df_saida = df_final[colunas_finais].copy()
    df_saida.columns = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas', 'RegistroANS', 'Modalidade', 'UF']

    # Preenchimento de nulos para garantir qualidade
    df_saida['Modalidade'] = df_saida['Modalidade'].fillna('NÃO ENCONTRADO')
    df_saida['UF'] = df_saida['UF'].fillna('NI')
    # Se não achou RegistroANS no merge, usa o ID que veio no arquivo de despesas
    df_saida['RegistroANS'] = df_saida['RegistroANS'].fillna(df_saida['CNPJ']) 

    df_saida.to_csv("data/processed/consolidado_enriquecido.csv", index=False)
    logger.info("Sucesso! Arquivo 'consolidado_enriquecido.csv' gerado.")
    
if __name__ == "__main__":
    enrich_data()