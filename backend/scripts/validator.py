import pandas as pd
import re
import os
import logging
import zipfile

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("validacao.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

INPUT_FILE = "data/processed/consolidado_despesas.csv"
OUTPUT_FILE = "data/processed/consolidado_validado.csv"

def validar_cnpj(cnpj):
    """Lógica rigorosa de dígitos verificadores para CNPJ (14 dígitos)."""
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    def calcular_digito(cnpj, pesos):
        soma = sum(int(a) * b for a, b in zip(cnpj, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    if int(cnpj[12]) != calcular_digito(cnpj[:12], pesos1):
        return False
    if int(cnpj[13]) != calcular_digito(cnpj[:13], pesos2):
        return False
    return True

def validar_identificador(valor):
    """
    Nova função: valida tanto Registro ANS quanto CNPJ.
    """
    # Remove qualquer caractere que não seja número (pontos, barras, traços)
    id_limpo = re.sub(r'\D', '', str(valor))
    
    if not id_limpo:
        return False

    # Caso 1: Registro ANS (Geralmente até 6 dígitos)
    if len(id_limpo) <= 6:
        # Apenas garante que é numérico e tem algum conteúdo
        return id_limpo.isdigit()
    
    # Caso 2: CNPJ (14 dígitos)
    if len(id_limpo) == 14:
        return validar_cnpj(id_limpo)
    
    # Caso 3: Formatos desconhecidos (ex: CNPJ incompleto com 11 dígitos)
    return False

def executar_validacao():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Arquivo {INPUT_FILE} não encontrado!")
        return

    logger.info("Iniciando validação de dados (Tópico 2.1)...")
    df = pd.read_csv(INPUT_FILE)
    total_inicial = len(df)

    # 1. Validação: Razão Social não vazia
    df = df[df['RazaoSocial'].notna() & (df['RazaoSocial'].str.strip() != "")]
    
    # 2. Validação: Valores numéricos positivos
    # Garante que a coluna é numérica antes da comparação
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce')
    df = df[df['ValorDespesas'] > 0]
    
    # 3. Validação de Identificador (Registro ANS ou CNPJ)
    df['id_valido'] = df['CNPJ'].apply(validar_identificador)
    
    # Separação
    validos = df[df['id_valido'] == True].copy()
    invalidos = df[df['id_valido'] == False].copy()

    if not invalidos.empty:
        logger.warning(f"{len(invalidos)} registros descartados por identificador inválido.")

    # Salvando o resultado limpo
    validos.drop(columns=['id_valido'], inplace=True)
    validos.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    
    logger.info(f"Validação concluída: {len(validos)} registros aprovados de {total_inicial} totais.")
    logger.info(f"Arquivo validado salvo em: {OUTPUT_FILE}")

    validos.columns = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
    validos.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    # Criando o arquivo ZIP
    zip_file = "data/processed/consolidado_despesas.zip"
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUTPUT_FILE, arcname="consolidado_despesas.csv")

    logger.info(f"Arquivo ZIP criado em: {zip_file}")

if __name__ == "__main__":
    executar_validacao()