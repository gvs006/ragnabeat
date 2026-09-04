# -*- coding: utf-8 -*-
"""
Procura arquivo com encoding estragado antes que ele chegue ao jogo.

    python docs/checar-encoding.py            varre o repo, so relata
    python docs/checar-encoding.py --tudo     lista tambem os arquivos sadios

Sai com codigo 1 se achar dano, para poder entrar num hook ou na CI.

O QUE ELE PROCURA
-----------------
1. CORROMPIDO - o caso grave. O arquivo era cp1252, algum editor o abriu
   como UTF-8, nao conseguiu decodificar os acentos, trocou cada um por
   U+FFFD e gravou. No disco isso vira a sequencia EF BF BD, e no jogo o
   jogador le "Bencao" como "Bï¿½nï¿½ï¿½o".

   A PERDA E IRREVERSIVEL sozinha: U+FFFD nao guarda qual acento era. So
   da para voltar palavra por palavra, no olho.

2. UTF-8 onde deveria ser cp1252 - ainda nao quebrou, mas vai. Assim que
   o servidor mandar esse texto para o cliente, cada acento sai como dois
   caracteres ("Ã©"), porque o cliente le cp1252.

3. BOM em arquivo que o rAthena le - os tres bytes do BOM entram no
   primeiro token e derrubam o parser sem mensagem clara.

O MAPA DE ENCODING DO PROJETO esta em docs/traducao.md. Resumo:

    npc/**/*.txt        cp1252   (script de NPC)
    conf/**             cp1252
    db/**/*.yml         cp1252   (o rapidyaml passa os bytes intactos)
    docs/**/*.md        UTF-8
    msgstringtable.csv  UTF-8    (cliente - fora deste repo)

EXCECOES CONHECIDAS estao na lista UPSTREAM_UTF8 abaixo: arquivos que
vieram do rAthena ja em UTF-8, ou ja com dano do proprio upstream. Nao
adianta consertar - o merge seguinte traz de volta.
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (prefixo do caminho, extensoes, encoding esperado)
REGRAS = [
    ('npc', ('.txt', '.yml'), 'cp1252'),
    ('conf', ('.txt', '.conf'), 'cp1252'),
    ('db', ('.yml', '.txt'), 'cp1252'),
    ('docs', ('.md',), 'utf-8'),
]

# Arquivos do upstream que ja nascem em UTF-8 (ou ja vem estragados de la).
# Consertar nao adianta: o proximo merge com rathena/rathena desfaz.
UPSTREAM_UTF8 = {
    'npc/custom/official/GeffenMagicTournament.txt',
    'npc/quests/skills/assassin_skills.txt',
    'npc/re/quests/juno_monster_society.txt',
    'npc/re/quests/quests_16_1.txt',
    'conf/battle/battle.conf',            # ja vem com BOM do rAthena
    'npc/re/quests/quests_eclage.txt',
    'db/re/mob_db.yml',
    'conf/msg_conf/map_msg_chn.conf',
    'conf/msg_conf/map_msg_grm.conf',
    'db/re/item_db_equip.yml',
    'db/re/item_db_etc.yml',
    'db/re/item_db_usable.yml',
    'db/import/item_randomopt_db.yml',
    'db/import/item_randomopt_group.yml',
}

IGNORAR_PASTA = {'.git', 'node_modules', '__pycache__', 'build', '3rdparty', 'tools'}


def classificar(caminho):
    dados = open(caminho, 'rb').read()
    if not dados:
        return 'vazio', 0
    if dados.startswith(b'\xef\xbb\xbf'):
        return 'bom', dados.count(b'\xef\xbf\xbd')
    altos = sum(1 for b in dados if b > 127)
    if not altos:
        return 'ascii', 0
    quebrados = dados.count(b'\xef\xbf\xbd')
    try:
        dados.decode('utf-8')
    except UnicodeDecodeError:
        return 'cp1252', 0
    return ('corrompido' if quebrados else 'utf-8'), quebrados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tudo', action='store_true', help='lista tambem o que esta certo')
    args = ap.parse_args()

    danos, avisos, ok = [], [], 0
    for prefixo, exts, esperado in REGRAS:
        base = os.path.join(RAIZ, prefixo)
        for pasta, subs, arquivos in os.walk(base):
            subs[:] = [s for s in subs if s not in IGNORAR_PASTA]
            for nome in arquivos:
                if not nome.endswith(exts):
                    continue
                cheio = os.path.join(pasta, nome)
                rel = os.path.relpath(cheio, RAIZ).replace(os.sep, '/')
                estado, quebrados = classificar(cheio)

                # A excecao vale para QUALQUER estado, inclusive BOM: sao
                # arquivos que o merge com o upstream reescreve de qualquer jeito.
                if estado in ('ascii', 'vazio') or rel in UPSTREAM_UTF8:
                    ok += 1
                    continue
                if estado == 'corrompido':
                    danos.append((rel, 'CORROMPIDO: %d acentos viraram U+FFFD' % quebrados))
                elif estado == 'bom':
                    danos.append((rel, 'BOM no inicio do arquivo'))
                elif estado.replace('-', '') != esperado.replace('-', ''):
                    avisos.append((rel, 'esta em %s, esperado %s' % (estado, esperado)))
                else:
                    ok += 1
                    if args.tudo:
                        print('  ok   %-58s %s' % (rel, estado))

    for rel, msg in danos:
        print('DANO   %-58s %s' % (rel, msg))
    for rel, msg in avisos:
        print('AVISO  %-58s %s' % (rel, msg))

    print()
    print('%d arquivos conferidos, %d com dano, %d com aviso' % (ok + len(danos) + len(avisos), len(danos), len(avisos)))
    if danos:
        print()
        print('DANO nao tem conserto automatico: o U+FFFD nao diz qual acento era.')
        print('Conserte palavra por palavra e regrave em cp1252. Depois confira que')
        print('o arquivo NAO decodifica mais como UTF-8 - se decodificar, sobrou dano.')
    return 1 if danos else 0


if __name__ == '__main__':
    sys.exit(main())
