"""Cálculo determinístico de fecha epidemiológica (ISO 8601) + parseo de
fechas en texto libre en español.

Nunca dejar que el LLM infiera día-de-la-semana / semana epidemiológica
a partir de una fecha en texto — los modelos de lenguaje son poco
confiables para aritmética de calendario, sobre todo en fechas futuras
lejanas. Este módulo calcula el dato exacto en Python y lo entrega ya
resuelto para que el LLM solo lo cite.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

DIAS_ISO = {
    1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves",
    5: "Viernes", 6: "Sábado", 7: "Domingo",
}

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# "1 de abril de 2030" / "1 de abril del 2030"
_RE_ES = re.compile(
    r"\b(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+(?:de|del)\s+(\d{4})\b",
    re.IGNORECASE,
)
# "2030-04-01"
_RE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# "01/04/2030" o "01-04-2030" (Colombia: día/mes/año)
_RE_NUM = re.compile(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b")


@dataclass
class EpiDate:
    fecha: date
    epi_year: int
    epi_week: int
    dia_iso: int
    dia_nombre: str
    week_start_date: date
    week_end_date: date

    def as_context_line(self) -> str:
        """Línea lista para inyectar como ChatSource — el LLM la cita, no la calcula."""
        return (
            f"{self.fecha.isoformat()} es {self.dia_nombre} (día ISO {self.dia_iso}). "
            f"epi_year={self.epi_year}, epi_week={self.epi_week:02d} "
            f"(semana del {self.week_start_date.isoformat()} al {self.week_end_date.isoformat()})."
        )


def resolve_epi_date(year: int, month: int, day: int) -> EpiDate:
    """Calcula año/semana epidemiológica ISO 8601 para una fecha dada."""
    d = date(year, month, day)
    iso_year, iso_week, iso_weekday = d.isocalendar()
    week_start = d - timedelta(days=iso_weekday - 1)
    week_end = week_start + timedelta(days=6)
    return EpiDate(
        fecha=d, epi_year=iso_year, epi_week=iso_week,
        dia_iso=iso_weekday, dia_nombre=DIAS_ISO[iso_weekday],
        week_start_date=week_start, week_end_date=week_end,
    )


def find_date_in_text(text: str) -> EpiDate | None:
    """Busca una fecha en texto libre en español y la resuelve de forma
    determinística. Devuelve None si no encuentra ninguna, o si la fecha
    detectada no es válida (ej. "31 de febrero")."""
    m = _RE_ES.search(text)
    if m:
        day_s, month_name, year_s = m.groups()
        month = MESES_ES.get(month_name.lower())
        if month:
            try:
                return resolve_epi_date(int(year_s), month, int(day_s))
            except ValueError:
                return None  # fecha inválida (ej. 31 de abril) — no inventar

    m = _RE_ISO.search(text)
    if m:
        year_s, month_s, day_s = m.groups()
        try:
            return resolve_epi_date(int(year_s), int(month_s), int(day_s))
        except ValueError:
            return None

    m = _RE_NUM.search(text)
    if m:
        day_s, month_s, year_s = m.groups()  # formato colombiano DD/MM/YYYY
        try:
            return resolve_epi_date(int(year_s), int(month_s), int(day_s))
        except ValueError:
            return None

    return None