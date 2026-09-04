# -*- coding: utf-8 -*-
"""
Traz para a pasta data/ do cliente os sprites de visual que o GRF do build nao
tem e o GRF do LATAM tem.

    python docs/cliente/importar-sprites-latam.py --dry    so relata
    python docs/cliente/importar-sprites-latam.py          copia

POR QUE EXISTE
O data.grf do build (kRO 2025-04-16) e o do cliente LATAM antigo NAO sao um
superconjunto do outro. Sao 268.764 arquivos contra 214.224, e cada um tem o
que o outro nao tem: o do build trouxe mapas e efeitos novos (issgard, heroage,
20th_firework) e ficou sem 71 mil arquivos de sprite de capa que o LATAM tem.

O resultado pratico e que centenas de trajes que existem no db/re, tem nome
PT-BR e tem View viravam SEM SPRITE - nao porque o sprite nao exista, mas
porque nao esta NESTE GRF.

COMO ENTRA
Os arquivos vao para a pasta data/ solta, nao para dentro de um GRF. O cliente
tem o patch DataFolderFirst, entao data/ vence o GRF - e o mesmo mecanismo que
ja usamos para o pcjobname.lub e para a tabela de preview. Repackar um GRF de
4 GB para acrescentar alguns MB seria caro e exigiria o GRF Editor, que e GUI.

O build.py copia data/ inteira, entao basta rodar isto antes do build.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLIENTE = Path(r'C:/RagnaClient/RagnaBeat.Dev')
GRF_BUILD = CLIENTE / 'data.grf'
GRF_LATAM = Path(r'C:/RagnaClient/old-client-apagar-dps/data.grf')
LATAM_LUA = CLIENTE / 'DEVTOOLS/PTBR/iteminfo_ptBR.lua'
DB_RE = REPO / 'db/re/item_db_equip.yml'
DESTINO = CLIENTE / 'data'

BS = chr(92)
SLOTS = ('Costume_Head_Top', 'Costume_Head_Mid', 'Costume_Head_Low',
         'Costume_Garment')
RE_ESC = re.compile(re.escape(BS) + r'(\d{1,3})')


def cru(s):
    return s.encode('cp949', 'replace').decode('latin-1').lower()


def desescapar(s):
    s = RE_ESC.sub(lambda m: chr(int(m.group(1))), s)
    return s.encode('latin-1', 'replace').decode('utf-8', 'replace')


def grf():
    spec = importlib.util.spec_from_file_location(
        'grf', REPO / 'docs/cliente/grf_listar.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def indice(mod, caminho):
    arqs, _ = mod.ler_tabela(caminho)
    return {e[0].decode('latin-1').lower(): e for e in arqs}


def dados_latam():
    txt = LATAM_LUA.read_bytes().decode('cp1252', 'replace')
    fora = {}
    for m in re.finditer(r'\[(\d+)\]\s*=\s*\{(.*?)\n  \}', txt, re.S):
        b = m.group(2)
        n = re.search(r'(?<!un)identifiedDisplayName\s*=\s*"([^"]*)"', b)
        r = re.search(r'(?<!un)identifiedResourceName\s*=\s*"([^"]*)"', b)
        if n:
            fora[int(m.group(1))] = (desescapar(n.group(1)),
                                     desescapar(r.group(1)) if r else '')
    return fora


def trajes():
    """Id -> (aegis, slots, tem_view) para todo traje do db/re."""
    t = DB_RE.read_bytes().decode('latin-1')
    fora = {}
    for b in re.split(r'(?m)^(?=  - Id: )', t):
        m = re.match(r'  - Id: (\d+)\s*$', b.split('\n')[0])
        if not m:
            continue
        slots = [k for k in SLOTS
                 if re.search(r'(?m)^      %s: true\s*$' % k, b)]
        if not slots:
            continue
        a = re.search(r'(?m)^    AegisName: (\S+)\s*$', b)
        v = re.search(r'(?m)^    View: (\d+)\s*$', b)
        fora[int(m.group(1))] = (a.group(1) if a else '?', slots,
                                 v is not None)
    return fora


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--so-cabeca', action='store_true',
                    dest='so_cabeca',
                    help='pula as capas, que custam ~200 arquivos cada')
    args = ap.parse_args()

    for p in (GRF_BUILD, GRF_LATAM, LATAM_LUA):
        if not p.exists():
            sys.exit('ERRO: nao achei %s' % p)

    mod = grf()
    print('lendo os dois GRFs...')
    build = indice(mod, GRF_BUILD)
    latam = indice(mod, GRF_LATAM)
    print('  build %d arquivos | LATAM %d' % (len(build), len(latam)))

    dir_item = 'data' + BS + 'sprite' + BS + cru('아이템') + BS
    dir_acc = 'data' + BS + 'sprite' + BS + cru('악세사리') + BS
    pref_capa = 'data' + BS + 'sprite' + BS + cru('로브') + BS

    nomes_latam = dados_latam()
    itens = trajes()

    # Falta no build, existe no LATAM. Um item so entra se TUDO que ele precisa
    # estiver la - meio sprite e pior que nenhum: o cliente abre caixa de erro.
    precisa = {}
    for oid, (aegis, slots, tem_view) in sorted(itens.items()):
        if not tem_view:
            continue                      # traje de efeito nao usa sprite
        nome, res = nomes_latam.get(oid, ('', ''))
        if not nome or not res:
            continue                      # sem texto PT-BR, nao entra mesmo

        alvos = [dir_item + cru(res) + '.spr', dir_item + cru(res) + '.act']
        if 'Costume_Garment' in slots:
            base = pref_capa + res.lower() + BS
            alvos += [n for n in latam if n.startswith(base)]
        else:
            for sx in ('남', '여'):
                base = dir_acc + cru(sx) + BS + cru(sx + '_' + res)
                alvos += [base + '.spr', base + '.act']

        # o .act as vezes nao existe nem num nem noutro; so o .spr e obrigatorio
        obrig = [a for a in alvos if a.endswith('.spr')]
        if all(a in build for a in obrig):
            continue                      # o build ja resolve este
        faltando = [a for a in alvos if a not in build and a in latam]
        if not faltando:
            continue
        if not all(a in build or a in latam for a in obrig):
            continue                      # nem juntos completam - pula
        eh_capa = 'Costume_Garment' in slots
        precisa[oid] = (nome, faltando, eh_capa)

    def peso(arqs):
        # indice 2 e o tamanho comprimido alinhado (o que ocupa no GRF);
        # o 3 e o tamanho real, que e o que vai ocupar solto em data/
        return (sum(latam[a][2] for a in arqs), sum(latam[a][3] for a in arqs))

    cabeca = {o: v for o, v in precisa.items() if not v[2]}
    capas = {o: v for o, v in precisa.items() if v[2]}

    print()
    print('%-8s %7s %9s %12s %12s' % ('grupo', 'itens', 'arquivos',
                                      'no GRF', 'solto em data/'))
    for rotulo, grupo in (('cabeca', cabeca), ('capa', capas),
                          ('TOTAL', precisa)):
        arqs = [a for v in grupo.values() for a in v[1]]
        c, r = peso(arqs)
        print('%-8s %7d %9d %9.1f MB %9.1f MB'
              % (rotulo, len(grupo), len(arqs), c / 1048576.0, r / 1048576.0))

    # A capa custa caro por um motivo estrutural: o sprite dela e por CLASSE.
    # Uma capa so tem 200 e poucos arquivos (cada job, cada sexo, cada evolucao),
    # enquanto um traje de cabeca tem 6. Trazer todas multiplicaria o download
    # do tester por um fator que nao se justifica num teste fechado.
    if capas:
        maior = max(capas.items(), key=lambda kv: len(kv[1][1]))
        print()
        print('a capa mais cara: %s = %d arquivos'
              % (maior[1][0][:40], len(maior[1][1])))

    print()
    for oid in list(cabeca)[:10]:
        print('  %-7d %-42s %d arquivos'
              % (oid, cabeca[oid][0][:42], len(cabeca[oid][1])))
    if len(cabeca) > 10:
        print('  ... e mais %d de cabeca' % (len(cabeca) - 10))

    if args.so_cabeca:
        precisa = cabeca
        print()
        print('--so-cabeca: as capas ficam de fora')

    if args.dry:
        print('\n>>> DRY RUN - nada copiado')
        return 0

    escritos = falhas = 0
    for _oid, (_nome, arqs, _capa) in precisa.items():
        for a in arqs:
            alvo = DESTINO / Path(a[len('data' + BS):].replace(BS, '/'))
            try:
                d = mod.ler_arquivo(GRF_LATAM, latam[a])
            except Exception as erro:
                print('  falhou %s: %s' % (a, erro))
                falhas += 1
                continue
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(d)
            escritos += 1
    print()
    print('gravados %d arquivos em %s (%d falhas)' % (escritos, DESTINO, falhas))
    print('Agora: python docs/gerar-visuais.py  e depois o build.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
