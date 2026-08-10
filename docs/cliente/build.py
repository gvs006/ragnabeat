# -*- coding: utf-8 -*-
"""
Monta a pasta de cliente que vai ser entregue aos jogadores.

    python build.py                  cria a proxima versao (patch +1)
    python build.py --minor          sobe o minor  (0.0.7 -> 0.1.0)
    python build.py --major          sobe o major  (0.4.2 -> 1.0.0)
    python build.py --version 2.0.0  forca uma versao
    python build.py --dry            so mostra o que faria, nao escreve nada

O builder SELECIONA e COPIA, e mais nada. Ele nao reescreve clientinfo.xml,
nao recompila lua, nao encripta GRF. Isso e deliberado - o que ele poderia
passar a fazer esta em docs/cliente/build-release.md.

Nada aqui depende do nome desta pasta: tudo e relativo a este arquivo. Pode
renomear a pasta de desenvolvimento a vontade.

Os GRFs entram por HARDLINK, nao por copia - sao 4 GB e o disco e apertado.
Hardlink so funciona no mesmo volume; se falhar, cai para copia com aviso.
ATENCAO: hardlink compartilha o conteudo. Editar o GRF de um build in-place
altera o da pasta de desenvolvimento junto. Para GRF, que e so leitura, ok.
"""
import os, re, sys, shutil, fnmatch
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / 'config.yml'
VERSAO = RAIZ / 'version.txt'
DESTINO = RAIZ / 'builds'

TAM_EXE_ESPERADO = 14987776
ITENS_ESPERADOS = 5296

# Mesmas assinaturas do pos-warp.py - se mudarem la, mudam aqui.
CP949 = b'\xb5\x03\x00\x00'
SIG_949 = re.compile(rb'(?:\x68' + re.escape(CP949) + rb'(?!\xff\x15)|\xb8' + re.escape(CP949) + rb')')
SIG_SETMBCP = re.compile(rb'\x68' + re.escape(CP949) + rb'\xff\x15')

# Entram por hardlink em vez de copia.
POR_HARDLINK = ['*.grf']

# Pastas que nao vao para o jogador.
PASTAS_FORA = {
    'builds',          # os proprios builds
    'DEVTOOLS',        # WARP, patchers, decompiladores, exes candidatos - 600 MB
    '_exes_antigos',   # exes descartados
    'GameGuard',       # anticheat desativado pelo patch NoGGuard
    'PatchClient',     # recursos do patcher oficial kRO, nao usamos
    '_tmpEmblem',      # emblemas de guilda baixados NA SUA sessao
    'docs',
    '__pycache__',
}

# Criadas vazias no destino: o cliente escreve nelas, mas o conteudo e pessoal.
# savedata guarda UI, atalhos e janelas de chat DO DESENVOLVEDOR.
PASTAS_VAZIAS = {'savedata', 'Replay', 'memo'}

# Arquivos que nao vao para o jogador, por padrao de nome.
ARQUIVOS_FORA = [
    # ferramentas e documentacao
    '*.py', '*.bat', '*.ps1', '*.md', '*.yml',
    # artefatos do WARP
    '*.epi', '*.secure.txt',
    # backups e testes
    '*.antes-*', '*.TESTE-*', '*.servicetype-korea', '*.bak', '*.old', '*.old-*',
    # executaveis que nao sao o cliente
    'BASE_*.exe', 'Ragexe.exe*', 'RagnaBeat-*.exe', 'RagnaBeat.exe.*',
    'Ragnarok.exe', 'Setup.exe', 'unins000.*',
    # residuos do patcher e do anticheat oficiais do kRO
    'Patch.inf', 'patch_allow.txt', 'patch2.txt', 'RagHash.dat',
    'GameGuard.des', 'v3hunt.dll', 'Uninstall.ico',
    # dumps de trabalho da traducao
    'msgstringtable_EN.txt',
    # config do proprio builder
    'version.txt',
]


def ler_config():
    """Leitor minimo de 'chave: valor'. Evita dependencia de PyYAML."""
    if not CONFIG.exists():
        return {}
    cfg = {}
    for linha in CONFIG.read_text(encoding='utf-8').splitlines():
        linha = linha.split('#', 1)[0].strip()
        if ':' in linha:
            k, v = linha.split(':', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def ler_versao():
    if not VERSAO.exists():
        return (0, 0, 0)
    txt = VERSAO.read_text(encoding='utf-8').strip()
    p = txt.split('.')
    if len(p) != 3 or not all(x.isdigit() for x in p):
        sys.exit('ERRO: version.txt invalido: %r (esperado X.Y.Z)' % txt)
    return tuple(int(x) for x in p)


def excluido(rel: Path):
    if any(parte in PASTAS_FORA or parte in PASTAS_VAZIAS for parte in rel.parts[:-1]):
        return True
    if rel.parts[0] in PASTAS_FORA or (len(rel.parts) == 1 and rel.parts[0] in PASTAS_VAZIAS):
        return True
    return any(fnmatch.fnmatch(rel.name, p) for p in ARQUIVOS_FORA)


def por_hardlink(rel: Path):
    return any(fnmatch.fnmatch(rel.name.lower(), p) for p in POR_HARDLINK)


def coletar():
    """Devolve (copiar, linkar) como listas de caminhos relativos."""
    copiar, linkar = [], []
    for base, dirs, arqs in os.walk(RAIZ):
        dirs[:] = [d for d in sorted(dirs) if d not in PASTAS_FORA and d not in PASTAS_VAZIAS]
        for a in sorted(arqs):
            rel = (Path(base) / a).relative_to(RAIZ)
            if excluido(rel):
                continue
            (linkar if por_hardlink(rel) else copiar).append(rel)
    return copiar, linkar


def humano(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or u == 'GB':
            return '%.1f %s' % (n, u)
        n /= 1024


def verificar(saida, cfg):
    """Checagens que impedem entregar um cliente quebrado."""
    problemas, avisos = [], []

    exe = saida / 'RagnaBeat.exe'
    if not exe.exists():
        problemas.append('RagnaBeat.exe ausente')
    else:
        d = exe.read_bytes()
        if len(d) != TAM_EXE_ESPERADO:
            problemas.append('RagnaBeat.exe tem %d bytes, esperado %d' % (len(d), TAM_EXE_ESPERADO))
        n949 = len(SIG_949.findall(d))
        if n949:
            problemas.append('%d constantes cp949 nao trocadas - acentos vao falhar '
                             '(rode o pos-warp.py)' % n949)
        if len(SIG_SETMBCP.findall(d)) != 1:
            problemas.append('_setmbcp nao esta preservado em cp949')
        kro = re.findall(rb'kro-[a-z0-9-]+\.ragnarok\.co\.kr', d)
        if kro:
            problemas.append('%d enderecos da Gravity no exe - o cliente nao vai conectar' % len(kro))

    item = saida / 'SystemEN' / 'itemInfo_C.lua'
    if not item.exists():
        avisos.append('SystemEN/itemInfo_C.lua ausente - sem traducao de itens')
    else:
        b = item.read_bytes()
        n = len(re.findall(rb'^\s*\[(\d+)\]\s*=\s*\{', b, re.M))
        if n != ITENS_ESPERADOS:
            avisos.append('itemInfo_C.lua com %d itens, esperado %d' % (n, ITENS_ESPERADOS))
        if b.count(b'{') != b.count(b'}'):
            problemas.append('itemInfo_C.lua com chaves desbalanceadas - derruba o arquivo inteiro')
        if len(re.findall(rb'identifiedResourceName\s*=\s*""', b)):
            avisos.append('ha itens com resourceName vazio - esses ficam sem sprite')

    for g in ('data.grf', 'en.grf'):
        d_, o_ = saida / g, RAIZ / g
        if not d_.exists():
            problemas.append('%s ausente' % g)
        elif o_.exists() and d_.stat().st_size != o_.stat().st_size:
            problemas.append('%s com tamanho diferente da origem' % g)

    vazados = [str(p.relative_to(saida)) for p in saida.rglob('*')
               if p.is_file() and excluido(p.relative_to(saida))]
    if vazados:
        problemas.append('arquivos de desenvolvimento vazaram: %s' % ', '.join(vazados[:5]))

    ci = saida / 'data' / 'clientinfo.xml'
    if ci.exists() and cfg.get('servidor'):
        m = re.search(rb'<display>([^<]*)</display>', ci.read_bytes())
        if m and m.group(1).decode('latin-1') != cfg['servidor']:
            avisos.append('config.yml diz servidor=%r mas clientinfo.xml mostra <display>%s</display>'
                          % (cfg['servidor'], m.group(1).decode('latin-1')))
    return problemas, avisos


def main():
    args = sys.argv[1:]
    dry = '--dry' in args
    cfg = ler_config()
    servidor = cfg.get('servidor', 'RagnaBeat')
    padrao = cfg.get('padrao_pasta', '{servidor}ProdV{versao}')

    maj, mnr, pat = ler_versao()
    if '--version' in args:
        alvo = args[args.index('--version') + 1]
        if not re.fullmatch(r'\d+\.\d+\.\d+', alvo):
            sys.exit('ERRO: --version espera X.Y.Z')
        maj, mnr, pat = (int(x) for x in alvo.split('.'))
    elif '--major' in args:
        maj, mnr, pat = maj + 1, 0, 0
    elif '--minor' in args:
        mnr, pat = mnr + 1, 0
    versao = '%d.%d.%d' % (maj, mnr, pat)

    nome = padrao.format(servidor=servidor, versao=versao)
    saida = DESTINO / nome

    print('servidor : %s' % servidor)
    print('versao   : %s' % versao)
    print('destino  : %s' % saida)
    print()

    if saida.exists() and not dry:
        sys.exit('ERRO: %s ja existe. Apague, ou use --version com outro valor.' % saida)

    copiar, linkar = coletar()
    bytes_copia = sum((RAIZ / r).stat().st_size for r in copiar)
    bytes_link = sum((RAIZ / r).stat().st_size for r in linkar)

    print('%d arquivos a copiar   (%s)' % (len(copiar), humano(bytes_copia)))
    print('%d por hardlink        (%s, sem ocupar disco novo)' % (len(linkar), humano(bytes_link)))
    print('%d pastas criadas vazias: %s' % (len(PASTAS_VAZIAS), ', '.join(sorted(PASTAS_VAZIAS))))
    print()

    if dry:
        print('--- primeiros 25 arquivos ---')
        for r in copiar[:25]:
            print('   ', r)
        if len(copiar) > 25:
            print('    ... e mais %d' % (len(copiar) - 25))
        print()
        for r in linkar:
            print('    [hardlink]', r)
        print()
        print('>>> DRY RUN - nada foi escrito')
        return 0

    for r in copiar:
        dst = saida / r
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RAIZ / r, dst)

    caiu_para_copia = []
    for r in linkar:
        dst = saida / r
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(RAIZ / r, dst)
        except OSError as e:
            caiu_para_copia.append((r, e))
            shutil.copy2(RAIZ / r, dst)

    for p in PASTAS_VAZIAS:
        (saida / p).mkdir(parents=True, exist_ok=True)

    if caiu_para_copia:
        print('*** HARDLINK FALHOU - virou copia real ***')
        for r, e in caiu_para_copia:
            print('    %s: %s' % (r, e))
        print('    Causa comum: destino em outro volume, ou volume nao-NTFS.')
        print()

    problemas, avisos = verificar(saida, cfg)
    print('=== verificacao ===')
    for a in avisos:
        print('  [aviso] %s' % a)
    for p in problemas:
        print('  [ERRO]  %s' % p)
    if not problemas and not avisos:
        print('  tudo certo')
    print()

    total = sum(f.stat().st_size for f in saida.rglob('*') if f.is_file())
    print('=== %s ===' % nome)
    print('  arquivos : %d' % (len(copiar) + len(linkar)))
    print('  logico   : %s' % humano(total))
    print('  em disco : %s  (o resto e hardlink)' % humano(bytes_copia))

    if problemas:
        print()
        print('>>> BUILD COM PROBLEMAS - nao distribua. version.txt NAO foi alterado.')
        return 1

    VERSAO.write_text('%d.%d.%d\n' % (maj, mnr, pat + 1), encoding='utf-8')
    print()
    print('>>> BUILD OK. proxima versao sera %d.%d.%d' % (maj, mnr, pat + 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
