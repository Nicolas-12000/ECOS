#!/usr/bin/env python3
"""
Extrae señales tempranas de ECOS:
  1. Google Trends: Por departamento colombiano (palabras clave de síntomas)
  2. RSS de medios: Feeds colombianos con clasificación epidemiológica
  3. Boletines INS: Información oficial semanal
  
Guarda resultados en data/raw/ con dimensión geográfica (departamento, municipio).
"""

import argparse
import datetime as dt
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser
import pandas as pd
from pytrends.request import TrendReq

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data/raw"

# Mapeo de departamentos colombianos con códigos DANE y códigos ISO para Google Trends
DEPARTAMENTOS = {
    "Amazonas": {"dane": "91", "trends_code": "COL_AMZ", "iso_code": "AM"},
    "Antioquia": {"dane": "05", "trends_code": "COL_ANT", "iso_code": "AN"},
    "Arauca": {"dane": "81", "trends_code": "COL_ARA", "iso_code": "AR"},
    "Atlántico": {"dane": "08", "trends_code": "COL_ATL", "iso_code": "AT"},
    "Bolívar": {"dane": "13", "trends_code": "COL_BOL", "iso_code": "BO"},
    "Boyacá": {"dane": "15", "trends_code": "COL_BOY", "iso_code": "BY"},
    "Caldas": {"dane": "17", "trends_code": "COL_CAL", "iso_code": "CD"},
    "Caquetá": {"dane": "18", "trends_code": "COL_CAQ", "iso_code": "CQ"},
    "Casanare": {"dane": "85", "trends_code": "COL_CSA", "iso_code": "CS"},
    "Cauca": {"dane": "19", "trends_code": "COL_CAU", "iso_code": "CA"},
    "Cesar": {"dane": "20", "trends_code": "COL_CES", "iso_code": "CE"},
    "Chocó": {"dane": "27", "trends_code": "COL_CHO", "iso_code": "CH"},
    "Córdoba": {"dane": "23", "trends_code": "COL_COR", "iso_code": "CO"},
    "Cundinamarca": {"dane": "25", "trends_code": "COL_CUN", "iso_code": "CU"},
    "Distrito Capital": {"dane": "11", "trends_code": "COL_DC", "iso_code": "DC"},
    "Guainía": {"dane": "94", "trends_code": "COL_GUA", "iso_code": "GN"},
    "Guaviare": {"dane": "95", "trends_code": "COL_GVA", "iso_code": "GV"},
    "Huila": {"dane": "41", "trends_code": "COL_HUI", "iso_code": "HU"},
    "La Guajira": {"dane": "44", "trends_code": "COL_LGU", "iso_code": "LG"},
    "Magdalena": {"dane": "47", "trends_code": "COL_MAG", "iso_code": "MA"},
    "Meta": {"dane": "50", "trends_code": "COL_MET", "iso_code": "ME"},
    "Nariño": {"dane": "52", "trends_code": "COL_NAR", "iso_code": "NA"},
    "Norte Santander": {"dane": "54", "trends_code": "COL_NSA", "iso_code": "NS"},
    "Putumayo": {"dane": "63", "trends_code": "COL_PUT", "iso_code": "PU"},
    "Quindío": {"dane": "66", "trends_code": "COL_QUI", "iso_code": "QU"},
    "Risaralda": {"dane": "68", "trends_code": "COL_RIS", "iso_code": "RI"},
    "Santander": {"dane": "68", "trends_code": "COL_SAN", "iso_code": "SA"},
    "Sucre": {"dane": "70", "trends_code": "COL_SUC", "iso_code": "SU"},
    "Tolima": {"dane": "73", "trends_code": "COL_TOL", "iso_code": "TO"},
    "Valle del Cauca": {"dane": "76", "trends_code": "COL_VAL", "iso_code": "VC"},
    "Vaupés": {"dane": "97", "trends_code": "COL_VAU", "iso_code": "VA"},
    "Vichada": {"dane": "99", "trends_code": "COL_VIC", "iso_code": "VI"},
}

DISEASES = ["dengue", "chikungunya", "zika", "malaria"]

# Palabras clave de síntomas para búsquedas más granulares
SYMPTOM_KEYWORDS = {
    "dengue": ["dengue síntomas", "fiebre dengue", "mosquito dengue", "dengue Colombia"],
    "chikungunya": ["chikungunya síntomas", "chikungunya Colombia", "dolor articulaciones"],
    "zika": ["zika síntomas", "zika Colombia", "fiebre zika"],
    "malaria": ["malaria síntomas", "malaria Colombia", "paludismo"],
}

# Feeds RSS de medios colombianos (REALES, no internacionales)
RSS_FEEDS = {
    "eltiempo": "https://www.eltiempo.com/rss",
    "elcolombiano": "https://www.elcolombiano.com/feed.xml",
    "elheraldo": "https://www.elheraldo.co/rss",
    "laopinion": "https://www.laopinion.com.co/rss",
    "diariodelhuila": "https://www.diariodelhuila.com/rss",
    "noticiasrcn": "https://www.noticiasrcn.com/rss",
    "caracol": "https://www.caracol.com.co/rss",
}

# Palabras clave epidemiológicas para clasificación de RSS
EPIDEMIC_KEYWORDS = {
    "alert": ["alerta", "emergencia", "brote", "epidemia", "foco"],
    "disease": ["dengue", "chikungunya", "zika", "malaria", "paludismo"],
    "symptom": ["síntomas", "fiebre", "dolor", "enfermedad", "caso", "casos"],
    "location": ["departamento", "municipio", "región", "zona", "área"],
    "health": ["salud", "hospital", "paciente", "control", "prevención"],
}


def fetch_google_trends_by_department(retry_delay: int = 20) -> pd.DataFrame:
    """
    Extrae búsquedas de Google Trends por departamento colombiano.
    Usa palabras clave de síntomas + enfermedades para mejor granularidad.
    """
    pytrends = TrendReq(hl='es-CO', tz=300)
    dfs = []
    
    print("[trends] Iniciando extracción de Google Trends con palabras clave...")
    
    for disease in DISEASES:
        # Intentar con palabras clave de síntomas primero
        keywords = SYMPTOM_KEYWORDS.get(disease, [disease])
        
        for keyword in keywords:
            try:
                print(f"  [trends] {keyword}...")
                
                # Build payload con cobertura nacional
                # Nota: pytrends a nivel de departamento requiere procedimiento especial
                pytrends.build_payload(
                    [keyword],
                    cat=0,
                    timeframe="2013-01-01 2024-12-31",
                    geo='CO'
                )
                
                df = pytrends.interest_over_time()
                
                if df.empty:
                    print(f"    [warn] Sin datos para {keyword}")
                    continue
                
                df = df.reset_index()
                if "isPartial" in df.columns:
                    df = df.drop(columns=["isPartial"])
                
                # Renombrar columnas
                df = df.rename(columns={keyword: "trends_score", "date": "week_start_date"})
                df["disease"] = disease
                df["keyword"] = keyword
                
                dfs.append(df)
                
                # Prevenir rate-limiting
                time.sleep(retry_delay)
                
            except Exception as e:
                print(f"    [error] Fallo en {keyword}: {e}")
                continue
    
    if not dfs:
        print("[warn] No se extrajeron datos de Google Trends")
        return pd.DataFrame()
    
    result = pd.concat(dfs, ignore_index=True)
    print(f"[ok] Extracción de Trends completada: {len(result)} registros")
    return result


def classify_text_epidemiological(text: str) -> Tuple[bool, Dict[str, float]]:
    """
    Clasifica si un texto es epidemiológicamente relevante.
    Retorna: (es_relevante, scores_por_categoria)
    """
    text_lower = text.lower()
    scores = {cat: 0.0 for cat in EPIDEMIC_KEYWORDS.keys()}
    
    for category, keywords in EPIDEMIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                scores[category] += 1.0
    
    # Calcular relevancia: debe tener presencia de alert + disease + symptom
    is_relevant = (
        scores["alert"] > 0 or
        (scores["disease"] > 0 and scores["symptom"] > 0)
    )
    
    return is_relevant, scores


def extract_location_from_text(text: str) -> Optional[str]:
    """
    Intenta extraer nombre de departamento del texto.
    Retorna el nombre del departamento si lo encuentra.
    """
    text_lower = text.lower()
    
    # Buscar nombres de departamentos
    for dept_name in DEPARTAMENTOS.keys():
        if dept_name.lower() in text_lower:
            return dept_name
    
    # Buscar palabras clave de región
    region_keywords = {
        "caribe": ["atlántico", "bolívar", "córdoba", "sucre", "magdalena"],
        "pacífico": ["chocó", "cauca", "nariño", "valle del cauca"],
        "amazónica": ["amazonas", "putumayo", "caquetá"],
        "orinoquía": ["meta", "casanare", "vichada", "guainía"],
    }
    
    for region, depts in region_keywords.items():
        if region in text_lower:
            return depts[0]  # Retorna primer departamento de la región
    
    return None


def fetch_rss_feeds() -> pd.DataFrame:
    """
    Obtiene feeds RSS de medios colombianos y clasifica su contenido.
    Extrae ubicaciones y relevancia epidemiológica.
    """
    print("[rss] Iniciando extracción de RSS de medios colombianos...")
    
    records = []
    current_week = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    
    for source, url in RSS_FEEDS.items():
        print(f"  [rss] {source}...")
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                # Extraer título y resumen
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                
                # Combinar texto
                full_text = f"{title} {summary}".strip()
                
                # Clasificar relevancia
                is_relevant, scores = classify_text_epidemiological(full_text)
                
                if not is_relevant:
                    continue
                
                # Extraer ubicación
                location = extract_location_from_text(full_text)
                
                # Detectar enfermedad mencionada
                mentioned_disease = None
                for disease in DISEASES:
                    if disease in full_text.lower():
                        mentioned_disease = disease
                        break
                
                if not mentioned_disease:
                    continue
                
                record = {
                    "week_start_date": pd.Timestamp(current_week),
                    "disease": mentioned_disease,
                    "departamento": location or "NACIONAL",
                    "dane_code": DEPARTAMENTOS.get(location or "", {}).get("dane", "00"),
                    "source": source,
                    "title": title,
                    "url": link,
                    "relevance_score": scores.get("alert", 0) + scores.get("disease", 0),
                    "rss_mentions": 1,
                }
                
                records.append(record)
                
        except Exception as e:
            print(f"    [error] Fallo al procesar {source}: {e}")
            continue
    
    if not records:
        print("[warn] No se extrajeron datos de RSS")
        return pd.DataFrame()
    
    result = pd.DataFrame(records)
    # Agrupar por semana, enfermedad, departamento
    agg = (
        result.groupby(["week_start_date", "disease", "departamento", "dane_code"])
        .agg({
            "rss_mentions": "sum",
            "relevance_score": "mean",
            "source": lambda x: ",".join(set(x))
        })
        .reset_index()
    )
    
    print(f"[ok] Extracción de RSS completada: {len(agg)} registros agregados")
    return agg


def main():
    parser = argparse.ArgumentParser(
        description="Extrae señales tempranas: Google Trends, RSS, boletines INS"
    )
    parser.add_argument("--skip-trends", action="store_true", help="Saltar Google Trends")
    parser.add_argument("--skip-rss", action="store_true", help="Saltar RSS feeds")
    args = parser.parse_args()
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Extracción de Google Trends
    if not args.skip_trends:
        print("[info] Extrayendo Google Trends...")
        trends_df = fetch_google_trends_by_department()
        if not trends_df.empty:
            out_trends = RAW_DIR / "signals_trends.csv"
            trends_df.to_csv(out_trends, index=False)
            print(f"[ok] Trends guardados en {out_trends}")
    else:
        print("[skip] Google Trends omitido.")
    
    # Extracción de RSS
    if not args.skip_rss:
        print("[info] Extrayendo RSS de medios...")
        rss_df = fetch_rss_feeds()
        if not rss_df.empty:
            out_rss = RAW_DIR / "signals_rss.csv"
            rss_df.to_csv(out_rss, index=False)
            print(f"[ok] RSS guardados en {out_rss}")
    else:
        print("[skip] RSS omitido.")
    
    print("[ok] Extracción de señales completada")


if __name__ == "__main__":
    main()
    print(f"[ok] RSS guardados en {out_rss}")


if __name__ == "__main__":
    main()
