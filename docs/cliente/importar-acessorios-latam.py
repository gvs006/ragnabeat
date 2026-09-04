# -*- coding: utf-8 -*-
"""
Traz do GRF do LATAM as tabelas de acessorio e os sprites de chapeu que o GRF
do build nao tem.

    python docs/cliente/importar-acessorios-latam.py --dry
    python docs/cliente/importar-acessorios-latam.py

POR QUE EXISTE
O cliente resolve o sprite de um traje de CABECA assim:

    View do item -> accessoryid.lub -> ACCESSORY_* -> accname.lub -> nome.spr

As duas tabelas ficam em data/luafiles514/lua files/datainfo/. As do nosso
build tem 2.670 entradas e param no View 2689. As do LATAM tem 2.857 e vao ate
2877 - ou seja, para acessorio o GRF "antigo" e o mais NOVO dos dois.

Por isso 28 trajes reprovaram com "sem entrada": o View deles e maior do que a
tabela do build conhece. Nao e arte faltando, e tabela velha.

E SEGURO TROCAR AS TABELAS
Conferido antes de escrever isto:
  - 0 chaves existem so no build (nada se perde)
  - 0 chaves tem View diferente entre os dois (nada se desloca)
A do LATAM e superconjunto estrito. As duas vao para a pasta data/ solta, que
vence o GRF pelo patch DataFolderFirst.

O QUE ELE COPIA
1. datainfo/accessoryid.lub e datainfo/accname.lub
2. todo .spr/.act de acessorio que a tabela nova referencia e que o build nao
   tem - so o que falta, nao a pasta inteira.
"""
import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLIENTE = Path(r'C:/RagnaClient/RagnaBeat.Dev')
GRF_BUILD = CLIENTE / 'data.grf'
GRF_LATAM = Path(r'C:/RagnaClient/old-client-apagar-dps/data.grf')
DESTINO = CLIENTE / 'data'
BS = chr(92)
BASE_DI = 'data' + BS + 'luafiles514' + BS + 'lua files' + BS + 'datainfo' + BS


def cru(s):
    return s.encode('cp949', 'replace').decode('latin-1').lower()


def carregar():
    spec = importlib.util.spec_from_file_location(
        'grf', REPO / 'docs/cliente/grf_listar.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    spec2 = importlib.util.spec_from_file_location(
        'lub', REPO / 'docs/cliente/lub_constantes.py')
    lub = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(lub)
    return mod, lub


def indice(mod, g):
    arqs, _ = mod.ler_tabela(g)
    return {e[0].decode('latin-1').lower(): e for e in arqs}


def tabela(mod, lub, g, por, caminho, tipo):
    e = por.get(caminho)
    if not e:
        return {}
    with tempfile.NamedTemporaryFile(suffix='.lub', delete=False) as f:
        f.write(mod.ler_arquivo(g, e))
        tmp = f.name
    fora = {}
    try:
        for c in lub.constantes(tmp):
            for a, b in zip(c, c[1:]):
                if (isinstance(a, str) and a.startswith('ACCESSORY_')
                        and isinstance(b, tipo)):
                    fora.setdefault(a, b)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return fora


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--tudo', action='store_true',
                    help='copia sprite de TODO acessorio novo (143 MB), e nao '
                         'so o que os nossos trajes usam')
    args = ap.parse_args()
    for p in (GRF_BUILD, GRF_LATAM):
        if not p.exists():
            sys.exit('ERRO: nao achei %s' % p)

    mod, lub = carregar()
    print('lendo os dois GRFs...')
    pb, pl = indice(mod, GRF_BUILD), indice(mod, GRF_LATAM)

    vb = tabela(mod, lub, GRF_BUILD, pb, BASE_DI + 'accessoryid.lub', float)
    vl = tabela(mod, lub, GRF_LATAM, pl, BASE_DI + 'accessoryid.lub', float)
    nb = tabela(mod, lub, GRF_BUILD, pb, BASE_DI + 'accname.lub', str)
    nl = tabela(mod, lub, GRF_LATAM, pl, BASE_DI + 'accname.lub', str)
    print('  accessoryid  build %d  latam %d' % (len(vb), len(vl)))
    print('  accname      build %d  latam %d' % (len(nb), len(nl)))

    # A troca so e segura se o LATAM cobrir tudo que o build tem.
    perdidas = (set(vb) - set(vl)) | (set(nb) - set(nl))
    divergentes = [k for k in set(vb) & set(vl) if int(vb[k]) != int(vl[k])]
    if perdidas or divergentes:
        sys.exit('ERRO: a tabela do LATAM NAO e superconjunto - %d chaves se '
                 'perderiam, %d Views mudariam. Nao troque.'
                 % (len(perdidas), len(divergentes)))
    print('  tabela do LATAM e superconjunto estrito: seguro trocar')

    dir_acc = 'data' + BS + 'sprite' + BS + cru('악세사리') + BS

    # Por padrao so vem o sprite que ALGUM traje nosso usa. Copiar a pasta
    # inteira sao 2.668 arquivos e 143 MB soltos - 21% a mais no download do
    # tester para trazer acessorio que nenhum item do db referencia.
    usados = None
    if not args.tudo:
        import re
        # So os que PODEM entrar no jogo: traje de cabeca do db/re que tenha
        # nome PT-BR no dump do LATAM. Sem esse corte vem sprite de 2.445 Views,
        # a maioria de item renewal que nunca vai para o nosso db.
        lua = (CLIENTE / 'DEVTOOLS/PTBR/iteminfo_ptBR.lua').read_bytes().decode('cp1252', 'replace')
        com_texto = set(int(x) for x in re.findall(r'\[(\d+)\]\s*=\s*\{', lua))
        db = (REPO / 'db/re/item_db_equip.yml').read_bytes().decode('latin-1')
        views = set()
        SL = ('Costume_Head_Top', 'Costume_Head_Mid', 'Costume_Head_Low')
        for b in re.split(r'(?m)^(?=  - Id: )', db):
            m0 = re.match(r'  - Id: (\d+)\s*$', b.split(chr(10))[0])
            if not m0 or int(m0.group(1)) not in com_texto:
                continue
            if not any(re.search(r'(?m)^      %s: true\s*$' % k, b) for k in SL):
                continue
            m = re.search(r'(?m)^    View: (\d+)\s*$', b)
            if m:
                views.add(int(m.group(1)))
        por_view = {int(v): k for k, v in vl.items()}
        usados = {por_view[v] for v in views if v in por_view}
        print('  cabeca com texto PT-BR: %d Views, %d com entrada na tabela'
              % (len(views), len(usados)))

    faltando = []
    for chave, spr in nl.items():
        if not spr:
            continue
        if usados is not None and chave not in usados:
            continue
        for sx in ('남', '여'):
            for ext in ('.spr', '.act'):
                alvo = dir_acc + cru(sx) + BS + cru(sx) + spr.lower() + ext
                if alvo in pb:
                    continue
                if alvo in pl:
                    faltando.append(alvo)

    bytes_ = sum(pl[a][3] for a in faltando)
    print()
    print('tabelas a copiar : 2')
    print('sprites a copiar : %d  (%.1f MB soltos)' % (len(faltando), bytes_ / 1048576.0))

    if args.dry:
        print('\n>>> DRY RUN - nada copiado')
        return 0

    for nome in (BASE_DI + 'accessoryid.lub', BASE_DI + 'accname.lub'):
        alvo = DESTINO / Path(nome[len('data' + BS):].replace(BS, '/'))
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(mod.ler_arquivo(GRF_LATAM, pl[nome]))
        print('  tabela  %s' % alvo.name)

    n = 0
    for a in faltando:
        alvo = DESTINO / Path(a[len('data' + BS):].replace(BS, '/'))
        alvo.parent.mkdir(parents=True, exist_ok=True)
        try:
            alvo.write_bytes(mod.ler_arquivo(GRF_LATAM, pl[a]))
            n += 1
        except Exception as erro:
            print('  falhou %s: %s' % (a, erro))
    print()
    print('gravados %d sprites em %s' % (n, DESTINO))
    print('Agora: python docs/gerar-visuais.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
