# -*- coding: utf-8 -*-
"""
Gera data\\msgstringtable.csv em PT-BR - a tabela que move a tela de login e a
maior parte do HUD.

O cliente le data\\msgstringtable.csv, 2 colunas em base64: chave,valor.
O RO LATAM traz data\\msgstringtable_ml.csv, 10 colunas - uma por idioma:

    0 chave   1 coreano   2 ingles   7 PORTUGUES   9 espanhol

Os payloads do LATAM estao em UTF-8; o nosso cliente renderiza cp1252, entao a
conversao acontece aqui. Nao assuma o encoding dos arquivos do LATAM - eles nao
sao uniformes. Ver docs/encoding.md.

Ordem de preferencia por chave: portugues, ingles, valor original.
Iteramos as chaves do NOSSO arquivo, para nao inventar chave que o cliente
nao conhece.

    python gen_msgstringtable.py           gera
    python gen_msgstringtable.py --dry     so relata
"""
import base64, sys
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parents[1]
NOSSO = AQUI / '_extraido' / 'msgstringtable.csv'
LATAM = AQUI / '_extraido' / 'msgstringtable_ml.csv'
DESTINO = RAIZ / 'data' / 'msgstringtable.csv'

COL_PT, COL_EN = 7, 2


def b64(x):
    try:
        return base64.b64decode(x)
    except Exception:
        return None


def carrega_latam():
    tab = {}
    for linha in LATAM.read_bytes().split(b'\n'):
        cols = linha.strip().split(b',')
        if len(cols) <= COL_PT:
            continue
        chave = b64(cols[0])
        if not chave:
            continue
        def pega(i):
            if i >= len(cols) or not cols[i]:
                return None
            crus = b64(cols[i])
            if not crus:
                return None
            try:
                return crus.decode('utf-8')
            except UnicodeDecodeError:
                return crus.decode('cp1252', 'replace')
        tab[chave] = (pega(COL_PT), pega(COL_EN))
    return tab


latam = carrega_latam()
print('LATAM: %d chaves' % len(latam))

saida, n_pt, n_en, n_orig, n_perda = [], 0, 0, 0, 0
for linha in NOSSO.read_bytes().split(b'\n'):
    cols = linha.strip().split(b',')
    if len(cols) < 2 or not cols[0]:
        continue
    chave_b, valor_b = cols[0], cols[1]
    chave = b64(chave_b)
    pt, en = latam.get(chave, (None, None))

    escolhido = None
    if pt and pt.strip():
        escolhido, n_pt = pt, n_pt + 1
    elif en and en.strip():
        escolhido, n_en = en, n_en + 1

    if escolhido is None:
        novo = valor_b
        n_orig += 1
    else:
        try:
            novo = base64.b64encode(escolhido.encode('cp1252'))
        except UnicodeEncodeError:
            novo = valor_b
            n_perda += 1
            if escolhido is pt:
                n_pt -= 1
            else:
                n_en -= 1
            n_orig += 1
    saida.append(chave_b + b',' + novo)

print('nosso : %d chaves' % len(saida))
print('  em portugues        : %d' % n_pt)
print('  em ingles (reserva) : %d' % n_en)
print('  original mantido    : %d' % n_orig)
if n_perda:
    print('  sem equivalente cp1252: %d (mantidos no original)' % n_perda)

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada gravado')
    raise SystemExit(0)

DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_bytes(b'\r\n'.join(saida) + b'\r\n')
print()
print('gravado: %s (%d bytes)' % (DESTINO, DESTINO.stat().st_size))
