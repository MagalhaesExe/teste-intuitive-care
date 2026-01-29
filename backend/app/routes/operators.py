from fastapi import APIRouter, Query
from backend.database.connection import get_db_connection

router = APIRouter()

@router.get("/operadoras")
def listar_operadoras(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    Lista operadoras com paginação.
    - page: número da página
    - limit: quantidade de registros por página
    """
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Busca os dados paginados
        cur.execute(
            "SELECT registro_ans, cnpj, razao_social, modalidade, uf FROM operadoras_ativas LIMIT %s OFFSET %s",
            (limit, offset)
        )
        data = cur.fetchall()
        
        # Busca o total para controle da paginação no Frontend
        cur.execute("SELECT COUNT(*) FROM operadoras_ativas")
        total = cur.fetchone()['count']
        
        return {
            "metadata": {
                "total": total,
                "page": page,
                "limit": limit
            },
            "data": data
        }
    finally:
        cur.close()
        conn.close()

@router.get("/operadoras/{cnpj}")
def detalhe_operadora(cnpj: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Busca detalhes cadastrais
        cur.execute("SELECT * FROM operadoras_ativas WHERE cnpj = %s", (cnpj,))
        operadora = cur.fetchone()
        if not operadora:
            return {"error": "Operadora não encontrada"}, 404
        return operadora
    finally:
        cur.close()
        conn.close()

@router.get("/operadoras/{cnpj}/despesas")
def historico_despesas(cnpj: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Busca histórico financeiro ordenado por período
        cur.execute("""
            SELECT trimestre, ano, valor_despesa 
            FROM despesas_consolidadas 
            WHERE cnpj = %s 
            ORDER BY ano DESC, trimestre DESC
        """, (cnpj,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()