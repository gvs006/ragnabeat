# -*- coding: utf-8 -*-
"""
Baixa as fontes do design (Cinzel e Barlow) para patcher/fontes/.

    python patcher/baixar-fontes.py

POR QUE NAO SUBSTITUIR POR FONTE DO WINDOWS
O design pede Cinzel (serifada, ar epico) e Barlow / Barlow Condensed. Nenhuma
das duas existe no Windows, e as substitutas obvias erram o tom: Georgia no
lugar da Cinzel fica editorial, Arial Narrow no lugar da Barlow Condensed fica
burocratica. Como o fundo do patcher e uma imagem que NOS geramos, a fonte so
precisa existir na hora de gerar - o tester nao precisa ter nada instalado.

Sao da Open Font License, entao podem ser versionadas junto com o projeto.

O gerar-visual.py cai para as fontes do Windows se esta pasta nao existir, mas
avisa alto: o desenho sai diferente do design aprovado.
"""
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI / 'fontes'
CSS = ('https://fonts.googleapis.com/css2'
       '?family=Cinzel:wght@700;900'
       '&family=Barlow:wght@400;500;600;700'
       '&family=Barlow+Condensed:wght@600;700'
       '&display=swap')
# O Google devolve woff2 para navegador moderno e ttf para User-Agent antigo.
# O Pillow so le ttf/otf, entao pedimos como se fossemos um navegador velho.
UA_TTF = 'Mozilla/5.0 (Windows NT 6.1)'


def buscar(url, ua=UA_TTF):
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    css = buscar(CSS).decode('utf-8')

    # cada bloco @font-face traz familia, peso e url do ttf
    import re
    blocos = re.findall(r'@font-face\s*\{(.*?)\}', css, re.S)
    baixados = 0
    for b in blocos:
        fam = re.search(r"font-family:\s*'([^']+)'", b)
        peso = re.search(r'font-weight:\s*(\d+)', b)
        url = re.search(r'src:\s*url\(([^)]+)\)', b)
        if not (fam and peso and url):
            continue
        nome = '%s-%s.ttf' % (fam.group(1).replace(' ', ''), peso.group(1))
        alvo = DESTINO / nome
        if alvo.exists():
            print('  ja tenho  %s' % nome)
            continue
        alvo.write_bytes(buscar(url.group(1)))
        print('  baixado   %-28s %6d bytes' % (nome, alvo.stat().st_size))
        baixados += 1

    if not baixados and not any(DESTINO.iterdir()):
        sys.exit('ERRO: nada baixado - o CSS do Google veio sem url de ttf?')
    print()
    print('%d arquivos em %s' % (len(list(DESTINO.iterdir())), DESTINO))
    return 0


if __name__ == '__main__':
    sys.exit(main())
