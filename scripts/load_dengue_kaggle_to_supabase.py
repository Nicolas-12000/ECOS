#!/usr/bin/env python3
"""Automatically download and load Dengue Kaggle dataset into Supabase.

Usage:
  .venv/bin/python scripts/load_dengue_kaggle_to_supabase.py
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from dotenv import load_dotenv
import psycopg
import pandas as pd
import kagglehub

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env", override=True)

SCHEMA_SQL = """
create schema if not exists analytics;

create table if not exists analytics.dengue_kaggle_dataset (
    ano integer not null,
    semana integer not null,
    municipio_code text not null,
    municipio text not null,
    enfermedad text not null default 'Dengue',
    casos_totales integer not null default 0,
    primary key (ano, semana, municipio_code, enfermedad)
);

create index if not exists idx_dengue_kaggle_municipio
    on analytics.dengue_kaggle_dataset (municipio_code);

create index if not exists idx_dengue_kaggle_ano_semana
    on analytics.dengue_kaggle_dataset (ano, semana);
"""

def main() -> int:
    parser = argparse.ArgumentParser(description="Automated Kaggle dataset ETL")
    parser.add_argument("--database-url", default=os.getenv("SUPABASE_DB_URL", ""))
    parser.add_argument("--schema", default="analytics")
    parser.add_argument("--table", default="dengue_kaggle_dataset")
    parser.add_argument("--truncate", action="store_true", help="Truncate table before loading")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Missing database URL. Set --database-url or SUPABASE_DB_URL.")

    table_ref = f"{args.schema}.{args.table}"

    print("[*] Descargando dataset desde Kaggle de forma automatica...")
    try:
        path = kagglehub.dataset_download('davidrestrepo/dengue')
        csv_path = Path(path) / "dengue_data_all_municipalities.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"No se encontro el archivo CSV en {path}")
        print(f"[ok] Dataset descargado en: {csv_path}")
    except Exception as e:
        raise SystemExit(f"Error descargando el dataset: {e}")

    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            # 1. Asegurar que existe el esquema
            print(f"[*] Configurando esquema en base de datos para {table_ref}...")
            cur.execute(SCHEMA_SQL)
            conn.commit()

            print(f"[*] Procesando y transformando datos (Wide to Long format)...")
            df = pd.read_csv(csv_path)

            # Extraer las columnas de casos semanales (formato YYYY/wXX)
            week_columns = [col for col in df.columns if re.match(r'^\d{4}/w\d{2}$', col)]
            
            # Melt para convertir de formato ancho a largo
            id_vars = ['Municipality code', 'Municipality']
            
            df_long = pd.melt(
                df,
                id_vars=id_vars,
                value_vars=week_columns,
                var_name='epi_week_str',
                value_name='casos_totales'
            )

            # Extraer año y semana
            df_long[['ano', 'semana']] = df_long['epi_week_str'].str.extract(r'^(\d{4})/w(\d{2})$')
            df_long['ano'] = df_long['ano'].astype(int)
            df_long['semana'] = df_long['semana'].astype(int)
            
            # Renombrar e inicializar columnas requeridas
            df_long['municipio_code'] = df_long['Municipality code'].astype(str)
            df_long['municipio'] = df_long['Municipality'].astype(str)
            df_long['enfermedad'] = 'Dengue'
            df_long['casos_totales'] = df_long['casos_totales'].fillna(0).astype(int)

            # Seleccionar columnas finales
            table_columns = ['ano', 'semana', 'municipio_code', 'municipio', 'enfermedad', 'casos_totales']
            df_final = df_long[table_columns].copy()

            # Exportar a CSV temporal para copia ultra-rapida
            temp_csv = csv_path.with_name(f"temp_{csv_path.name}")
            df_final.to_csv(temp_csv, index=False, header=False, encoding='utf-8')

            if args.truncate:
                print(f"[*] Truncando tabla {table_ref}...")
                cur.execute(f"TRUNCATE TABLE {table_ref}")

            print(f"[*] Insertando {len(df_final)} registros historicos en {table_ref}...")
            try:
                with temp_csv.open("r", encoding="utf-8") as f:
                    copy_sql = (
                        f"COPY {table_ref} ({', '.join(table_columns)}) "
                        "FROM STDIN WITH (FORMAT csv, HEADER false)"
                    )
                    with cur.copy(copy_sql) as copy:
                        while True:
                            chunk = f.read(1024 * 1024)
                            if not chunk:
                                break
                            copy.write(chunk)
                conn.commit()
                print(f"[ok] Carga completada exitosamente.")
            finally:
                if temp_csv.exists():
                    temp_csv.unlink()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
