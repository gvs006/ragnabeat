# Ragnabeat

Servidor **pre-renewal** (`PRERE` em [src/config/renewal.hpp:8](src/config/renewal.hpp#L8)),
`PACKETVER 20250416`, rates 500x/20x, limites 99/70, stack Docker + MariaDB.

- **O que construir** → [ROADMAP.md](ROADMAP.md)
- **Como o que existe funciona** → [docs/](docs/README.md)
- **Cliente e tradução** → [docs/cliente/estado-e-plano.md](docs/cliente/estado-e-plano.md) e [docs/traducao.md](docs/traducao.md)

---

## Encoding: cp1252, e o erro custa caro

Todo `.txt` de NPC, `.conf` e `.yml` próprio do servidor é **cp1252**. Só
`docs/**/*.md` é UTF-8.

Não é preferência: o cliente converte texto com o codepage **1252 compilado no
binário** ([docs/cliente/acentuacao.md](docs/cliente/acentuacao.md)). UTF-8 chega
nele como dois caracteres por acento.

Em 03/set/2026 o editor abriu cinco arquivos cp1252 como UTF-8 e **gravou**,
trocando cada acento por `U+FFFD`. `Bênção` virou `Bï¿½nï¿½ï¿½o` na tela. A perda é
irreversível sozinha — o `U+FFFD` não guarda qual acento era; a volta foi palavra
por palavra.

```bash
python docs/checar-encoding.py     # antes de commitar qualquer coisa com acento
```

Os dois erros possíveis não são simétricos: **cp1252 lido como UTF-8 destrói**;
UTF-8 lido como cp1252 vira `Ã©`, feio mas reversível. Por isso o
[ragnabeat.code-workspace](ragnabeat.code-workspace) trava
`files.autoGuessEncoding: false`. Abra o projeto **pelo workspace**, não pela
pasta, ou a regra não vale.

---

## Trazer conteúdo do renewal: sempre adaptar, nunca copiar

**Nada de `db/re/` funciona direto aqui.** Aquelas entradas são `Mode: Renewal` e
nem carregam; quando copiadas, trazem números calculados para fórmulas que este
servidor não usa. O porte do Bio Lab 4 (03/set/2026) é o caso de referência — os
mobs vieram **invulneráveis**, e o log só dizia `Invalid monster defense 667,
capping...`.

Checklist para cada mob vindo do renewal:

1. **DEF e MDEF são percentuais no pre-re.** `DEF 100 = imune a dano físico`, e o
   teto é `DEFTYPE_MAX = CHAR_MAX = 127` ([src/config/const.hpp:55](src/config/const.hpp#L55)).
   O renewal usa `SHRT_MAX` e valores na casa das centenas. Capar não resolve —
   127 já é invulnerável. **Reescreva.**
2. **Nível** acima de 99 não faz sentido com o teto 99/70.
3. **EXP costuma vir zerada** — o renewal define exp de MVP por outro caminho.
   Confira `BaseExp`/`JobExp`, senão matar o bicho não dá nada.
4. **Drops apontam para itens que podem não existir aqui.** Tire, ou confira um
   por um.
5. **As habilidades não vêm junto** — e, quando vêm, precisam de auditoria.
   `db/re/mob_skill_db.txt` não é lido neste build (`mob.cpp:7231`, a lista
   `dbsubpath` monta `db/pre-re/`). Sem copiar as linhas para
   `db/import/mob_skill_db.txt`, o mob entra **mudo**.

   Copiadas, confira o **nível de cada linha**. `MAX_SKILL_LEVEL` é 13
   ([skill.hpp:43](src/map/skill.hpp#L43)) e acima disso o rAthena **não lê a
   tabela: ele extrapola** — pega os três últimos níveis definidos e projeta a
   reta ([skill.cpp:166](src/map/skill.cpp#L166)). Um `MG_FIREBALL` nível 43,
   normal no renewal, inventa um valor 30 níveis além do que o db descreve.
   Corte para o `MaxLevel` real da skill no pre-re.

   Nível acima do máximo mas **até 13** é seguro: o índice é limitado e a skill
   usa o valor do nível mais alto definido.

   Depois confira as skills de dano na fórmula, não pelo nome. Duas que
   assustam e não são o que parecem: `NPC_SELFDESTRUCTION` causa o **HP atual**
   do mob ([battle.cpp:6528](src/map/battle.cpp#L6528)), então o teto é a
   condição de disparo; e `CR_ACIDDEMONSTRATION` no pre-re usa o **INT do
   conjurador ao quadrado** ([battle.cpp:6589](src/map/battle.cpp#L6589)) — se
   você rebalancear o INT do mob, refaça essa conta.

**Como rebalancear:** escolha um conteúdo pre-re equivalente como régua e
**remapeie linearmente** cada stat da faixa de origem para a faixa alvo. Isso
preserva a ordem entre os mobs — quem era o mais tanque continua sendo — em vez
de digitar números no olho. O Bio Lab 4 usou o `lhz_dun03` como régua; a conta
inteira está no cabeçalho de [db/ragnabeat_biolab4.yml](db/ragnabeat_biolab4.yml).

O mesmo vale para item, skill e mapa vindos do renewal: assuma que o número está
errado até provar o contrário.

---

## Arquivos gerados não se edita à mão

Estes são reescritos por script e qualquer edição manual some na próxima
regeneração:

| Arquivo | Gerador |
|---|---|
| `db/import/item_db.yml` | `docs/cliente/gen-nomes-servidor.py` |
| `db/ragnabeat_mob_names.yml` | `docs/gerar-nomes-mob.py` |
| `db/ragnabeat_mobs.yml` | `docs/gerar-champions.py` |
| `npc/custom/champions.txt` | `docs/gerar-champions.py` |
| `patcher/config.ini`, `patcher/images/` | `patcher/gerar-visual.py` |

Conteúdo próprio vai em **outro** `.yml`, enganchado pelo `Footer:`/`Imports:` —
é o que fazem `db/ragnabeat_mob_nomes_extra.yml` e `db/ragnabeat_biolab4.yml`.

---

## Nome de monstro vem do servidor

Diferente de item, que o cliente resolve. O campo é `Name:` do `mob_db`, e
**`override_mob_names: 1`** em [conf/import/battle_conf.txt](conf/import/battle_conf.txt)
é o que faz o servidor usá-lo — com `0` ele usa o nome cravado na linha de spawn,
que está em inglês em todo `npc/pre-re/mobs/`. Não use `2`: no db em YAML isso lê
`JapaneseName`, presente em 147 entradas.

---

## Testar uma mudança sem derrubar o servidor

O map-server sobe com `OpenStdin=false`, então não dá para mandar comando ao
console. Para conferir se um script ou db carrega, rode uma instância
descartável — ela lê tudo, imprime os erros e sai:

```bash
docker exec ragnabeat_server sh -lc 'cd /server && \
  cp conf/map_athena.conf /tmp/mt.conf && \
  printf "\nchar_ip: 127.0.0.1\nchar_port: 1\nmap_port: 16899\n" >> /tmp/mt.conf && \
  ./map-server --run-once --map-config /tmp/mt.conf 2>&1 | grep -i "error\|warning"'
```

O `char_ip` inválido é de propósito: impede que ela registre no char-server e
atrapalhe a que está no ar.

Depois: `@reloadscript` para NPC; **restart** para `conf/` e `db/`.
