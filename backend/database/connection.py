import psycopg2
from psycopg2.extras import RealDictCursor
import os

DB_CONFIG = {
    "host": "localhost",
    "database": "ans_db",
    "user": "postgres",
    "password": "admin"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    return conn