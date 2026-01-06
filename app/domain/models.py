"""
app.domain.models

Modelos de dominio (dataclasses).

Estos modelos representan datos normalizados para cálculo y reportes.
El resto del sistema trabaja con estos modelos y no con Excel directamente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class LogEntry:
    """
    Representa una marca individual (timestamp) de un empleado.

    Attributes:
        emp_no: ID del empleado (string por robustez).
        name: Nombre del empleado.
        day: Fecha (YYYY-MM-DD).
        time_str: Hora original como texto (ej: "07:05").
        ts: Fecha+hora como datetime.
        order_in_day: Orden relativo de la marca en el día (1,2,3,...).
    """
    emp_no: str
    name: str
    day: date
    time_str: str
    ts: datetime
    order_in_day: int


@dataclass(frozen=True)
class DaySummary:
    """
    Resumen diario por empleado.

    Attributes:
        emp_no: ID del empleado.
        name: Nombre del empleado.
        day: Fecha del resumen.
        first_ts: Primera marca del día.
        last_ts: Última marca del día.
        marks: Cantidad de marcas detectadas.
        needs_review: True si no cumple la regla esperada (ej. no son 4 marcas).
        review_reason: Texto corto con el motivo (None si no aplica).
    """
    emp_no: str
    name: str
    day: date
    first_ts: Optional[datetime]
    last_ts: Optional[datetime]
    marks: int
    needs_review: bool
    review_reason: Optional[str]
