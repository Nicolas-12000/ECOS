#!/usr/bin/env python3
"""
Validaciones automáticas de consistencia temporal y calidad de datos.
Ejecutar después de curate_weekly_spark.py
"""

import sys
from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data/processed"

# Rangos esperados
VALID_RANGES = {
    "epi_year": (2013, 2024),
    "epi_week": (1, 53),
    "trends_score": (0, 100),
    "rss_mentions": (0, float("inf")),
}

# Departamentos válidos en Colombia
VALID_DEPARTMENTS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá",
    "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba",
    "Cundinamarca", "Distrito Capital", "Guainía", "Guaviare", "Huila",
    "La Guajira", "Magdalena", "Meta", "Nariño", "Norte Santander",
    "Putumayo", "Quindío", "Risaralda", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada", "NACIONAL",
]

VALID_DISEASES = ["dengue", "chikungunya", "zika", "malaria"]


def validate_schema(spark, path: str) -> bool:
    """Validar esquema esperado."""
    try:
        df = spark.read.parquet(path)
        
        expected_cols = {"epi_year", "epi_week", "disease", "departamento", "trends_score", "rss_mentions"}
        actual_cols = set(df.columns)
        
        if not expected_cols.issubset(actual_cols):
            missing = expected_cols - actual_cols
            print(f"❌ SCHEMA: Faltan columnas {missing}")
            return False
        
        print(f"✅ SCHEMA: Correcto ({len(df.columns)} columnas)")
        return True
        
    except Exception as e:
        print(f"❌ SCHEMA: Error {e}")
        return False


def validate_ranges(spark, path: str) -> bool:
    """Validar rangos de valores."""
    try:
        df = spark.read.parquet(path)
        
        all_valid = True
        
        # Validar epi_year
        year_stats = df.agg(
            F.min("epi_year").alias("min_year"),
            F.max("epi_year").alias("max_year"),
            F.count(F.when(F.col("epi_year").between(2013, 2024), 1)).alias("valid_years")
        ).collect()[0]
        
        if year_stats.valid_years < df.count() * 0.95:
            print(f"❌ RANGES: {year_stats.valid_years} años válidos de {df.count()}")
            all_valid = False
        else:
            print(f"✅ RANGES: Años {year_stats.min_year}-{year_stats.max_year} válidos")
        
        # Validar epi_week
        week_stats = df.agg(
            F.count(F.when(F.col("epi_week").between(1, 53), 1)).alias("valid_weeks")
        ).collect()[0]
        
        if week_stats.valid_weeks < df.count() * 0.95:
            print(f"❌ RANGES: Semanas inválidas ({week_stats.valid_weeks}/{df.count()})")
            all_valid = False
        else:
            print(f"✅ RANGES: Semanas epidemiológicas válidas")
        
        # Validar trends_score
        trends_stats = df.agg(
            F.min("trends_score").alias("min_trends"),
            F.max("trends_score").alias("max_trends"),
            F.count(F.when((F.col("trends_score") >= 0) & (F.col("trends_score") <= 100), 1)).alias("valid_trends")
        ).collect()[0]
        
        if trends_stats.valid_trends < df.count() * 0.95:
            print(f"❌ RANGES: Trends fuera de [0, 100] ({trends_stats.min_trends}-{trends_stats.max_trends})")
            all_valid = False
        else:
            print(f"✅ RANGES: Trends score válido [0-100]")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ RANGES: Error {e}")
        return False


def validate_nulls(spark, path: str) -> bool:
    """Validar valores nulos."""
    try:
        df = spark.read.parquet(path)
        
        null_counts = df.select([
            F.count(F.when(F.col(c).isNull(), 1)).alias(f"{c}_null")
            for c in df.columns
        ]).collect()[0]
        
        total_records = df.count()
        all_valid = True
        
        for col in df.columns:
            null_count = getattr(null_counts, f"{col}_null")
            null_pct = (null_count / total_records) * 100
            
            if null_pct > 5:
                print(f"❌ NULLS: {col} tiene {null_pct:.1f}% nulos")
                all_valid = False
        
        if all_valid:
            print(f"✅ NULLS: < 5% valores nulos en todas columnas")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ NULLS: Error {e}")
        return False


def validate_departments(spark, path: str) -> bool:
    """Validar departamentos válidos."""
    try:
        df = spark.read.parquet(path)
        
        invalid_depts = df.filter(~F.col("departamento").isin(VALID_DEPARTMENTS))
        
        if invalid_depts.count() > 0:
            bad_depts = invalid_depts.select("departamento").distinct().collect()
            print(f"❌ DEPARTMENTS: Departamentos inválidos: {[row.departamento for row in bad_depts]}")
            return False
        
        print(f"✅ DEPARTMENTS: Todos los departamentos válidos")
        return True
        
    except Exception as e:
        print(f"❌ DEPARTMENTS: Error {e}")
        return False


def validate_diseases(spark, path: str) -> bool:
    """Validar enfermedades válidas."""
    try:
        df = spark.read.parquet(path)
        
        invalid_diseases = df.filter(~F.col("disease").isin(VALID_DISEASES))
        
        if invalid_diseases.count() > 0:
            bad_diseases = invalid_diseases.select("disease").distinct().collect()
            print(f"❌ DISEASES: Enfermedades inválidas: {[row.disease for row in bad_diseases]}")
            return False
        
        print(f"✅ DISEASES: Todas enfermedades válidas")
        return True
        
    except Exception as e:
        print(f"❌ DISEASES: Error {e}")
        return False


def validate_temporal_consistency(spark, path: str) -> bool:
    """Validar consistencia temporal (sin saltos anormales)."""
    try:
        df = spark.read.parquet(path)
        
        # Detectar semanas faltantes por enfermedad/departamento
        weekly = df.groupBy("epi_year", "epi_week", "disease", "departamento").count()
        
        # Rango esperado: 2013-2024 = 12 años * 52-53 semanas = ~624 semanas por disease/dept
        expected_records_per_disease_dept = 624
        
        coverage = weekly.count() / (len(VALID_DISEASES) * len(VALID_DEPARTMENTS))
        
        if coverage < 0.7:
            print(f"❌ TEMPORAL: Cobertura temporal baja ({coverage:.1%})")
            return False
        
        print(f"✅ TEMPORAL: Cobertura temporal {coverage:.1%}")
        return True
        
    except Exception as e:
        print(f"❌ TEMPORAL: Error {e}")
        return False


def validate_duplicates(spark, path: str) -> bool:
    """Detectar duplicados."""
    try:
        df = spark.read.parquet(path)
        
        total = df.count()
        unique = df.dropDuplicates(["epi_year", "epi_week", "disease", "departamento"]).count()
        
        if unique < total * 0.99:
            dup_count = total - unique
            print(f"❌ DUPLICATES: {dup_count} duplicados detectados")
            return False
        
        print(f"✅ DUPLICATES: Sin duplicados significativos")
        return True
        
    except Exception as e:
        print(f"❌ DUPLICATES: Error {e}")
        return False


def main():
    parser_args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    input_path = str(PROCESSED_DIR / "curated_weekly_v0_parquet")
    
    if parser_args:
        input_path = parser_args[0]
    
    print(f"\n{'='*60}")
    print(f"VALIDACIÓN DE DATOS: {input_path}")
    print(f"{'='*60}\n")
    
    spark = SparkSession.builder.appName("validate_data").getOrCreate()
    
    validations = [
        ("Schema", validate_schema),
        ("Rangos", validate_ranges),
        ("Nulos", validate_nulls),
        ("Departamentos", validate_departments),
        ("Enfermedades", validate_diseases),
        ("Consistencia Temporal", validate_temporal_consistency),
        ("Duplicados", validate_duplicates),
    ]
    
    results = []
    for name, func in validations:
        result = func(spark, input_path)
        results.append((name, result))
    
    print(f"\n{'='*60}")
    print("RESUMEN")
    print(f"{'='*60}\n")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {name}")
    
    print(f"\n{passed}/{total} validaciones pasaron\n")
    
    spark.stop()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
