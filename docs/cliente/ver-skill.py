# -*- coding: utf-8 -*-
"""Mostra o bloco de uma skill do skilldescript, com os escapes resolvidos."""
import io, re, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ALVO = Path(__file__).resolve().parents[2] / 'data' / 'luafiles514' / 'lua files' / 'skillinfoz' / 'skilldescript.lub'
d = ALVO.read_bytes().decode('latin-1')

ESC = re.compile(r'\\(\d{1,3})')


def resolve(t):
    return ESC.sub(lambda m: bytes([int(m.group(1))]).decode('cp1252', 'replace'), t)


for chave in sys.argv[1:] or ['SM_MAGNUM', 'AL_ANGELUS']:
    m = re.search(r'  \[SKID\.' + chave + r'\] = \{.*?\n  \},', d, re.S)
    if not m:
        print('%s: nao encontrado' % chave)
        continue
    print('=== %s ===' % chave)
    for linha in resolve(m.group()).split('\n'):
        # tira os codigos de cor para leitura
        print(re.sub(r'\^[0-9a-fA-F]{6}', '', linha).rstrip())
    print()
