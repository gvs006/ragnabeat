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
# Antes era o total EXATO de itens do itemInfo_C.lua, atualizado a mao a cada
# item novo. Deixou de funcionar em 12/ago/2026, quando entraram 1.020 visuais
# de uma vez - manter o numero na mao vira ritual, e ritual quebrado vira aviso
# ignorado.
#
# O que a checagem quer pegar de verdade e ARQUIVO TRUNCADO: uma geracao que
# der errado no meio derruba o total para perto de zero. Um piso resolve isso
# sem exigir manutencao. O total real e so informativo.
ITENS_MINIMO = 5000

# Mesmas assinaturas do pos-warp.py - se mudarem la, mudam aqui.
CP949 = b'\xb5\x03\x00\x00'
SIG_949 = re.compile(rb'(?:\x68' + re.escape(CP949) + rb'(?!\xff\x15)|\xb8' + re.escape(CP949) + rb')')
SIG_SETMBCP = re.compile(rb'\x68' + re.escape(CP949) + rb'\xff\x15')

# Entram por hardlink em vez de copia.
#
# As .pal entraram aqui em 03/set/2026: sao 40.954 palettes de montaria geradas
# por docs/cliente/gerar-palettes-montaria.py. Copiar uma a uma levava minutos e
# duplicava 40 MB por build; hardlink e instantaneo e nao gasta disco.
POR_HARDLINK = ['*.grf', '*.pal']

# Pastas que nao vao para o jogador.
PASTAS_FORA = {
    'builds',          # os proprios builds
    'savedata-padrao', # copiada para dentro de savedata\, nao vai como pasta
    'DEVTOOLS',        # WARP, patchers, decompiladores, exes candidatos - 600 MB
    '_exes_antigos',   # exes descartados
    'GameGuard',       # anticheat desativado pelo patch NoGGuard
    'PatchClient',     # recursos do patcher oficial kRO, nao usamos
    '_tmpEmblem',      # emblemas de guilda baixados NA SUA sessao
    'docs',
    '__pycache__',
    # Extracao da data.grf feita a mao com o GRF Editor, para consertar a
    # pasta data\ solta. Sao 214.803 arquivos e varios GB - se entrar num
    # build, entrega a GRF inteira duas vezes. Ver leia-me.md, secao do
    # DataFolderFirst.
    'GRF-EXTRAIDA-RAGNABEATDEV',
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
    'BASE_*.exe', 'Ragexe.exe*', 'MidgardEternal-*.exe', 'MidgardEternal.exe.*',
    'Ragnarok.exe', 'Setup.exe', 'unins000.*',
    # MidgardEternal2.exe e o 3 sao copias para abrir mais de um cliente.
    # Ficaram de fora a partir da 0.0.11: o build entrega UM executavel. Cada
    # copia e um binario a mais para lembrar de repatchar quando o IP mudar, e
    # um deles ja tinha ido para um build apontando para 127.0.0.1 por
    # exatamente esse motivo. Quem precisar de dois clientes copia o exe.
    'MidgardEternal[0-9].exe',
    # residuos do rename de 03/set/2026
    'RagnaBeat*.exe',
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



def linhas_sem_fechar(dados):
    """Linhas cuja string Lua nao fecha - devolve os numeros (base 1).

    A contagem simples de aspas NAO pega isto: uma linha terminada em barra
    invertida + aspa tem numero par de aspas e mesmo assim nunca fecha. Foi o
    que derrubou o cliente em 12/ago/2026, quando o gerador de itens partiu as
    descricoes em cima das aspas escapadas do LATAM:

        "...admiradores de \",          <- a barra escapa a aspa de fechar

    O cliente responde com uma caixa "unfinished string near ..." e PERDE o
    itemInfo inteiro - nao e degradacao, e tudo ou nada. Por isso e problema
    que bloqueia o release, nao aviso.

    A varredura imita o Lua: dentro da string, barra invertida pula o proximo
    caractere.
    """
    barra = 92
    fora = []
    for n, linha in enumerate(dados.split(bytes([10])), 1):
        i = linha.find(b'"')
        if i < 0:
            continue
        i += 1
        fechou = False
        while i < len(linha):
            if linha[i] == barra:
                i += 2
                continue
            if linha[i:i + 1] == b'"':
                fechou = True
                break
            i += 1
        if not fechou:
            fora.append(n)
    return fora


def endereco_do_clientinfo(saida):
    """O <address> do clientinfo.xml entregue, ou None."""
    alvo = saida / 'data' / 'clientinfo.xml'
    if not alvo.exists():
        return None
    m = re.search(rb'<address>\s*([^<\s]+)\s*</address>', alvo.read_bytes())
    return m.group(1).decode('latin-1') if m else None


def verificar(saida, cfg):
    """Checagens que impedem entregar um cliente quebrado."""
    problemas, avisos = [], []

    exe = saida / 'MidgardEternal.exe'
    if not exe.exists():
        problemas.append('MidgardEternal.exe ausente')
    else:
        d = exe.read_bytes()
        if len(d) != TAM_EXE_ESPERADO:
            problemas.append('MidgardEternal.exe tem %d bytes, esperado %d'
                             % (len(d), TAM_EXE_ESPERADO))
        n949 = len(SIG_949.findall(d))
        if n949:
            problemas.append('%d constantes cp949 nao trocadas - acentos vao falhar '
                             '(rode o pos-warp.py)' % n949)
        # O _setmbcp tem DOIS estados validos, e a diferenca e visivel para o
        # jogador - por isso o build informa qual esta indo, em vez de exigir um:
        #   1 em 949  -> acento no chat e nos itens; mensagens do
        #                msgstringtable SEM acento (cp949 nao tem c-cedilha)
        #   0, em 1252 -> acento tambem nas mensagens (pos-warp --setmbcp)
        # Ver docs/cliente/acentuacao.md.
        n_mbcp = len(SIG_SETMBCP.findall(d))
        if n_mbcp > 1:
            problemas.append('%d sites de _setmbcp - esperado 0 ou 1' % n_mbcp)
        else:
            print('  acento nas mensagens do sistema: %s'
                  % ('NAO (_setmbcp em 949)' if n_mbcp == 1
                     else 'sim (_setmbcp em 1252)'))
        kro = re.findall(rb'kro-[a-z0-9-]+\.ragnarok\.co\.kr', d)
        if kro:
            problemas.append('%d enderecos da Gravity no exe - o cliente nao vai conectar' % len(kro))

    # Todo exe de cliente entregue precisa apontar para o servidor - inclusive
    # os secundarios. Em 03/set/2026 o RagnaBeat3.exe foi para o 0.0.11 ainda
    # com 127.0.0.1: fora desta maquina ele conecta em si mesmo e trava em
    # "Please wait", sem deixar rastro no log do servidor. Ninguem notou porque
    # so o RagnaBeat.exe era verificado, e o endereco do login NAO vem do
    # clientinfo.xml - vai compilado no binario. Ver pos-warp.py.
    endereco = endereco_do_clientinfo(saida)
    if endereco:
        # O que define um exe de CLIENTE aqui e o tamanho, nao o nome. Um glob
        # 'RagnaBeat*.exe' parecia obvio e pegava junto o RagnaBeatPatcher.exe,
        # que e o Thor e nao tem endereco nenhum dentro - o build so nao
        # quebrava porque o montar.py roda depois da verificacao. Sorte, nao
        # projeto: bastaria reverificar um build ja montado para falhar.
        for outro in sorted(saida.glob('*.exe')):
            if outro.stat().st_size != TAM_EXE_ESPERADO:
                continue
            if endereco.encode('latin-1') not in outro.read_bytes():
                problemas.append(
                    '%s nao aponta para %s - rode "python pos-warp.py %s"'
                    % (outro.name, endereco, outro.name))
    else:
        avisos.append('nao achei o <address> do clientinfo.xml - os exes '
                      'secundarios nao foram conferidos')

    item = saida / 'SystemEN' / 'itemInfo_C.lua'
    if not item.exists():
        avisos.append('SystemEN/itemInfo_C.lua ausente - sem traducao de itens')
    else:
        b = item.read_bytes()
        n = len(re.findall(rb'^\s*\[(\d+)\]\s*=\s*\{', b, re.M))
        if n < ITENS_MINIMO:
            problemas.append('itemInfo_C.lua com so %d itens (piso %d) - '
                             'parece truncado' % (n, ITENS_MINIMO))
        else:
            print('  itemInfo_C.lua: %d itens' % n)
        if b.count(b'{') != b.count(b'}'):
            problemas.append('itemInfo_C.lua com chaves desbalanceadas - derruba o arquivo inteiro')
        if len(re.findall(rb'identifiedResourceName\s*=\s*""', b)):
            avisos.append('ha itens com resourceName vazio - esses ficam sem sprite')
        abertas = linhas_sem_fechar(b)
        if abertas:
            problemas.append('itemInfo_C.lua tem %d string(s) que nao fecham '
                             '(1a na linha %d) - o cliente aborta com '
                             '"unfinished string"' % (len(abertas), abertas[0]))

    # A sonda de acento (docs/cliente/sonda-acento.py) reescreve uma mensagem do
    # msgstringtable para diagnostico. Ela JA VAZOU para os builds 0.0.5, 0.0.6 e
    # 0.0.7 em 12/ago/2026, porque o build foi rodado justamente para testa-la e
    # ninguem a tirou antes. E ferramenta de diagnostico: nao pode sair para o
    # jogador.
    msg = saida / 'data' / 'msgstringtable.csv'
    if msg.exists() and b'U09OREE' in msg.read_bytes():   # base64 de "SONDA"
        problemas.append('msgstringtable.csv ainda tem a sonda de acento - '
                         'rode: python docs/cliente/sonda-acento.py --tirar')

    for g in ('data.grf', 'en.grf'):
        d_, o_ = saida / g, RAIZ / g
        if not d_.exists():
            problemas.append('%s ausente' % g)
        elif o_.exists() and d_.stat().st_size != o_.stat().st_size:
            problemas.append('%s com tamanho diferente da origem' % g)

    # As preferencias padrao sao postas de proposito dentro de savedata\, que de
    # resto e uma pasta excluida - a checagem precisa conhecer a excecao.
    padrao = RAIZ / 'savedata-padrao'
    esperados = {Path('savedata') / f.name for f in padrao.iterdir() if f.is_file()} \
        if padrao.is_dir() else set()

    vazados = [str(p.relative_to(saida)) for p in saida.rglob('*')
               if p.is_file() and excluido(p.relative_to(saida))
               and p.relative_to(saida) not in esperados]
    if vazados:
        problemas.append('arquivos de desenvolvimento vazaram: %s' % ', '.join(vazados[:5]))

    ci = saida / 'data' / 'clientinfo.xml'
    if ci.exists() and cfg.get('servidor'):
        m = re.search(rb'<display>([^<]*)</display>', ci.read_bytes())
        # Compara sem espacos: o config.yml compoe NOME DE PASTA, onde espaco
        # atrapalha ("MidgardEternal"), e o clientinfo mostra o nome como o
        # jogador le ("Midgard Eternal"). Sao a mesma marca escrita para dois
        # publicos, e cobrar igualdade literal so gera aviso que se aprende a
        # ignorar - que e como um aviso morre.
        def _norm(s):
            return s.replace(' ', '').lower()
        if m and _norm(m.group(1).decode('latin-1')) != _norm(cfg['servidor']):
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

    # savedata\ sai vazia (o conteudo do desenvolvedor e pessoal), mas o jogador
    # novo recebe as preferencias que o servidor escolheu. So os poucos valores
    # de savedata-padrao\ - o cliente completa o resto e reescreve ao fechar.
    padrao = RAIZ / 'savedata-padrao'
    if padrao.is_dir():
        for f in sorted(padrao.iterdir()):
            if f.is_file():
                shutil.copy2(f, saida / 'savedata' / f.name)
                print('  padrao do jogador: savedata\\%s' % f.name)

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
