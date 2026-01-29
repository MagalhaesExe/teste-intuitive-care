import pandas as pd
import zipfile
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_FILE = "data/processed/consolidado_enriquecido.csv"
OUTPUT_FILE = "data/processed/despesas_agregadas.csv"
ZIP_FINAL = "Teste_Alex_Magalhaes.zip" 

def executar_agregacao():
    if not os.path.exists(INPUT_FILE):
        logger.error("Arquivo enriquecido não encontrado!")
        return

    df = pd.read_csv(INPUT_FILE)

    logger.info("Iniciando cálculos de agregação...")

    # Agregação para análise de performance financeira por UF
    # Calcula métricas de tendência central (média) e dispersão (desvio padrão)
    agg_df = df.groupby(['RazaoSocial', 'UF']).agg(
        TotalDespesas=('ValorDespesas', 'sum'),
        MediaTrimestral=('ValorDespesas', 'mean'),
        DesvioPadrao=('ValorDespesas', 'std')
    ).reset_index()

    # Tratamento de Desvio Padrão: 
    # Operadoras com apenas 1 registro terão NaN no Desvio Padrão
    agg_df['DesvioPadrao'] = agg_df['DesvioPadrao'].fillna(0)

    # Ordenação por TotalDespesas (Maior para Menor)
    agg_df = agg_df.sort_values(by='TotalDespesas', ascending=False)

    agg_df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Arquivo agregado salvo em: {OUTPUT_FILE}")

    with zipfile.ZipFile(ZIP_FINAL, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUTPUT_FILE, arcname="despesas_agregadas.csv")
    
    logger.info(f"Desafio concluído! Arquivo final gerado: {ZIP_FINAL}")

if __name__ == "__main__":
    executar_agregacao()