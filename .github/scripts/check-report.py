import json
import os
import re
import sys
from pathlib import Path

UNITS = {'ns': 1e-9, 'µs': 1e-6, 'us': 1e-6, 'ms': 1e-3, 's': 1.0}
SUMMARY = re.compile(r'experimental checks (.+): (\d+) attempted, (\d+) failures, (\d+) fallbacks')
WALL = 'Elapsed (wall clock) time'


def seconds(text):
    match = re.fullmatch(r'([0-9.]+)(ns|µs|us|ms|s)', text)
    return float(match.group(1)) * UNITS[match.group(2)] if match else None


def clock_seconds(text):
    total = 0.0
    for part in text.split(':'):
        total = total * 60 + float(part)
    return total


def duration(value):
    return f'{int(value // 60)}m {value % 60:.1f}s' if value >= 60 else f'{value:.2f}s'


class Trace:
    def __init__(self, path):
        self.completed = 0
        self.pending = None
        self.error = None
        self.summary = None
        self.timing = {}
        for line in path.read_text().splitlines():
            self.feed(line)

    def feed(self, line):
        kind, _, rest = line.partition(' ')
        if kind == 'start':
            index = int(rest.split()[0])
            if self.pending is not None or index != self.completed:
                self.error = 'Missing, repeated or out-of-order declaration start'
            self.pending = index
        elif kind == 'end':
            index = int(rest.split()[0])
            if self.pending != index or index != self.completed:
                self.error = 'Missing, repeated or out-of-order declaration completion'
            self.pending = None
            self.completed += 1
        elif kind == 'import':
            self.time('import_seconds', rest.split()[0])
        elif match := SUMMARY.fullmatch(line):
            self.summary = dict(zip(('attempted', 'failures', 'fallbacks'), map(int, match.groups()[1:])))
            self.time('check_seconds', match.group(1))

    def time(self, key, text):
        if (value := seconds(text)) is not None:
            self.timing[key] = value


def main():
    report = Path(sys.argv[1])
    status = int(sys.argv[2])
    expected = int(os.environ['DECLARATIONS'])
    trace = Trace(report / 'trace.log')
    timing = dict(trace.timing)
    time_file = report / 'time.txt'
    if time_file.exists():
        for line in time_file.read_text().splitlines():
            if WALL in line:
                timing['wall_seconds'] = clock_seconds(line.rsplit(' ', 1)[1])
    complete = (status == 0 and trace.completed == expected and trace.pending is None
                and trace.summary == {'attempted': expected, 'failures': 0, 'fallbacks': 0}
                and not (report / 'failures.log').stat().st_size)
    error = trace.error or (None if complete else 'Incomplete or unsuccessful corpus check')
    result = {
        'status': 'failed' if error else 'checked',
        'declarations': trace.completed,
        'exit_code': status,
        'sha256': Path(sys.argv[3]).read_text().split()[0],
        **(trace.summary or {}),
        **timing,
    }
    if error:
        result['error'] = error
    (report / 'result.json').write_text(json.dumps(result, indent=2) + '\n')

    rows = [('Status', result['status']), ('Declarations', f'{trace.completed:,}')]
    if trace.summary:
        rows.append(('Checked', '{attempted:,} attempted, {failures:,} failures, {fallbacks:,} fallbacks'
                     .format(**trace.summary)))
    for key, label in (('wall_seconds', 'Wall time'), ('import_seconds', 'Import'), ('check_seconds', 'Check')):
        if key in timing:
            rows.append((label, duration(timing[key])))
    rows += [('Exit code', str(status)), ('Export SHA-256', result['sha256'])]
    if error:
        rows.append(('Error', error))
    text = ''.join(f'{label:<16}{value}\n' for label, value in rows)
    (report / 'summary.txt').write_text(text)
    print(text, end='')
    if 'wall_seconds' in timing:
        line = f"Wall time {duration(timing['wall_seconds'])}"
        if {'import_seconds', 'check_seconds'} <= timing.keys():
            line += f" (import {timing['import_seconds']:.1f}s, check {timing['check_seconds']:.1f}s)"
        (report / 'wall.txt').write_text(line + '\n')
    if error:
        raise SystemExit(1)


main()
