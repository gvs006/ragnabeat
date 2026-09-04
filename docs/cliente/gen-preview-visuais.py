# -*- coding: utf-8 -*-
"""
Liga o botao de PREVIEW na janela de descricao dos itens de visual.

O cliente nao decide isso em codigo. O exe chama a funcao Lua IsEffectHatItem
(string em 0x00C11CF8) e so desenha o botao quando ela devolve true:

    function IsEffectHatItem(itemID)              -- hateffect_f.lub
      for k, v in pairs(effectHatItemTable) do
        if v == itemID then return true end
      end
      return false
    end

A effectHatItemTable original tem 126 IDs - so os "hats de efeito" oficiais.
Nossos visuais nao estao la, e por isso nao aparece preview neles.

Este script reescreve a tabela como a UNIAO dos 126 originais com os IDs de
db/ragnabeat_visuais.yml. Os originais sao preservados: tirar um deles apagaria
o preview de um item que hoje tem.

Confirmado que a tabela e usada SO pelo IsEffectHatItem - varredura nos 471
lubs de luafiles514 nao achou outro leitor. Acrescentar ID nao mexe em
renderizacao de efeito: quem faz isso e a hatEffectTable, que e outra.

Nao precisa tocar no exe. O patch NoEquipPreview do WARP (que DESLIGA isso)
nao esta aplicado no nosso perfil, entao a feature ja esta ligada - faltava
so o dado.

    python gen_preview_visuais.py           gera e instala
    python gen_preview_visuais.py --dry     so relata
"""
import re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grf_listar import ler_tabela, ler_arquivo

AQUI = Path(__file__).parent
REPO = AQUI.parents[1]
# Este script morou dentro da pasta do cliente e usava caminho relativo. Ao
# vir para o repo os relativos passaram a apontar para o proprio repo, e ele
# procurava um data.grf que nunca existiu aqui. Agora aponta para o cliente
# explicitamente, como o resto das ferramentas.
CLIENTE = Path(r'C:/RagnaClient/RagnaBeat.Dev')
GRF = CLIENTE / 'data.grf'
UNLUAC = CLIENTE / 'DEVTOOLS/PTBR/unluac.jar'
VISUAIS = REPO / 'db/ragnabeat_visuais.yml'

BS = chr(92)
INTERNO = ('data' + BS + 'luafiles514' + BS + 'lua files' + BS +
           'hateffectinfo' + BS + 'effecthatitemtable.lub')
DESTINO = (CLIENTE / 'data' / 'luafiles514' / 'lua files' / 'hateffectinfo'
           / 'effecthatitemtable.lub')
# O extraido e lixo de trabalho: fica no cliente, sob DEVTOOLS, que o build.py
# ja exclui. No repo ele viraria arquivo nao versionado aparecendo no status.
TEMP = CLIENTE / 'DEVTOOLS' / 'PTBR' / '_extraido' / 'effecthatitemtable.ORIGINAL.lub'


def ids_originais():
    """Le a tabela compilada do GRF e decompila com o unluac."""
    arq, _ = ler_tabela(GRF)
    alvo = INTERNO.lower().encode('latin-1')
    achado = [e for e in arq if e[0].lower() == alvo]
    if not achado:
        raise SystemExit('nao achei %s dentro do %s' % (INTERNO, GRF.name))
    TEMP.parent.mkdir(parents=True, exist_ok=True)
    TEMP.write_bytes(ler_arquivo(GRF, achado[0]))
    saida = subprocess.run(['java', '-jar', str(UNLUAC), str(TEMP)],
                           capture_output=True, text=True)
    if saida.returncode != 0:
        raise SystemExit('unluac falhou: %s' % saida.stderr[:200])
    return [int(x) for x in re.findall(r'^\s*(\d+),?\s*$', saida.stdout, re.M)]


def ids_visuais():
    txt = VISUAIS.read_text(encoding='cp1252', errors='replace')
    return [int(x) for x in re.findall(r'^\s*-\s*Id:\s*(\d+)', txt, re.M)]


orig = ids_originais()
novos = ids_visuais()
print('originais na tabela do GRF : %d' % len(orig))
print('visuais em %s : %d' % (VISUAIS.name, len(novos)))

vistos, final = set(), []
for i in orig + novos:
    if i not in vistos:
        vistos.add(i)
        final.append(i)
print('acrescentados (sem repetir) : %d' % (len(final) - len(orig)))
print('total na tabela nova        : %d' % len(final))

linhas = [
    '-- effectHatItemTable - GERADO por DEVTOOLS/PTBR/gen_preview_visuais.py',
    '--',
    '-- Decide em quais itens o cliente desenha o botao de PREVIEW na janela de',
    '-- descricao. O exe chama IsEffectHatItem(id), definido em hateffect_f.lub,',
    '-- que so varre esta lista. NAO EDITE A MAO: regenere.',
    '--',
    '-- Os %d primeiros sao os originais do data.grf e nao podem sair - tirar um' % len(orig),
    '-- apagaria o preview de um item que hoje tem.',
    '',
    'effectHatItemTable = {',
]
linhas += ['  %d,' % i for i in final[:-1]] + ['  %d' % final[-1], '}', '']

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada gravado')
    raise SystemExit(0)

DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_text('\n'.join(linhas), encoding='cp1252')
print()
print('gravado: %s (%d bytes)' % (DESTINO, DESTINO.stat().st_size))
