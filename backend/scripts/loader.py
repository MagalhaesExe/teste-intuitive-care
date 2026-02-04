import pandas as pd
import psycopg2
from psycopg2 import extras
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
"host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "ans_dashboard"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", "5432"),
}

def load_data():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Extrai dimensões únicas de operadoras para garantir a normalização no banco        
        file_enriquecido = "data/processed/consolidado_enriquecido.csv"
        if os.path.exists(file_enriquecido):
            logger.info("Carregando Operadoras Ativas...")
            df_cad = pd.read_csv(file_enriquecido)
            
            # Remove duplicatas baseadas no Registro ANS para integridade da Chave Primária
            operadoras = df_cad[['RegistroANS', 'CNPJ', 'RazaoSocial', 'Modalidade', 'UF']].drop_duplicates(subset=['RegistroANS'])
            
            # Conversão para tuplas para compatibilidade com o adaptador psycopg2
            data_ops = [tuple(x) for x in operadoras.values]
            
            # Estratégia de UPSERT (ON CONFLICT): Garante que o script seja idempotente,
            # atualizando dados existentes em vez de falhar por duplicidade.
            sql_ops = """
                INSERT INTO operadoras_ativas (registro_ans, cnpj, razao_social, modalidade, uf)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (registro_ans) DO UPDATE SET razao_social = EXCLUDED.razao_social;
            """
            extras.execute_batch(cur, sql_ops, data_ops)

        logger.info("Carregando Despesas Consolidadas...")

        # Tratamento de Strings em campos numéricos via Pandas: Força conversão numérica
        # transformando strings inválidas em 0 para evitar erros de cast no PostgreSQL
        df_cad['ValorDespesas'] = pd.to_numeric(df_cad['ValorDespesas'], errors='coerce').fillna(0)
        
        data_fin = [tuple(x) for x in df_cad[['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas', 'RegistroANS', 'Modalidade', 'UF']].values]
        
        sql_fin = """
            INSERT INTO despesas_consolidadas (cnpj, razao_social, trimestre, ano, valor_despesa, registro_ans, modalidade, uf)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        # TRUNCATE é utilizado para cargas 'Full', limpando a tabela 
        # e resetando sequências de ID antes da nova inserção em lote.
        cur.execute("TRUNCATE TABLE despesas_consolidadas RESTART IDENTITY;")

        # Uso de execute_batch para reduzir o overhead de rede através de múltiplos INSERTs agrupados
        extras.execute_batch(cur, sql_fin, data_fin)

        # Persistência dos resultados estatísticos agregados por Operadora/UF
        file_agg = "data/processed/despesas_agregadas.csv"
        if os.path.exists(file_agg):
            logger.info("Carregando Dados Agregados...")
            df_agg = pd.read_csv(file_agg)
            
            data_agg = [tuple(x) for x in df_agg.values]
            sql_agg = """
                INSERT INTO despesas_agregadas (razao_social, uf, total_despesas, media_trimestral, desvio_padrao)
                VALUES (%s, %s, %s, %s, %s);
            """
            
            # Substituição total dos dados (Full Refresh) da tabela de análise
            cur.execute("TRUNCATE TABLE despesas_agregadas RESTART IDENTITY;")
            extras.execute_batch(cur, sql_agg, data_agg)

        conn.commit()
        logger.info("Carga concluída com sucesso!")

    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Erro crítico na carga: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    load_data()