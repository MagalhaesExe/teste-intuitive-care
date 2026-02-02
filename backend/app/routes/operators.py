from fastapi import APIRouter, Query
from backend.database.analysis.connection import get_db_connection

router = APIRouter()

@router.get("/operadoras")
def listar_operadoras(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), search: str = None):
    """
    Recupera a lista de operadoras ativas com suporte a paginação e busca textual.
    
    - **Filtro**: O parâmetro `search` busca por correspondência parcial em `razao_social` ou `cnpj`.
    - **Performance**: Realiza apenas as queries estritamente necessárias.
    """
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        where_clause = ""
        params = []
        
        if search:
            # Prepara o filtro para SQL seguro            
            # ILIKE é específico do PostgreSQL para comparações que ignoram maiúsculas/minúsculas
            where_clause = "WHERE razao_social ILIKE %s OR cnpj LIKE %s"
            search_val = f"%{search.strip()}%"
            params = [search_val, search_val]

        # Contagem total com filtro
        cur.execute(f"SELECT COUNT(*) FROM operadoras_ativas {where_clause}", params)
        total = cur.fetchone()['count']

        # Busca paginada com filtro
        query = f"""
            SELECT * FROM operadoras_ativas 
            {where_clause} 
            ORDER BY razao_social 
            LIMIT %s OFFSET %s
        """
        cur.execute(query, params + [limit, offset])
        data = cur.fetchall()

        return {
            "metadata": {"total": total, "page": page, "limit": limit},
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

@router.get("/operadoras/{cnpj}/detalhes")
def obter_detalhes_operadora(cnpj: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Busca dados cadastrais básicos
        cur.execute("SELECT * FROM operadoras_ativas WHERE cnpj = %s", [cnpj])
        operadora = cur.fetchone()

        if not operadora:
            return {"error": "Operadora não encontrada"}

        # Busca histórico de despesas (ordem cronológica)
        cur.execute("""
            SELECT ano, trimestre, valor_despesa 
            FROM despesas_consolidadas 
            WHERE cnpj = %s 
            ORDER BY ano DESC, trimestre DESC
        """, [cnpj])
        despesas = cur.fetchall()

        return {
            "info": operadora,
            "historico": despesas
        }
    finally:
        cur.close()
        conn.close()