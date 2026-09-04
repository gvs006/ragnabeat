# -*- coding: utf-8 -*-
"""
Troca as texturas da tela de login e do menu ESC pelas PT-BR do RO LATAM.

Sao as 111 imagens onde o texto esta PINTADO dentro do BMP - nao existe string
para traduzir. 33 esc_*.bmp (as abas do menu ESC) mais 78 arquivos de
login_interface\\, todos em data\\texture\\<pasta de UI em cp949>\\.

Fonte: C:\\Gravity\\Ragnarok\\data.grf. A raiz data\\texture\\ desse GRF e a
PT-BR - as subarvores data\\english\\ e data\\spanish\\ e que sao os overrides,
e nao existe data\\portuguese\\. E da mesma raiz que ja saiu o msgstringtable.

Nem toda imagem pode ser trocada. O nosso cliente e kRO 2025-04-16 e o LATAM e
de um episodio mais velho, entao parte da arte mudou de tamanho (warning.bmp e
1920x1440 aqui e 640x480 la) e parte nem existe la (os botoes de OTP, por
exemplo). Trocar assim quebraria o layout. Por isso a triagem:

    TROCA    mesmas dimensoes e mesmo bpp, conteudo diferente -> instalavel
    IGUAL    ja e a mesma imagem
    DIVERGE  dimensao, bpp ou formato diferente -> fica de fora
    SEM PAR  nao existe no GRF do LATAM

    python gen_texturas_ptbr.py           extrai, tria e instala as TROCA
    python gen_texturas_ptbr.py --dry     extrai e tria, nao instala nada

O destino e a pasta solta data\\texture\\, que vence o GRF pelo patch
DataFolderFirst - mesmo caminho que o cashshop customizado ja usa. O original
fica ao lado como <nome>.antes-latam.bmp; o build.py ignora '*.antes-*'.
"""
import struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grf_listar import ler_tabela, ler_arquivo

AQUI = Path(__file__).parent
RAIZ = AQUI.parents[1]                       # ...\RagnaBeat.Dev
NOSSO_GRF = RAIZ / 'data.grf'
LATAM_GRF = Path(r'C:\Gravity\Ragnarok\data.grf')
EXTRAIDO = AQUI / '_extraido' / 'texturas'
TRIAGEM = EXTRAIDO / 'TRIAGEM.txt'

BS = chr(92).encode()
# 'À¯ÀúÀÎÅÍÆäÀÌ½º' - a pasta de UI, em cp949. Mesmo filtro do _gerar_lista.py.
UI = b'\xc0\xaf\xc0\xfa\xc0\xce\xc5\xcd\xc6\xe4\xc0\xcc\xbd\xba'


def alvo(nome):
    ln = nome.lower()
    return UI.lower() in ln and (BS + b'esc_' in ln or b'login_interface' + BS in ln)


def formato(dados):
    """(largura, altura, bpp) de um BMP, ou None se nao for BMP."""
    if len(dados) < 30 or dados[:2] != b'BM':
        return None
    larg, alt = struct.unpack('<ii', dados[18:26])
    return (larg, alt, struct.unpack('<H', dados[28:30])[0])


def caminho_disco(nome, base):
    """Monta o caminho preservando os bytes cp949 do nome interno. Decodificar
    em cp1252 devolve exatamente a sequencia que o Windows converte de volta
    quando o cliente abre o arquivo pela API ANSI - ver docs/cliente/leia-me.md."""
    return base / nome.decode('cp1252').replace(chr(92), '/')


def extrair_todos(grf, entradas, base):
    saida = {}
    for e in entradas:
        dados = ler_arquivo(grf, e)
        destino = caminho_disco(e[0], base)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(dados)
        saida[e[0].lower()] = dados
    return saida


for g in (NOSSO_GRF, LATAM_GRF):
    if not g.exists():
        raise SystemExit('nao achei %s' % g)

nossos = [e for e in ler_tabela(NOSSO_GRF)[0] if alvo(e[0])]
latam = {e[0].lower(): e for e in ler_tabela(LATAM_GRF)[0] if alvo(e[0])}
print('alvos no nosso data.grf : %d' % len(nossos))
print('alvos no GRF do LATAM   : %d' % len(latam))

print('extraindo...')
dados_nossos = extrair_todos(NOSSO_GRF, nossos, EXTRAIDO / 'nosso')
dados_latam = extrair_todos(LATAM_GRF, [latam[k] for k in latam], EXTRAIDO / 'latam')

triado = {'TROCA': [], 'IGUAL': [], 'DIVERGE': [], 'SEM PAR': []}
for e in sorted(nossos, key=lambda x: x[0]):
    nome = e[0]
    nosso = dados_nossos[nome.lower()]
    par = dados_latam.get(nome.lower())
    curto = nome.decode('cp1252').split(chr(92), 2)[-1]

    if par is None:
        triado['SEM PAR'].append((curto, 'nao existe no GRF do LATAM'))
    elif nosso == par:
        triado['IGUAL'].append((curto, ''))
    else:
        fa, fb = formato(nosso), formato(par)
        if fa is None or fb is None:
            triado['DIVERGE'].append((curto, 'nao e BMP nos dois lados'))
        elif fa != fb:
            triado['DIVERGE'].append(
                (curto, 'nosso %dx%d %dbpp, latam %dx%d %dbpp' % (fa + fb)))
        else:
            triado['TROCA'].append((curto, '%dx%d %dbpp' % fa))

linhas = []
for cat in ('TROCA', 'DIVERGE', 'SEM PAR', 'IGUAL'):
    linhas.append('=== %s (%d) ===' % (cat, len(triado[cat])))
    for curto, obs in triado[cat]:
        linhas.append('  %-52s %s' % (curto, obs))
    linhas.append('')

TRIAGEM.parent.mkdir(parents=True, exist_ok=True)
TRIAGEM.write_text('\r\n'.join(linhas), encoding='cp1252')
print()
print('\n'.join(linhas))
print('triagem salva em', TRIAGEM)

if '--dry' in sys.argv:
    print()
    print('>>> DRY RUN - nada instalado')
    raise SystemExit(0)

trocar = set(c for c, _ in triado['TROCA'])
instalados = 0
for e in sorted(nossos, key=lambda x: x[0]):
    if e[0].decode('cp1252').split(chr(92), 2)[-1] not in trocar:
        continue
    destino = caminho_disco(e[0], RAIZ)
    destino.parent.mkdir(parents=True, exist_ok=True)
    backup = destino.with_name(destino.name.replace('.', '.antes-latam.', 1))
    if destino.exists() and not backup.exists():
        backup.write_bytes(destino.read_bytes())
    elif not destino.exists() and not backup.exists():
        backup.write_bytes(dados_nossos[e[0].lower()])   # o original vinha do GRF
    destino.write_bytes(dados_latam[e[0].lower()])
    instalados += 1

print()
print('instalados em %s: %d arquivos' % (RAIZ / 'data' / 'texture', instalados))
