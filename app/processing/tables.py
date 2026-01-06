"""
app.processing.tables

Generación de tablas “presentables” a partir de LogEntry.

Novedad:
- build_daily_marks_table ahora recibe (start_date, end_date) y crea filas incluso si no hay marcas.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from app.domain.models import LogEntry

_WEEKDAY_ES: Dict[int, str] = {
    0: "LUNES",
    1: "MARTES",
    2: "MIERCOLES",
    3: "JUEVES",
    4: "VIERNES",
    5: "SABADO",
    6: "DOMINGO",
}


def _date_range(start: date, end: date) -> list[date]:
    d = start
    out: list[date] = []
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def _format_time_h_mm(h: int, m: int) -> str:
    return f"{h}:{m:02d}"


def build_daily_marks_table(
    entries: Iterable[LogEntry],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Construye una tabla por empleado y por día con todas las marcas del periodo,
    incluyendo días sin marcas (quedan en blanco).

    Returns:
        DataFrame con:
          No, Nombre, Fecha, DiaSemana, Marca1..MarcaN
    """
    # (emp_no, name) conjunto de empleados presentes
    employees: set[tuple[str, str]] = set()

    # Agrupar marcas por día
    buckets: Dict[Tuple[str, str, date], List[LogEntry]] = defaultdict(list)
    for e in entries:
        employees.add((e.emp_no, e.name))
        buckets[(e.emp_no, e.name, e.day)].append(e)

    all_days = _date_range(start_date, end_date)

    # Determinar max marcas en cualquier día para definir columnas Marca1..MarcaN
    max_marks = 0
    for key, day_entries in buckets.items():
        max_marks = max(max_marks, len(day_entries))

    rows: list[dict] = []
    for (emp_no, name) in sorted(employees):
        for d in all_days:
            day_entries = sorted(buckets.get((emp_no, name, d), []), key=lambda x: x.ts)
            times = [_format_time_h_mm(x.ts.hour, x.ts.minute) for x in day_entries]

            row = {
                "No": emp_no,
                "Nombre": name,
                "Fecha": d,
                "DiaSemana": _WEEKDAY_ES[d.weekday()],
            }
            for i in range(max_marks):
                row[f"Marca{i+1}"] = times[i] if i < len(times) else ""
            rows.append(row)

    df = pd.DataFrame(rows).sort_values(["No", "Fecha"]).reset_index(drop=True)
    return df


def build_week_table_for_employee(df_daily: pd.DataFrame, emp_no: str) -> pd.DataFrame:
    """
    Devuelve tabla “bonita” (DiaSemana + Marca1..MarcaN) para un empleado.
    """
    df_emp = df_daily[df_daily["No"] == str(emp_no)].copy()

    order_map = {name: idx for idx, name in enumerate(
        ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    )}
    df_emp["_w"] = df_emp["DiaSemana"].map(order_map).fillna(999).astype(int)

    df_emp = df_emp.sort_values(["Fecha", "_w"]).drop(columns=["_w"])

    marca_cols = [c for c in df_emp.columns if c.startswith("Marca")]
    return df_emp[["DiaSemana", *marca_cols]].reset_index(drop=True)
