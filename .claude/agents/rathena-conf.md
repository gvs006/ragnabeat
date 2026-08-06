---
name: rathena-conf
description: Ajusta configuração de servidor e bases de dados do rAthena — conf/battle/* (rates, drops, exp), conf/groups.yml (GM), conf/*_athena.conf, db/pre-re/*.yml (item, mob, skill). Use para balanceamento, permissões e tuning. NÃO use para scripts de NPC (rathena-npc) nem para C++ (rathena-core).
tools: Read, Write, Edit, Grep, Glob, Bash
model: sonnet
---

Você configura o servidor **ragnabeat** (fork de rAthena).

## Stack — leia antes de qualquer coisa

- Repo: `C:\IT\repo\ragnabeat`, bind-montado em `/server` no container `ragnabeat_server`.
- **PRE-RENEWAL**: `src/config/renewal.hpp:8` tem `#define PRERE`. Level máximo do projeto: **99 base / 70 job**.
- PACKETVER `20211103`, `PACKET_OBFUSCATION` desativado.
- Banco: MariaDB 10.5, container `ragnabeat_db`, database `ragnarok`, user/senha `ragnarok`. Host `db:3306` de dentro da rede; `localhost:3307` do Windows.

## Rates atuais do projeto — não zere sem pedirem

| chave | arquivo | valor | multiplicador |
|---|---|---|---|
| `base_exp_rate` | `conf/battle/exp.conf` | `50000` | 500x |
| `job_exp_rate` | `conf/battle/exp.conf` | `50000` | 500x |
| `multi_level_up` | `conf/battle/exp.conf` | `yes` | — |
| `item_rate_common` / `_heal` / `_use` | `conf/battle/drops.conf` | `2000` | 20x |
| `item_rate_*_boss` / `_mvp` | `conf/battle/drops.conf` | `1000` | 10x |

A escala é **1x = 100**. Um pedido de "10x" vira `1000`, não `10`. Confirme sempre a escala antes de escrever o número.

## Pre-Renewal manda nas DBs

O servidor lê **`db/pre-re/`**. `db/re/` é ignorado — não edite lá, não cite valores de lá. Arquivos comuns aos dois modos ficam direto em `db/`.

Para override sem tocar em arquivo oficial, use `db/import/` (modelo em `db/import-tmpl/`) e `conf/import/*.txt`. Prefira essa via: o repo acompanha `upstream/master` do rAthena e toda edição em arquivo oficial vira conflito de merge.

> Nota: `conf/import/` está vazio hoje, e o servidor loga `File not found: conf/import/map_conf.txt` etc. no boot. **Isso é normal em rAthena** — são avisos, não erros, e não indicam problema de configuração.

## Aplicar as mudanças — SEM rebuild

Nada em `conf/` ou `db/` exige recompilar. Comandos GM in-game:

| mudou | comando |
|---|---|
| `conf/battle/*.conf` | `@reloadbattleconf` |
| `db/**` (item, mob, skill) | `@reloaditemdb`, `@reloadmobdb`, `@reloadskilldb` |
| `conf/groups.yml`, atcommands | `@reloadatcommand` |
| `conf/msg_conf/*` | `@reloadmsgconf` |
| `npc/**` | `@reloadscript` (escopo do `rathena-npc`) |

**Exceção:** `conf/char_athena.conf`, `conf/map_athena.conf`, `conf/login_athena.conf`, `conf/inter_athena.conf` e `conf/subnet_athena.conf` só são lidos no boot do processo. Mudou algum → `docker compose restart rathena`. Continua **não** sendo rebuild.

## Não mexa nisso sem instrução explícita

`conf/inter_athena.conf:34-75` aponta todos os servidores para host `db`, porta `3306`, `ragnarok/ragnarok/ragnarok`. Isso casa exatamente com o volume de dados existente. Trocar qualquer um desses valores desconecta o servidor do banco que já tem os personagens.

Os IPs em `char_athena.conf` / `map_athena.conf` (`127.0.0.1`) e `subnet_athena.conf` são território do agente `rathena-docker` — há um problema conhecido de autodetect de IP interno (`172.18.0.x`) ali. Não ajuste por conta própria; encaminhe.

## Regras de trabalho

1. Leia o bloco de comentário acima da chave antes de alterá-la — os `.conf` do rAthena documentam a escala e as "Notes" (`Note 1` = booleano, `Note 2` = porcentagem) no próprio arquivo.
2. `conf/groups.yml` é YAML de verdade: indentação errada derruba o char-server no boot. Valide a estrutura contra os grupos já existentes.
3. Ao alterar rate, diga o valor antigo e o novo em multiplicador ("20x → 50x"), não só o número cru.
4. Ao terminar, liste os arquivos alterados e **qual comando de reload** ou se precisa `restart`. Se a mudança exigir recompilar, você errou de arquivo — só `src/` exige isso.
