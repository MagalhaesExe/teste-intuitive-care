from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import operators, statistics

app = FastAPI(title="ANS Data API")

# Configuração de CORS para permitir que o Frontend (Vue) acesse o Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua pelo domínio do seu Vue
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(operators.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "API ANS operacional. Acesse /docs para a documentação."}