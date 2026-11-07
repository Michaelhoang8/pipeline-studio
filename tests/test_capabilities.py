import json
import csv
import io
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from portfolio import capabilities as c, data_apps as d
from portfolio.db import initialize, connect, SCHEMA
from portfolio.validation import ValidationError, NotFoundError

def enhanced(path, data, function):
    return c.enrich(path, data, function(data))

class AnalysisCapabilities(unittest.TestCase):

    def test_clean_provenance_reconciles_and_escapes_headers(self):
        data = {'csv': '=name,value\n A , 1 \nA,1\n,\nB,2\n'}
        r = enhanced('/api/data/clean', data, d.clean)
        self.assertEqual(r['row_audit'][0][1:3], ['Trimmed', 2])
        self.assertEqual(r['row_audit'][1][1:4], ['Removed duplicate', '', 2])
        self.assertEqual(r['row_audit'][2][1], 'Dropped blank row')
        self.assertEqual(r['row_audit'][3][2], 3)
        self.assertIn("'=name", r['audit_csv'])

    def test_clean_audit_with_disabled_steps(self):
        data = {'csv': 'x\n a \na\na\n', 'options': {'trim': False, 'deduplicate': False}}
        r = enhanced('/api/data/clean', data, d.clean)
        self.assertTrue(all((row[1] == 'Unchanged' for row in r['row_audit'])))
        self.assertEqual(r['output_rows'], 3)
if __name__ == '__main__':
    unittest.main()
