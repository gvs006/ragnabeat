# -*- coding: utf-8 -*-
"""
Gera db/import/item_db.yml com os nomes de item em PT-BR, para o @ii funcionar
com acento.

O @ii compara com o nome que esta no BANCO DO SERVIDOR, nao com o que o cliente
mostra. Por isso traduzir o itemInfo_C.lua nao bastou: o cliente exibia
"Pocao Vermelha" e o servidor continuava com "Red Potion".

Fonte: o proprio itemInfo_C.lua, que ja tem os 5.296 nomes em PT-BR e ja esta
em cp1252. Casamento por ID do item - o mesmo criterio que funcionou no cliente.

Encoding: grava em cp1252. O rAthena le os .yml com rapidyaml, zero-copy sobre
o buffer bruto, entao os bytes atravessam intactos. Medido em 11/ago/2026.
Ver docs/encoding.md.

    python gen_nomes_servidor.py            gera
    python gen_nomes_servidor.py --dry      so relata, nao grava
"""
import re, sys, glob
from pathlib import Path

BS = chr(92)
LIMITE = 49          # ITEM_NAME_LENGTH e 50, menos o terminador


def achar_cliente():
    for d in Path(__file__).resolve().parents:
        if (d / 'DATA.ini').exists() and (d / 'SystemEN').is_dir():
            return d
    raise SystemExit('nao achei a pasta do cliente')


def achar_servidor():
    for base in (Path(r'C:/IT/repo/ragnabeat'),):
        if (base / 'db' / 'pre-re').is_dir():
            return base
    raise SystemExit('nao achei o repositorio do servidor')


CLIENTE = achar_cliente()
SERVIDOR = achar_servidor()

# --- 1. o que o servidor tem -------------------------------------------------
RE_ITEM = re.compile(
    r'^  - Id:\s*(\d+)\s*$\n\s*AegisName:\s*(\S+)\s*$\n\s*Name:\s*(.+?)\s*$',
    re.M)

srv = {}
for p in sorted(glob.glob(str(SERVIDOR / 'db' / 'pre-re' / 'item_db*.yml'))):
    txt = open(p, 'rb').read().decode('latin-1')
    for m in RE_ITEM.finditer(txt):
        srv[int(m.group(1))] = (m.group(2), m.group(3).strip('"\''))

# --- 2. o que o cliente tem em PT-BR ----------------------------------------
RE_BLOCO = re.compile(r'\[(\d+)\]\s*=\s*\{(.*?)\n\t\}', re.S)
# O (?<!un) e obrigatorio: "unidentifiedDisplayName" contem
# "identifiedDisplayName" como substring, e sem o lookbehind o regex casa com o
# nome do item NAO-IDENTIFICADO - que em boa parte dos itens e string vazia.
RE_NOME = re.compile(r'(?<!un)identifiedDisplayName\s*=\s*"((?:[^"' + BS + BS + r']|' + BS + BS + r'.)*)"')
RE_COR = re.compile(r'\^[0-9a-fA-F]{6}')

cli = {}
txt = open(CLIENTE / 'SystemEN' / 'itemInfo_C.lua', 'rb').read().decode('cp1252')
for m in RE_BLOCO.finditer(txt):
    n = RE_NOME.search(m.group(2))
    if n:
        nome = RE_COR.sub('', n.group(1)).replace(BS + '"', '"').strip()
        if nome:
            cli[int(m.group(1))] = nome

# --- 3. cruzar ---------------------------------------------------------------
comuns = sorted(set(srv) & set(cli))
longos = [i for i in comuns if len(cli[i]) > LIMITE]
iguais = [i for i in comuns if cli[i] == srv[i][1]]
usar = [i for i in comuns if i not in longos and i not in iguais]

print('servidor pre-re : %d itens' % len(srv))
print('cliente PT-BR   : %d itens' % len(cli))
print('em comum        : %d (%.1f%% do servidor)' % (len(comuns), 100.0 * len(comuns) / len(srv)))
print('  ja identicos  : %d (nao precisam de override)' % len(iguais))
print('  acima de %d ch: %d (pulados - estourariam ITEM_NAME_LENGTH)' % (LIMITE, len(longos)))
print('  a gravar      : %d' % len(usar))
print('sem traducao    : %d itens do servidor ficam em ingles' % (len(srv) - len(comuns)))

if longos:
    print()
    print('  exemplos pulados por tamanho:')
    for i in longos[:3]:
        print('    %6d (%d ch) %s' % (i, len(cli[i]), cli[i][:60]))

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada gravado')
    raise SystemExit(0)

# --- 4. gravar ---------------------------------------------------------------
def yaml_str(s):
    """Aspas duplas com escape - cobre : # - e acento sem depender de heuristica."""
    return '"' + s.replace(BS, BS + BS).replace('"', BS + '"') + '"'


linhas = [
    '# Nomes de item em PT-BR - gerado por DEVTOOLS/PTBR/gen_nomes_servidor.py',
    '#',
    '# NAO EDITE A MAO: regenere. A fonte e o itemInfo_C.lua do cliente, casado',
    '# por ID do item.',
    '#',
    '# Existe para o @ii encontrar por nome acentuado. O @ii compara com o nome',
    '# do BANCO, nao com o que o cliente mostra.',
    '#',
    '# Encoding: cp1252, sem BOM. O rapidyaml passa os bytes intactos.',
    '# Ver docs/encoding.md.',
    '',
    'Header:',
    '  Type: ITEM_DB',
    '  Version: 3',
    '',
    'Body:',
]
for i in usar:
    aegis, _ = srv[i]
    linhas.append('  - Id: %d' % i)
    linhas.append('    AegisName: %s' % aegis)
    linhas.append('    Name: %s' % yaml_str(cli[i]))

destino = SERVIDOR / 'db' / 'import' / 'item_db.yml'
destino.write_bytes(('\n'.join(linhas) + '\n').encode('cp1252'))
print()
print('gravado: %s (%d itens, %d bytes)' % (destino, len(usar), destino.stat().st_size))
