# -*- coding: utf-8 -*-
"""
Conserta as descricoes que o gerador partiu em cima de aspas escapadas.

A fonte do LATAM escreve aspas dentro da descricao com barra invertida antes,
que e Lua valido. O gerador tratou isso como fim de string e cortou ali,
jogando fora o texto ENTRE as aspas e deixando uma string que nunca fecha.

O cliente morre ao carregar: "unfinished string near ...". Nao e aviso - e
caixa de erro e o itemInfo inteiro se perde.

Este script acha as linhas cuja string nao fecha, descobre de que item sao,
pega a linha correspondente no iteminfo_ptBR.lua e funde as duas de volta
numa so.

    python _corrigir_aspas.py           conserta
    python _corrigir_aspas.py --dry     so relata
"""
import re, sys
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parents[1]
NOSSO = RAIZ / 'SystemEN' / 'itemInfo_C.lua'
LATAM = AQUI / 'iteminfo_ptBR.lua'

BARRA = bytes([92])
ASPA_ESC = BARRA + b'"'

UM = re.compile(re.escape(BARRA) + rb'(\d{1,3})')
ESCAPES = re.compile(b'(?:' + re.escape(BARRA) + rb'\d{1,3})+')


def para_cp1252(linha):
    """Escape decimal de UTF-8 vira byte cp1252 cru, que e o que o nosso
    arquivo usa. Escape que nao for UTF-8 valido fica como esta."""
    def sub(m):
        crus = bytes(int(x) for x in UM.findall(m.group(0)))
        try:
            texto = crus.decode('utf-8')
        except UnicodeDecodeError:
            return m.group(0)
        try:
            return texto.encode('cp1252')
        except UnicodeEncodeError:
            return m.group(0)
    return ESCAPES.sub(sub, linha)


def fecha(s):
    """True se a string da linha fecha dentro dela - varredura como a do Lua,
    pulando o caractere seguinte a cada barra invertida."""
    i = s.find(b'"')
    if i < 0:
        return None
    i += 1
    while i < len(s):
        c = s[i:i + 1]
        if c == BARRA:
            i += 2
            continue
        if c == b'"':
            return True
        i += 1
    return False


linhas = NOSSO.read_bytes().split(b'\n')
ruins = [n for n, l in enumerate(linhas) if fecha(l) is False]
print('linhas com string que nao fecha: %d' % len(ruins))
if not ruins:
    raise SystemExit(0)

latam = LATAM.read_bytes()
consertadas, falhas = 0, []

for n in ruins:
    item = None
    for k in range(n, -1, -1):
        m = re.match(rb'\s*\[(\d+)\]\s*=\s*\{', linhas[k])
        if m:
            item = m.group(1)
            break
    if item is None:
        falhas.append((n, 'nao achei o item dono da linha'))
        continue

    mi = re.search(rb'\[' + item + rb'\]\s*=\s*\{', latam)
    if not mi:
        falhas.append((n, 'item %s ausente no LATAM' % item.decode()))
        continue
    bloco = latam[mi.start():mi.start() + 6000]
    # (?<!un) porque identifiedDescriptionName e substring de unidentified...
    # E a armadilha que docs/traducao.md ja registrava.
    md = re.search(rb'(?<!un)identifiedDescriptionName\s*=\s*\{(.*?)\n\s*\}', bloco, re.S)
    if not md:
        falhas.append((n, 'item %s sem descricao identificada no LATAM' % item.decode()))
        continue

    corpo = linhas[n].strip()
    if ASPA_ESC not in corpo:
        falhas.append((n, 'formato inesperado'))
        continue
    prefixo = corpo[1:corpo.rfind(ASPA_ESC)]

    escolhida = None
    for cand in md.group(1).split(b'\n'):
        cand = para_cp1252(cand.strip())
        if ASPA_ESC in cand and cand.startswith(b'"' + prefixo):
            escolhida = cand
            break
    if escolhida is None:
        falhas.append((n, 'nao casei o prefixo dentro do item %s' % item.decode()))
        continue
    if not escolhida.endswith(b','):
        escolhida += b','
    if fecha(escolhida) is not True:
        falhas.append((n, 'a linha do LATAM tambem nao fecha'))
        continue

    recuo = linhas[n][:len(linhas[n]) - len(linhas[n].lstrip())]
    print('  item %-7s linhas %d+%d -> 1' % (item.decode(), n + 1, n + 2))
    linhas[n] = recuo + escolhida
    linhas[n + 1] = None

print()
print('consertadas: %d | falhas: %d' % (len(ruins) - len(falhas), len(falhas)))
for n, motivo in falhas:
    print('  [!!] linha %d: %s' % (n + 1, motivo))

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada gravado')
    raise SystemExit(0)
if falhas:
    print()
    print('>>> nada gravado: resolva as falhas antes')
    raise SystemExit(1)

novas = [l for l in linhas if l is not None]
(NOSSO.parent / (NOSSO.name + '.antes-aspas')).write_bytes(NOSSO.read_bytes())
NOSSO.write_bytes(b'\n'.join(novas))
print()
print('gravado: %s (%d linhas, %d a menos)' % (NOSSO.name, len(novas), len(linhas) - len(novas)))
