# -*- coding: utf-8 -*-
"""
Reescreve as descricoes de Impacto Explosivo e Angelus para o comportamento
pre-renewal, que e o do NOSSO servidor.

Fonte da verdade (rAthena deste repositorio):
  SM_MAGNUM  src/map/skills/swordman/magnum.cpp:17-30, 52-57
             3x3 interno = 100 + 20*Nv | anel 5x5 = 100 + 10*Nv
             precisao +10%*Nv | 20% do ataque vira Fogo por 10s
             db/pre-re/skill_db.yml: Element Fire, SplashArea 2, Knockback 2,
             Duration2 10000, HpCost 20/20/19/19/18/18/17/17/16/16
             skill.cpp:3538 - exige o HP mas NAO consome
  AL_ANGELUS src/map/status.cpp:11620  val2 = 5*val1  (DEF +5%*Nv)
             src/map/status.cpp:7882   ramo #else = pre-renewal
             src/map/status.cpp:3187   o bonus de HP max esta dentro de
                                       #ifdef RENEWAL -> nao existe aqui
             db/pre-re/skill_db.yml: Duration1 = 30000*Nv

O texto do LATAM descrevia a versao renewal: ATQ unico de 120 a 300%,
"dano fisico aumentado em 20%" (na verdade e propriedade Fogo) e um bonus de
HP maximo no Angelus que o pre-renewal nao concede.
"""
import re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FONTE = Path(__file__).parent / '_extraido' / 'skilldescript.PTBR.lua'
ALVO = RAIZ / 'data' / 'luafiles514' / 'lua files' / 'skillinfoz' / 'skilldescript.lub'

C = '^000000'      # fim de cor
B = '^777777'      # cinza, o realce que o arquivo usa


def esc(t):
    """Converte nao-ASCII para escape decimal, como o unluac gera."""
    return ''.join(c if ord(c) < 127 else '\\%d' % c.encode('cp1252')[0] for c in t)


def bloco(chave, linhas):
    corpo = ',\r\n'.join('    "%s"' % esc(l) for l in linhas)
    return '  [SKID.%s] = {\r\n%s\r\n  },' % (chave, corpo)


# --- Impacto Explosivo ------------------------------------------------------
atq3, atq5 = [100 + 20 * n for n in range(1, 11)], [100 + 10 * n for n in range(1, 11)]
hp = [20, 20, 19, 19, 18, 18, 17, 17, 16, 16]

magnum = [
    'Impacto Explosivo',
    'Nível máximo: %s10%s' % (B, C),
    'Pré-requisitos: %sGolpe Fulminante 5%s' % (B, C),
    'Tipo: %sOfensiva%s' % (B, C),
    'Descrição:',
    '%sCausa dano físico de propriedade Fogo em' % B,
    '5x5 células ao redor e empurra os alvos.',
    'O dano depende da distância: quem está nas',
    '3x3 células internas recebe mais.',
    'Aumenta a Precisão em 10% por nível e, por',
    '10 segundos, 20% do seu ataque passa a ter',
    'propriedade Fogo.',
    'Exige HP para ser usada, mas não o consome.%s' % C,
    'Nível l ATQ 3x3 l ATQ 5x5 l HP exigido',
]
for i in range(10):
    magnum.append('[Nv %d]: %s%d%%%s l %s%d%%%s l %s%d%s'
                  % (i + 1, B, atq3[i], C, B, atq5[i], C, B, hp[i], C))

# --- Angelus ----------------------------------------------------------------
angelus = [
    'Angelus',
    'Nível máximo: %s10%s' % (B, C),
    'Pré-requisitos: %sProteção Divina 3%s' % (B, C),
    'Tipo: %sSuporte%s' % (B, C),
    'Descrição:',
    '%sReza para aumentar a DEF proveniente da VIT' % B,
    'de todos do grupo que estão na tela do',
    'usuário.%s' % C,
    'Nível l DEF l Duração',
]
for n in range(1, 11):
    angelus.append('[Nv %d]: %s+%d%%%s l %s%d segundos%s' % (n, B, 5 * n, C, B, 30 * n, C))

# --- aplicar ----------------------------------------------------------------
d = FONTE.read_bytes().decode('latin-1')
for chave, linhas in (('SM_MAGNUM', magnum), ('AL_ANGELUS', angelus)):
    pat = re.compile(r'  \[SKID\.%s\] = \{.*?\n  \},' % chave, re.S)
    if not pat.search(d):
        sys.exit('ERRO: bloco de %s nao encontrado' % chave)
    d = pat.sub(lambda m: bloco(chave, linhas).replace('\\', '\\\\'), d, count=1)
    # o replace acima protege a barra invertida do re.sub; desfaz o dobramento
    d = d.replace('\\\\', '\\')
    print('%-12s reescrito (%d linhas)' % (chave, len(linhas)))

if d.count('{') != d.count('}'):
    sys.exit('ERRO: chaves desbalanceadas depois da edicao')

ALVO.write_bytes(d.encode('latin-1'))
print()
print('gravado: %s (%d bytes)' % (ALVO, len(d)))
