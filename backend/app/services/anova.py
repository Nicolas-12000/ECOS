import numpy as np
import pandas as pd
from scipy.stats import f_oneway, kruskal, levene, tukey_hsd
from typing import List, Dict, Any, Tuple
import logging
from app.core.db import get_db_connection

logger = logging.getLogger(__name__)

def run_dengue_anova(
    table_names: List[str],
    years: List[int],
    disease: str = "dengue",
    transform: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta el análisis ANOVA de una vía y comparaciones múltiples Tukey HSD 
    para evaluar los patrones de enfermedades entre múltiples años y datasets.
    """
    if len(years) * len(table_names) < 3:
        raise ValueError("Se requieren al menos 3 grupos (combinación de años y tablas) para realizar un análisis ANOVA comparativo.")

    all_dfs = []
    
    with get_db_connection() as conn:
        for table_name in table_names:
            query = ""
            params = (years,)

            if table_name == "fact_core_weekly":
                query = """
                    SELECT epi_year as year, epi_week as week, SUM(cases_total) as cases
                    FROM public.fact_core_weekly
                    WHERE disease = %s AND epi_year = ANY(%s)
                    GROUP BY epi_year, epi_week
                    ORDER BY epi_year, epi_week
                """
                params = (disease, years)
            elif table_name == "dengue_kaggle_dataset" and disease == "dengue":
                query = """
                    SELECT ano as year, semana as week, SUM(casos_totales) as cases
                    FROM analytics.dengue_kaggle_dataset
                    WHERE enfermedad = 'Dengue' AND ano = ANY(%s)
                    GROUP BY ano, semana
                    ORDER BY ano, semana
                """
            elif table_name == "anova_dataset" and disease == "dengue":
                query = """
                    SELECT ano as year, semana as week, SUM(casos_totales) as cases
                    FROM analytics.anova_dataset
                    WHERE enfermedad = 'Dengue' AND ano = ANY(%s)
                    GROUP BY ano, semana
                    ORDER BY ano, semana
                """
            else:
                continue

            df_temp = pd.read_sql_query(query, conn, params=params)
            if not df_temp.empty:
                df_temp['table'] = table_name
                all_dfs.append(df_temp)

    if not all_dfs:
        raise ValueError(f"No se encontraron registros de {disease} para los años y tablas seleccionados en la base de datos.")

    df = pd.concat(all_dfs, ignore_index=True)

    # Asegurar tipos numéricos y manejar nulos
    df['year'] = df['year'].astype(int)
    df['cases'] = pd.to_numeric(df['cases'], errors='coerce').fillna(0).astype(float)
    
    # Crear identificador de grupo (Tabla + Año)
    df['group'] = df.apply(lambda row: f"{row['table']} ({row['year']})", axis=1)

    # 3. Aplicar transformación opcional (log1p) para estabilizar la varianza
    if transform:
        df['cases_transformed'] = np.log1p(df['cases'])
        value_column = 'cases_transformed'
    else:
        value_column = 'cases'

    # 4. Agrupar datos por (tabla, año) para análisis estadístico
    groups_data = {}
    unique_groups = sorted(df['group'].unique())
    
    for g in unique_groups:
        g_data = df[df['group'] == g][value_column].values
        if len(g_data) > 0:
            groups_data[g] = g_data

    # Validar que tengamos datos suficientes para cada grupo
    actual_groups = sorted(list(groups_data.keys()))
    if len(actual_groups) < 3:
        raise ValueError("No hay datos suficientes para al menos 3 de los grupos seleccionados.")

    groups_list = [groups_data[g] for g in actual_groups]

    # 5. Calcular estadísticas descriptivas
    descriptives = []
    for g in actual_groups:
        data_orig = df[df['group'] == g]['cases'].values
        g_info = df[df['group'] == g].iloc[0]
        descriptives.append({
            "group": g,
            "table": g_info['table'],
            "year": int(g_info['year']),
            "n": int(len(data_orig)),
            "mean": float(np.mean(data_orig)),
            "std": float(np.std(data_orig)),
            "min": float(np.min(data_orig)),
            "max": float(np.max(data_orig)),
            "median": float(np.median(data_orig)),
            "sum": float(np.sum(data_orig))
        })

    # 6. Realizar pruebas de supuestos
    # Prueba de homogeneidad de varianzas (Levene)
    levene_stat, levene_p = float('nan'), float('nan')
    try:
        if len(groups_list) >= 2:
            levene_res = levene(*groups_list)
            levene_stat = float(levene_res.statistic)
            levene_p = float(levene_res.pvalue)
    except Exception as e:
        logger.warning(f"Error al calcular la prueba de Levene: {e}")

    # 7. Realizar pruebas globales (ANOVA y Kruskal-Wallis)
    anova_f, anova_p = float('nan'), float('nan')
    kruskal_h, kruskal_p = float('nan'), float('nan')

    try:
        anova_res = f_oneway(*groups_list)
        anova_f = float(anova_res.statistic)
        anova_p = float(anova_res.pvalue)
    except Exception as e:
        logger.warning(f"Error al ejecutar ANOVA: {e}")

    try:
        kruskal_res = kruskal(*groups_list)
        kruskal_h = float(kruskal_res.statistic)
        kruskal_p = float(kruskal_res.pvalue)
    except Exception as e:
        logger.warning(f"Error al ejecutar Kruskal-Wallis: {e}")

    # 8. Realizar pruebas post-hoc de comparaciones múltiples (Tukey HSD)
    tukey_results = []
    try:
        tukey_res = tukey_hsd(*groups_list)
        ci = tukey_res.confidence_interval(confidence_level=0.95)
        
        n_groups = len(actual_groups)
        for i in range(n_groups):
            for j in range(i + 1, n_groups):
                group_a = actual_groups[i]
                group_b = actual_groups[j]
                
                # Diferencia de medias en escala original
                mean_a_orig = next(d['mean'] for d in descriptives if d['group'] == group_a)
                mean_b_orig = next(d['mean'] for d in descriptives if d['group'] == group_b)
                diff_orig = mean_a_orig - mean_b_orig

                # Diferencia y p-values del test (puede ser en escala transformada si transform=True)
                diff_test = float(tukey_res.statistic[i, j])
                p_val = float(tukey_res.pvalue[i, j])
                ci_low = float(ci.low[i, j])
                ci_high = float(ci.high[i, j])
                
                # Interpretación en lenguaje claro para el par
                sig_text = "significativa" if p_val < 0.05 else "no significativa"
                direction = "mayor" if diff_orig > 0 else "menor"
                diff_abs_str = f"{abs(diff_orig):,.1f}"
                
                if p_val < 0.05:
                    narrative = (
                        f"El promedio de casos en {group_a} fue significativamente {direction} "
                        f"que en {group_b} por una diferencia de {diff_abs_str} casos semanales."
                    )
                else:
                    narrative = (
                        f"No hay diferencias estadísticamente relevantes entre {group_a} y {group_b}. "
                        f"Las fluctuaciones semanales de casos se comportaron dentro de rangos similares."
                    )

                tukey_results.append({
                    "group_a": group_a,
                    "group_b": group_b,
                    "mean_diff_test": diff_test,
                    "mean_diff_original": diff_orig,
                    "p_value": p_val,
                    "ci_lower": ci_low,
                    "ci_upper": ci_high,
                    "significant": bool(p_val < 0.05),
                    "narrative": narrative
                })
    except Exception as e:
        logger.error(f"Error al ejecutar Tukey HSD: {e}")

    # 9. Generar Interpretación General en Lenguaje Claro
    significant_anova = bool(anova_p < 0.05) if not np.isnan(anova_p) else False
    
    # Definición de Hipótesis
    hypotheses = {
        "null": f"No existen diferencias significativas entre los grupos. El comportamiento de {disease} es estadísticamente igual en todos los años/fuentes seleccionados.",
        "alternative": f"Existen diferencias significativas en al menos uno de los grupos. El comportamiento de {disease} varía de forma sistemática entre los periodos o fuentes analizadas.",
        "outcome": "alternative" if significant_anova else "null",
        "conclusion": (
            "Se rechaza la hipótesis nula en favor de la alternativa." if significant_anova 
            else "No hay evidencia suficiente para rechazar la hipótesis nula."
        )
    }

    # Encontrar año de mayor y menor carga
    highest_group_desc = max(descriptives, key=lambda d: d['mean'])
    lowest_group_desc = min(descriptives, key=lambda d: d['mean'])
    
    # Contar comparaciones significativas
    sig_pairs = sum(1 for t in tukey_results if t['significant'])
    total_pairs = len(tukey_results)
    
    summary_title = ""
    summary_text = ""
    epidemiological_impact = ""
    
    if significant_anova:
        summary_title = "¡Diferencias Significativas Detectadas!"
        # Format p-value to 5 decimals as requested, avoiding scientific notation
        if anova_p < 0.00001:
            p_val_str = "< 0.00001"
        else:
            p_val_str = f"{anova_p:.5f}"
        
        summary_text = (
            f"El análisis estadístico demuestra de forma contundente (p-value = {p_val_str}) que el comportamiento "
            f"de {disease} no fue igual en todos los grupos. Las variaciones en la cantidad de casos semanales no son "
            f"casualidad, sino que representan cambios sistemáticos reales. "
            f"El grupo de mayor intensidad fue {highest_group_desc['group']} (con un promedio de {highest_group_desc['mean']:,.1f} casos semanales), "
            f"mientras que el grupo más leve fue {lowest_group_desc['group']} (con un promedio de {lowest_group_desc['mean']:,.1f} casos semanales)."
        )
        
        if sig_pairs > 0:
            epidemiological_impact = (
                f"Se confirmaron diferencias significativas en {sig_pairs} de las {total_pairs} parejas de grupos comparadas. "
                f"Esto sugiere la presencia de factores dinámicos —como el Fenómeno de El Niño, "
                f"diferencias en la calidad de recolección entre datasets, o brotes excepcionales— "
                f"que alteraron las tasas de transmisión o reporte de {disease} en los periodos analizados."
            )
        else:
            epidemiological_impact = (
                "Aunque la prueba global muestra diferencias, las comparaciones individuales por parejas son sutiles. "
                "Esto suele ocurrir cuando hay una tendencia de cambio gradual a lo largo de los grupos."
            )
    else:
        summary_title = "Sin Diferencias Estadísticamente Significativas"
        p_val_str = f"{anova_p:.5f}"
        summary_text = (
            f"El análisis no encontró evidencias suficientes para afirmar que {disease} se comportara de forma "
            f"distinta entre los grupos seleccionados (p-value = {p_val_str}). A pesar de que a simple vista un grupo "
            f"pueda registrar más casos totales que otro, la variabilidad semana a semana es normal y las diferencias "
            f"promedio se explican por fluctuaciones de azar."
        )
        epidemiological_impact = (
            f"Desde una perspectiva de salud pública, esto sugiere que la transmisión de {disease} en estos grupos se mantuvo "
            "estable y consistente entre los diferentes años y fuentes de datos analizadas."
        )

    # 10. Estructurar el JSON de respuesta para el Dashboard
    weeks_list = sorted(list(df['week'].unique()))
    chart_data = []
    for w in weeks_list:
        row = {"week": int(w)}
        for g in actual_groups:
            val = df[(df['group'] == g) & (df['week'] == w)]['cases'].values
            if len(val) > 0:
                row[g] = float(val[0])
            else:
                row[g] = None
        chart_data.append(row)

    return {
        "metadata": {
            "tables": table_names,
            "disease": disease,
            "transform_applied": transform,
            "analyzed_groups": actual_groups
        },
        "descriptives": descriptives,
        "hypothesis_tests": {
            "anova": {
                "f_statistic": anova_f if not np.isnan(anova_f) else None,
                "p_value": anova_p if not np.isnan(anova_p) else None,
                "significant": significant_anova
            },
            "kruskal_wallis": {
                "h_statistic": kruskal_h if not np.isnan(kruskal_h) else None,
                "p_value": kruskal_p if not np.isnan(kruskal_p) else None,
                "significant": bool(kruskal_p < 0.05) if not np.isnan(kruskal_p) else False
            },
            "levene_homocedasticity": {
                "statistic": levene_stat if not np.isnan(levene_stat) else None,
                "p_value": levene_p if not np.isnan(levene_p) else None,
                "significant": bool(levene_p < 0.05) if not np.isnan(levene_p) else False
            }
        },
        "tukey_hsd": tukey_results,
        "hypotheses": hypotheses,
        "interpretation": {
            "title": summary_title,
            "summary": summary_text,
            "epidemiological_impact": epidemiological_impact
        },
        "chart_data": chart_data
    }
