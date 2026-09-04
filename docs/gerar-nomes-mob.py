# -*- coding: utf-8 -*-
"""
Traduz os nomes de monstro do servidor para PT-BR.

    python docs/gerar-nomes-mob.py            gera
    python docs/gerar-nomes-mob.py --dry      so relata, nao grava

POR QUE ISSO E DIFERENTE DOS ITENS
Nome de item o CLIENTE resolve - por isso o itemInfo_C.lua traduz 5.301 itens
sem tocar no servidor. Nome de monstro nao: e o campo Name: do mob_db, mandado
pelo servidor. Traduzir monstro e mexer no db.

A FONTE
DEVTOOLS/PTBR/latam/i18n/sc/*.csv - 1.494 planilhas do cliente RO LATAM, com
uma linha por texto e uma coluna por idioma, tudo em base64:

    coluna 2 = ingles      coluna 7 = portugues

Sao os nomes OFICIAIS do bRO, nao traducao automatica:
    Zombie Slaughter -> Massacre
    Soldier Skeleton -> Esqueleto Soldado
    Nightmare Terror -> Pesadelo Sombrio
    Poring           -> Poring            (varios nao mudam mesmo)

Casamento por nome em ingles exato. Nome que nao aparecer na base fica como
esta - melhor ingles do que chute.

SAIDAS
    db/ragnabeat_mob_names.yml  o override que o servidor carrega
    docs/_nomes-mob.tsv         o mapa ingles->portugues, que o
                                gerar-champions.py reaproveita
"""
import base64
import binascii
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
I18N = Path(r'C:/RagnaClient/RagnaBeat.Dev/DEVTOOLS/PTBR/latam/i18n/sc')
MOB_PRE = REPO / 'db/pre-re/mob_db.yml'
SAIDA_DB = REPO / 'db/ragnabeat_mob_names.yml'
SAIDA_MAPA = REPO / 'docs/_nomes-mob.tsv'

COL_EN, COL_PT = 2, 7
NAME_LENGTH = 23


def deb64(s):
    if not s:
        return ''
    try:
        return base64.b64decode(s + '=' * (-len(s) % 4)).decode('utf-8', 'replace')
    except (binascii.Error, ValueError):
        return ''


def carregar_i18n():
    """ingles -> portugues, varrendo todas as planilhas.

    A base repete o mesmo texto em ingles com traducoes diferentes conforme o
    contexto - "Isis" aparece 8x como "Isis" e 1x como "Ovo de Isis" (o ovo de
    pet). Pegar a primeira ocorrencia colocava OVO como nome de monstro. Por
    isso vale o VOTO DA MAIORIA: a traducao mais frequente e a do monstro,
    porque e a que aparece em drop, quest, bestiario e navegacao.
    """
    cand = defaultdict(Counter)
    arquivos = sorted(I18N.glob('*.csv'))
    for f in arquivos:
        try:
            linhas = f.read_bytes().decode('utf-8', 'replace').splitlines()
        except OSError:
            continue
        for linha in csv.reader(linhas):
            if len(linha) <= COL_PT:
                continue
            en = deb64(linha[COL_EN]).strip()
            pt = deb64(linha[COL_PT]).strip()
            # so interessa texto curto de uma linha - nome, nao dialogo
            if not en or not pt or len(en) > 40 or len(pt) > 40:
                continue
            if '\n' in en or '\n' in pt:
                continue
            cand[en][pt] += 1
    mapa = {en: c.most_common(1)[0][0] for en, c in cand.items()}
    return mapa, len(arquivos), cand


def mobs_do_servidor():
    """[(id, nome_ingles)] na ordem do arquivo."""
    t = MOB_PRE.read_bytes().decode('latin-1')
    fora = []
    for b in re.split(r'(?m)^(?=  - Id: )', t):
        m = re.match(r'  - Id: (\d+)\s*$', b.split('\n')[0])
        if not m:
            continue
        n = re.search(r'(?m)^    Name: (.+)$', b)
        a = re.search(r'(?m)^    AegisName: (\S+)\s*$', b)
        if n and a:
            fora.append((int(m.group(1)), a.group(1), n.group(1).strip()))
    return fora


def main():
    seco = '--dry' in sys.argv
    if not I18N.is_dir():
        raise SystemExit('nao achei a base i18n em %s' % I18N)

    print('lendo a base i18n do LATAM...')
    mapa, n_arq, cand = carregar_i18n()
    print('  %d planilhas, %d textos curtos distintos' % (n_arq, len(mapa)))
    ambiguos = sum(1 for c in cand.values() if len(c) > 1)
    print('  %d tinham mais de uma traducao - resolvidos por maioria' % ambiguos)

    mobs = mobs_do_servidor()
    print('mobs em db/pre-re: %d' % len(mobs))

    traduzidos, iguais, sem, longos = [], 0, [], []
    for oid, aegis, en in mobs:
        pt = mapa.get(en)
        if not pt:
            sem.append((oid, en))
            continue
        if pt == en:
            iguais += 1
            continue
        if len(pt) > NAME_LENGTH:
            longos.append((oid, en, pt))
            continue
        traduzidos.append((oid, aegis, en, pt))

    print()
    print('  traduzidos       : %d' % len(traduzidos))
    print('  ja iguais em PT  : %d (Poring, Familiar, ...)' % iguais)
    print('  sem traducao     : %d (ficam em ingles)' % len(sem))
    print('  PT acima de %d ch: %d (pulados)' % (NAME_LENGTH, len(longos)))
    for oid, en, pt in longos[:6]:
        print('        %s -> %s' % (en, pt))

    if seco:
        print()
        print('>>> DRY RUN - nada gravado. Amostra:')
        for oid, aegis, en, pt in traduzidos[:15]:
            print('   %5d  %-26s -> %s' % (oid, en, pt))
        return 0

    cab = '''# Nomes de monstro em PT-BR - GERADO, NAO EDITE A MAO
#
# Fonte: docs/gerar-nomes-mob.py, que le a base i18n do cliente RO LATAM
# (DEVTOOLS/PTBR/latam/i18n/sc/*.csv). Sao os nomes oficiais do bRO.
#
# Nome de monstro vem do SERVIDOR, diferente de nome de item - por isso isto
# e um override de mob_db e nao um arquivo de cliente.
#
# Monstro sem entrada na base fica em ingles de proposito.

Header:
  Type: MOB_DB
  Version: 5

Body:
'''
    corpo = []
    for oid, aegis, en, pt in traduzidos:
        corpo.append('  - Id: %d' % oid)
        corpo.append('    AegisName: %s' % aegis)
        corpo.append('    Name: %s' % pt)
    SAIDA_DB.write_bytes((cab + '\n'.join(corpo) + '\n').encode('cp1252', 'replace'))

    linhas = ['# ingles\tportugues - gerado por docs/gerar-nomes-mob.py']
    for oid, aegis, en, pt in traduzidos:
        linhas.append('%s\t%s' % (en, pt))
    SAIDA_MAPA.write_bytes(('\n'.join(linhas) + '\n').encode('cp1252', 'replace'))

    print()
    for p in (SAIDA_DB, SAIDA_MAPA):
        print('gravado: %-32s %d bytes' % (p.relative_to(REPO), p.stat().st_size))
    print()
    print('Falta: enganchar em db/import/mob_db.yml e regerar os champions')
    return 0


if __name__ == '__main__':
    sys.exit(main())
