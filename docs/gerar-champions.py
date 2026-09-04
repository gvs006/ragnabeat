# -*- coding: utf-8 -*-
"""
Gera os Champion Mobs do RagnaBeat para pre-renewal.

    python docs/gerar-champions.py            gera
    python docs/gerar-champions.py --dry      so relata, nao grava

O QUE ELE FAZ, E POR QUE NAO E UM COPIA-E-COLA
O upstream tem npc/re/mobs/championmobs.txt e as entradas C1_..C5_ em
db/re/mob_db.yml. Trazer aquilo direto quebraria o servidor: os champions de
renewal vem com nivel 124 (o teto aqui e 99), 175 mil de HP e tabelas de drop
apontando para itens que nao existem em pre-renewal.

Entao, em vez de importar, cada champion e MONTADO A PARTIR DO MOB BASE do
nosso db/pre-re. Herda nivel, raca, elemento, tamanho, IA e drops - tudo ja
balanceado para este episodio - e so HP, ataque e experiencia sao
multiplicados. Nada de renewal entra de carona.

Sao descartados automaticamente:
  - champion cujo mob base nao existe em pre-renewal   (mob so de renewal)
  - champion cujo mob base e MVP                        (pedido: sem MVP)
  - spawn em mapa onde o nosso episodio nao spawna nada (mapa de renewal)

Saidas:
  db/ragnabeat_mobs.yml     os mobs
  db/import/mob_db.yml      rodape que puxa o de cima para a cadeia do mob_db
  npc/custom/champions.txt  os spawns

Os multiplicadores estao logo abaixo. Mexer neles e regerar e o jeito de
rebalancear - nao edite os arquivos de saida a mao, eles sao sobrescritos.
Justificativa dos numeros em docs/rebalance.md secao 9.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MULT_HP = 8
MULT_ATK = 1.5
MULT_EXP = 4

NAME_LENGTH = 23        # limite do rAthena (NAME_LENGTH 24), menos o terminador

# O nome do upstream ("Zombie Slaughter Ringleader") estoura os 23 caracteres em
# 13 casos, e descartar o mob por causa do nome seria bobo. Entao o nome e
# montado aqui: prefixo curto em PT-BR + nome do mob base do NOSSO db.
#   C1 Swift  C2 Solid  C3 Furious  C4 Elusive  C5 Ringleader
PREFIXO = {'C1': 'Veloz', 'C2': 'Rijo', 'C3': 'Furioso',
           'C4': 'Esquivo', 'C5': 'Lider'}

FONTE_SPAWN = REPO / 'npc/re/mobs/championmobs.txt'
MOB_RE = REPO / 'db/re/mob_db.yml'
MOB_PRE = REPO / 'db/pre-re/mob_db.yml'

SAIDA_MOBS = REPO / 'db/ragnabeat_mobs.yml'
SAIDA_IMPORT = REPO / 'db/import/mob_db.yml'
SAIDA_SPAWN = REPO / 'npc/custom/champions.txt'


def blocos(caminho):
    """AegisName -> (id, texto do bloco)."""
    t = caminho.read_bytes().decode('latin-1')
    fora = {}
    for b in re.split(r'(?m)^(?=  - Id: )', t):
        m = re.match(r'  - Id: (\d+)\s*$', b.split('\n')[0])
        if not m:
            continue
        a = re.search(r'(?m)^    AegisName: (\S+)\s*$', b)
        if a:
            fora[a.group(1)] = (int(m.group(1)), b.rstrip('\n'))
    return fora


def nomes_ptbr():
    """ingles -> portugues, do docs/_nomes-mob.tsv (gerar-nomes-mob.py).
    Se o arquivo nao existir, os champions nascem com o nome em ingles."""
    arq = REPO / 'docs/_nomes-mob.tsv'
    if not arq.exists():
        return {}
    fora = {}
    for linha in arq.read_bytes().decode('cp1252').splitlines():
        if linha.startswith('#') or '	' not in linha:
            continue
        en, pt = linha.split('	', 1)
        fora[en] = pt
    return fora


def mapas_vivos():
    """Mapas onde o nosso pre-renewal ja spawna alguma coisa."""
    vivos = set()
    for f in (REPO / 'npc/pre-re/mobs').rglob('*.txt'):
        for linha in f.read_bytes().decode('latin-1').splitlines():
            if linha.lstrip().startswith('//'):
                continue
            m = re.match(r'^(\S+),\d+,\d+(?:,\d+,\d+)?\tmonster\t', linha)
            if m:
                vivos.add(m.group(1).lower())
    return vivos


def escalar(bloco, oid, aegis, nome):
    """Reescreve o bloco do mob base como o champion."""
    saida = []
    for linha in bloco.split('\n'):
        m = re.match(r'^  - Id: \d+\s*$', linha)
        if m:
            saida.append('  - Id: %d' % oid)
            continue
        m = re.match(r'^    AegisName: \S+\s*$', linha)
        if m:
            saida.append('    AegisName: %s' % aegis)
            continue
        m = re.match(r'^    Name: .+$', linha)
        if m:
            saida.append('    Name: %s' % nome)
            continue
        # so campos de primeiro nivel (4 espacos) - assim nao pega Rate: de drop
        m = re.match(r'^    (Hp|Attack|Attack2|BaseExp|JobExp): (\d+)\s*$', linha)
        if m:
            campo, valor = m.group(1), int(m.group(2))
            if campo == 'Hp':
                valor = valor * MULT_HP
            elif campo in ('Attack', 'Attack2'):
                valor = int(round(valor * MULT_ATK))
            else:
                valor = valor * MULT_EXP
            saida.append('    %s: %d' % (campo, valor))
            continue
        saida.append(linha)
    return '\n'.join(saida)


def main():
    seco = '--dry' in sys.argv

    champs_re = blocos(MOB_RE)
    base_pre = blocos(MOB_PRE)
    por_id_re = {v[0]: (k, v[1]) for k, v in champs_re.items()}
    vivos = mapas_vivos()
    nomes_pt = nomes_ptbr()

    spawns = []
    for linha in FONTE_SPAWN.read_bytes().decode('latin-1').splitlines():
        if linha.lstrip().startswith('//'):
            continue
        m = re.match(r'^(\S+),(\d+),(\d+)\tmonster\t([^\t]+)\t(\d+),(\d+),(\d+)', linha)
        if m:
            spawns.append({'mapa': m.group(1), 'x': m.group(2), 'y': m.group(3),
                           'nome': m.group(4).strip(), 'id': int(m.group(5)),
                           'qtd': m.group(6), 'delay': m.group(7)})

    usados, desc = {}, {'sem_base': 0, 'base_mvp': 0, 'mapa_morto': 0, 'cortado': 0}
    mortos, cortados = set(), []
    linhas_spawn = []
    for s in spawns:
        if s['mapa'].lower() not in vivos:
            desc['mapa_morto'] += 1
            mortos.add(s['mapa'])
            continue
        entrada = por_id_re.get(s['id'])
        if not entrada:
            desc['sem_base'] += 1
            continue
        aegis, _ = entrada
        m = re.match(r'^(C\d)_(.+)$', aegis)
        if not m or m.group(2) not in base_pre:
            desc['sem_base'] += 1
            continue
        base_aegis = m.group(2)
        _, bloco_base = base_pre[base_aegis]
        if re.search(r'(?m)^\s+Mvp: true', bloco_base):
            desc['base_mvp'] += 1
            continue

        nome_base = re.search(r'(?m)^    Name: (.+)$', bloco_base).group(1).strip()
        # o mob base do db esta em ingles; se ja existe traducao PT-BR
        # (docs/gerar-nomes-mob.py), usa ela para o champion nascer em PT-BR
        nome_base = nomes_pt.get(nome_base, nome_base)
        nome = '%s %s' % (PREFIXO[m.group(1)], nome_base)
        if len(nome) > NAME_LENGTH:
            cortados.append('%s -> %s' % (nome, nome[:NAME_LENGTH].rstrip()))
            nome = nome[:NAME_LENGTH].rstrip()
            desc['cortado'] += 1

        usados[s['id']] = (aegis, nome, bloco_base, base_aegis)
        linhas_spawn.append('%s,%s,%s\tmonster\t%s\t%d,%s,%s'
                            % (s['mapa'], s['x'], s['y'], nome,
                               s['id'], s['qtd'], s['delay']))

    print('nomes PT-BR no mapa  : %d' % len(nomes_pt))
    print('spawns na fonte      : %d' % len(spawns))
    print('  fora - mapa morto  : %d' % desc['mapa_morto'])
    print('  fora - sem base    : %d' % desc['sem_base'])
    print('  fora - base e MVP  : %d' % desc['base_mvp'])
    print('  nomes cortados em %d ch: %d' % (NAME_LENGTH, desc['cortado']))
    for c in sorted(set(cortados)):
        print('        %s' % c)
    print('  mapas descartados  : %d -> %s' % (len(mortos), ', '.join(sorted(mortos)[:14])))
    print('spawns gerados       : %d' % len(linhas_spawn))
    print('mobs gerados         : %d' % len(usados))
    print('multiplicadores      : HP x%s, ATQ x%s, EXP x%s'
          % (MULT_HP, MULT_ATK, MULT_EXP))

    if seco:
        print()
        print('>>> DRY RUN - nada gravado')
        for oid in sorted(usados)[:3]:
            aegis, nome, bloco, base = usados[oid]
            print()
            print(escalar(bloco, oid, aegis, nome)[:500])
        return 0

    cab_mobs = '''# Champion Mobs do RagnaBeat - GERADO, NAO EDITE A MAO
#
# Fonte: docs/gerar-champions.py. Cada champion e montado a partir do mob base
# de db/pre-re/mob_db.yml, herdando nivel, raca, elemento, tamanho, IA e drops.
# So HP, ataque e experiencia sao multiplicados - por isso nada de renewal
# (nivel 124, item inexistente) entra junto.
#
# Multiplicadores: HP x%s, ATQ x%s, EXP x%s
# Para rebalancear, mude-os no script e regere.
#
# Spawns em npc/custom/champions.txt. Justificativa em docs/rebalance.md, 9.

Header:
  Type: MOB_DB
  Version: 5

Body:
''' % (MULT_HP, MULT_ATK, MULT_EXP)

    corpo = []
    for oid in sorted(usados):
        aegis, nome, bloco, base = usados[oid]
        corpo.append('  # base: %s' % base)
        corpo.append(escalar(bloco, oid, aegis, nome))
    SAIDA_MOBS.write_bytes((cab_mobs + '\n'.join(corpo) + '\n').encode('latin-1'))

    SAIDA_IMPORT.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_IMPORT.write_bytes(('''# GERADO por docs/gerar-champions.py - NAO EDITE A MAO
#
# Existe so para enganchar db/ragnabeat_mobs.yml na cadeia do mob_db. O
# rAthena carrega db/import/mob_db.yml por ultimo; o rodape abaixo puxa o
# nosso arquivo depois dele.

Header:
  Type: MOB_DB
  Version: 5

Footer:
  Imports:
  - Path: db/ragnabeat_mob_names.yml
  - Path: db/ragnabeat_mobs.yml
''').encode('latin-1'))

    cab_spawn = '''//===== rAthena Script =======================================
//= Champion Mobs - spawns
//===== Descricao: ===========================================
//= GERADO por docs/gerar-champions.py. NAO EDITE A MAO.
//=
//= Versao pre-renewal do npc/re/mobs/championmobs.txt do
//= upstream, que nao e carregado aqui (a arvore que roda e a
//= npc/pre-re/).
//=
//= Ficaram de fora os spawns em mapa que o nosso episodio nao
//= usa e os champions cujo mob base e MVP ou so existe em
//= renewal.
//=
//= Os mobs estao em db/ragnabeat_mobs.yml.
//============================================================

'''
    SAIDA_SPAWN.write_bytes((cab_spawn + '\n'.join(linhas_spawn) + '\n').encode('latin-1'))

    print()
    for p in (SAIDA_MOBS, SAIDA_IMPORT, SAIDA_SPAWN):
        print('gravado: %-28s %d bytes' % (p.relative_to(REPO), p.stat().st_size))
    print()
    print('Falta registrar npc/custom/champions.txt em npc/scripts_custom.conf')
    return 0


if __name__ == '__main__':
    sys.exit(main())
