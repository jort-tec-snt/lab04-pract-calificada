"""Validación y almacenamiento local de los datos consultados en ONPE."""

from contextlib import contextmanager
from pathlib import Path
import re
import sqlite3


FIELDS = ("dni", "miembro", "nombres", "region", "provincia", "distrito", "direccion")
HEADERS = ("DNI", "Miembro de mesa", "Nombres", "Región", "Provincia", "Distrito", "Dirección del local de votación")


class ValidationError(ValueError):
    pass


def validate_record(data):
    if not isinstance(data, dict):
        raise ValidationError("La solicitud debe contener los datos del registro.")
    if data.get("operator_is_member") is not True:
        raise ValidationError("Primero confirma en el portal que eres miembro de mesa, según el enunciado.")
    if data.get("confirmed") is not True:
        raise ValidationError("Confirma que contrastaste los datos con la consulta electoral.")
    result = {}
    for field in FIELDS:
        value = data.get(field)
        if not isinstance(value, str):
            raise ValidationError(f"Completa el campo {field}.")
        value = value.strip()
        if not value or len(value) > (300 if field == "direccion" else 150):
            raise ValidationError(f"Revisa la longitud del campo {field}.")
        if any(ord(character) < 32 for character in value):
            raise ValidationError(f"El campo {field} contiene caracteres no válidos.")
        result[field] = value
    if not re.fullmatch(r"[0-9]{8}", result["dni"]):
        raise ValidationError("El DNI debe contener exactamente 8 dígitos.")
    if result["miembro"] not in ("Sí", "No"):
        raise ValidationError("Selecciona si la persona es miembro de mesa.")
    return result


@contextmanager
def connect(database):
    connection = sqlite3.connect(database, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize(database):
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with connect(database) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS registros (
            dni TEXT PRIMARY KEY,
            miembro TEXT NOT NULL CHECK (miembro IN ('Sí', 'No')),
            nombres TEXT NOT NULL,
            region TEXT NOT NULL,
            provincia TEXT NOT NULL,
            distrito TEXT NOT NULL,
            direccion TEXT NOT NULL
        )""")


def list_records(database):
    with connect(database) as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM registros ORDER BY nombres, dni")]


def add_record(database, data):
    record = validate_record(data)
    try:
        with connect(database) as connection:
            connection.execute("INSERT INTO registros VALUES (?, ?, ?, ?, ?, ?, ?)",
                               tuple(record[field] for field in FIELDS))
    except sqlite3.IntegrityError:
        raise ValidationError("Ese DNI ya está registrado. Revisa la lista antes de agregarlo nuevamente.") from None
    return record


def remove_record(database, dni):
    with connect(database) as connection:
        return connection.execute("DELETE FROM registros WHERE dni = ?", (dni,)).rowcount > 0
