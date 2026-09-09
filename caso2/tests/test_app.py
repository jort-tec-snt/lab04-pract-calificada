from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from openpyxl import load_workbook

from app import create_app
from records import HEADERS
from test_records import example


class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.directory.name) / "test.sqlite3")})
        self.client = self.app.test_client()

    def test_home_portal_and_health(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"https://consultaelectoral.onpe.gob.pe/inicio", response.data)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_export_contains_required_columns_and_literal_text(self):
        record = example()
        record["nombres"] = '=HYPERLINK("https://example.invalid")'
        self.assertEqual(self.client.post("/api/registros", json=record).status_code, 201)
        response = self.client.get("/exportar.xlsx")
        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(BytesIO(response.data))
        sheet = workbook.active
        self.assertEqual(tuple(cell.value for cell in sheet[1]), HEADERS)
        self.assertEqual(sheet["A2"].value, "00123456")
        self.assertEqual(sheet["C2"].value, record["nombres"])
        self.assertEqual(sheet["C2"].data_type, "s")
        workbook.close()

    def test_invalid_requests_and_empty_export(self):
        self.assertEqual(self.client.post("/api/registros", json={}).status_code, 400)
        self.assertEqual(self.client.get("/exportar.xlsx").status_code, 400)

    def test_create_list_duplicate_delete(self):
        record = example()
        self.assertEqual(self.client.post("/api/registros", json=record).status_code, 201)
        self.assertEqual(self.client.post("/api/registros", json=record).status_code, 400)
        self.assertEqual(len(self.client.get("/api/registros").json["records"]), 1)
        self.assertEqual(self.client.delete("/api/registros/00123456").status_code, 200)
        self.assertEqual(self.client.get("/api/registros").json["records"], [])


if __name__ == "__main__":
    unittest.main()
