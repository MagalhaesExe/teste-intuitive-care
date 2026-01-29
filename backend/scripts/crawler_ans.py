import os
import requests
from bs4 import BeautifulSoup
import zipfile
import logging
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("execucao.log"),
        logging.StreamHandler()              
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
DOWNLOAD_DIR = "data/raw"

def download_and_extract():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        logger.info(f"Diretório criado: {DOWNLOAD_DIR}")

    logger.info(f"Buscando anos em: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Filtra links que representam anos e ordena de forma decrescente para priorizar dados recentes
        links = [a['href'] for a in soup.find_all('a', href=True)]
        years = sorted([l for l in links if l.strip('/').isdigit()], reverse=True)
        
        logger.info(f"Anos encontrados: {years}")

        found_quarters = []
        for year in years:
            # Estratégia de parada: busca apenas os trimestres mais recentes conforme limite definido
            if len(found_quarters) >= 1: break
            year_url = BASE_URL + year if BASE_URL.endswith('/') else BASE_URL + '/' + year
            logger.info(f"Acessando ano: {year_url}")
            
            # Acessa a pasta do ano para buscar subpastas de trimestres
            res_year = requests.get(year_url, timeout=15)
            soup_year = BeautifulSoup(res_year.text, 'html.parser')
            
            q_links = [a['href'] for a in soup_year.find_all('a', href=True) if a['href'] not in ['../', './', '/']]
            q_links = sorted([q for q in q_links if q.endswith('/')], reverse=True)
            
            # Coleta as URLs finais onde os arquivos ZIP residem
            for q in q_links:
                if len(found_quarters) >= 3: break
                q_full_url = year_url
                found_quarters.append(q_full_url)

        for q_url in found_quarters:
            logger.info(f"Verificando arquivos em: {q_url}")
            res_q = requests.get(q_url, timeout=15)
            soup_q = BeautifulSoup(res_q.text, 'html.parser')
            
            zips = [a['href'] for a in soup_q.find_all('a', href=True) if a['href'].lower().endswith('.zip')]
            
            if not zips:
                logger.warning(f"Nenhum ZIP encontrado nesta pasta específica.")
                continue

            for zip_name in zips:
                zip_url = q_url + zip_name if q_url.endswith('/') else q_url + '/' + zip_name
                clean_zip_name = zip_name.strip('/').split('/')[-1]
                path = os.path.join(DOWNLOAD_DIR, clean_zip_name)
                
                # Download via Stream para otimizar consumo de memória com arquivos grandes
                logger.info(f"Baixando: {clean_zip_name}...")
                r = requests.get(zip_url, stream=True)
                if r.status_code == 200:
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Extração e limpeza imediata do arquivo ZIP para economizar espaço em disco
                    try:
                        with zipfile.ZipFile(path, 'r') as zip_ref:
                            folder_name = clean_zip_name.replace('.zip', '').replace('.ZIP', '')
                            extract_folder = os.path.join(DOWNLOAD_DIR, folder_name)
                            zip_ref.extractall(extract_folder)
                            logger.info(f"Extraído em: {extract_folder}")
                    except Exception as e:
                        logger.error(f"ERRO ao extrair {clean_zip_name}: {e}")
                    
                    if os.path.exists(path):
                        os.remove(path)
                else:
                    logger.error(f"Falha no download. Status: {r.status_code}")

    except Exception as e:
        logger.error(f"Erro geral no crawler: {e}")

if __name__ == "__main__":
    download_and_extract()