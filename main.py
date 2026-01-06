"""
main.py

CLI principal.

Flujo:
1) Lee argumentos (--file, --out, --out_summary, --out_issues, --out_table, --emp_no)
2) Valida que exista la hoja Logs
3) Lee el sheet Logs "crudo" (sin headers)
4) Parsea a List[LogEntry]
5) Exporta logs normalizados a CSV
6) Genera resumen diario y marca needs_review si #marcas != expected_marks_per_day
7) Exporta CSV con resumen diario y CSV con solo los casos a revisar
8) Genera tabla tipo "LUNES 7:30 11:13 12:13 17:00" (todas las marcas) y la exporta
9) (Opcional) imprime en consola la tabla para un empleado específico

Uso:
    python main.py --file "001_2025_1_MON.XLS"

Ejemplos:
    # Exportar todos con nombres por defecto
    python main.py --file "files/001_2025_1_MON.XLS"

    # Elegir rutas específicas
    python main.py --file "files/test2.XLS" --out logs.csv --out_table tabla.csv

    # Imprimir la tabla "bonita" para un empleado en consola
    python main.py --file "files/001_2025_1_MON.XLS" --emp_no 12

"""

from __future__ import annotations

import argparse
from typing import List, Optional

import pandas as pd

from app.config import AppConfig
from app.io.excel_reader import ExcelReader
from app.parsing.logs_parser import LogsSheetParser
from app.processing.summaries import summarize_days
from app.processing.tables import build_daily_marks_table, build_week_table_for_employee


def entries_to_dataframe(entries) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "No": e.emp_no,
                "Nombre": e.name,
                "Fecha": e.day,
                "Hora": e.time_str,
                "Datetime": e.ts,
                "Orden_en_dia": e.order_in_day,
            }
            for e in entries
        ]
    )


def summaries_to_dataframe(summaries) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "No": s.emp_no,
                "Nombre": s.name,
                "Fecha": s.day,
                "Primera": s.first_ts,
                "Ultima": s.last_ts,
                "Marcas": s.marks,
                "Revisar": s.needs_review,
                "Motivo": s.review_reason,
            }
            for s in summaries
        ]
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parser de XLS (sheet Logs) -> CSV normalizado.")
    parser.add_argument("--file", required=True, help="Ruta al archivo .XLS")

    parser.add_argument("--out", default="logs_limpios.csv", help="CSV de salida (logs normalizados)")
    parser.add_argument("--out_summary", default="resumen_diario.csv", help="CSV de salida (resumen diario)")
    parser.add_argument("--out_issues", default="revisar.csv", help="CSV de salida (solo casos a revisar)")
    parser.add_argument("--out_table", default="tabla_diaria_marcas.csv", help="CSV de salida (tabla por día)")

    parser.add_argument("--emp_no", default=None, help="ID de empleado para imprimir tabla en consola (opcional)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    cfg = AppConfig()

    reader = ExcelReader(args.file)
    sheets = reader.list_sheets()
    if cfg.sheet_logs not in sheets:
        raise ValueError(f"No existe la hoja {cfg.sheet_logs!r}. Hojas disponibles: {sheets}")

    raw = reader.read_sheet_raw(cfg.sheet_logs)

    parser_logs = LogsSheetParser(no_col=cfg.no_col, name_col=cfg.name_col)

    # IMPORTANTE: ahora obtenemos también el periodo
    entries, period = parser_logs.parse_with_period(raw)

    # Exportar logs normalizados (solo lo que existe)
    df_logs = entries_to_dataframe(entries)
    df_logs.to_csv(args.out, index=False)
    print(f"OK: exportado {len(df_logs)} filas a {args.out}")

    # Resumen diario INCLUYENDO días sin marcas
    day_summaries = summarize_days(
        entries,
        expected_marks=cfg.expected_marks_per_day,
        start_date=period.start_date,
        end_date=period.end_date,
    )
    df_sum = summaries_to_dataframe(day_summaries)
    df_sum.to_csv(args.out_summary, index=False)
    print(f"OK: exportado resumen diario a {args.out_summary}")

    # Casos a revisar (incluye marks=0)
    df_issues = df_sum[df_sum["Revisar"] == True].copy()
    df_issues.to_csv(args.out_issues, index=False)
    print(f"OK: exportado casos a revisar ({len(df_issues)}) a {args.out_issues}")

    # Tabla tipo tu ejemplo, INCLUYENDO días sin marcas
    df_table = build_daily_marks_table(entries, period.start_date, period.end_date)
    df_table.to_csv(args.out_table, index=False)
    print(f"OK: exportada tabla diaria (incluye días vacíos) a {args.out_table}")

    # (Opcional) imprimir tabla bonita para un empleado
    if args.emp_no is not None:
        df_pretty = build_week_table_for_employee(df_table, emp_no=str(args.emp_no))
        print("\nTabla estilo ejemplo para empleado:", args.emp_no)
        if len(df_pretty) == 0:
            print("(No se encontraron registros para ese empleado.)")
        else:
            print(df_pretty.to_string(index=False))


if __name__ == "__main__":
    main()
