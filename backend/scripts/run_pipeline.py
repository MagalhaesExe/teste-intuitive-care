import subprocess
import sys
import time
import logging
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

log_file_path = os.path.join(SCRIPT_DIR, "pipeline_execution.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_step(script_name):
    full_script_path = os.path.join(SCRIPT_DIR, script_name)
    logging.info(f"Iniciando: {script_name}...")
    start = time.time()
    
    try:
        if not os.path.exists(full_script_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {full_script_path}")
        
        # sys.executable garante o uso do mesmo Python do venv
        subprocess.run([sys.executable, full_script_path], check=True)
        
        end = time.time()
        logging.info(f"Sucesso: {script_name} (Tempo: {end - start:.2f}s)\n")
        
    except FileNotFoundError as e:
        logging.error(str(e))
        logging.critical("O pipeline foi interrompido: arquivo faltando.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        logging.error(f"Erro crítico ao executar: {script_name}")
        logging.critical("O pipeline foi interrompido.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        sys.exit(1)

def main():
    logging.info("INICIANDO O PIPELINE DE DADOS ANS\n")
    logging.info(f"Diretório de execução: {SCRIPT_DIR}")
    
    steps = [
        "crawler_ans.py",  # 1. Baixa o CSV
        "processor.py",    # 2. Limpa e normaliza os dados
        "validator.py",    # 3. Verifica se o arquivo é válido
        "enricher.py",     # 4. Adiciona dados extras
        "aggregator.py",   # 5. Cria resumos/agregados
        "loader.py"        # 6. Salva no Banco de Dados
    ]

    for script in steps:
        run_step(script)

    logging.info("PIPELINE CONCLUÍDO COM SUCESSO! O banco de dados está populado.")

if __name__ == "__main__":
    main()