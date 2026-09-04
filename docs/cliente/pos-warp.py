# -*- coding: utf-8 -*-
"""
Aplica os ajustes que o WARP nao faz, e que sao PERDIDOS a cada rebuild.

Rode isto SEMPRE depois de gerar um build novo no warp2025:

    python pos-warp.py RagnaBeat.exe

O que ele faz:
  1. Redireciona os enderecos fixos da Gravity para SERVIDOR (ver a
     constante no topo) - o cliente NAO le o clientinfo.xml para isso
     (o cliente 2025 ignora o clientinfo.xml para o endereco de login)
  2. Corrige o separador do caminho do itemInfo para contrabarra
     (o WARP grava com '/', o cliente Windows precisa de '\')
  3. Troca o codepage do decoder de texto, cp949 -> cp1252
     Com --setmbcp troca tambem a 7a constante, o que faz acento
     funcionar nas mensagens do msgstringtable. Leia o risco e o
     teste obrigatorio no bloco do passo 3.
     E ISTO QUE FAZ OS ACENTOS FUNCIONAREM. Descoberto em 10/ago/2026.
     O cliente converte texto para Unicode ele mesmo, com 949 compilado no
     binario. Nenhum patch do WARP alcanca isso - nem charset de fonte,
     nem servicetype, nem AlwaysAscii. Ver docs/cliente/acentuacao.md.
     So o par do decoder e trocado; as outras 5 constantes 949 do binario
     ficam como estao, senao os sprites dos itens quebram.
  4. Manifesto requireAdministrator -> asInvoker. Sem isso o botao START do
     Thor Patcher falha EM SILENCIO: CreateProcess nao consegue elevar.
  5. Data folder first - DESLIGADO por padrao (--folderfirst para ligar). O
     patch do WARP nao funciona em cliente 2025, e o conserto obvio pula o
     fallback. Leia o bloco antes de mexer.
  6. Rotulos compilados no exe: Peso, Base, Classe, e o formato "%s [%s]" do
     nome de guilda. Esses textos NAO vem do msgstringtable.
  7. Codepage da tabela de idioma, o ramo coreano. E ISTO que faz as mensagens
     automaticas sairem COM acento - achado em 04/set/2026, depois de o
     --setmbcp nao resolver. Sao codepages diferentes.

O script e idempotente: se nada precisar mudar, ele nao grava nada.
FECHE O CLIENTE antes de rodar - o Windows nao deixa sobrescrever exe em uso.
"""
import sys, os, re, shutil, subprocess

# Endereco do servidor gravado DENTRO do exe.
#
# O cliente 2025 NAO usa o clientinfo.xml para achar o login: ele le esta
# tabela de enderecos em .rdata. Enquanto ficou 127.0.0.1 so funcionava nesta
# maquina - o cliente de outra pessoa conectava nela mesma e travava em
# "Please wait", sem nada aparecer no log do servidor.
#
# 100.76.66.99 e o IP desta maquina no Tailscale. Trocar aqui exige regerar o
# release (build.py), porque o endereco vai COMPILADO no exe entregue.
SERVIDOR = '100.76.66.99'

# (hostname original da Gravity, leva porta?)
# O slot em disco tem o tamanho do hostname original, entao ha folga de sobra.
GRAVITY = [
    (b'kro-qm-1a.ragnarok.co.kr:6900',    True),
    (b'kro-qm-1a.ragnarok.co.kr:6951',    True),
    (b'kro-acc1.ragnarok.co.kr:6900',     True),
    (b'kro-agency.ragnarok.co.kr',        False),
    (b'kro-qm-2a.ragnarok.co.kr:6900',    True),
    (b'kro-acc3.ragnarok.co.kr:6900',     True),
    (b'kro-agency-s.ragnarok.co.kr:6954', True),
    # Dois IPs crus na MESMA tabela, logo depois dos sete hostnames (0x00C2860C
    # e 0x00C2861C no build 2025-04-16). Passaram despercebidos ate 11/ago/2026
    # porque nao tem "ragnarok.co.kr" no nome.
    #
    # 211.172.247.115 e um IP publico coreano da Gravity; 192.168.5.52 e uma LAN
    # interna deles. Os dois sao inalcancaveis daqui - o cliente fica preso ate o
    # TCP desistir, e e por isso que "esperar um pouco" fazia o login funcionar.
    (b'192.168.5.52',    False),
    (b'211.172.247.115', False),
]

def _destino(tem_porta):
    return (SERVIDOR + ':6900' if tem_porta else SERVIDOR).encode('ascii')

REDIRECIONAR = [(h, _destino(pt)) for h, pt in GRAVITY]

# Enderecos que podem JA estar gravados, de uma execucao anterior. Sem isto o
# script so funciona sobre uma saida virgem do WARP: depois da primeira passada
# os hostnames nao existem mais e trocar de endereco seria impossivel sem
# refazer o exe.
ANTERIORES = [b'127.0.0.1']

# Os 9 slots da tabela tem 16 bytes ou mais. Existe um decimo '127.0.0.1' em
# 0x00C28154 com slot de 12 bytes que NAO faz parte dela - o piso de 16 e o que
# impede de encostar nele quando o endereco novo for curto o bastante para caber.
SLOT_MINIMO = 16

# 949 = cp949 (coreano, duplo-byte)  ->  1252 (latino, byte unico)
#
# O binario tem 7 constantes 949. Por padrao trocamos 6; a excecao e o
# _setmbcp, que configura o codepage multibyte de TODO o CRT.
#
# POR QUE EXISTE A OPCAO --setmbcp (12/ago/2026)
# Deixar o _setmbcp em 949 tem um preco que so apareceu depois: as mensagens do
# msgstringtable (as que o cliente exibe ao entrar no jogo) saem SEM ACENTO.
# Medido com docs/cliente/sonda-acento.py, que poe a mesma palavra em tres
# codificacoes na mesma linha:
#
#     UTF-8  -> "acao"   o acento some, sem erro
#     cp1252 -> "a??o"   bytes invalidos viram ?
#
# A causa: o cliente le o CSV como UTF-8 (certo), mas converte a string larga
# para multibyte usando o codepage do CRT - que e o do _setmbcp. E o cp949
# NAO CONSEGUE representar c-cedilha nem a-til, nem em byte duplo; o Windows
# entao aplica "best fit" e troca cada um pela letra base, em silencio.
#
# Ou seja: com o _setmbcp em 949, NENHUMA codificacao do msgstringtable carrega
# acento. Nao e problema do arquivo.
#
# O RISCO, que e o motivo de nao ser o padrao: o CRT passa a tratar como
# byte unico os nomes de arquivo em cp949 de dentro do GRF (resourceName de
# item). Um par cp949 cujo segundo byte seja 0x5C viraria barra de caminho.
# A doc registra que trocar as 7 JA FOI TESTADO e renderizou acento; o que
# nunca foi testado e o efeito nos nomes de arquivo.
#
# TESTE OBRIGATORIO depois de ligar:
#   1. entrar no jogo e conferir acento no bloco de mensagens da entrada
#   2. @item 5376 e passar o mouse - e um item com resourceName coreano
#      (sa-ta-nik-che-in). Se abrir "Cannot find File", reverta.
#   3. conferir que os sprites de mapa e mob continuam carregando
#
# Para reverter: rebuild no WARP a partir do BASE e rodar o pos-warp sem a
# opcao. Ver docs/cliente/acentuacao.md.
#
# Como distinguir o _setmbcp dos outros sem depender de offset fixo: e o unico
# 'push 949' seguido de FF 15 (call indireto pela IAT). Os outros sao seguidos
# de E8 (call rel32) ou E9 (jmp).
#
#   0x0022807D  push 949 + E8     -> troca
#   0x0022EDF9  push 949 + E8     -> troca
#   0x0095226A  push 949 + E8     -> troca
#   0x00978155  push 949 + E9     -> troca
#   0x004CC3DC  push 949 + FF 15  -> so com --setmbcp (_setmbcp)
#   0x00654EE3  mov eax, 949      -> troca
#   0x0065501B  mov eax, 949      -> troca
#
# Historico: trocar so 2 sites (o par 0x22807D/0x22EDF9) NAO faz os acentos
# funcionarem - foi testado. Trocar os 7 tambem funciona; ficamos em 6 porque
# nao ha ganho em mexer no CRT inteiro.
CP949  = b'\xb5\x03\x00\x00'
CP1252 = b'\xe4\x04\x00\x00'
SIG_949  = re.compile(rb'(?:\x68' + re.escape(CP949)  + rb'(?!\xff\x15)|\xb8' + re.escape(CP949)  + rb')')
# O _setmbcp e o unico 'push 949' seguido de FF 15. O SIG_949 o exclui; com
# --setmbcp ele volta pela SIG_SETMBCP.
SIG_SETMBCP = re.compile(rb'\x68' + re.escape(CP949) + rb'\xff\x15')
CODEPAGE_ESPERADO = 6


# MANIFESTO - por que o cliente nao pode pedir elevacao
#
# O exe sai do WARP com requestedExecutionLevel="requireAdministrator". Isso
# quebra o botao START do Thor Patcher: o patcher roda como asInvoker, e o
# CreateProcess NAO consegue elevar - falha com ERROR_ELEVATION_REQUIRED e nada
# acontece na tela. O jogador nao ve erro nenhum.
#
# Esse bug so reproduz numa sessao NAO elevada: rodando o patcher a partir de um
# terminal de admin ele funciona, e a conclusao vira "esta tudo certo aqui".
#
# A troca tem que ter O MESMO TAMANHO em bytes - o manifesto e um recurso com
# tamanho declarado. Por isso o preenchimento com espaco, que o XML ignora.
MANIFESTO_DE = b'"requireAdministrator"'
MANIFESTO_PARA = b'"asInvoker"' + b' ' * 11
MANIFESTOS_ESPERADOS = 2

# DATA FOLDER FIRST - o patch do WARP nao funciona em cliente 2025
#
# Scripts/Patches/DataFolderFirst.qjs tem um ramo para Exe.BuildDate >= 20250300
# que acha o padrao, escreve o comentario "NOP out the JZ near" e faz
# "return true" SEM PATCHEAR NADA. O WARP reporta sucesso, o patch aparece
# marcado na lista, e o binario sai identico ao original. Conferido byte a byte:
# o JZ esta intacto no exe limpo E no que sai do WARP.
#
# O ESTRAGO: arquivo solto em data/ que NAO existe na GRF continua sendo achado
# (os sprites e paletas que adicionamos). Mas arquivo solto que CONFLITA com a
# GRF perde em silencio - e ai entra o msgstringtable.csv traduzido, os .lub de
# visuais, as texturas PT-BR. Tudo que a gente achava que estava valendo.
#
# O codigo, em 0x0066E822 do exe limpo:
#
#   80 7D 10 00        cmp byte ptr [ebp+10h], 0   ; g_readFolderFirst
#   0F 84 B8 00 00 00  jz  +0xB8                   ; pula a abertura do solto
#   6A 00 68 80 ...    push ...                    ; args de CreateFileA
#   FF 75 08           push [ebp+8]                ; o caminho
#   FF 15 24 D2 F9 00  call CreateFileA            ; abre do disco
#
# Anular o JZ com 6 NOPs faz o cliente SEMPRE tentar o disco antes da GRF.
# Mesmo tamanho, sem deslocar nada.
#
# ATENCAO - ESTE PATCH ESTA ERRADO. NAO LIGUE O --folderfirst ATE CORRIGIR.
#
# Testado a noite toda em 04/set/2026. Anular o JZ de 0x0066E822 forca o
# caminho de leitura do disco MAS PULA O BLOCO SEGUINTE, que e onde mora o
# fallback. Resultado: todo arquivo que nao esteja solto simplesmente falha.
# Os sintomas foram aparecendo um por um conforme se completava a pasta:
# JOBID nil -> SKID nil -> table index is nil -> EFST_IDs nil ->
# getTableSize nil -> "Cannot open file", esse ultimo sem sumir nem com a
# arvore luafiles514 INTEIRA (478 arquivos) solta.
#
# O ALVO CERTO, descoberto desmontando o destino do salto:
#
#   0x0066E822  0F 84 B8 00 00 00   jz +0xB8   <- o que eu anulei (ERRADO)
#   0x0066E8E0  80 3D 2C 11 57 01 00  cmp byte ptr [0157112C], 0  <- g_readFolderFirst
#   0x0066E8E6  0F 84 E4 00 00 00   jz +0xE4   <- ESTE e o candidato
#
# 0x0157112C e a global g_readFolderFirst. A versao pre-2025 do proprio
# DataFolderFirst.qjs diz que o certo e "set g_readFolderFirst to 1", nao
# anular o teste do parametro. Nao ha nenhuma escrita imediata nessa global
# no binario (procurei por C6 05 2C 11 57 01), so a leitura em 0x0066E8E0.
#
# Proximo passo para quem retomar: anular o jz de 0x0066E8E6 em vez do de
# 0x0066E822, ou achar quem escreve a global e forcar 1. Testar com a pasta
# data/ INCOMPLETA de proposito - se o fallback estiver certo, um arquivo
# ausente tem que vir da GRF sem erro.
#
# A busca e por padrao, nao por offset fixo, para sobreviver a troca de build.
_ARGS_CREATEFILE = bytes([0x6A, 0x00, 0x68, 0x80, 0x00, 0x00, 0x00, 0x6A, 0x03,
                          0x6A, 0x00, 0x6A, 0x01, 0x68, 0x00, 0x00, 0x00, 0x80,
                          0xFF, 0x75, 0x08, 0xFF, 0x15])
FOLDER_JZ = re.compile(bytes([0x0F, 0x84]) + b'....' + _ARGS_CREATEFILE, re.S)
FOLDER_NOP = re.compile(bytes([0x90]) * 6 + _ARGS_CREATEFILE, re.S)
NOP6 = bytes([0x90]) * 6


# ROTULOS COMPILADOS NO EXE - o msgstringtable NAO alcanca estes
#
# Descoberto em 04/set/2026, depois de uma noite inteira procurando no lugar
# errado. O "Weight" da janela Alt+V NAO vem do msgstringtable: e uma string
# fixa no .rdata do cliente. A chave MSI_WEIGHT existe e esta traduzida como
# "Peso : %3d / %3d", mas o cliente nunca a consulta para esse campo.
#
# Por isso NADA adiantou: nem a pasta data/ solta, nem o DataFolderFirst, nem
# uma GRF propria em prioridade 0. O texto nunca esteve em arquivo nenhum.
#
# A pista estava na primeira captura e passou batido: o ThanatosRO mostra
# "Peso : 1874 / 5450" no MESMO formato "%3d / %3d" do original em ingles.
# Eles patcharam a string no binario. O teste que teria matado a duvida em
# cinco minutos era comparar o FORMATO exibido com o formato da chave.
#
# REGRA DO SLOT: a troca tem que caber. Cada string vive num slot terminado
# em nul, e escrever alem dele invade a string seguinte. Traducao mais curta
# e preenchida com nul; mais longa que o original e RECUSADA pelo script.
#
# Os especificadores (%3d, %s, %d%%) tem que sobreviver iguais e na mesma
# ordem, senao o cliente formata lixo ou quebra.
ROTULOS = [
    (b'Weight : %3d / %3d',       b'Peso : %3d / %3d'),
    (b'Max Weight : %3d',         b'Peso Max. : %3d'),
    (b'Num: %d/%d Weight: %d/%d', b'Num: %d/%d Peso: %d/%d'),
    (b'Weight %d%%',              b'Peso %d%%'),
    (b'Base Lv. %d',              b'Base %d'),
    (b'Job Lv. %d',               b'Classe %d'),
    # Nome de guilda sobre a cabeca: "Guilda (Cargo)" -> "Guilda [Cargo]".
    # Mesmo tamanho em bytes, troca limpa, e o slot e unico no binario.
    #
    # Isto NAO se resolve pelo servidor. Duas tentativas em clif.cpp falharam:
    # pondo colchetes no slot de cargo o jogador ve "([Cargo])", e esvaziando o
    # slot ve "Guilda [Cargo] ()" - o cliente desenha os parenteses mesmo com o
    # campo vazio. O formato e dele, e mora nesta string.
    (b'%s (%s)',                  b'%s [%s]'),
]


# A TABELA DE IDIOMA - a oitava constante 949, invisivel ate 04/set/2026
#
# Esta e a que faz as mensagens automaticas sairem SEM ACENTO
# ("Alimentacao automatica de mascote desligada"), e ela ficou escondida por
# meses porque a busca so cobria 'push 949' (68) e 'mov eax, 949' (B8).
#
# O cliente tem uma tabela que escolhe o codepage pelo idioma do servico:
#
#   0x006582D2  mov [0156F528], 949    coreano   <- o ramo que usamos
#   0x006582E8  mov [0156F528], 932    japones
#   0x00658303  mov [0156F528], 936    chines simplificado
#   0x0065831E  mov [0156F528], 950    chines tradicional
#   0x00658339  mov [0156F528], 874    tailandes
#   0x0065838B  mov [0156F528], 1252   latino ocidental
#   0x006583A8  mov [0156F528], 1251   cirilico
#
# O global 0156F528 e referenciado 53 vezes, a maioria como 'push [global]' -
# ou seja, entregue como ARGUMENTO de conversao. Com 949 ali, o Windows nao
# consegue representar 'a-til' nem 'c-cedilha' no destino, aplica best-fit e
# devolve a letra base em silencio. Dai "Alimentacao".
#
# POR QUE O --setmbcp NAO RESOLVIA: e outro codepage. O _setmbcp configura o
# CRT; este aqui e do proprio cliente. Trocar um nao mexe no outro, e por isso
# o teste com --setmbcp deu o mesmo resultado nos dois valores.
#
# COMO FOI ACHADO, para repetir o metodo: procurar o dword 949 (B5 03 00 00) no
# binario INTEIRO, sem filtrar por opcode. Deu 9 ocorrencias - cinco eram
# deslocamento de jmp/call/jne (coincidencia, 0x3B5) e quatro eram atribuicao
# real na forma C7, que nenhuma busca anterior cobria.
#
# Sobram tres nao tocadas, todas gravando em variavel local. Ficam como
# candidatas se aparecer outro texto sem acento:
#
#   0x006B6798  mov [ebp-4], 949
#   0x006DFAF0  mov [ebp-4], 949
#   0x0077CF7B  mov [ebp-0EECh], 949
#
# So o ramo COREANO e trocado. Os outros idiomas ficam como estao - nao usamos,
# e mexer no que nao se testa e como este arquivo acumula armadilha.
CP_TABELA_GLOBAL = bytes([0x28, 0xF5, 0x56, 0x01])   # 0x0156F528, little-endian
SIG_CP_TABELA = re.compile(
    b'\xc7\x05' + re.escape(CP_TABELA_GLOBAL) + re.escape(CP949), re.S)
SIG_CP_TABELA_OK = re.compile(
    b'\xc7\x05' + re.escape(CP_TABELA_GLOBAL) + re.escape(CP1252), re.S)


def cliente_rodando(exe):
    nome = os.path.basename(exe)
    try:
        saida = subprocess.run(['tasklist', '/fi', 'imagename eq ' + nome],
                               capture_output=True, text=True, timeout=10).stdout
        return nome.lower() in saida.lower()
    except Exception:
        return False


def main():
    exe = sys.argv[1] if len(sys.argv) > 1 else 'RagnaBeat.exe'
    if not os.path.exists(exe):
        print('ERRO: nao encontrei %s' % exe)
        return 1

    d = bytearray(open(exe, 'rb').read())
    tam = len(d)
    mudou = False

    print('=== 1. enderecos da Gravity ===')
    n = 0
    for antigo, novo in REDIRECIONAR:
        i = bytes(d).find(antigo)
        if i < 0:
            continue
        d[i:i + len(antigo)] = novo + b'\x00' * (len(antigo) - len(novo))
        print('  0x%08X  %-34s -> %s' % (i, antigo.decode(), novo.decode()))
        n += 1
        mudou = True

    # Segunda passada: exe que JA passou por aqui antes. Os hostnames da Gravity
    # nao existem mais, entao a ancora vira o endereco gravado da vez passada -
    # senao trocar de endereco exigiria refazer o exe no WARP.
    #
    # Se o slot leva porta ou nao, quem diz e o proprio conteudo atual.
    for anterior in ANTERIORES:
        for m in re.finditer(re.escape(anterior) + rb'(:\d+)?\x00', bytes(d)):
            ini = m.start()
            fim = ini
            while d[fim] != 0:
                fim += 1
            slot = fim
            while slot < tam and d[slot] == 0:
                slot += 1
            largura = slot - ini
            atual = bytes(d[ini:fim])
            destino = _destino(b':' in atual)
            if largura < SLOT_MINIMO or len(destino) >= largura or atual == destino:
                continue
            d[ini:ini + largura] = destino + b'\x00' * (largura - len(destino))
            print('  0x%08X  %-34s -> %s' % (ini, atual.decode(), destino.decode()))
            n += 1
            mudou = True

    if n == 0:
        print('  ja apontam para %s, nada a fazer' % SERVIDOR)

    print()
    print('=== 2. separador do caminho ===')
    m = 0
    for x in re.finditer(rb'SystemEN/[A-Za-z0-9_.]+', bytes(d)):
        ini, fim = x.start(), x.end()
        d[ini:fim] = bytes(d[ini:fim]).replace(b'/', b'\\')
        print('  0x%08X  corrigido para contrabarra' % ini)
        m += 1
        mudou = True
    if m == 0:
        print('  ja esta com contrabarra, nada a fazer')

    print()
    print('=== 3. codepage cp949 -> cp1252 (acentuacao) ===')
    mexer_setmbcp = '--setmbcp' in sys.argv
    achados = [x.start() for x in SIG_949.finditer(bytes(d))]
    if mexer_setmbcp:
        # o _setmbcp e o unico 'push 949' seguido de FF 15, e o SIG_949 o
        # exclui de proposito - aqui ele entra de volta
        extras = [x.start() for x in SIG_SETMBCP.finditer(bytes(d))]
        if extras:
            print('  --setmbcp ligado: a 7a constante entra tambem')
            print('  (acento nas mensagens do msgstringtable; leia o TESTE')
            print('   OBRIGATORIO no cabecalho deste arquivo)')
            achados = sorted(achados + extras)
    for off in achados:
        ins = 'push 949' if d[off] == 0x68 else 'mov eax, 949'
        d[off + 1:off + 5] = CP1252
        print('  0x%08X  %-12s -> 1252' % (off, ins))
        mudou = True
    if not achados:
        print('  ja esta em cp1252, nada a fazer')
    else:
        # Numa primeira passada aparecem os 6 (ou 7 com --setmbcp). Numa
        # segunda, as ja trocadas nao contam mais - entao so vale reclamar
        # quando o total passa do teto, nunca quando fica abaixo.
        teto = CODEPAGE_ESPERADO + (1 if mexer_setmbcp else 0)
        if len(achados) > teto:
            print('  !! esperava no maximo %d sites, encontrei %d - conferir'
                  % (teto, len(achados)))

    print()
    print('=== 4. manifesto: requireAdministrator -> asInvoker ===')
    n_man = 0
    while True:
        i = bytes(d).find(MANIFESTO_DE)
        if i < 0:
            break
        d[i:i + len(MANIFESTO_DE)] = MANIFESTO_PARA
        print('  0x%08X  requireAdministrator -> asInvoker' % i)
        n_man += 1
        mudou = True
    if n_man == 0:
        print('  ja esta em asInvoker, nada a fazer')
    elif n_man != MANIFESTOS_ESPERADOS:
        print('  !! esperava %d manifestos, troquei %d - conferir'
              % (MANIFESTOS_ESPERADOS, n_man))

    print()
    print('=== 5. data folder first (o WARP nao aplica em cliente 2025) ===')
    # OPT-IN, e o motivo esta no bloco DATA FOLDER FIRST la em cima:
    # ligar isto QUEBRA o cliente enquanto a nossa pasta data/ solta estiver
    # incompleta. Testado em 04/set/2026 - o cliente subiu com
    # "SkillInfoList.lua:140: attempt to index global 'JOBID' (a nil value)",
    # "ResetTheHotkey attempt to call a nil value" e "cant open file".
    #
    # Nao e bug do patch: e a pasta solta ganhando com meia duzia de .lub
    # enquanto o resto da cadeia continua na GRF. Ate a data/ estar completa,
    # so com --folderfirst.
    quer_ff = '--folderfirst' in sys.argv
    if not quer_ff:
        print('  DESLIGADO - passe --folderfirst para ligar')
        # NAO da para desfazer aqui: o NOP apaga o deslocamento do salto, que
        # muda de build para build. Chutar o valor antigo seria pior que o
        # problema. Se o exe ja veio anulado, o caminho e regerar do WARP.
        if FOLDER_NOP.search(bytes(d)):
            print('  !! ESTE EXE JA ESTA ANULADO de uma passada anterior.')
            print('     Nao da para desfazer aqui - o NOP apagou o deslocamento')
            print('     do salto. Regere o exe no WARP e rode este script de novo.')
    else:
        n_ff = 0
        for x in list(FOLDER_JZ.finditer(bytes(d))):
            off = x.start()
            d[off:off + 6] = NOP6
            print('  0x%08X  jz anulado - a pasta data/ passa a vencer a GRF' % off)
            n_ff += 1
            mudou = True
        if n_ff == 0:
            if FOLDER_NOP.search(bytes(d)):
                print('  ja esta anulado, nada a fazer')
            else:
                print('  !! padrao nao encontrado - o build mudou? conferir a mao')

    print()
    print('=== 6. rotulos compilados no exe (o msgstringtable nao alcanca) ===')
    n_rot = 0
    for velho, novo in ROTULOS:
        if len(novo) > len(velho):
            print('  !! %r nao cabe no slot de %r - PULADO'
                  % (novo.decode('latin-1'), velho.decode('latin-1')))
            continue
        i = bytes(d).find(velho + b'\x00')
        if i < 0:
            if bytes(d).find(novo + b'\x00') >= 0:
                continue
            print('  !! %r nao encontrado' % velho.decode('latin-1'))
            continue
        d[i:i + len(velho) + 1] = novo + b'\x00' * (len(velho) - len(novo) + 1)
        print('  0x%08X  %-26s -> %s'
              % (i, velho.decode('latin-1'), novo.decode('latin-1')))
        n_rot += 1
        mudou = True
    if n_rot == 0:
        print('  ja estao traduzidos, nada a fazer')

    print()
    print('=== 7. codepage da tabela de idioma (o ramo coreano) ===')
    n_tab = 0
    for x in list(SIG_CP_TABELA.finditer(bytes(d))):
        off = x.start() + 6
        d[off:off + 4] = CP1252
        print('  0x%08X  mov [0156F528], 949 -> 1252' % x.start())
        n_tab += 1
        mudou = True
    if n_tab == 0:
        if SIG_CP_TABELA_OK.search(bytes(d)):
            print('  ja esta em 1252, nada a fazer')
        else:
            print('  !! padrao nao encontrado - o build mudou? conferir a mao')

    if mudou:
        if cliente_rodando(exe):
            print()
            print('*** FECHE O CLIENTE E RODE DE NOVO ***')
            print('    O Windows nao permite sobrescrever um exe em execucao.')
            return 1
        shutil.copy(exe, exe + '.antes-pos-warp')
        try:
            open(exe, 'wb').write(bytes(d))
        except PermissionError:
            print()
            print('*** SEM PERMISSAO PARA GRAVAR ***')
            print('    Provavel causa: o cliente esta aberto. Feche e rode de novo.')
            return 1
        print()
        print('gravado. backup em %s.antes-pos-warp' % exe)
    else:
        print()
        print('nada foi alterado - o exe ja estava pronto.')

    d2 = open(exe, 'rb').read()
    alvo_ip = _destino(True)
    ok_ip = d2.count(alvo_ip) == 6
    ok_kro = len(re.findall(rb'kro-[a-z0-9-]+\.ragnarok\.co\.kr', d2)) == 0
    cam = re.search(rb'SystemEN[\\/][A-Za-z0-9_.]+', d2)
    ok_cam = bool(cam) and b'/' not in cam.group(0)
    n949 = len(SIG_949.findall(d2))
    n_setmbcp = len(SIG_SETMBCP.findall(d2))
    # o _setmbcp saiu daqui: com --setmbcp o alvo dele inverte, e a
    # regra passou a viver em ok_mbcp, calculado mais abaixo
    ok_cp = n949 == 0

    print()
    print('=== verificacao ===')
    print('  [%s] enderecos %-16s: %d de 6' % ('OK' if ok_ip else '!!', SERVIDOR, d2.count(alvo_ip)))
    print('  [%s] hosts da Gravity        : %d (tem que ser 0)' % ('OK' if ok_kro else '!!',
          len(re.findall(rb'kro-[a-z0-9-]+\.ragnarok\.co\.kr', d2))))
    print('  [%s] caminho do itemInfo     : %s' % ('OK' if ok_cam else '!!',
          cam.group(0).decode() if cam else 'nao patcheado no WARP'))
    print('  [%s] constantes cp949 abertas : %d (tem que ser 0)' % ('OK' if n949 == 0 else '!!', n949))
    # Com --setmbcp o _setmbcp VAI para 1252 de proposito, entao o alvo inverte.
    alvo_mbcp = 0 if mexer_setmbcp else 1
    rotulo_mbcp = ('_setmbcp trocado p/ 1252' if mexer_setmbcp
                   else '_setmbcp preservado em 949')
    ok_mbcp = (n_setmbcp == alvo_mbcp)
    print('  [%s] %-26s: %d (tem que ser %d)'
          % ('OK' if ok_mbcp else '!!', rotulo_mbcp, n_setmbcp, alvo_mbcp))
    n_admin = d2.count(MANIFESTO_DE)
    ok_man = n_admin == 0
    print('  [%s] manifesto sem elevacao   : %d pedido(s) (tem que ser 0)'
          % ('OK' if ok_man else '!!', n_admin))
    anulado = FOLDER_JZ.search(d2) is None
    ok_ff = (quer_ff == anulado)
    print('  [%s] data folder first       : %s'
          % ('OK' if ok_ff else '!!',
             'LIGADO - a pasta data/ vence a GRF' if anulado
             else 'desligado - a GRF manda (use --folderfirst para trocar)'))
    faltam = [v for v, n in ROTULOS
              if len(n) <= len(v) and d2.find(v + b'\x00') >= 0]
    ok_rot = not faltam
    print('  [%s] rotulos traduzidos      : %d ainda em ingles'
          % ('OK' if ok_rot else '!!', len(faltam)))
    ok_tab = SIG_CP_TABELA.search(d2) is None
    print('  [%s] tabela de idioma        : %s'
          % ('OK' if ok_tab else '!!',
             'ramo coreano em 1252' if ok_tab else 'AINDA EM 949 - texto sai sem acento'))
    print('       tamanho                 : %d' % len(d2))
    print()
    if ok_ip and ok_kro and ok_cam and ok_cp and ok_mbcp and ok_man and ok_ff and ok_rot and ok_tab:
        print('>>> PRONTO PARA USAR')
        return 0
    print('>>> ATENCAO: algo acima esta marcado com !!')
    return 1


if __name__ == '__main__':
    sys.exit(main())
