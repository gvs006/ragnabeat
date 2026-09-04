# -*- coding: utf-8 -*-
"""
Servidor HTTP do patcher: publica patcher/web/ na tailnet.

    python patcher/servir.py            roda em primeiro plano, com log na tela
    python patcher/servir.py --quieto   sem barulho, log so no arquivo
    python patcher/servir.py --porta N  outra porta

POR QUE ISTO EXISTE, JA QUE INCOMODA
O Thor Patcher busca a configuracao remota (main.ini) e a lista de patches por
HTTP. Nao ha como evitar: sem servidor o patcher nao passa da tela inicial. O
que da para fazer - e esta feito - e o FinishOnConnectionFailure=true no
config.ini, que solta o jogador para o jogo mesmo se o servidor estiver fora.
Ou seja, se isto cair, o tester ainda consegue jogar; ele so nao recebe aviso
nem patch.

POR QUE NAO E `python -m http.server`
Aquele e de uma conexao por vez. Com varios testers abrindo o patcher junto, um
espera o outro, e o Thor tem TimeOut proprio - o sintoma seria "as vezes nao
abre", que e o pior tipo de bug para depurar. ThreadingHTTPServer resolve.

POR QUE NAO E `tailscale serve`
Ele serve uma pasta e viveria dentro do tailscaled, sem processo extra - seria
melhor. Mas serve por HTTPS no nome MagicDNS, e o Thor e de 2014: nao da para
contar com TLS moderno nele. Se um dia o patcher for trocado, vale revisitar.

SEGURANCA
Escuta em 0.0.0.0, mas quem alcanca a porta e so a tailnet: a regra de firewall
'RagnaBeat - rAthena via Tailscale' limita a 100.64.0.0/10. Serve arquivos
estaticos de UMA pasta e nao aceita upload. Ainda assim, nao ponha nada em
patcher/web/ que nao possa ser lido por quem esta no tailnet.
"""
import argparse
import sys
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI / 'web'
LOG = AQUI / '_servir.log'
PORTA = 8099


class Handler(SimpleHTTPRequestHandler):
    """Igual ao padrao, so que sem cache e com log em arquivo."""

    def end_headers(self):
        # O NoticeBox e um controle do Internet Explorer, e o IE cacheia com
        # entusiasmo: depois de editar o status.html as linhas novas nao
        # apareceram, veio a versao antiga. Para o tester isso e pior - ele
        # ficaria vendo o aviso da semana passada sem jeito de forcar
        # atualizacao. As tres linhas cobrem IE velho e proxy no meio.
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        SimpleHTTPRequestHandler.end_headers(self)

    def log_message(self, formato, *args):
        linha = '%s %s %s\n' % (datetime.now().strftime('%d/%m %H:%M:%S'),
                                self.address_string(), formato % args)
        try:
            with open(LOG, 'a', encoding='utf-8') as f:
                f.write(linha)
        except OSError:
            pass
        if not self.server.quieto:
            sys.stdout.write(linha)
            sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--porta', type=int, default=PORTA)
    ap.add_argument('--quieto', action='store_true')
    args = ap.parse_args()

    if not (RAIZ / 'main.ini').exists():
        sys.exit('ERRO: nao achei %s - o patcher precisa dele' % (RAIZ / 'main.ini'))

    srv = ThreadingHTTPServer(('0.0.0.0', args.porta),
                              partial(Handler, directory=str(RAIZ)))
    srv.quieto = args.quieto
    # daemon_threads: conexao pendurada nao segura o desligamento
    srv.daemon_threads = True

    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('%s === subiu na porta %d, servindo %s ===\n'
                % (datetime.now().strftime('%d/%m %H:%M:%S'), args.porta, RAIZ))
    if not args.quieto:
        print('servindo %s em http://0.0.0.0:%d/' % (RAIZ, args.porta))
        print('log em %s' % LOG)
        print('Ctrl+C para parar.')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nparado.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
