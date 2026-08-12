# -*- coding: utf-8 -*-
"""
Gera data\\msgstringtable.csv em PT-BR - a tabela que move a tela de login e a
maior parte do HUD.

O cliente le data\\msgstringtable.csv, 2 colunas em base64: chave,valor.
O RO LATAM traz data\\msgstringtable_ml.csv, 10 colunas - uma por idioma:

    0 chave   1 coreano   2 ingles   7 PORTUGUES   9 espanhol

ENCODING: este arquivo e a EXCECAO do projeto. Os .lub sao cp1252, mas o
payload base64 do msgstringtable.csv e UTF-8 - conferido no proprio arquivo do
nosso GRF, cujo texto coreano decodifica como UTF-8 e falha em cp949/cp1252.
Na primeira versao eu converti para cp1252 e TODO acento virou "?" na tela.
Como o LATAM tambem usa UTF-8 aqui, o base64 e copiado como esta, sem
reconverter. Ver docs/encoding.md.

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


# Traducoes do LATAM que estao ERRADAS na origem: o portugues deles nao
# corresponde a chave. Corrigidas aqui, em UTF-8 como o resto.
CORRIGIR = {
    # o ingles diz "Do you agree?"; o PT-BR do LATAM fala de Replay.
    # E a PRIMEIRA tela que o jogador ve.
    b'MSI_DO_YOU_AGREE': 'Você concorda?',
}


def carrega_latam():
    """Devolve {chave: (base64_pt, base64_en)} - base64 CRU, sem reconverter."""
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
            if crus is None or not crus.strip():
                return None
            return cols[i]          # o base64 original, intacto

        tab[chave] = (pega(COL_PT), pega(COL_EN))
    return tab


latam = carrega_latam()
print('LATAM: %d chaves' % len(latam))

saida, n_pt, n_en, n_orig, n_corr = [], 0, 0, 0, 0
for linha in NOSSO.read_bytes().split(b'\n'):
    cols = linha.strip().split(b',')
    if len(cols) < 2 or not cols[0]:
        continue
    chave_b, valor_b = cols[0], cols[1]
    chave = b64(chave_b)
    pt, en = latam.get(chave, (None, None))

    if chave in CORRIGIR:
        novo = base64.b64encode(CORRIGIR[chave].encode('utf-8'))
        n_corr += 1
    elif pt:
        novo, n_pt = pt, n_pt + 1
    elif en:
        novo, n_en = en, n_en + 1
    else:
        novo, n_orig = valor_b, n_orig + 1
    saida.append(chave_b + b',' + novo)

print('nosso : %d chaves' % len(saida))
print('  em portugues        : %d' % n_pt)
print('  corrigidas a mao    : %d' % n_corr)
print('  em ingles (reserva) : %d' % n_en)
print('  original mantido    : %d' % n_orig)

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada gravado')
    raise SystemExit(0)

DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_bytes(b'\r\n'.join(saida) + b'\r\n')
print()
print('gravado: %s (%d bytes)' % (DESTINO, DESTINO.stat().st_size))
