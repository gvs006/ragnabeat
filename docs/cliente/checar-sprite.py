# -*- coding: utf-8 -*-
"""
Diz se o cliente TEM os sprites de um item, antes de a gente colocar o item no
servidor.

    python checar-sprite.py 5376 5451 1746

Por que existe: trazer um item do renewal para o pre-renewal precisa das tres
camadas casadas - servidor (db), nome/descricao (itemInfo do cliente) e
SPRITE (data.grf). A terceira nao e garantida: descobrimos em 11/ago/2026 que a
"Lendarias Asas de Demonio" (5376) tem entrada no itemInfo e icone de
collection, mas nenhum sprite - equipar dava
"Cannot find File : sprite\\<coreano>.act" e o cliente reclamava na cara do
jogador.

O nome do arquivo de sprite vem do identifiedResourceName, que esta em coreano
no DEVTOOLS/PTBR/iteminfo_ptBR.lua (dump do RO LATAM, 16.731 itens).

Saida por item:
    drop        data\\sprite\\<item>\\<res>.spr + .act  - o item caido no chao
    vestido     o sprite que aparece no personagem, procurado nas tres pastas
                que o cliente usa: <acessorio> (chapeu), <arma> e <robe>
                (manto). Espera-se 2 - masculino e feminino.
    collection  o icone grande da descricao

drop=False e sempre problema: o cliente aborta com uma caixa de erro na cara do
jogador. vestido=0 so e problema para chapeu, arma e manto - acessorio de dedo
e carta nao tem sprite vestido mesmo.
"""
import importlib.util
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LATAM = Path(r'C:/RagnaClient/RagnaBeat.Dev/DEVTOOLS/PTBR/iteminfo_ptBR.lua')
BS = chr(92)

# Nomes de pasta do GRF, em coreano. O GRF guarda os bytes cp949 crus, entao a
# comparacao e feita em latin-1 para nao mexer em byte nenhum.
PASTA_ITEM = '\uc544\uc774\ud15c'          # item - o objeto caido no chao
PASTA_COLLECTION = '\uc720\uc800\uc778\ud130\ud398\uc774\uc2a4' + BS + 'collection'
# O sprite vestido mora em pastas diferentes conforme o tipo de equipamento.
PASTAS_VESTIDO = (
    '\uc545\uc138\uc0ac\ub9ac',  # acessorio - chapeus e afins
    '\ubb34\uae30',              # arma
    '\ub85c\ube0c',              # robe - mantos
)


def crua(s):
    """Texto coreano -> a mesma sequencia de bytes que esta dentro do GRF."""
    return s.encode('cp949').decode('latin-1').lower()


# Os dois clientes NAO tem o mesmo conteudo. Descoberto em 11/ago/2026: o
# data.grf de C:/RagnaClient e v3 com 269 mil arquivos, e o do RagnaBeat.Dev
# (que e o que vira build para os jogadores) e v2 com 215 mil. Um sprite pode
# existir num e faltar no outro - e o que vale e o do build.
GRFS = [
    ('build ', r'C:/RagnaClient/RagnaBeat.Dev/data.grf'),
    ('prod  ', r'C:/RagnaClient/data.grf'),
]


def carregar_grfs():
    spec = importlib.util.spec_from_file_location('grf', AQUI / 'grf_listar.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fora = []
    for rotulo, caminho in GRFS:
        p = Path(caminho)
        if not p.exists():
            continue
        arquivos, _ = mod.ler_tabela(p)
        fora.append((rotulo, p, set(n.decode('latin-1').lower() for n, *_ in arquivos)))
    if not fora:
        raise SystemExit('nao achei nenhum GRF conhecido')
    return fora


def desescapar(s):
    """Os nomes do LATAM vem com bytes UTF-8 escapados em decimal: \\195\\173."""
    s = re.sub(re.escape(BS) + r'(\d{1,3})', lambda m: chr(int(m.group(1))), s)
    return s.encode('latin-1', 'replace').decode('utf-8', 'replace')


def dados_latam(ids):
    if not LATAM.exists():
        raise SystemExit('nao achei %s' % LATAM)
    txt = LATAM.read_bytes().decode('cp1252', 'replace')
    fora = {}
    for m in re.finditer(r'\[(\d+)\]\s*=\s*\{(.*?)\n  \}', txt, re.S):
        oid = int(m.group(1))
        if oid not in ids:
            continue
        nome = re.search(r'(?<!un)identifiedDisplayName\s*=\s*"([^"]*)"', m.group(2))
        res = re.search(r'(?<!un)identifiedResourceName\s*=\s*"([^"]*)"', m.group(2))
        fora[oid] = (desescapar(nome.group(1)) if nome else '?',
                     desescapar(res.group(1)) if res else '')
    return fora


def main():
    ids = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if not ids:
        raise SystemExit(__doc__)

    grfs = carregar_grfs()
    for rotulo, p, nomes in grfs:
        print('%s %-45s %d arquivos' % (rotulo, p, len(nomes)))
    print()

    dir_item = 'data' + BS + 'sprite' + BS + crua(PASTA_ITEM) + BS
    dirs_vestido = ['data' + BS + 'sprite' + BS + crua(p) + BS for p in PASTAS_VESTIDO]
    dir_col = 'data' + BS + 'texture' + BS + crua(PASTA_COLLECTION) + BS

    info = dados_latam(set(ids))
    problemas = 0
    for oid in ids:
        nome, res = info.get(oid, ('<ausente no LATAM>', ''))
        if not res:
            print('%-7d %-32s SEM identifiedResourceName' % (oid, nome[:32]))
            problemas += 1
            continue
        r = crua(res)
        linha = '%-7d %-32s' % (oid, nome[:32])
        falta_no_build = False
        for rotulo, _p, nomes in grfs:
            drop = (dir_item + r + '.spr') in nomes and (dir_item + r + '.act') in nomes
            vestido = sum(1 for n in nomes if n.endswith('.spr') and r in n
                          and any(n.startswith(d) for d in dirs_vestido))
            col = sum(1 for n in nomes if n.startswith(dir_col) and r in n)
            linha += '  |%s drop=%-5s vestido=%-2d col=%d' % (rotulo.strip(), drop, vestido, col)
            if rotulo.strip() == 'build' and not drop:
                falta_no_build = True
        if falta_no_build:
            linha += '   <<< FALTA NO BUILD'
            problemas += 1
        print(linha)
    print()
    print('%d item(ns) que quebrariam no cliente entregue' % problemas)
    return 1 if problemas else 0


if __name__ == '__main__':
    sys.exit(main())
