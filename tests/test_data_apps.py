import csv
import io
import json
import unittest
from portfolio import data_apps as d
from portfolio.validation import ValidationError

class DataTests(unittest.TestCase):

    def test_csv_quotes_bom_and_embedded_newline(self):
        headers, rows = d.parse({'csv': '\ufeffname,note\nAda,"hello, world\nsecond line"\n'})
        self.assertEqual(headers, ['name', 'note'])
        self.assertEqual(rows, [['Ada', 'hello, world\nsecond line']])

    def test_csv_rejects_invalid_shapes_and_limits(self):
        for source in ['', 'x,x\n1,2', 'x,\n1,2', 'x,y\n1', 'x\n"unterminated', 'x\n' + '1\n' * 5001, 'x\n' + 'a' * 1000001]:
            with self.subTest(source=source[:30]), self.assertRaises(ValidationError):
                d.parse({'csv': source})

    def test_clean_order_and_formula_export(self):
        result = d.clean({'csv': 'name,amount\n Ada , 10 \nAda,10\n,\n=1+1,-20\n'})
        self.assertEqual((result['output_rows'], result['duplicates_removed'], result['empty_rows_removed']), (2, 1, 1))
        exported = list(csv.reader(io.StringIO(result['csv'])))
        self.assertEqual(exported[-1], ["'=1+1", '-20'])
        again = d.clean({'csv': result['csv']})
        self.assertEqual(again['csv'], result['csv'])

    def test_disabled_clean_steps_preserve_cells(self):
        r = d.clean({'csv': 'x\n a \n a \n', 'options': {'trim': False, 'deduplicate': False, 'drop_empty': False}})
        self.assertEqual(r['preview'], [[' a '], [' a ']])
        with self.assertRaises(ValidationError):
            d.clean({'csv': 'x\n1', 'options': {'trim': 'false'}})
