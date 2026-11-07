import csv
import io
import re
from .validation import ValidationError

def parse(data):
    source = data.get('csv')
    if not isinstance(source, str) or not source.strip() or len(source.encode('utf-8')) > 1000000:
        raise ValidationError('Provide a nonempty UTF-8 CSV of at most 1 MB')
    try:
        reader = csv.reader(io.StringIO(source.lstrip('\ufeff')), strict=True)
        headers = [h.strip() for h in next(reader)]
        if not 1 <= len(headers) <= 50 or any((not h for h in headers)) or len(set(headers)) != len(headers):
            raise ValidationError('Use 1–50 unique, nonempty column names')
        records = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(headers):
                raise ValidationError(f'CSV line {reader.line_num}: expected {len(headers)} fields, got {len(row)}')
            records.append(row)
            if len(records) > 5000:
                raise ValidationError('CSV limit is 5,000 data rows')
        if not records:
            raise ValidationError('Include at least one data row')
        return (headers, records)
    except (csv.Error, StopIteration) as error:
        raise ValidationError(f'Invalid CSV: {error}') from error

def safe_csv(headers, records, *, include_header=True):

    def safe(value):
        if re.fullmatch('-[0-9]+(?:\\.[0-9]+)?', value):
            return value
        return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r')) else value
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    if include_header:
        writer.writerow([safe(h) for h in headers])
    writer.writerows([[safe(value) for value in row] for row in records])
    return output.getvalue()

def clean(data):
    headers, records = parse(data)
    options = data.get('options', {})
    if not isinstance(options, dict):
        raise ValidationError('options must be an object')
    for key in ('trim', 'deduplicate', 'drop_empty'):
        if key in options and type(options[key]) is not bool:
            raise ValidationError(f'{key} must be a boolean')
    output, seen = ([], set())
    trimmed = duplicates = empty = 0
    for original in records:
        row = [v.strip() for v in original] if options.get('trim', True) else original[:]
        trimmed += sum((a != b for a, b in zip(original, row)))
        if options.get('drop_empty', True) and all((not v.strip() for v in row)):
            empty += 1
            continue
        key = tuple(row)
        if options.get('deduplicate', True) and key in seen:
            duplicates += 1
            continue
        seen.add(key)
        output.append(row)
    return {'input_rows': len(records), 'output_rows': len(output), 'trimmed_cells': trimmed, 'duplicates_removed': duplicates, 'empty_rows_removed': empty, 'headers': headers, 'preview': output[:20], 'csv': safe_csv(headers, output)}
