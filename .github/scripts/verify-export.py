import hashlib
import json
import os
import sys

DECLARATIONS = ('axiom', 'def', 'thm', 'opaque', 'quot')
PREFIXES = tuple(f'{{"{key}":'.encode() for key in ('in', *DECLARATIONS, 'inductive'))


def check_metadata(meta):
    expected = {
        ('format', 'version'): os.environ['EXPORT_FORMAT'],
        ('lean', 'version'): os.environ['LEAN_VERSION'],
        ('lean', 'githash'): os.environ['LEAN_GITHASH'],
        ('exporter', 'name'): 'olean-export',
        ('exporter', 'version'): os.environ['EXPORTER_VERSION'],
    }
    actual = {(a, b): meta[a][b] for a, b in expected}
    if actual != expected:
        raise SystemExit(f'Unexpected export metadata: {meta}')


def name_of(names, record):
    if 'str' in record:
        node = record['str']
        segment = json.dumps(node['str'], ensure_ascii=False)
    else:
        node = record['num']
        segment = str(node['i'])
    return f"{names[node['pre']]}/{segment}"


def declarations(path):
    names = {0: ''}
    with open(path, 'rb') as source:
        check_metadata(json.loads(next(source))['meta'])
        for line in source:
            if not line.startswith(PREFIXES):
                continue
            record = json.loads(line)
            if 'in' in record:
                names[record['in']] = name_of(names, record)
            for kind in DECLARATIONS:
                if kind in record:
                    yield names[record[kind]['name']]
            if 'inductive' in record:
                for kind in ('types', 'ctors', 'recs'):
                    yield from (names[d['name']] for d in record['inductive'][kind])


def main():
    found = sorted(declarations(sys.argv[1]))
    coverage = hashlib.sha256(('\n'.join(found) + '\n').encode()).hexdigest()
    if (len(found), coverage) != (int(os.environ['DECLARATIONS']), os.environ['COVERAGE']):
        raise SystemExit(f'Export coverage mismatch: {len(found)} declarations, {coverage}')
    print(f"Verified Lean {os.environ['LEAN_VERSION']}: {len(found)} declaration names; coverage {coverage}")


main()
