"""
app.processing.summaries

Procesamiento y validaciones sobre LogEntry.

Novedad:
- summarize_days puede recibir start_date/end_date y crear resúmenes aunque no existan marcas.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Iterable, List, Tuple, Optional

from app.domain.models import DaySummary, LogEntry


def _date_range(start: date, end: date) -> list[date]:
    """Rango inclusivo de fechas."""
    d = start
    out: list[date] = []
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def summarize_days(
    entries: Iterable[LogEntry],
    expected_marks: int = 4,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[DaySummary]:
    """
    Resume marcas por empleado y día y valida cantidad esperada.

    Si start_date y end_date se proporcionan, se incluyen también los días sin marcas:
        marks=0, needs_review=True (porque != expected_marks)

    Args:
        entries: Iterable de LogEntry.
        expected_marks: # de marcas esperadas por día (tu regla: 4).
        start_date: fecha inicio del periodo (opcional).
        end_date: fecha fin del periodo (opcional).

    Returns:
        Lista de DaySummary ordenada por empleado y fecha.
    """
    # Agrupar por (emp_no, name, day)
    buckets: dict[Tuple[str, str, date], list[datetime]] = defaultdict(list)
    employees: set[tuple[str, str]] = set()

    for e in entries:
        employees.add((e.emp_no, e.name))
        buckets[(e.emp_no, e.name, e.day)].append(e.ts)

    # Si no se pasa periodo, solo resumimos días presentes
    if start_date is None or end_date is None:
        keys = list(buckets.keys())
    else:
        all_days = _date_range(start_date, end_date)
        keys = [(emp_no, name, d) for (emp_no, name) in employees for d in all_days]

    out: List[DaySummary] = []
    for (emp_no, name, day) in keys:
        ts_list = buckets.get((emp_no, name, day), [])
        ts_list = sorted(ts_list)
        marks = len(ts_list)

        needs_review = (marks != expected_marks)
        reason = None
        if needs_review:
            reason = f"Se esperaban {expected_marks} marcas, pero se encontraron {marks}."

        out.append(
            DaySummary(
                emp_no=emp_no,
                name=name,
                day=day,
                first_ts=ts_list[0] if ts_list else None,
                last_ts=ts_list[-1] if ts_list else None,
                marks=marks,
                needs_review=needs_review,
                review_reason=reason,
            )
        )

    out.sort(key=lambda s: (s.emp_no, s.day))
    return out
