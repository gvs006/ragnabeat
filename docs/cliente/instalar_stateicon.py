# -*- coding: utf-8 -*-
"""
Instala os nomes/descricoes de buff (icones de estado) em PT-BR do RO LATAM.

Mesmo padrao das skills: os arquivos do LATAM indexam por constante
(EFST_XXX), e a nossa versao - kRO mais nova - nao define 15 delas. Sem os
apelidos, o cliente abre "table index is nil".

As 15 nao sao erro de digitacao: sao efeitos regionais (HELM_*, JPNONLY_*,
OVERSEA_BUFF_*) ou removidos, que so existem na versao do LATAM. Recebem o
valor que o LATAM usa. Verificado que nenhum desses valores colide com efeito
nosso, entao acrescentar e inofensivo.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).parent
DST = RAIZ / 'data' / 'luafiles514' / 'lua files' / 'stateicon'
LATAM = AQUI / 'latam' / 'luafiles514' / 'lua files' / 'stateicon'

FALTAM = [
    ('EFST_HELM_VERKANA', 926), ('EFST_HELM_RHYDO', 927), ('EFST_HELM_TURISUS', 928),
    ('EFST_HELM_HAGALAS', 929), ('EFST_HELM_ISIA', 930), ('EFST_HELM_ASIR', 931),
    ('EFST_HELM_URJ', 932), ('EFST_JPNONLY_TACTICS', 1147), ('EFST_DEFSCROLL', 1321),
    ('EFST_C_BUFF_16', 1524), ('EFST_C_BUFF_17', 1525), ('EFST_OVERSEA_BUFF_12', 1595),
    ('EFST_OVERSEA_BUFF_30', 1614), ('EFST_OVERSEA_BUFF_31', 1615), ('EFST_BLOCK', 1688),
]

DST.mkdir(parents=True, exist_ok=True)

# --- efstids.lub: o nosso, decompilado, mais os 15 apelidos -----------------
src = (AQUI / '_extraido' / 'efstids.NOSSO.lua').read_bytes().decode('latin-1').rstrip()
extra = ['', '', '-- ' + '-' * 72,
         '-- Acrescentados em 11/ago/2026 para os arquivos de estado do RO LATAM.',
         '--',
         '-- Sao efeitos regionais ou removidos que a nossa versao (kRO 2024) nao',
         '-- define. Sem eles, EFST_X devolve nil e o cliente abre "table index is',
         '-- nil" ao carregar StateIconInfo. Valores conferidos como livres - nenhum',
         '-- colide com efeito nosso. Ver docs/cliente/skills.md, mesmo padrao.',
         '-- ' + '-' * 72]
for nome, val in FALTAM:
    extra.append('EFST_IDs.%-22s = %d' % (nome, val))

texto = src + '\n'.join(extra) + '\n'
(DST / 'efstids.lub').write_bytes(texto.encode('latin-1'))
print('efstids.lub  : %d bytes (%d apelidos)' % (len(texto), len(FALTAM)))

# --- os arquivos de texto do LATAM -----------------------------------------
import shutil
for f in ('stateiconinfo.lub',):
    shutil.copy2(LATAM / f, DST / f)
    print('%-13s: %d bytes (LATAM PT-BR)' % (f, (DST / f).stat().st_size))

# --- conferir que nao sobrou constante indefinida ---------------------------
def toks(p):
    return set(x.decode() for x in re.findall(rb'[A-Z][A-Z0-9_]{3,44}', Path(p).read_bytes()))

definidos = set(re.findall(r'([A-Z][A-Z0-9_]+)\s*=', texto))
lat_ids = toks(LATAM / 'efstids.lub')
usa = toks(DST / 'stateiconinfo.lub')
# 'EFST_ID' e falso positivo: o regex casa o prefixo do nome da tabela EFST_IDs
falta = sorted((usa & lat_ids) - definidos - {'EFST_ID', 'EFST_IDs'})
print()
print('constantes ainda indefinidas:', falta if falta else 'NENHUMA')
print('nome da tabela conferido:', 'EFST_IDs' if 'EFST_IDs = {' in texto else 'ATENCAO - divergente')
