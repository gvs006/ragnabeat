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
import re, sys
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

# --- efstids.lub: o nosso, decompilado, mais os 15 que faltam ---------------
#
# ATENCAO: a tabela original tem uma armadilha deliberada no fim:
#
#     __newindex = function() error("unknown state") end
#     }
#     setmetatable(EFST_IDs, EFST_IDs)
#
# Ou seja, ACRESCENTAR chave depois da construcao dispara "unknown state" e a
# tabela nunca termina de carregar - e ai TODAS as constantes ficam indefinidas,
# o que faz o StateIconInfo estourar em seguida com "table index is nil".
# Foi exatamente isso que aconteceu na primeira tentativa.
#
# Por isso as entradas vao DENTRO do literal, antes do __newindex.
src = (AQUI / '_extraido' / 'efstids.NOSSO.lua').read_bytes().decode('latin-1')

marca = '  __newindex = function()'
if marca not in src:
    raise SystemExit('ERRO: nao achei o __newindex - o formato mudou, revisar')

bloco = ['  -- ' + '-' * 70,
         '  -- Acrescentados em 11/ago/2026 para os arquivos de estado do RO LATAM.',
         '  -- Efeitos regionais ou removidos que a nossa versao (kRO 2024) nao tem.',
         '  -- Valores do LATAM, conferidos como livres: nenhum colide com efeito',
         '  -- nosso. Precisam ficar AQUI DENTRO - ver o __newindex logo abaixo.',
         '  -- ' + '-' * 70]
for nome, val in FALTAM:
    bloco.append('  %-24s = %d,' % (nome, val))

texto = src.replace(marca, '\n'.join(bloco) + '\n' + marca, 1)

# conferencias antes de gravar
if texto.count('{') != src.count('{') or texto.count('}') != src.count('}'):
    raise SystemExit('ERRO: contagem de chaves mudou')
for nome, _ in FALTAM:
    if ('  %s ' % nome) not in texto:
        raise SystemExit('ERRO: %s nao entrou' % nome)
if texto.index('EFST_BLOCK') > texto.index(marca):
    raise SystemExit('ERRO: as entradas ficaram DEPOIS do __newindex')

(DST / 'efstids.lub').write_bytes(texto.encode('latin-1'))
print('efstids.lub  : %d bytes (%d entradas, dentro do literal)' % (len(texto), len(FALTAM)))

# --- stateiconinfo: do LATAM, com os escapes convertidos para cp1252 --------
#
# O stateiconinfo.lub do LATAM vem em UTF-8, ao contrario do skilldescript que
# vem em cp1252. Copiar direto daria mojibake. Ver docs/encoding.md.
fonte = AQUI / '_extraido' / 'stateiconinfo.LATAM.lua'
if not fonte.exists():
    raise SystemExit('rode antes: java -jar unluac.jar "%s" > %s' % (LATAM / 'stateiconinfo.lub', fonte))

sys.path.insert(0, str(AQUI))
from _utf8_para_cp1252 import converte

novo, n_conv, perdidos = converte(fonte.read_bytes().decode('latin-1'))
(DST / 'stateiconinfo.lub').write_bytes(novo.encode('latin-1'))
print('stateiconinfo: %d bytes (%d sequencias UTF-8 -> cp1252, %d sem equivalente)'
      % ((DST / 'stateiconinfo.lub').stat().st_size, n_conv, len(perdidos)))

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
