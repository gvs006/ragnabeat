# -*- coding: utf-8 -*-
"""
Ponte TCP do IP do Tailscale para o loopback.

POR QUE ISTO EXISTE
-------------------
O Docker Desktop roda no backend WSL2, que usa "localhost forwarding": as
portas publicadas respondem em 127.0.0.1 sem que exista socket em escuta do
lado do Windows. Confirmado em 12/ago/2026:

    Get-NetTCPConnection -State Listen -LocalPort 6900   -> nada
    netstat -ano | findstr :6900                          -> nada LISTENING
    conectar em 127.0.0.1:6900                            -> ok
    conectar em 192.168.1.5:6900 ou 100.76.66.99:6900     -> timeout

Ou seja, o "0.0.0.0:6900->6900/tcp" que o `docker ps` mostra e a intencao do
Docker dentro da VM, nao uma ligacao real na maquina. Nenhuma outra interface
alcanca - nem a LAN.

O QUE JA FOI TENTADO E NAO RESOLVEU
-----------------------------------
1. `netsh interface portproxy` - as 14 regras sao aceitas sem erro e nenhuma
   chega a criar listener. Nao e a pilha IPv6 (esta ligada na interface do
   Tailscale) nem o IP Helper (esta rodando).
2. Publicar amarrado ao IP no compose (`100.76.66.99:16900:6900`) - o
   `docker ps` passa a mostrar o IP, e continua inalcancavel.
3. `tailscale serve --tcp` - funciona para OUTRO aparelho do tailnet, mas nao
   atende conexao da propria maquina. Foi por isso que o cliente local passou a
   travar em "Please wait" depois que o exe passou a apontar para o IP do
   Tailscale.

A ponte resolve os tres casos porque cria um socket Windows comum: quem chega
pelo tailnet e quem chega da propria maquina caem no mesmo listener.

SEGURANCA
---------
So aceita origem da faixa CGNAT do Tailscale (100.64.0.0/10) e da propria
maquina. A Ethernet aqui e rede "Public"; sem esse filtro a ponte seria um
buraco onde o Docker nao era. A regra de firewall
"RagnaBeat - rAthena via Tailscale" ja limita o mesmo, mas defesa em duas
camadas custa pouco.

USO
---
    python docs/ponte-portas.py            usa o IP do Tailscale detectado
    python docs/ponte-portas.py --ip X     forca um IP de escuta
    python docs/ponte-portas.py --quieto   so erros

Para deixar rodando sozinho, ver docs/infra-docker.md - Tarefa Agendada no
logon com pythonw.exe.
"""
import argparse
import ipaddress
import socket
import subprocess
import sys
import threading
import time

# 6900 login, 6121 char, 5121 map. O bloco 6950-6960 e a faixa que o cliente
# 2025 sorteia em runtime - ver docs/infra-docker.md.
PORTAS = [6900, 6121, 5121] + list(range(6950, 6961))

# O Docker publica em porta+DESLOCAMENTO, so no loopback; a ponte fica dona da
# porta real. Isto NAO e enfeite:
#
# publicar uma porta no Docker Desktop a RESERVA no Windows - qualquer bind
# nela passa a dar WinError 10013, em qualquer endereco, inclusive 0.0.0.0 -
# e mesmo assim so o 127.0.0.1 e atendido. Medido em 12/ago/2026: das 14
# portas, as 11 que o Docker conseguiu publicar ficaram impossiveis de ligar,
# e as 3 que ele nao publicou (6121, 6951, 6955) ligaram normalmente.
#
# Com o deslocamento, quem fica reservado e o 16900, que ninguem usa, e o 6900
# de verdade sobra para a ponte.
#
# TEM QUE BATER COM docker-compose.yml.
DESLOCAMENTO = 10000

# Local e tailnet. O 127.0.0.1 e o que faz o cliente DESTA maquina funcionar:
# o endereco vai compilado no exe, entao o cliente daqui tambem procura o IP do
# Tailscale - e ele nao se alcanca sozinho por netstack.
def enderecos_de_escuta(ip):
    return ['127.0.0.1', ip]

TAILNET = ipaddress.ip_network('100.64.0.0/10')
LOCAIS = (ipaddress.ip_network('127.0.0.0/8'),)

BUFFER = 65536


def ip_do_tailscale():
    for cmd in (['tailscale', 'ip', '-4'],
                [r'C:\Program Files\Tailscale\tailscale.exe', 'ip', '-4']):
        try:
            saida = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue
        if saida.returncode == 0:
            for linha in saida.stdout.split():
                linha = linha.strip()
                if linha:
                    return linha
    raise SystemExit('nao consegui descobrir o IP do Tailscale - passe --ip')


def permitido(ip):
    try:
        end = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return end in TAILNET or any(end in r for r in LOCAIS)


def tubo(origem, destino):
    try:
        while True:
            dados = origem.recv(BUFFER)
            if not dados:
                break
            destino.sendall(dados)
    except OSError:
        pass
    finally:
        for s in (origem, destino):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                s.close()
            except OSError:
                pass


def atender(cliente, endereco, porta, log):
    if not permitido(endereco[0]):
        log('recusado %s:%s (fora do tailnet)' % endereco)
        cliente.close()
        return
    try:
        servidor = socket.create_connection(('127.0.0.1', porta + DESLOCAMENTO), timeout=10)
    except OSError as e:
        log('porta %d indisponivel para %s: %s' % (porta, endereco[0], e))
        cliente.close()
        return
    cliente.settimeout(None)
    servidor.settimeout(None)
    threading.Thread(target=tubo, args=(cliente, servidor), daemon=True).start()
    threading.Thread(target=tubo, args=(servidor, cliente), daemon=True).start()


def escutar(ip, porta, log):
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((ip, porta))
    except OSError as e:
        log('[!!] nao consegui ouvir em %s:%d - %s' % (ip, porta, e))
        return
    srv.listen(64)
    log('  %s:%-5d -> 127.0.0.1:%d' % (ip, porta, porta + DESLOCAMENTO))
    while True:
        try:
            cliente, endereco = srv.accept()
        except OSError:
            time.sleep(0.5)
            continue
        atender(cliente, endereco, porta, log)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ip')
    p.add_argument('--quieto', action='store_true')
    args = p.parse_args()

    def log(msg):
        if not args.quieto or msg.startswith('[!!]'):
            print(msg, flush=True)

    ip = args.ip or ip_do_tailscale()
    escuta = enderecos_de_escuta(ip)
    log('ponte ativa em %s (%d portas, +%d no Docker)'
        % (', '.join(escuta), len(PORTAS), DESLOCAMENTO))
    for endereco in escuta:
        for porta in PORTAS:
            threading.Thread(target=escutar, args=(endereco, porta, log), daemon=True).start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
