from . import data_apps

def table(title, headers, rows):
    return {'title': title, 'headers': headers, 'rows': rows}

def enrich(path, data, result):
    """Attach diagnostics without changing existing response fields."""
    tables, notes = ([], [])
    headers, rows = data_apps.parse(data)
    options = data.get('options', {})
    audit, seen = ([], {})
    output_number = 1
    for record, original in enumerate(rows, 2):
        row = [v.strip() for v in original] if options.get('trim', True) else original[:]
        changed = [headers[i] for i, (a, b) in enumerate(zip(original, row)) if a != b]
        key = tuple(row)
        duplicate_of = ''
        if options.get('drop_empty', True) and all((not v.strip() for v in row)):
            action = 'Dropped blank row'
            output_record = ''
        elif options.get('deduplicate', True) and key in seen:
            action = 'Removed duplicate'
            duplicate_of = seen[key]
            output_record = ''
        else:
            seen.setdefault(key, record)
            output_number += 1
            output_record = output_number
            action = 'Trimmed' if changed else 'Unchanged'
        audit.append([record, action, output_record, duplicate_of, ', '.join(changed)])
    result['row_audit'] = audit
    result['audit_csv'] = data_apps.safe_csv(['source_record', 'action', 'output_record', 'duplicate_of', 'trimmed_columns'], [[str(v) for v in row] for row in audit])
    tables = [table('Cleaning provenance · first 50 records', ['Source record', 'Action', 'Output record', 'Duplicate of', 'Trimmed columns'], audit[:50])]
    notes = ['Record numbers include the header as record 1. Audit exports contain all records; original field values are omitted. A duplicate points to the first retained source record.']
    if tables or notes:
        result['capabilities'] = {'tables': tables, 'notes': notes}
    return result
