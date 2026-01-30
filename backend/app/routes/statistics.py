from fastapi import APIRouter
from backend.database.connection import get_db_connection

router = APIRouter()

@router.get("/estatisticas")
def obter_estatisticas():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Total e Média Geral
        cur.execute("SELECT SUM(valor_despesa) as total, AVG(valor_despesa) as media FROM despesas_consolidadas")
        geral = cur.fetchone()

        # Top 5 Operadoras em Despesas
        cur.execute("""
            SELECT razao_social, SUM(valor_despesa) as total 
            FROM despesas_consolidadas 
            GROUP BY razao_social 
            ORDER BY total DESC 
            LIMIT 5
        """)
        top_5 = cur.fetchall()

        return {
            "geral": {
                "total": float(geral['total'] or 0),
                "media": float(geral['media'] or 0)
            },
            "top_operadoras": [
                {"razao_social": r['razao_social'], "total": float(r['total'])} 
                for r in top_5
            ]
        }
    
    finally:
        cur.close()
        conn.close()