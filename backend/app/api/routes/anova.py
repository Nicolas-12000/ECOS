from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
from app.services.anova import run_dengue_anova
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/dengue")
def get_dengue_anova(
    years: str = Query(..., description="Años separados por coma para comparar (ej: 2010,2013,2016,2019)"),
    tables: str = Query("fact_core_weekly", description="Tablas de origen separadas por coma (fact_core_weekly, dengue_kaggle_dataset, anova_dataset)"),
    disease: str = Query("dengue", description="Enfermedad a analizar (dengue, zika, malaria, chikungunya)"),
    transform: bool = Query(False, description="Aplicar transformación logarítmica log1p a los casos")
):
    """
    Realiza una prueba estadística ANOVA y comparaciones post-hoc Tukey HSD 
    para evaluar los patrones de enfermedades entre múltiples años y datasets.
    """
    # 1. Validar y procesar los años
    try:
        years_list = [int(y.strip()) for y in years.split(",") if y.strip()]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="El parámetro 'years' debe ser una lista de números enteros separados por comas."
        )

    # 2. Validar y procesar las tablas
    tables_list = [t.strip() for t in tables.split(",") if t.strip()]
    valid_tables = ["fact_core_weekly", "dengue_kaggle_dataset", "anova_dataset"]
    
    for table in tables_list:
        if table not in valid_tables:
            raise HTTPException(
                status_code=422,
                detail=f"Tabla inválida: '{table}'. Debe ser una de: {', '.join(valid_tables)}"
            )
            
    # Validar que si no es dengue, solo se use fact_core_weekly
    if disease != "dengue" and any(t != "fact_core_weekly" for t in tables_list):
        raise HTTPException(
            status_code=400,
            detail=f"Para la enfermedad '{disease}', solo se permite el uso de la tabla 'fact_core_weekly'."
        )

    if len(years_list) * len(tables_list) < 3:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 3 grupos (combinación de años y tablas) para realizar una comparación ANOVA."
        )

    # 3. Ejecutar análisis ANOVA
    try:
        results = run_dengue_anova(
            table_names=tables_list,
            years=years_list,
            disease=disease,
            transform=transform
        )
        return jsonable_encoder(results)
    except ValueError as ve:
        logger.warning(f"Error de validación en ANOVA: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error inesperado en servicio ANOVA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error interno al procesar las pruebas estadísticas: {str(e)}"
        )
