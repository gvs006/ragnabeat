# -*- coding: utf-8 -*-
"""
Gera as palettes de cor de roupa que faltam nos corpos MONTADOS.

    python gerar-palettes-montaria.py --dry        so mede, nao grava
    python gerar-palettes-montaria.py --teste      gera 1 caso, para olhar
    python gerar-palettes-montaria.py              gera tudo

O PROBLEMA
Em 02/set/2026 uma Bruxa montou e o cliente passou a dar erro de palette,
inutilizando a personagem. A montaria existe para classe antiga (a raposa da
maga); o defeito e nosso.

O palette.grf (pacote Kamishi, 111 MB) estendeu para 700 cores APENAS os corpos
normais. Os 34 corpos montados do cliente ficaram com as cores oficiais do
data.grf:

    하이위저드     (Bruxa, normal)    700 cores (0..699)
    여우하이위저드  (Bruxa na raposa)    4 cores (0..3)

Montar com cor acima do teto faz o cliente procurar um .pal inexistente.
Como conf/import/battle_conf.txt permite max_cloth_color 699, qualquer jogador
que passe pelo Estilista e depois monte trava do mesmo jeito.

COMO A GERACAO FUNCIONA, E POR QUE ELA E CORRETA
Um .pal tem 256 entradas RGBA (1024 bytes). Comparando as 4 cores OFICIAIS de
um corpo (as do data.grf - o palette.grf sobrescreve ate a cor 0, entao a
derivacao TEM que ler so o data.grf), os indices que mudam sao os que a cor de
roupa controla. Medido na Bruxa feminina:

    corpo normal  (하이위저드_여)     21 indices variam  -> a roupa
    corpo montado (여우하이위저드_여)  27 indices variam  -> roupa + montaria

A diferenca, 6 indices (235, 237-239, 252-253), e A RAPOSA.

E o dado que fecha o algoritmo: uma cor custom do palette.grf muda 208 dos 256
indices - repinta o personagem quase inteiro, nao so a roupa - mas NUNCA toca
os 6 indices da montaria. Conferido nas cores 125, 400 e 699.

Entao a geracao da cor N do corpo montado e:

    saida = palette N do corpo NORMAL (custom, inteira)
    saida[indices da montaria] = palette 0 do corpo MONTADO

O personagem fica com o visual custom COMPLETO (os 208 indices), e a montaria
volta a cor original. Nada e chutado: os indices da montaria saem por diferenca
dos proprios arquivos oficiais.

NOME DOS ARQUIVOS
O cliente monta o caminho com bytes cp949 crus e chama a API ANSI do Windows.
Em disco isso vira o nome "mojibake" - os mesmos bytes lidos como latin1. E a
convencao que os sprites soltos ja usam (data/sprite/¾ÆÀÌÅÛ/...). Ver
docs/encoding.md.

A pasta data/ solta vence o GRF porque o patch DataFolderFirst esta aplicado.
"""
import collections
import re
import sys
from pathlib import Path

# os nomes de job sao coreanos; o console do Windows e cp1252
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grf_listar as G

BS = chr(92)
CLIENTE = Path(r'C:/RagnaClient/RagnaBeat.Dev')
GRFS = ['data.grf', 'palette.grf']
DEST = CLIENTE / 'data' / 'palette' / '\ubab8'.encode('cp949').decode('latin1')
PASTA = 'data' + BS + 'palette' + BS + '\ubab8' + BS
GENEROS = ['\ub0a8', '\uc5ec']          # 남 masculino, 여 feminino
COR_MAX = 699                            # bate com max_cloth_color
RE_PAL = re.compile(r'^(.*)_([^_]+)_(\d+)\.pal$')


def catalogar(apenas=None):
    """{(job, genero): {cor: (grf, entrada)}} dos .pal de corpo.

    `apenas` limita a um GRF. E preciso porque o palette.grf sobrescreve as
    cores 0..3 do corpo normal - derivar os indices dali daria 60 em vez de 21.
    """
    cat = collections.defaultdict(dict)
    for nome_grf in (apenas or GRFS):
        caminho = str(CLIENTE / nome_grf)
        try:
            ents, _ = G.ler_tabela(caminho)
        except Exception as e:
            print('  !! nao consegui ler %s: %s' % (nome_grf, e))
            continue
        for e in ents:
            bruto = e[0].decode('cp949', 'replace') if isinstance(e[0], bytes) else str(e[0])
            s = bruto.replace('/', BS)
            if PASTA not in s:
                continue
            m = RE_PAL.match(s.split(BS)[-1])
            if not m:
                continue
            job, gen, cor = m.group(1), m.group(2), int(m.group(3))
            # o palette.grf entra depois e tem prioridade, igual ao DATA.ini
            cat[(job, gen)][cor] = (caminho, e)
    return cat


def _varia(cat, job, gen):
    """Indices RGBA que mudam entre as cores oficiais deste corpo."""
    if (job, gen) not in cat:
        return None
    cores = sorted(cat[(job, gen)])[:8]
    if len(cores) < 2:
        return None
    pals = [G.ler_arquivo(*cat[(job, gen)][c]) for c in cores]
    pals = [p for p in pals if p and len(p) == 1024]
    if len(pals) < 2:
        return None
    return {i for i in range(256)
            if len({bytes(p[i * 4:i * 4 + 4]) for p in pals}) > 1}


def indices_da_montaria(oficial, mont, norm, gen):
    """O que o corpo montado tem de variavel a mais que o normal = o bicho."""
    vm, vn = _varia(oficial, mont, gen), _varia(oficial, norm, gen)
    if vm is None or vn is None:
        return None
    return sorted(vm - vn)


def montados(cat):
    """{montado: normal} - corpo montado e o que termina com um nome base."""
    jobs = {j for j, _ in cat}
    # corpo "base" = o que recebeu a extensao do palette.grf (centenas de cores)
    base = set()
    for j in jobs:
        for g in GENEROS:
            if (j, g) in cat and max(cat[(j, g)], default=0) > 100:
                base.add(j)
                break
    par = {}
    ordenada = sorted(base, key=len, reverse=True)
    for j in jobs:
        if j in base:
            continue
        # Familia coreana: o nome do bicho vem na FRENTE (여우하이위저드).
        for b in ordenada:
            if j.endswith(b) and j != b:
                par[j] = b
                break
        else:
            # Familia inglesa: o sufixo e "_riding" (arch_mage_riding). Sem este
            # ramo os 22 corpos de 4a classe ficavam de fora - foi o bug que
            # deixou meister_riding e night_watch_riding com 8 cores.
            if j.lower().endswith('_riding'):
                cand = j[:-len('_riding')]
                if cand in base:
                    par[j] = cand
                else:
                    for b in ordenada:
                        if cand.startswith(b):
                            par[j] = b
                            break
    return par


def gerar_um(cat, mont, norm, gen, cor, idx_montaria):
    # a custom inteira (personagem repintado por completo)...
    saida = G.ler_arquivo(*cat[(norm, gen)][cor])
    # ...e o bicho de volta na cor original dele
    bicho = G.ler_arquivo(*cat[(mont, gen)][min(cat[(mont, gen)])])
    if not saida or not bicho or len(saida) != 1024 or len(bicho) != 1024:
        return None
    saida = bytearray(saida)
    for i in idx_montaria:
        saida[i * 4:i * 4 + 4] = bicho[i * 4:i * 4 + 4]
    return bytes(saida)


def nome_disco(job, gen, cor):
    return ('%s_%s_%d.pal' % (job, gen, cor)).encode('cp949').decode('latin1')


def main():
    dry = '--dry' in sys.argv
    teste = '--teste' in sys.argv

    print('lendo os GRFs...')
    cat = catalogar()                       # merge: o palette.grf vence
    oficial = catalogar(['data.grf'])       # so kRO, para derivar os indices
    par = montados(cat)
    print('corpos montados encontrados: %d' % len(par))

    if teste:
        # o caso da Katy: Bruxa feminina, cor 125
        HW = '\ud558\uc774\uc704\uc800\ub4dc'
        par = {'\uc5ec\uc6b0' + HW: HW}
        GEN, CORES = ['\uc5ec'], [125]
    else:
        GEN, CORES = GENEROS, None

    DEST.mkdir(parents=True, exist_ok=True)
    total = pulados = 0
    for mont in sorted(par):
        norm = par[mont]
        for gen in GEN:
            if (mont, gen) not in cat or (norm, gen) not in cat:
                continue
            idx = indices_da_montaria(oficial, mont, norm, gen)
            if idx is None:
                print('  !! %s_%s: nao consegui derivar os indices da montaria' % (mont, gen))
                continue
            teto = max(cat[(mont, gen)])
            alvos = CORES if CORES else range(teto + 1, COR_MAX + 1)
            feitos = 0
            for cor in alvos:
                if cor in cat[(mont, gen)]:
                    pulados += 1
                    continue
                if cor not in cat[(norm, gen)]:
                    pulados += 1
                    continue
                dados = gerar_um(cat, mont, norm, gen, cor, idx)
                if dados is None:
                    pulados += 1
                    continue
                if not dry:
                    (DEST / nome_disco(mont, gen, cor)).write_bytes(dados)
                feitos += 1
            total += feitos
            print('  %-22s %s  teto oficial %2d  -> %4d palettes (%d indices da montaria preservados)'
                  % (mont, gen, teto, feitos, len(idx)))

    print()
    print('%s: %d palettes, %d puladas' % ('SIMULACAO' if dry else 'GRAVADAS', total, pulados))
    if not dry:
        print('destino: %s' % DEST)


if __name__ == '__main__':
    main()
