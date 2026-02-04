# Teste Técnico Intuitive Care

Este projeto é uma aplicação fullstack para visualização e busca de dados de Operadoras de Planos de Saúde (ANS), conforme solicitado no teste técnico da Intuitive Care.

--- 

## Tecnologias Utilizadas

**Frontend:**
- Vue.js 3
- Tailwind CSS (Estilização)
- Chart.js (Visualização de dados)
- Axios (Comunicação com API)

**Backend:**
- Python / FastAPI
- PostgreSQL
- Uvicorn

---

## Como rodar o projeto

### Opção 1: Rodando com Docker
Esta é a forma mais simples de rodar o projeto. Você não precisa instalar Python ou Node.js na sua máquina, apenas o Docker.

**Pré-requisitos:** Docker e Docker Compose instalados.

#### 1. Clone o repositório:
```bash
git clone https://github.com/MagalhaesExe/teste-intuitive-care.git

cd Teste_Alex_Magalhaes
```

#### 2. Suba os containers: 
Este comando vai baixar as imagens, criar o banco, configurar a API e compilar o Frontend.
```bash
docker compose up --build -d
```

#### 3. Popule o Banco de Dados: 
O banco inicia vazio (apenas com as tabelas criadas). Execute o script de ETL para baixar e processar os CSVs da ANS:
```bash
docker compose exec backend python backend/scripts/run_pipeline.py
```

*Aguarde a mensagem "PIPELINE CONCLUÍDO COM SUCESSO".*

#### 4. Acesse a aplicação:
- Frontend (Dashboard): `http://localhost:8080`
- Backend (Documentação API): `http://localhost:8000/docs`

### Opção 2: Rodando manualmente

**Pré-requisitos:**
- Python 3.10+
- Node.js 20.19+
- PostgreSQL (Local ou via Docker)

#### 1. Clone o repositório:
```bash
git clone https://github.com/MagalhaesExe/teste-intuitive-care.git
```

#### 2. Inicie o Banco de Dados
- **Linux (Ubuntu/Debian):**
```bash
sudo systemctl start postgresql
```

- **macOS:**
```bash
brew services start postgresql
```

- **Windows:**
Abra o menu Iniciar > "Serviços" > Procure por "PostgreSQL" > Clique em "Iniciar".

#### 3. Abra o diretório:
```bash
cd Teste_Alex_Magalhaes
```

#### 3. Configurar o Banco de Dados (PostgreSQL)
É recomendado subir apenas o banco via Docker para evitar instalar o Postgres localmente:

```bash
docker compose up -d db
```

#### 4. Configurando o Backend (Python)
1. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (Crie um arquivo `.env` na raiz do backend):
```bash
DB_HOST=localhost
DB_PORT=5433
DB_NAME=ans_dashboard
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```
4. Execute o Pipeline de dados (se o banco estiver vazio):
```bash
python backend/scripts/run_pipeline.py
```

*(Aguarde até aparecer a mensagem de "Pipeline concluído com sucesso").*

5. Iniciar o servidor
Com o banco populado, inicie a API:

```bash
uvicorn backend.app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

#### 5. Configurar o frontend

1. Abra um **novo terminal**, volte para a raiz do projeto e entre na pasta frontend:
```bash
cd frontend
```

2. Instale as dependências e rode o projeto:
```bash
npm install
```

3. Configure a variável de ambiente (Crie um arquivo `.env` na raiz do frontend):
```bash
VITE_API_URL=http://localhost:8000
```

4. Rode o servidor de desenvolvimento:
```bash
npm run dev
```

O painel estará disponível em: `http://localhost:5173`

---

## Decisões Técnicas e Trade-offs

Durante o desenvolvimento, algumas escolhas arquiteturais foram feitas visando escalabilidade, manutenibilidade e a performance da aplicação. 

Abaixo, detalho os principais trade-offs:

### Processamento de Arquivos: Em Memória vs. Incremental
**Decisão:** Processamento Incremental (Iterativo por arquivo).

- **Contexto:** O download envolve múltiplos arquivos ZIP contendo dados históricos trimestrais. Somados, o volume de dados descompactados pode exceder a memória RAM disponível em ambientes de execução padrão (containers ou máquinas locais modestas).
- **Abordagem Escolhida (Incremental):** O pipeline foi desenhado para baixar, extrair, ler e processar **um arquivo por vez** (ou em *chunks*). Após o processamento e inserção no banco de dados, a memória é liberada antes de iniciar o próximo arquivo.
- **Justificativa (Trade-off):**
    - **Prós:** Garante que a aplicação não sofra *crash* por falta de memória (Out of Memory), independentemente de quantos anos de histórico sejam baixados. Aumenta a robustez do sistema.
    - **Contras:** Pode ser ligeiramente mais lento do que carregar tudo na memória de uma vez (devido ao overhead de I/O constante de leitura/escrita no banco), mas a estabilidade e a escalabilidade foram priorizadas em detrimento de milissegundos de performance.

---

### Consolidação e Qualidade de Dados
**Estratégia de Tratamento:**

- **CNPJs Duplicados com Razões Sociais Diferentes:**
    - *Problema:* O mesmo CNPJ aparecia com grafias diferentes ao longo dos trimestres (ex: "Empresa X" vs "Empresa X Ltda").
    - *Decisão:* Padronização pelo registro mais recente.
    - *Justificativa:* Assume-se que a grafia do último trimestre processado é a mais atualizada/correta. Isso evita que a mesma empresa apareça duplicada em agrupamentos (`group by`) no Dashboard.

- **Valores Zerados ou Negativos em Despesas:**
    - *Problema:* Registros contendo valores negativos (possíveis estornos contábeis) ou zerados.
    - *Decisão:* **Filtragem Rígida.** Registros com valor menor ou igual a zero foram descartados.
    - *Justificativa:* O foco do dashboard é visualizar o volume de *despesas realizadas*. Valores zerados apenas inflariam o banco de dados sem agregar valor analítico, e valores negativos (créditos/estornos) poderiam distorcer os gráficos de soma total de despesas. Optou-se por manter apenas os desembolsos positivos.

- **Inconsistência de Datas/Trimestres:**
    - *Problema:* Formatos variados nos arquivos originais.
    - *Decisão:* Criação de colunas derivadas explícitas: `Trimestre` (Int) e `Ano` (Int).
    - *Justificativa:* Facilita a indexação no banco de dados e a filtragem no Frontend, evitando parsing de strings complexas (ex: "1º Trim/2023") durante a consulta.

---

### Validação de Dados: Tratamento de CNPJs/Identificadores Inválidos
**Decisão:** Filtragem Estrita (Descarte de registros inválidos).

- **Contexto:** Os arquivos brutos da ANS apresentam uma mistura de identificadores: alguns utilizam o CNPJ (14 dígitos), enquanto outros utilizam o Registro ANS (6 dígitos). Além disso, há possíveis erros de digitação ou formatação na fonte.
- **Estratégia Implementada:** 
    1. **Validação Híbrida:** O algoritmo identifica automaticamente o tipo de documento. Se tiver até 6 dígitos, valida como numérico (Registro ANS); se tiver 14, aplica o cálculo oficial de Dígitos Verificadores.
    2. **Ação:** Registros que falham na validação (não são nem CNPJ válido nem Registro ANS válido) são **excluídos** do dataset final.
- **Justificativa (Trade-off):**
    - **Prós:** Garante a integridade referencial do Banco de Dados. Impede que erros de formatação quebrem o pipeline de inserção no PostgreSQL e assegura que todas as operadoras no Dashboard sejam entidades legítimas.
    - **Contras:** Perda de dados (Data Loss). Se uma operadora tiver um erro de digitação no arquivo original (ex: um dígito trocado), seus dados financeiros são ignorados em vez de serem corrigidos ou marcados para revisão manual.
    - **Mitigação:** O sistema gera um log (`warning`) informando a quantidade exata de registros descartados, permitindo monitoramento da qualidade da fonte.

---

### Enriquecimento e Cruzamento de Dados
**Estratégia de Processamento: In-Memory Join**
- **Estratégia Implementada:** 
    - **Contexto:** O arquivo de cadastro de operadoras ativas possui um volume controlado, cabendo confortavelmente na memória RAM junto com o consolidado financeiro.
    - **Decisão:** Carregamento total dos datasets em DataFrames e execução de `pd.merge`.  
    - **Justificativa (Trade-off):**
        - **Prós:** Alta performance e simplicidade de implementação. Evita a latência de I/O de banco de dados ou a complexidade de setup de um motor distribuído para um volume de dados "Small Data".
        - **Contras:** Se o cadastro de operadoras crescesse exponencialmente (ex: milhões de registros), essa abordagem causaria estouro de memória. Nesse caso hipotético, a solução seria migrar para joins via Banco de Dados ou Dask.

**Tratamento de Registros sem Match (Left Join)**
- **Problema:** Operadoras presentes no arquivo financeiro (passado) podem não constar no arquivo de operadoras ativas (presente) por terem sido canceladas ou liquidadas.
- **Decisão:** Utilização de Left Join (mantendo a esquerda/financeiro) e preenchimento de nulos com flags (`"NI"`, `"NÃO ENCONTRADO"`).    
- **Justificativa (Trade-off):** A integridade do fato financeiro é prioritária. Se uma despesa ocorreu, ela deve constar no Dashboard, independentemente do status atual da operadora. O uso de Inner Join descartaria despesas legítimas de operadoras inativas, distorcendo os totais contábeis.

**Tratamento de Duplicidade no Cadastro**
- **Problema:** Ocorrência de múltiplos registros para a mesma chave de identificação no arquivo cadastral.
- **Decisão:** Deduplicação preventiva (`drop_duplicates(keep='first')`) na chave de junção do dataset cadastral antes do merge.    
- **Justificativa (Trade-off):** Evita o "Produto Cartesiano" (explosão de linhas) durante o join, que duplicaria erroneamente os valores de despesas financeiras.

---

### Agregação e Estratégia de Ordenação
**Decisão:** Ordenação em Memória (In-Memory Sort) pós-agregação.

- **Contexto:** A ordenação é uma operação custosa (O(N log N)). Em Big Data, ordenar milhões de registros brutos pode travar a máquina.
- **Estratégia Implementada:**
    1.  **Agregação Primeiro:** O script primeiro agrupa os dados por `RazaoSocial` e `UF`. Isso reduz a cardinalidade do dataset de milhares de transações individuais para apenas algumas centenas de linhas (uma por operadora/estado).
    2.  **Ordenação Depois:** A função `sort_values` é aplicada apenas no dataset reduzido (`agg_df`).
- **Justificativa (Trade-off):**
    - **Eficiência:** Ordenar o dataset *agregado* é ordens de magnitude mais rápido do que tentar ordenar o dataset *bruto* antes de processar. O volume de dados resultante cabe confortavelmente na memória RAM, tornando desnecessário o uso de algoritmos de "External Merge Sort" (ordenação em disco) ou banco de dados para essa etapa final.
    - **Métricas Estatísticas:** O cálculo do Desvio Padrão (`std`) foi incluído para identificar a volatilidade das despesas. Foi implementado um tratamento explícito (`fillna(0)`) para operadoras com apenas um registro, evitando valores `NaN` no relatório final.

---

### Modelagem de Dados e SQL (DDL)

A arquitetura do banco de dados foi desenhada focando em performance de leitura para o Dashboard (perfil OLAP), em vez de otimização de escrita (perfil OLTP).

#### Estratégia de Normalização
**Decisão:** Desnormalizada para Consultas (`despesas_consolidadas`).
- **Contexto:** 
    - **Desnormalizada:** Manter informações como `RazaoSocial`, `UF` e `Modalidade` diretamente na tabela de despesas. Embora a tabela `operadoras_ativas` exista como referência cadastral, a tabela principal `despesas_consolidadas` armazena dados redundantes (`RazaoSocial`, `UF`).
- **Justificativa (Trade-off):**
    - **Performance de Leitura:** Elimina a necessidade de realizar JOINs custosos em queries de agregação massiva. Para um Dashboard que filtra "Despesas por UF", ler direto de uma única tabela é significativamente mais rápido.
    - **Imutabilidade Histórica:** A Razão Social de uma empresa pode mudar. Ao gravar o nome na tabela de despesas no momento da carga, preservamos o "retrato" do dado naquele período, sem que uma alteração cadastral futura mude o histórico financeiro retroativamente.

#### Tipos de Dados (Data Types)
**1. Valores Monetários**
- **Decisão:** `DECIMAL(18, 2)` (PostgreSQL).
- **Comparativo:**
    - *FLOAT/DOUBLE:* Descartados. Utilizam aritmética de ponto flutuante, o que introduz erros de precisão em somas financeiras (ex: 0.1 + 0.2 resultando em 0.300000004).
    - *INTEGER:* Seria uma opção válida (armazenar centavos), mas exigiria conversão na camada de aplicação.
- **Justificativa (Trade-off):** O tipo `DECIMAL` garante precisão exata, essencial para dados contábeis da ANS, simplificando as somas (`SUM`) diretamente no banco sem erros de arredondamento.

**2. Datas e Carimbos de Tempo**
- **Decisão:** `DATE` para fatos de negócio e `TIMESTAMP` para auditoria.
- **Comparativo:**
    - *VARCHAR:* Descartado. Armazenar datas como texto impede o uso de funções nativas de data (`date_trunc`, `extract`) e inviabiliza índices temporais eficientes.
- **Justificativa (Trade-off):** O uso de tipos nativos permite indexação cronológica e facilita queries de "Time Series" (ex: evolução de despesas por ano/trimestre) diretamente via SQL.

---

### Importação de Dados e Tratamento de Inconsistências
**Estratégia Implementada:** Pré-processamento na Camada de Aplicação (Python) vs. Tratamento no Banco (SQL).
- **Decisão:** O tratamento de dados foi realizado **antes** da importação (`Clean First`), utilizando Pandas. O Banco de Dados recebe apenas dados higienizados e tipados corretamente.
- **Justificativa da Abordagem:**
    - **Strings em Campos Numéricos:** O script Python converteu preventivamente os valores, descartando linhas inválidas. Isso evita falhas de transação (`Data Type Mismatch`) durante o comando `COPY`.
    - **Valores NULL:** Campos obrigatórios (como `UF` ou `Modalidade`) receberam valores padrão ("NI" - Não Informado) durante o enriquecimento. Isso permite definir as colunas do banco como `NOT NULL` sem risco de erro na carga.
    - **Datas:** Padronizadas para inteiros (`Trimestre`, `Ano`) ou formato ISO (`YYYY-MM-DD`) no Python, eliminando a necessidade de funções complexas de conversão de data (`TO_DATE`) dentro do SQL.

**Comando de Importação:**
Optou-se pelo comando `COPY` (PostgreSQL) em vez de `INSERT` linha a linha, devido à performance superior para grandes volumes de dados.

---

### Análise de Dados e Queries SQL

#### Localização do Arquivo
As queries SQL completas encontram-se no arquivo:
`backend/database/analysis/queries.sql`

#### Como Executar as Queries
Execute o comando abaixo na raiz do projeto para rodar o arquivo SQL diretamente no banco:
```bash
docker compose exec -T db psql -U postgres -d ans_dashboard < backend/database/analysis/queries.sql
```

**1. Operadoras com Maior Crescimento Percentual:**
- **Estratégia Implementada:** CTEs (Common Table Expressions) para primeiro identificar, individualmente por operadora, qual era o seu trimestre inicial e final disponível. Em seguida, realizou-se a busca dos valores exatos nesses períodos e foi calculado a variação percentual.
- **Tratamento de Dados Parciais:** Como nem todas as operadoras possuem dados em todos os trimestres (ex: operadoras que entraram ou saíram do mercado), a query não fixa "1º Tri de 2025", mas sim o mínimo e máximo período disponível para aquele CNPJ. Isso garante que o cálculo de crescimento seja justo e reflita a jornada real daquela operadora no banco de dados.

**2. Distribuição de Despesas por UF:**     
- **Estratégia Implementada:** Agrupamento por `uf` (`GROUP BY uf`), calculando a soma total das despesas e a média aritmética.
- **Desafio Adicional:** Para calcular a média por operadora de forma precisa, utilizou-se `COUNT(DISTINCT registro_ans)`. Isso evita que operadoras com múltiplos lançamentos no mesmo estado inflem artificialmente a contagem, garantindo uma média real por entidade empresarial.

**3. Frequência de Despesas Acima da Média:**     
- **Estratégia Implementada:** 
    1. Foi calculado a média global de todas as despesas do banco. 
    2. Foi filtrado os registros que individualmente superam essa média. 
    3. As ocorrências por operadoras foram contadas e filtradas apenas aquelas com COUNT >= 2.
    - **Justificativa (Trade-off):** **Subquery com CTE** prioriza a legibilidade e manutenibilidade. Embora existam formas de resolver com *Window Functions*, a separação lógica da "Média Geral" em uma CTE torna o código muito mais fácil de ser auditado e compreendido por outros desenvolvedores, sem sacrificar a performance em volumes de dados médios.

---

### Escolha do Framework: FastAPI
**Justificativa (Trade-off):** 
- **Performance:** O FastAPI é construído sobre o padrão ASGI (Starlette e Pydantic), sendo significativamente mais rápido que o Flask (WSGI) para operações assíncronas.
- **Complexidade e Produtividade:** Como o projeto exige validação de dados e documentação, o FastAPI reduz a complexidade ao gerar automaticamente o Swagger UI (OpenAPI), eliminando a necessidade de bibliotecas extras para documentar as rotas.
- **Manutenção:** O uso de Type Hints (Dicas de Tipo) do Python 3.10+ facilita a manutenção a longo prazo, pois os erros de tipo são capturados antes mesmo da execução, tornando o código mais legível e seguro.

---

### Estratégia de Paginação: Offset-based
**Justificativa (Trade-off):** 
- **Volume de Dados:** Para o volume de dados das operadoras da ANS (que, embora relevante, não atinge a escala de "Big Data" de redes sociais com bilhões de registros), o `OFFSET` oferece uma performance excelente com uma implementação simples.
- **Frequência de Atualizações:** Como a base da ANS é atualizada trimestralmente, o maior problema da paginação por offset (pular registros se um novo dado for inserido enquanto o usuário navega) é praticamente inexistente, já que os dados são estáticos entre as cargas.
- **Flexibilidade para o Frontend:** Esta abordagem permite que o usuário pule diretamente para qualquer página (ex: ir da página 1 para a 50), algo que o *Cursor-based* dificulta por exigir que você saiba o ID do último registro da página anterior.

---

### Cache vs Queries Diretas:
**Estratégia Implementada:** Cálculo em tempo de execução.

**Justificativa (Trade-off):** 
- **Consistência Total:** Como os cálculos são feitos diretamente sobre os dados consolidados no momento da requisição, não há risco de exibir dados obsoletos (stale data).
- **Frequência de Atualizações:** Os dados da ANS são atualizados trimestralmente. Em um cenário real, isso tornaria o cálculo "na hora" pouco eficiente se houvesse milhões de acessos, mas perfeitamente aceitável para um volume controlado e dados que não mudam a cada segundo.
- **Simplicidade de Implementação:** Evita a complexidade de gerenciar a invalidação de cache (Opção B) ou criar triggers/jobs de atualização para uma tabela de estatísticas (Opção C).

---

### Estrutura de Resposta: Dados + Metadados
**Justificativa (Trade-off):** 
- **Controle de Interface (UX/UI):** Para criar uma paginação funcional no Vue.js, o componente de frontend precisa saber não apenas os dados, mas o total de registros existentes no banco. Sem o campo `total`, o frontend não consegue calcular quantas páginas existem no total ou desativar o botão "Próximo" quando chegar ao fim.
- **Independência de Estado:** Ao retornar `page` e `limit` junto com os dados, a API se torna "autoexplicativa". O frontend pode usar esses valores para confirmar que a resposta recebida corresponde à página solicitada, evitando erros de dessincronização em conexões lentas.
- **Padronização de API:** Envelopar a resposta em um objeto (ex: `{ data: [], metadata: {} }`) é uma convenção de mercado que facilita a manutenção.

---

### Estratégia de Busca/Filtro: Busca no Servidor
**Justificativa (Trade-off):** 
- **Coerência Arquitetural:** Esta escolha é mandatória dada a decisão de utilizar *Offset-based pagination* no backend. Como o frontend recebe apenas uma "fatia" (ex: 10 registros) dos dados por vez, uma busca realizada apenas no navegador (Client-side) seria incompleta, pois ignoraria os registros das outras páginas não carregadas.
- **Performance e Escalabilidade:** Delegamos o processamento pesado de filtragem para o PostgreSQL. Bancos de dados relacionais são otimizados com índices (B-Tree) para realizar buscas textuais e filtros complexos em milissegundos, muito mais rápido do que iterar arrays gigantes via JavaScript no navegador do usuário.
- **Economia de Banda:** Em um cenário mobile ou de conexão instável, trafegar apenas os resultados filtrados (Payload reduzido) melhora significativamente o *Time-to-Interactive* da aplicação, evitando o download desnecessário de datasets completos da ANS.

---

### Composables (Vue 3)
**Justificativa (Trade-off):** 
- **Modularidade e "Clean Code":** 
    - Com a **Composition API**, podemos extrair a lógica de negócio (o *fetch*, o estado de loading, a paginação) para um arquivo separado (ex: `useOperadoras.js`).
    - Isso deixa o componente visual (`.vue`) focado apenas em renderizar o HTML/CSS, enquanto a lógica "suja" fica isolada e testável.
- **Reusabilidade (DRY - Don't Repeat Yourself):** Se no futuro for necessário criar uma "Página de Relatórios" que também precisa listar operadoras, basta importar `const { operadoras, fetch } = useOperadoras()`.

---

### Performance da Tabela
**Estratégia Implementada:** Paginação no Servidor (Server-Side Pagination)

**Justificativa (Trade-off):** 
- **Volume de Dados e Latência de Rede:** 
    - O banco de dados da ANS contém milhares de registros (operadoras) e milhões de linhas de histórico (despesas). Tentar carregar todo esse dataset de uma vez ("Client-Side Rendering") resultaria em um payload JSON gigantesco (vários MBs), causando alta latência inicial e travamento do navegador em dispositivos com menos memória.
    - Com a paginação no servidor (`LIMIT/OFFSET` no SQL), é transferido apenas o necessário para a visualização atual (ex: 10 registros), mantendo o tempo de resposta da API abaixo de 100ms, independentemente do tamanho total do banco.
- **Performance de Renderização (DOM):** O navegador tem dificuldade em renderizar e manipular milhares de elementos HTML (`<tr>`, `<td>`) simultaneamente. A paginação garante que o DOM permaneça leve, com um número constante de elementos, garantindo rolagem suave e interações rápidas.
- **Experiência do Usuário (UX):**
    - Em sistemas corporativos/administrativos, o usuário raramente precisa "rolar infinitamente". O padrão de uso é Busca Direta ou navegação controlada.
    - A paginação oferece previsibilidade ("Estou na página 2 de 50") e permite ao usuário retornar facilmente a um ponto específico, o que seria difícil com *Infinite Scroll*.

---

### Tratamento de Erros e Loading
Para garantir uma experiência de usuário fluida e resiliente, foi implementado uma estratégia robusta de feedback visual baseada em três pilares:
- **1. Gerenciamento de Estado de Carregamento (Loading):** As variáveis reativas (Composables) controlam o ciclo de vida das requisições assíncronas.
    - **Implementação:** O estado `loading` é ativado antes da requisição e desativado estritamente no bloco `finally`. Isso garante que a interface nunca fique travada em um estado de carregamento eterno, mesmo se ocorrer um erro fatal.
    - **Impacto na UI:** Durante o processamento, elementos de ação (botões de busca, paginação) são desabilitados visualmente (`opacity-50` / `disabled`). Isso previne **"Rage Clicks"** (cliques múltiplos por impaciência), evitando requisições duplicadas e sobrecarga desnecessária no backend.

- **2. Tratamento de Dados Vazios (Empty States):** Evita-se a renderização de tabelas vazias, que podem parecer erros de carregamento para o usuário.
    - Se a API retorna um array vazio (`length === 0`), a interface substitui a tabela por um componente de "Empty State" com uma mensagem instrutiva (ex: "Nenhum registro encontrado para estes filtros"), orientando o usuário a ajustar sua busca.

---

## Documentação da API (Postman)
Foi disponibilizado uma **Coleção do Postman** completa para facilitar testes manuais, integração e validação de cenários específicos.

**O que está incluído na coleção?**

A coleção (`ans_dashboard_collection.json`) cobre 100% dos endpoints desenvolvidos e foi estruturada para demonstrar não apenas o "Caminho Feliz", mas também o tratamento de exceções.

**1. Rotas Mapeadas:**
- `GET /operadoras`: Listagem com paginação e busca textual.
- `GET /operadoras/{id}`: Detalhes de uma operadora específica.
- `GET /despesas/consolidadas`: Filtros avançados por ano, trimestre e UF.
- `GET /despesas/estatisticas`GET /despesas/estatisticas: Endpoints analíticos (Queries SQL complexas).: Endpoints analíticos.

**2. Exemplos de Uso:** Cada requisição na coleção já vem acompanhada de exemplos de resposta salvos, ilustrando:
- **Status 200 OK:** Estrutura do JSON retornado com dados reais.
- **Status 404 Not Found:** Formato padrão de erro quando um ID não existe.
- **Status 422 Validation Error:** Exemplo de resposta quando parâmetros inválidos são enviados.

**3. Variáveis de Ambiente:** A variável `{{base_url}}` permite a troca rápida de ambientes (ex: localhost:8000 vs. Servidor de Produção) sem precisar editar as URLs manualmente.
