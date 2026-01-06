"""
app.io.excel_reader

Lectura de archivos Excel.

Este módulo está aislado para que el resto del proyecto NO dependa de detalles
de cómo se lee un Excel (.xls, .xlsx, engine, etc.).

Actualmente:
- El archivo es .XLS (formato binario viejo), por eso usamos engine="xlrd".

Si en el futuro migras a .XLSX:
- podrías reemplazar engine por "openpyxl" o ajustar la implementación aquí.
"""

from __future__ import annotations

from typing import List

import pandas as pd


class ExcelReader:
    """
    Encapsula operaciones comunes de lectura de Excel.

    Args:
        path: Ruta al archivo Excel.

    Notes:
        - Para .XLS usamos xlrd.
        - Leemos "crudo" (header=None) para no perder el layout original.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def list_sheets(self) -> List[str]:
        """
        Lista nombres de hojas disponibles en el archivo.

        Returns:
            Lista de strings con los nombres de hojas.
        """
        xls = pd.ExcelFile(self.path, engine="xlrd")
        return list(xls.sheet_names)

    def read_sheet_raw(self, sheet_name: str) -> pd.DataFrame:
        """
        Lee una hoja como DataFrame "crudo" (sin headers).

        Args:
            sheet_name: Nombre de la hoja a leer.

        Returns:
            DataFrame con celdas tal cual vienen del Excel.

        Raises:
            ValueError: Si la hoja no existe o si hay error de lectura.
        """
        return pd.read_excel(
            self.path,
            sheet_name=sheet_name,
            engine="xlrd",
            header=None,
        )
