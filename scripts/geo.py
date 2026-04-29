"""Shared geographic mappings for ECOS pipelines."""

from __future__ import annotations

import unicodedata

DEPARTMENTS = [
    {"code": "05", "name": "ANTIOQUIA", "iso": "CO-ANT", "region": "ANDINA", "lat": 6.2518, "lon": -75.5636},
    {"code": "08", "name": "ATLANTICO", "iso": "CO-ATL", "region": "CARIBE", "lat": 10.9685, "lon": -74.7813},
    {"code": "11", "name": "BOGOTA", "iso": "CO-DC", "region": "ANDINA", "lat": 4.6097, "lon": -74.0817},
    {"code": "13", "name": "BOLIVAR", "iso": "CO-BOL", "region": "CARIBE", "lat": 10.3997, "lon": -75.4762},
    {"code": "15", "name": "BOYACA", "iso": "CO-BOY", "region": "ANDINA", "lat": 5.5353, "lon": -73.3678},
    {"code": "17", "name": "CALDAS", "iso": "CO-CAL", "region": "ANDINA", "lat": 5.0689, "lon": -75.5174},
    {"code": "18", "name": "CAQUETA", "iso": "CO-CAQ", "region": "AMAZONIA", "lat": 1.6144, "lon": -75.6062},
    {"code": "19", "name": "CAUCA", "iso": "CO-CAU", "region": "PACIFICO", "lat": 2.4454, "lon": -76.6132},
    {"code": "20", "name": "CESAR", "iso": "CO-CES", "region": "CARIBE", "lat": 10.4631, "lon": -73.2532},
    {"code": "23", "name": "CORDOBA", "iso": "CO-COR", "region": "CARIBE", "lat": 8.7480, "lon": -75.8814},
    {"code": "25", "name": "CUNDINAMARCA", "iso": "CO-CUN", "region": "ANDINA", "lat": 4.5981, "lon": -74.0758},
    {"code": "27", "name": "CHOCO", "iso": "CO-CHO", "region": "PACIFICO", "lat": 5.6947, "lon": -76.6611},
    {"code": "41", "name": "HUILA", "iso": "CO-HUI", "region": "ANDINA", "lat": 2.9273, "lon": -75.2819},
    {"code": "44", "name": "LA GUAJIRA", "iso": "CO-LAG", "region": "CARIBE", "lat": 11.5440, "lon": -72.9069},
    {"code": "47", "name": "MAGDALENA", "iso": "CO-MAG", "region": "CARIBE", "lat": 11.2408, "lon": -74.1990},
    {"code": "50", "name": "META", "iso": "CO-MET", "region": "ORINOQUIA", "lat": 4.1420, "lon": -73.6266},
    {"code": "52", "name": "NARINO", "iso": "CO-NAR", "region": "PACIFICO", "lat": 1.2136, "lon": -77.2811},
    {"code": "54", "name": "NORTE DE SANTANDER", "iso": "CO-NSA", "region": "ANDINA", "lat": 7.8939, "lon": -72.5078},
    {"code": "63", "name": "QUINDIO", "iso": "CO-QUI", "region": "ANDINA", "lat": 4.5339, "lon": -75.6811},
    {"code": "66", "name": "RISARALDA", "iso": "CO-RIS", "region": "ANDINA", "lat": 4.8133, "lon": -75.6961},
    {"code": "68", "name": "SANTANDER", "iso": "CO-SAN", "region": "ANDINA", "lat": 7.1193, "lon": -73.1227},
    {"code": "70", "name": "SUCRE", "iso": "CO-SUC", "region": "CARIBE", "lat": 9.3047, "lon": -75.3978},
    {"code": "73", "name": "TOLIMA", "iso": "CO-TOL", "region": "ANDINA", "lat": 4.4389, "lon": -75.2322},
    {"code": "76", "name": "VALLE DEL CAUCA", "iso": "CO-VAC", "region": "PACIFICO", "lat": 3.4516, "lon": -76.5320},
    {"code": "81", "name": "ARAUCA", "iso": "CO-ARA", "region": "ORINOQUIA", "lat": 7.0847, "lon": -70.7591},
    {"code": "85", "name": "CASANARE", "iso": "CO-CAS", "region": "ORINOQUIA", "lat": 5.3378, "lon": -72.3959},
    {"code": "86", "name": "PUTUMAYO", "iso": "CO-PUT", "region": "AMAZONIA", "lat": 1.1478, "lon": -76.6478},
    {"code": "88", "name": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA", "iso": "CO-SAP", "region": "CARIBE", "lat": 12.5847, "lon": -81.7006},
    {"code": "91", "name": "AMAZONAS", "iso": "CO-AMA", "region": "AMAZONIA", "lat": -4.2153, "lon": -69.9406},
    {"code": "94", "name": "GUAINIA", "iso": "CO-GUA", "region": "AMAZONIA", "lat": 3.8653, "lon": -67.9239},
    {"code": "95", "name": "GUAVIARE", "iso": "CO-GUV", "region": "AMAZONIA", "lat": 2.5729, "lon": -72.6459},
    {"code": "97", "name": "VAUPES", "iso": "CO-VAU", "region": "AMAZONIA", "lat": 1.2503, "lon": -70.2339},
    {"code": "99", "name": "VICHADA", "iso": "CO-VID", "region": "ORINOQUIA", "lat": 6.1822, "lon": -67.4815},
]

DEPT_CODE_TO_NAME = {item["code"]: item["name"] for item in DEPARTMENTS}
DEPT_NAME_TO_CODE = {item["name"]: item["code"] for item in DEPARTMENTS}
DEPT_CODE_TO_ISO = {item["code"]: item["iso"] for item in DEPARTMENTS}
DEPT_CODE_TO_LATLON = {item["code"]: (item["lat"], item["lon"]) for item in DEPARTMENTS}
REGION_MAP = {item["name"]: item["region"] for item in DEPARTMENTS if item.get("region")}


def normalize_text(value: str) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace(".", " ")
    value = " ".join(value.upper().split())
    return value
