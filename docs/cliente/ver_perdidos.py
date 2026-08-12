# -*- coding: utf-8 -*-
"""Lista os caracteres do fonte decompilado que nao cabem em cp1252."""
import re, io, sys, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ESCAPES = re.compile(r'(?:\\(\d{1,3}))+')
UM = re.compile(r'\\(\d{1,3})')

d = Path(sys.argv[1]).read_bytes().decode('latin-1')
sem = []
for m in ESCAPES.finditer(d):
    crus = bytes(int(x) for x in UM.findall(m.group(0)))
    try:
        t = crus.decode('utf-8')
    except UnicodeDecodeError:
        continue
    try:
        t.encode('cp1252')
    except UnicodeEncodeError:
        sem.append(t)

c = collections.Counter(sem)
print('sequencias sem equivalente em cp1252: %d  (distintas: %d)' % (len(sem), len(c)))
print()
for t, n in c.most_common(12):
    pontos = ' '.join('U+%04X' % ord(x) for x in t[:5])
    print('  %4dx  %-16r  %s' % (n, t, pontos))
