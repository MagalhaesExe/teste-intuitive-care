# Teste Técnico Intuitive Care

Este projeto é uma aplicação fullstack para visualização e busca de dados de Operadoras de Planos de Saúde (ANS), conforme solicitado no teste técnico da Intuitive Care.

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

## Como rodar o projeto
Siga os passos abaixo para executar a aplicação localmente.

### 1. Configurar o backend
Entre na pasta do backend:
```bash
cd backend
```

Crie o ambiente virtual:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```
Instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Configurar o Banco de Dados (PostgreSQL)
Antes de prosseguir, crie um banco de dados no seu PostgreSQL (ex: `ans_dashboard).

Em seguida, crie um arquivo chamado **`.env`** dentro da pasta `backend/` e adicione a string de conexão:

```bash
# Arquivo: backend/.env
DB_HOST=localhost
DB_NAME=ans_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_PORT=5432
```

### 3. Popular o Banco de Dados
Execute o script de pipeline. Ele fará o download, validação, processamento e carga dos dados no PostgreSQL automaticamente.

```bash
python backend/scripts/run_pipeline.py
```

(Aguarde até aparecer a mensagem de "Pipeline concluído com sucesso").

### 4. Iniciar o servidor
Com o banco populado, inicie a API:

```bash
uvicorn backend.app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

### 5. Configurar o frontend
Abra um **novo terminal**, volte para a raiz do projeto e entre na pasta frontend:

```bash
cd frontend
```

Instale as dependências e rode o projeto:

```bash
npm install
npm run dev
```
O painel estará disponível em: `http://localhost:5173`