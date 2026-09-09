from pathlib import Path
import tempfile
import unittest

from records import ValidationError, add_record, extract_onpe_record, initialize, list_records, remove_record, validate_record


def example():
    # Datos sintéticos exclusivos de las pruebas; nunca se cargan en la aplicación.
    return dict(dni="00123456", miembro="Sí", nombres="Persona de prueba", region="Región de prueba",
                provincia="Provincia de prueba", distrito="Distrito de prueba", direccion="Local de prueba",
                confirmed=True, operator_is_member=True)


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = str(Path(self.directory.name) / "test.sqlite3")
        initialize(self.database)

    def test_preserves_dni_leading_zeros_and_persists(self):
        add_record(self.database, example())
        initialize(self.database)
        self.assertEqual(list_records(self.database)[0]["dni"], "00123456")

    def test_duplicate_is_rejected(self):
        add_record(self.database, example())
        with self.assertRaises(ValidationError):
            add_record(self.database, example())
        self.assertEqual(len(list_records(self.database)), 1)

    def test_requires_real_consultation_confirmation(self):
        for field in ("confirmed", "operator_is_member"):
            value = example()
            value[field] = False
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_record(value)

    def test_rejects_invalid_dni(self):
        for dni in ("123", "123456789", "1234567X", "１２３４５６７８"):
            value = example()
            value["dni"] = dni
            with self.subTest(dni=dni), self.assertRaises(ValidationError):
                validate_record(value)

    def test_rejects_missing_fields_and_non_objects(self):
        with self.assertRaises(ValidationError):
            validate_record(None)
        value = example()
        del value["direccion"]
        with self.assertRaises(ValidationError):
            validate_record(value)

    def test_delete_only_selected_record(self):
        add_record(self.database, example())
        self.assertFalse(remove_record(self.database, "' OR 1=1 --"))
        self.assertEqual(len(list_records(self.database)), 1)
        self.assertTrue(remove_record(self.database, "00123456"))
        self.assertEqual(list_records(self.database), [])

    def test_extracts_real_definitiva_shape(self):
        result = extract_onpe_record({"success": True, "data": {
            "dni": "00123456", "nombres": "ANA", "apellidos": "PEREZ",
            "ubigeo": "LIMA / LIMA / ATE", "direccion": "CALLE 1",
            "cargo": "NO ERES MIEMBRO DE MESA", "miembroMesa": False,
        }})
        self.assertEqual(result["nombres"], "ANA PEREZ")
        self.assertEqual(result["distrito"], "ATE")
        self.assertEqual(result["miembro"], "No")

    def test_extract_rejects_waf_or_incomplete_payload(self):
        with self.assertRaises(ValidationError):
            extract_onpe_record({"success": True, "data": {"token": "[REDACTADO]"}})


if __name__ == "__main__":
    unittest.main()
