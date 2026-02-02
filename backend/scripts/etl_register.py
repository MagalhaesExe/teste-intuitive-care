import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_FILE = "data/raw/cadastro_operadoras.csv"
OUTPUT_FILE = "data/processed/cadastro_operadoras_limpo.csv"

def limpar_cadastro():
    logging.info("Lendo arquivo bruto da ANS...")
    try:
        df = pd.read_csv(INPUT_FILE, sep=';', encoding='latin-1', dtype=str)
    except Exception as e:
        logging.error(f"Erro ao ler: {e}")
        return

    logging.info(f"Colunas encontradas: {list(df.columns)}")

    colunas_banco = pd.DataFrame()

    try:
        colunas_banco['registro_ans'] = df['REGISTRO_OPERADORA'] 
        colunas_banco['cnpj'] = df['CNPJ']
        colunas_banco['razao_social'] = df['Razao_Social']
        colunas_banco['modalidade'] = df['Modalidade']
        colunas_banco['uf'] = df['UF']
        colunas_banco['data_registro_ans'] = df['Data_Registro_ANS']
                    
    except KeyError as e:
        logger.error(f"Coluna não encontrada no CSV: {e}")
        logger.info("Verifique se o arquivo data/raw/cadastro_operadoras.csv está correto.")
        return
    
    colunas_banco.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', sep=',')
    logging.info(f"Arquivo limpo gerado com sucesso: {OUTPUT_FILE}")

if __name__ == "__main__":
    limpar_cadastro()