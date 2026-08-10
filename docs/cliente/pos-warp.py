# -*- coding: utf-8 -*-
"""
Aplica os ajustes que o WARP nao faz, e que sao PERDIDOS a cada rebuild.

Rode isto SEMPRE depois de gerar um build novo no warp2025:

    python pos-warp.py RagnaBeat.exe

O que ele faz:
  1. Redireciona os enderecos fixos da Gravity para 127.0.0.1
     (o cliente 2025 ignora o clientinfo.xml para o endereco de login)
  2. Corrige o separador do caminho do itemInfo para contrabarra
     (o WARP grava com '/', o cliente Windows precisa de '\')
  3. Troca as constantes de codepage cp949 -> cp1252
     E ISTO QUE FAZ OS ACENTOS FUNCIONAREM. Descoberto em 10/ago/2026.
     O cliente converte texto para Unicode ele mesmo, com 949 compilado no
     binario. Nenhum patch do WARP alcanca isso - nem charset de fonte,
     nem servicetype, nem AlwaysAscii. Ver docs/cliente/acentuacao.md.

O script e idempotente: se nada precisar mudar, ele nao grava nada.
FECHE O CLIENTE antes de rodar - o Windows nao deixa sobrescrever exe em uso.
"""
import sys, os, re, shutil, subprocess

REDIRECIONAR = [
    (b'kro-qm-1a.ragnarok.co.kr:6900',    b'127.0.0.1:6900'),
    (b'kro-qm-1a.ragnarok.co.kr:6951',    b'127.0.0.1:6900'),
    (b'kro-acc1.ragnarok.co.kr:6900',     b'127.0.0.1:6900'),
    (b'kro-agency.ragnarok.co.kr',        b'127.0.0.1'),
    (b'kro-qm-2a.ragnarok.co.kr:6900',    b'127.0.0.1:6900'),
    (b'kro-acc3.ragnarok.co.kr:6900',     b'127.0.0.1:6900'),
    (b'kro-agency-s.ragnarok.co.kr:6954', b'127.0.0.1:6900'),
]

# 949 = cp949 (coreano, duplo-byte)  ->  1252 (latino, byte unico)
# Os 7 sites saiam do build do WARP com 949. Trocar todos foi o que fez os
# acentos renderizarem. Se algum dia um deles quebrar sprite ou nome de
# arquivo, o suspeito e o _setmbcp em ~0x4CC3DC - da para excluir so ele.
CODEPAGE = [
    (b'\x68\xb5\x03\x00\x00', b'\x68\xe4\x04\x00\x00', 'push 949'),
    (b'\xb8\xb5\x03\x00\x00', b'\xb8\xe4\x04\x00\x00', 'mov eax, 949'),
]


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
    if n == 0:
        print('  ja redirecionados, nada a fazer')

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
    c = 0
    for antigo, novo, nome in CODEPAGE:
        i = 0
        while True:
            i = bytes(d).find(antigo, i)
            if i < 0:
                break
            d[i:i + len(antigo)] = novo
            print('  0x%08X  %-12s -> 1252' % (i, nome))
            c += 1
            i += len(antigo)
            mudou = True
    if c == 0:
        print('  ja esta em cp1252, nada a fazer')

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
    ok_ip = d2.count(b'127.0.0.1:6900') == 6
    ok_kro = len(re.findall(rb'kro-[a-z0-9-]+\.ragnarok\.co\.kr', d2)) == 0
    cam = re.search(rb'SystemEN[\\/][A-Za-z0-9_.]+', d2)
    ok_cam = bool(cam) and b'/' not in cam.group(0)
    n949 = sum(d2.count(a) for a, _, _ in CODEPAGE)
    ok_cp = n949 == 0

    print()
    print('=== verificacao ===')
    print('  [%s] enderecos 127.0.0.1     : %d de 6' % ('OK' if ok_ip else '!!', d2.count(b'127.0.0.1:6900')))
    print('  [%s] hosts da Gravity        : %d (tem que ser 0)' % ('OK' if ok_kro else '!!',
          len(re.findall(rb'kro-[a-z0-9-]+\.ragnarok\.co\.kr', d2))))
    print('  [%s] caminho do itemInfo     : %s' % ('OK' if ok_cam else '!!',
          cam.group(0).decode() if cam else 'nao patcheado no WARP'))
    print('  [%s] codepage cp949 restante : %d (tem que ser 0)' % ('OK' if ok_cp else '!!', n949))
    print('       tamanho                 : %d' % len(d2))
    print()
    if ok_ip and ok_kro and ok_cam and ok_cp:
        print('>>> PRONTO PARA USAR')
        return 0
    print('>>> ATENCAO: algo acima esta marcado com !!')
    return 1


if __name__ == '__main__':
    sys.exit(main())
