import pandas as pd
import psycopg2
from psycopg2 import extras
import os
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações do Banco (Ajuste com suas credenciais)
DB_CONFIG = {
    "host": "localhost",
    "database": "ans_db",
    "user": "postgres",
    "password": "admin"
}

CSV_FILE = "data/processed/consolidado_validado.csv"

def load_data():
    if not os.path.exists(CSV_FILE):
        logger.error(f"Arquivo {CSV_FILE} não encontrado. Rode o processor.py primeiro.")
        return

    df = pd.read_csv(CSV_FILE)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        logger.info("Carregando dados das Operadoras...")
        operadoras = df[['CNPJ', 'RazaoSocial']].drop_duplicates()
        for _, row in operadoras.iterrows():
            cur.execute("""
                INSERT INTO operadoras (registro_ans, razao_social)
                VALUES (%s, %s)
                ON CONFLICT (registro_ans) DO UPDATE SET razao_social = EXCLUDED.razao_social;
            """, (str(row['CNPJ']), row['RazaoSocial']))

        logger.info("Limpando registros financeiros antigos para nova carga...")
        cur.execute("TRUNCATE TABLE demonstracoes_financeiras RESTART IDENTITY;")

        logger.info("Carregando Demonstrações Financeiras...")
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO demonstracoes_financeiras (registro_ans, ano, trimestre, valor_despesas)
                VALUES (%s, %s, %s, %s);
            """, (str(row['CNPJ']), int(row['Ano']), int(row['Trimestre']), float(row['ValorDespesas'])))

        conn.commit()
        logger.info("Carga finalizada com sucesso!")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro na carga de dados: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    load_data()