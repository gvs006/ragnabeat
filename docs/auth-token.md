# Web Auth Token — por que está desligado

Escrito em 09/ago/2026. Registra a correção do bloqueio de login e o que ela custa.

> **Estado atual: `use_web_auth_token: no`**, definido em [conf/import/login_conf.txt](../conf/import/login_conf.txt).
> É um contorno, não uma solução. Ver [Como religar](#como-religar) e o item 1 de [seguranca.md](seguranca.md).

---

## O sintoma

O cliente 2025-04-16 travava em **"Please wait"** logo após informar login e senha.
No log do login-server aparecia o `request connect` e, em seguida,
`Web Auth Token for account ... was disabled` — e **nunca** o `Char load request`.
Ou seja: o login era aceito, mas o cliente não avançava para o char-server.

## A causa

O cliente moderno não usa só os sockets de login/char/map. Ele busca dados adicionais
por **HTTP** num quarto serviço, o *web-server*, autenticando-se com um token que o
login-server entrega dentro do pacote de aceite.

O web-server do rAthena escuta na **8888**:

| Onde | O quê |
|---|---|
| [conf/web_athena.conf:13](../conf/web_athena.conf#L13) | `web_port: 8888` |
| [src/web/web.cpp:290](../src/web/web.cpp#L290) | mesmo valor como default hardcoded |
| [src/web/web.cpp:504](../src/web/web.cpp#L504) | `http_server->listen(...)` |

**A 8888 do host está ocupada pelo OpenTelemetry Collector.** Por isso o
[docker-compose.yml](../docker-compose.yml) publica o web-server na **8889**
(`8889:8888`) — e o cliente não sabe disso. Ele procura o token onde espera encontrar,
não encontra, e fica preso na tela de espera.

## O fluxo completo do token

Vale ter mapeado, porque é ele que decide o que quebra ao desligar a flag.

**1. Configuração**

| Onde | O quê |
|---|---|
| [conf/login_athena.conf:174](../conf/login_athena.conf#L174) | `use_web_auth_token: yes` (upstream, não modificado) |
| [src/login/login.cpp:667](../src/login/login.cpp#L667) | leitura da diretiva |
| [src/login/login.cpp:791](../src/login/login.cpp#L791) | default no código: `true` |
| [conf/login_athena.conf:179](../conf/login_athena.conf#L179) | `disable_webtoken_delay: 10000` (ms) |

O `import: conf/import/login_conf.txt` está em
[conf/login_athena.conf:194](../conf/login_athena.conf#L194) — **depois** da diretiva.
Por isso o override do `import/` vence.

**2. Geração** — [src/login/account.cpp:651-712](../src/login/account.cpp#L651-L712), dentro do save da conta

- Guarda: `acc->sex != 'S' && login_config.use_web_auth_token && refresh_token` — conta de servidor nunca recebe token
- Escolhe a query por capacidade do MySQL, uma vez só (`static bool initialized`):
  1. `LEFT( SHA2( CONCAT( UUID(), RAND() ), 256 ), 16 )` — preferida
  2. `LEFT( MD5( CONCAT( UUID(), RAND() ) ), 16 )` — fallback
  3. `LEFT( CONCAT( UUID(), RAND() ), 16 )` — **sem hash nenhum**, com `ShowWarning`
- Trunca em `WEB_AUTH_TOKEN_LENGTH - 1` = **16 chars** ([src/common/mmo.hpp:121](../src/common/mmo.hpp#L121) → `16+1`)
- Relê o valor gerado do banco e copia para `acc->web_auth_token`

**3. Entrega ao cliente**

| Onde | O quê |
|---|---|
| [src/login/login.cpp:426](../src/login/login.cpp#L426) | `if( login_config.use_web_auth_token )` → copia para a sessão |
| [src/login/loginclif.cpp:127](../src/login/loginclif.cpp#L127) | grava no campo `token` do `PACKET_AC_ACCEPT_LOGIN`, sob `#if PACKETVER >= 20170315` |
| [src/common/packets.hpp:195](../src/common/packets.hpp#L195) | o campo `char token[WEB_AUTH_TOKEN_LENGTH]` no struct do pacote `0xac4` |

Nosso `PACKETVER` é **20250416** (`src/custom/defines_pre.hpp`), então o campo existe e
o cliente o espera.

**4. Ciclo de vida**

| Evento | Onde | Efeito no banco |
|---|---|---|
| char-server reporta conta online | [src/login/login.cpp:105](../src/login/login.cpp#L105) → [account.cpp:914](../src/login/account.cpp#L914) | `web_auth_token_enabled = '1'` |
| conta fica offline | [src/login/login.cpp:127](../src/login/login.cpp#L127) → [account.cpp:952](../src/login/account.cpp#L952) | agenda timer de 10 s |
| timer dispara | [src/login/account.cpp:935-941](../src/login/account.cpp#L935-L941) | `web_auth_token_enabled = '0'` + o `ShowInfo` que vimos no log |
| boot / limpeza | [src/login/account.cpp:960](../src/login/account.cpp#L960) | `web_auth_token = NULL` em todas as contas |

O delay de 10 s existe por causa de uma corrida documentada no próprio conf: o char-server
poderia revogar o token antes de o cliente terminar de salvar as configs.

**5. Validação** — [src/web/auth.cpp:16-50](../src/web/auth.cpp#L16-L50)

```sql
SELECT `account_id` FROM `login`
 WHERE (`account_id` = ? AND `web_auth_token` = ? AND `web_auth_token_enabled` = '1')
```

Exige os campos multipart `AuthToken` e `AID` (mais `GDID` quando checa líder de guild).
Falhou → `ShowWarning("Request with AID %d and token %s unverified")`.

**6. Persistência** — [sql-files/main.sql:789-793](../sql-files/main.sql#L789-L793)

```sql
`web_auth_token` varchar(17) null,
`web_auth_token_enabled` tinyint(2) NOT NULL default '0',
UNIQUE KEY `web_auth_token_key` (`web_auth_token`)
```

O `varchar(17)` casa com `16+1`; o valor gravado tem 16 chars.
Migração equivalente em [sql-files/upgrades/upgrade_20200625.sql](../sql-files/upgrades/upgrade_20200625.sql).

> **Nada disso passa pelo char-server ou pelo map-server.** Não há uma única
> referência a `web_auth_token` em `src/char/` ou `src/map/` — eles só participam
> indiretamente, pelos pacotes de online/offline.

## A correção aplicada

[conf/import/login_conf.txt](../conf/import/login_conf.txt):

```
use_web_auth_token: no
```

Com a flag desligada, o login-server nunca gera nem envia token, o cliente para de
esperá-lo, e o login completa. Confirmado no log: `'<conta>' logged in`, com o
inventário carregado.

Escolhemos `conf/import/` e não editar `conf/login_athena.conf` direto porque é a
convenção do projeto — customização em `import/` não conflita no merge com o upstream
(ver *Convenções* no [ROADMAP.md](../ROADMAP.md)).

### O que isso custa

`isAuthorized()` passa a **falhar sempre**: sem geração, o token fica `NULL` e
`web_auth_token_enabled` fica `0`, e a query de validação nunca casa.

Isso é *fail-closed* — o web-server rejeita tudo, não libera nada. **Não abre buraco de
autenticação.** Mas desliga junto todas as features que dependem dele, em `src/web/`:

| Controller | Feature no cliente |
|---|---|
| `emblem_controller.cpp` | emblema de guild (upload e download) |
| `charconfig_controller.cpp` | configs de personagem salvas no servidor |
| `userconfig_controller.cpp` | configs de conta salvas no servidor |
| `partybooking_controller.cpp` | mural de recrutamento de party |
| `merchantstore_controller.cpp` | busca de lojas de mercador |

Na prática: emblema de guild não sobe, e as preferências de interface do jogador não
sobrevivem a uma troca de máquina. Aceitável enquanto o servidor não tem guildas ativas —
**revisitar antes de abrir para jogadores**.

## Como religar

1. Liberar a **8888** no host — remapear o OpenTelemetry Collector para outra porta,
   ou desligá-lo se não estiver em uso
2. Em [docker-compose.yml](../docker-compose.yml), trocar `"8889:8888"` por `"8888:8888"`
3. Remover a linha `use_web_auth_token: no` de [conf/import/login_conf.txt](../conf/import/login_conf.txt)
   (o default volta a ser `yes`, por [conf/login_athena.conf:174](../conf/login_athena.conf#L174))
4. `docker compose up -d --force-recreate`
5. Testar: logar, entrar com um personagem, e conferir que **não** aparece
   `Request with AID ... unverified` no log do web-server

Alternativa, se a 8888 não puder ser liberada: descobrir se o cliente aceita um endereço
de web-server configurável (via `clientinfo.xml` ou patch no WARP). **Não investigado** —
o cliente 2025 já ignora o `clientinfo.xml` para o endereço do login
(ver [cliente/leia-me.md](cliente/leia-me.md)), então é provável que ignore aqui também.

## Pendências de segurança

Este documento é o ponto de partida da análise de segurança do projeto. Os itens
levantados durante a investigação — token em claro, HTTP sem TLS, o fallback sem hash,
o banco publicado no host — estão catalogados em **[seguranca.md](seguranca.md)**.
Nenhum foi corrigido.
