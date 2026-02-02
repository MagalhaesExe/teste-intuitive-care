from fastapi import APIRouter
from backend.database.analysis.connection import get_db_connection

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

@router.get("/estatisticas/uf")
def despesas_por_uf():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Join: Tabela de Despesas (d) + Tabela de Operadoras (o)
        query = """
            SELECT o.uf, SUM(d.valor_despesa) as total 
            FROM despesas_consolidadas d
            JOIN operadoras_ativas o ON d.cnpj = o.cnpj
            GROUP BY o.uf 
            ORDER BY total DESC
        """
        cur.execute(query)
        results = cur.fetchall()
        
        # Garante que 'total' seja convertido de decimal para float
        return [
            {"uf": row['uf'], "total": float(row['total'])} 
            for row in results if row['uf'] is not None
        ]
    except Exception as e:
        print(f"Erro no banco: {e}") 
        return []
    finally:
        cur.close()
        conn.close()