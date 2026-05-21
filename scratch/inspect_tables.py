import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        print("--- public.fact_core_weekly (dengue - lowercase) ---")
        try:
            cur.execute("select count(1), min(epi_year), max(epi_year), count(distinct epi_year) from public.fact_core_weekly where disease = 'dengue'")
            res = cur.fetchone()
            print(f"Total Rows: {res[0]}, Min Year: {res[1]}, Max Year: {res[2]}, Unique Years: {res[3]}")
            
            cur.execute("select epi_year, count(1), sum(cases_total) from public.fact_core_weekly where disease = 'dengue' group by epi_year order by epi_year")
            print("By Year:")
            for r in cur.fetchall():
                print(f"  Year {r[0]}: {r[1]} rows, {r[2]} total cases")
        except Exception as e:
            print("Error:", e)
