-- Tabela para Dados Cadastrais das Operadoras 
-- Utilizada para armazenar o CSV de dados cadastrais
CREATE TABLE IF NOT EXISTS operadoras_ativas (
    registro_ans VARCHAR(20) PRIMARY KEY,
    cnpj VARCHAR(14) UNIQUE,             
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100),
    uf CHAR(2),
    data_registro_ans DATE,
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para dados consolidados de despesas
-- Esta tabela recebe o conteúdo do consolidado_enriquecido.csv
CREATE TABLE IF NOT EXISTS despesas_consolidadas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14),
    razao_social VARCHAR(255),
    trimestre INTEGER,
    ano INTEGER,
    valor_despesa DECIMAL(18, 2),
    registro_ans VARCHAR(20),
    modalidade VARCHAR(100),
    uf CHAR(2),
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para dados agregados
-- Esta tabela recebe o conteúdo do despesas_agregadas.csv
CREATE TABLE IF NOT EXISTS despesas_agregadas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(255) NOT NULL,
    uf CHAR(2),
    total_despesas DECIMAL(18, 2),
    media_trimestral DECIMAL(18, 2),
    desvio_padrao DECIMAL(18, 2),
    data_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_operadoras_uf ON operadoras_ativas(uf);
CREATE INDEX IF NOT EXISTS idx_agregadas_total ON despesas_agregadas(total_despesas DESC);
CREATE INDEX IF NOT EXISTS idx_operadoras_modalidade ON operadoras_ativas(modalidade);
CREATE INDEX IF NOT EXISTS idx_dc_cnpj ON despesas_consolidadas(cnpj);