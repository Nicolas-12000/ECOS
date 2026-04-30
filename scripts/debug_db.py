import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

def debug_db():
    db_url = os.getenv("SUPABASE_DB_URL")
    print(f"Connecting to: {db_url}")
    
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # 1. Check table existence
                cur.execute("SELECT count(*) FROM public.fact_core_weekly")
                count = cur.fetchone()['count']
                print(f"Total rows in fact_core_weekly: {count}")
                
                # 2. Test summary query
                query = """
                    SELECT 
                        SUM(cases_total) as total_cases,
                        AVG(temp_avg_c) as avg_temp,
                        AVG(precipitation_mm) as avg_precip,
                        epi_year, epi_week, week_start_date
                    FROM public.fact_core_weekly
                    GROUP BY epi_year, epi_week, week_start_date
                    ORDER BY week_start_date DESC
                    LIMIT 1
                """
                cur.execute(query)
                row = cur.fetchone()
                print(f"Summary query result: {row}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_db()
