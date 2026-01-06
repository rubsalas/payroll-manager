"""
app.config

Configuración centralizada del proyecto.

Este módulo evita valores "hardcodeados" repetidos en muchos archivos.
Aquí defines parámetros de layout del Excel y reglas generales del parseo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """
    Configuración de la aplicación.

    Attributes:
        sheet_logs: Nombre del sheet con las marcas.
        no_col: Columna donde se encuentra el número/ID del empleado en la fila "No :".
        name_col: Columna donde se encuentra el nombre del empleado.
        expected_marks_per_day: Cantidad esperada de marcas por día (para validación).
    """
    sheet_logs: str = "Logs"
    no_col: int = 2
    name_col: int = 10

    # Regla de negocio (según lo que pediste): deben ser 4 marcas por día.
    expected_marks_per_day: int = 4
