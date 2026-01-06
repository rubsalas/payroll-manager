"""
app.parsing.logs_parser

Parser del sheet "Logs".

Convierte el layout tipo calendario por empleado en una lista normalizada de LogEntry.

Novedad:
- Ahora también extrae el rango del periodo (start_date y end_date) desde la fila "Period".
- Se agrega parse_with_period() para devolver (entries, period_info).
- parse() se mantiene por compatibilidad (devuelve solo entries).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Tuple

import pandas as pd

from app.domain.models import LogEntry


@dataclass(frozen=True)
class PeriodInfo:
    """Información del periodo detectado en el XLS."""
    start_date: date
    end_date: date


class PeriodExtractor:
    """
    Extrae el periodo desde un texto tipo:
        '2025/01/18 ~ 01/25'
    donde la parte final viene sin año.

    Soporta cruce de mes/año (si end_month < start_month => year+1).
    """

    PERIOD_RE = re.compile(r"(\d{4})/(\d{2})/(\d{2})\s*~\s*(\d{2})/(\d{2})")

    def extract(self, raw: pd.DataFrame) -> PeriodInfo:
        col0 = raw[0].astype(str)
        matches = raw.index[col0.str.contains("Period", na=False)]
        if len(matches) == 0:
            raise ValueError("No encontré la fila 'Period' en la hoja Logs.")

        r = int(matches[0])
        text = str(raw.loc[r, 2])  # en tu archivo suele estar en col 2

        m = self.PERIOD_RE.search(text)
        if not m:
            raise ValueError(f"No pude parsear el periodo desde: {text!r}")

        start_y = int(m.group(1))
        start_m = int(m.group(2))
        start_d = int(m.group(3))

        end_m = int(m.group(4))
        end_d = int(m.group(5))

        end_y = start_y
        if end_m < start_m:
            end_y = start_y + 1  # cruce de año

        start_date = date(start_y, start_m, start_d)
        end_date = date(end_y, end_m, end_d)

        return PeriodInfo(start_date=start_date, end_date=end_date)


class LogsSheetParser:
    """
    Parser principal del sheet "Logs".

    Args:
        no_col: Columna del "No" del empleado.
        name_col: Columna del "Name".
    """

    TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")

    def __init__(self, no_col: int = 2, name_col: int = 10) -> None:
        self.no_col = no_col
        self.name_col = name_col

    def parse_with_period(self, raw: pd.DataFrame) -> tuple[list[LogEntry], PeriodInfo]:
        """
        Parsea el sheet y devuelve las marcas + el periodo (start/end).

        Returns:
            (entries, period_info)
        """
        period = PeriodExtractor().extract(raw)

        no_rows = raw.index[raw[0].astype(str).eq("No :")]
        entries: List[LogEntry] = []

        for r in no_rows:
            r = int(r)
            date_row = r - 1
            logs_row = r + 1
            if date_row < 0 or logs_row >= len(raw):
                continue

            emp_no = raw.loc[r, self.no_col]
            name = raw.loc[r, self.name_col]

            emp_no_str = str(emp_no).strip()
            name_str = "" if pd.isna(name) else str(name).strip()

            day_cols = self._find_day_columns(raw, date_row)

            for c, day_int in day_cols:
                cell = raw.loc[logs_row, c]
                if pd.isna(cell):
                    continue

                marks = [t.strip() for t in str(cell).splitlines() if t.strip()]

                order = 0
                for t in marks:
                    if not self.TIME_RE.match(t):
                        continue
                    hh, mm = map(int, t.split(":"))

                    # OJO: el XLS usa un solo mes dentro del periodo en tu archivo.
                    # Usamos el mes/año del start_date.
                    ts = datetime(period.start_date.year, period.start_date.month, day_int, hh, mm)

                    order += 1
                    entries.append(
                        LogEntry(
                            emp_no=emp_no_str,
                            name=name_str,
                            day=ts.date(),
                            time_str=t,
                            ts=ts,
                            order_in_day=order,
                        )
                    )

        entries.sort(key=lambda e: (e.emp_no, e.day, e.ts))
        return entries, period

    def parse(self, raw: pd.DataFrame) -> list[LogEntry]:
        """
        Compatibilidad: devuelve solo entries.
        """
        entries, _ = self.parse_with_period(raw)
        return entries

    def _find_day_columns(self, raw: pd.DataFrame, date_row: int) -> List[Tuple[int, int]]:
        """
        Encuentra columnas que tienen un día 1..31 en la fila date_row.
        """
        out: List[Tuple[int, int]] = []
        for c in range(raw.shape[1]):
            v = raw.loc[date_row, c]
            if pd.isna(v):
                continue
            try:
                day_int = int(float(v))
            except Exception:
                continue
            if 1 <= day_int <= 31:
                out.append((c, day_int))
        return out
