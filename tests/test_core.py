import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from instrument_log_parser.cli import main
from instrument_log_parser.core import Parser, columns_of, load_config

EX = os.path.join(os.path.dirname(__file__), "..", "examples")
CONFIG = load_config(os.path.join(EX, "plate_reader.json"))
with open(os.path.join(EX, "run1.log"), encoding="utf-8") as fh:
    LOG = fh.read()


class ParserTests(unittest.TestCase):
    def test_rows_carry_context(self):
        rows, warnings = Parser(CONFIG).parse_text(LOG)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["sample"], "S-001")
        self.assertEqual(rows[2]["sample"], "S-002")
        self.assertEqual(rows[2]["wavelength_nm"], "600")
        self.assertEqual(rows[0]["run_date"], "2026-03-01")

    def test_decimal_comma_and_numeric_warning(self):
        rows, warnings = Parser(CONFIG).parse_text(LOG, "run1.log")
        self.assertEqual(rows[0]["od"], "0.112")
        self.assertEqual(len(warnings), 1)
        self.assertIn("run1.log:9", warnings[0])

    def test_reset_clears_context(self):
        rows, _ = Parser(CONFIG).parse_text(LOG + "\n10:00:00  T=25,0 C  OD=0,5\n")
        self.assertNotIn("sample", rows[-1])

    def test_findall_and_requires_record_rule(self):
        p = Parser({"record": [{"pattern": r"(?P<k>\w)=(?P<v>\d)", "findall": True}], "numeric": ["v"]})
        rows, _ = p.parse_text("a=1 b=2 c=3")
        self.assertEqual([(r["k"], r["v"]) for r in rows], [("a", "1"), ("b", "2"), ("c", "3")])
        with self.assertRaises(ValueError):
            Parser({"context": []})

    def test_columns_order(self):
        self.assertEqual(columns_of([{"_line": 1, "a": 1}, {"b": 2, "_rule": "x"}]), ["a", "b", "_line", "_rule"])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "tidy.csv")
            with redirect_stderr(io.StringIO()):
                code = main([os.path.join(EX, "plate_reader.json"), os.path.join(EX, "*.log"), "-o", out, "--no-meta"])
            self.assertEqual(code, 1)
            with open(out, encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[1]["od"], "0.135")
            self.assertNotIn("_line", rows[0])


if __name__ == "__main__":
    unittest.main()
