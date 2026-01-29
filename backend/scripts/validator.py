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
    # Validação de formato e eliminação de sequências repetidas (ex: 11111111111111)
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    def calcular_digito(cnpj, pesos):
        # Lógica de cálculo do dígito verificador
        soma = sum(int(a) * b for a, b in zip(cnpj, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # Pesos definidos pela Receita Federal para os dois dígitos verificadores
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    # Verificação cruzada dos dígitos finais para autenticação da string
    if int(cnpj[12]) != calcular_digito(cnpj[:12], pesos1):
        return False
    if int(cnpj[13]) != calcular_digito(cnpj[:13], pesos2):
        return False
    return True

def validar_identificador(valor):
    # Sanitização: Normaliza a entrada removendo caracteres não numéricos
    # Garante que máscaras de CNPJ (pontos, barras, traços) não interfiram na validação
    id_limpo = re.sub(r'\D', '', str(valor))
    
    if not id_limpo:
        return False

    # Caso 1: Registro ANS 
    # Identificadores curtos (até 6 dígitos) representam o registro da operadora na agência
    if len(id_limpo) <= 6:
        return id_limpo.isdigit()
    
    # Caso 2: CNPJ
    # Identificadores de 14 dígitos passam pela validação rigorosa de dígitos verificadores
    if len(id_limpo) == 14:
        return validar_cnpj(id_limpo)
    
    # Caso 3: Formatos desconhecidos
    return False

def executar_validacao():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Arquivo {INPUT_FILE} não encontrado!")
        return

    logger.info("Iniciando validação de dados (Tópico 2.1)...")
    df = pd.read_csv(INPUT_FILE)
    total_inicial = len(df)

    # 1º Validação: Razão Social não vazia
    # Garante que todo dado financeiro esteja atrelado a uma entidade válida.
    df = df[df['RazaoSocial'].notna() & (df['RazaoSocial'].str.strip() != "")]
    
    # 2º Validação: Valores numéricos positivos
    # Despesas negativas ou zeradas são filtradas para manter apenas fatos financeiros relevantes.
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce')
    df = df[df['ValorDespesas'] > 0]
    
    # 3º Validação: Identificador (Registro ANS ou CNPJ)
    # Separa registros confiáveis de possíveis ruídos ou erros de digitação na fonte.
    df['id_valido'] = df['CNPJ'].apply(validar_identificador)
    
    validos = df[df['id_valido'] == True].copy()
    invalidos = df[df['id_valido'] == False].copy()

    if not invalidos.empty:
        logger.warning(f"{len(invalidos)} registros descartados por identificador inválido.")

    validos.drop(columns=['id_valido'], inplace=True)
    validos.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    
    logger.info(f"Validação concluída: {len(validos)} registros aprovados de {total_inicial} totais.")
    logger.info(f"Arquivo validado salvo em: {OUTPUT_FILE}")

    validos.columns = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
    validos.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    # O arquivo ZIP reduz o overhead de transferência e cumpre requisitos de armazenamento otimizado.
    zip_file = "data/processed/consolidado_despesas.zip"
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUTPUT_FILE, arcname="consolidado_despesas.csv")

    logger.info(f"Arquivo ZIP criado em: {zip_file}")

if __name__ == "__main__":
    executar_validacao()