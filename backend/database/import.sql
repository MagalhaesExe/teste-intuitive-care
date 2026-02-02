-- O arquivo deve estar acessível ao servidor do banco de dados
COPY operadoras_ativas(registro_ans, cnpj, razao_social, modalidade, uf, data_registro_ans)
FROM '/data/processed/cadastro_operadoras_limpo.csv' 
DELIMITER ','
CSV HEADER
ENCODING 'UTF8';

-- Importação da Tabela de Despesas Consolidadas
COPY despesas_consolidadas(cnpj, razao_social, trimestre, ano, valor_despesa, registro_ans, modalidade, uf)
FROM '/data/processed/consolidado_enriquecido.csv'
DELIMITER ','
CSV HEADER
ENCODING 'UTF8';

-- Importação da Tabela Agregada
COPY despesas_agregadas(razao_social, uf, total_despesas, media_trimestral, desvio_padrao)
FROM '/data/processed/despesas_agregadas.csv'
DELIMITER ','
CSV HEADER
ENCODING 'UTF8';