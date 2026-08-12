# -*- coding: utf-8 -*-
"""
Gera data\\luafiles514\\lua files\\datainfo\\pcjobname.lub com os nomes de classe
em PT-BR - o texto que aparece abaixo do nick.

As duas versoes guardam isso em lugares diferentes:

    nosso   pcjobname.lub            PCJobNameTable    = { [JOBID.X] = "..." }
    LATAM   pcjobnamegender_ptbr.lub PCJobNameTableMan = { [JOBID.X] = "..." }

As chaves JOBID sao as mesmas, entao da para casar direto. O cliente le
"Lua Files\\DataInfo\\PCJobName", entao geramos no formato NOSSO com o texto
DELES.

O arquivo do LATAM ja esta em cp1252 (Novi\\231o = Novico), mas isso e conferido
em vez de assumido - os arquivos do LATAM nao tem encoding uniforme.

    python gen_nomes_classe.py            gera
    python gen_nomes_classe.py --dry      so relata
"""
import re, sys
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parents[1]
NOSSO = AQUI / '_extraido' / 'pcjobname.NOSSO.lua'
LATAM = AQUI / '_extraido' / 'pcjobnamegender_ptbr.lua'
DESTINO = RAIZ / 'data' / 'luafiles514' / 'lua files' / 'datainfo' / 'pcjobname.lub'

ENTRADA = re.compile(r'\[(JOBID\.[A-Z_0-9]+)\]\s*=\s*"((?:[^"\\]|\\.)*)"')


def tabela(caminho, nome_tabela):
    txt = caminho.read_bytes().decode('latin-1')
    i = txt.find(nome_tabela)
    if i < 0:
        raise SystemExit('nao achei %s em %s' % (nome_tabela, caminho.name))
    # do inicio da tabela ate a chave que a fecha
    fim = txt.find('\n}', i)
    return dict(ENTRADA.findall(txt[i:fim if fim > 0 else len(txt)]))


nosso = tabela(NOSSO, 'PCJobNameTable')
latam = tabela(LATAM, 'PCJobNameTableMan')

traduzidos = [k for k in nosso if k in latam and latam[k].strip()]
mantidos = [k for k in nosso if k not in traduzidos]

print('classes no nosso : %d' % len(nosso))
print('no LATAM         : %d' % len(latam))
print('  traduzidas     : %d' % len(traduzidos))
print('  em ingles      : %d' % len(mantidos))
print()
for k in ('JOBID.JT_MONK_H', 'JOBID.JT_KNIGHT_H', 'JOBID.JT_ASSASSIN_H', 'JOBID.JT_NOVICE'):
    if k in nosso:
        antes = nosso[k]
        depois = latam.get(k, '(sem traducao)')
        print('  %-24s %-18s -> %s' % (k.replace('JOBID.', ''), antes, depois))

if mantidos:
    print()
    print('  exemplos que ficam em ingles:', [k.replace('JOBID.', '') for k in mantidos[:6]])

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada gravado')
    raise SystemExit(0)

linhas = [
    '-- Nomes de classe em PT-BR - gerado por DEVTOOLS/PTBR/gen_nomes_classe.py',
    '--',
    '-- NAO EDITE A MAO: regenere. Fonte: pcjobnamegender_ptbr.lub do RO LATAM,',
    '-- casado por chave JOBID. Formato e nome de tabela sao os NOSSOS, porque e',
    '-- isso que o cliente le em "Lua Files\\DataInfo\\PCJobName".',
    '--',
    '-- Encoding: cp1252. Ver docs/encoding.md.',
    '',
    'PCJobNameTable = {',
]
itens = list(nosso.keys())
for n, k in enumerate(itens):
    valor = latam.get(k) if k in traduzidos else nosso[k]
    virg = ',' if n < len(itens) - 1 else ''
    linhas.append('  [%s] = "%s"%s' % (k, valor, virg))
linhas.append('}')

# O arquivo original define a TABELA e tambem a FUNCAO que o cliente chama.
# Gerar so a tabela deixa ReqPCJobName nil, e o cliente entra em laco com
# "attempt to call a nil value" - foi o que aconteceu na primeira tentativa.
# Reproduzido identico ao original decompilado.
linhas += [
    '',
    'function ReqPCJobName(JobID)',
    '  if nil == PCJobNameTable[JobID] then',
    '    return ""',
    '  end',
    '  return PCJobNameTable[JobID]',
    'end',
]

DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_bytes(('\n'.join(linhas) + '\n').encode('latin-1'))
print()
print('gravado: %s (%d classes, %d bytes)' % (DESTINO, len(nosso), DESTINO.stat().st_size))
