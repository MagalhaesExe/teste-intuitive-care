import pandas as pd
import os
import glob
import re
import zipfile
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processamento.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

RAW_DIR = "data/raw"
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "consolidado_despesas.csv")

def extrair_data_do_caminho(path):
    nome_arq = os.path.basename(path)
    ano = "2025"
    trimestre = "1"
    
    match_ano = re.search(r"20\d{2}", nome_arq)
    if match_ano:
        ano = match_ano.group()
    
    match_tri = re.search(r"(\d)T", nome_arq.upper())
    if match_tri:
        trimestre = match_tri.group(1)
        
    return ano, trimestre

def process_files():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Diretório de saída criado: {OUTPUT_DIR}")

    all_data = []
    files = glob.glob(f"{RAW_DIR}/**/*.csv", recursive=True) + glob.glob(f"{RAW_DIR}/**/*.txt", recursive=True)

    if not files:
        logger.warning("Nenhum arquivo encontrado em data/raw")
        return

    for file_path in files:
        logger.info(f"Iniciando leitura: {os.path.basename(file_path)}")
        ano, trimestre = extrair_data_do_caminho(file_path)
        
        try:
            # Processamento incremental (Trade-off técnico: Memória vs Performance)
            chunks = pd.read_csv(file_path, sep=';', engine='python', encoding='latin-1', chunksize=100000, on_bad_lines='skip')
            
            for chunk in chunks:
                chunk.columns = [c.upper().strip().replace('"', '') for c in chunk.columns]
                
                if 'DESCRICAO' in chunk.columns:
                    chunk['DESCRICAO'] = chunk['DESCRICAO'].astype(str).str.strip()
                    
                    mask = (chunk['DESCRICAO'].str.contains("EVENTOS", na=False, case=False)) & \
                           (chunk['DESCRICAO'].str.contains("SINISTROS", na=False, case=False))
                    
                    filtered = chunk[mask].copy()
                    
                    if not filtered.empty:
                        res = pd.DataFrame()
                        res['CNPJ'] = filtered['REG_ANS']
                        res['RazaoSocial'] = filtered.get('RAZAO_SOCIAL', 'OPERADORA ' + filtered['REG_ANS'].astype(str))
                        res['Trimestre'] = trimestre
                        res['Ano'] = ano
                        
                        def limpar_valor(v):
                            v = str(v).replace('"', '').strip()
                            if not v or v == 'nan': return 0.0
                            if '.' in v and ',' in v:
                                v = v.replace('.', '')
                            v = v.replace(',', '.')
                            try:
                                return float(v)
                            except:
                                return 0.0

                        res['ValorDespesas'] = filtered['VL_SALDO_FINAL'].apply(limpar_valor)
                        res = res[res['ValorDespesas'] > 0]
                        all_data.append(res)
                        
        except Exception as e:
            logger.error(f"Erro ao processar o arquivo {file_path}: {e}")

    if all_data:
        logger.info("Consolidando dados filtrados...")
        final_df = pd.concat(all_data, ignore_index=True)
        
        final_df = final_df.groupby(['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano'], as_index=False).agg({
            'ValorDespesas': 'sum'
        })
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        logger.info(f"Sucesso! {len(final_df)} registros consolidados em {OUTPUT_FILE}")    
    else:
        logger.error("O filtro 'EVENTOS/SINISTROS' não encontrou dados válidos nos arquivos.")
        return False
    
def criar_zip():
    if not os.path.exists(OUTPUT_FILE):
        logger.error("Arquivo CSV não encontrado para compactação.")
        return

    zip_path = os.path.join(OUTPUT_DIR, "consolidado_despesas.zip")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(OUTPUT_FILE, arcname="consolidado_despesas.csv")
        logger.info(f"Arquivo compactado com sucesso em: {zip_path}")
    except Exception as e:
        logger.error(f"Falha ao criar arquivo ZIP: {e}")

if __name__ == "__main__":
    if process_files():
        criar_zip()