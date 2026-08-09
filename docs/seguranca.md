# Backlog de segurança

Aberto em 09/ago/2026, a partir da investigação do [web auth token](auth-token.md).

**Este documento não corrige nada.** Ele existe para que os itens abaixo sejam decididos
conscientemente, e não descobertos no dia em que o servidor abrir. Hoje a stack roda em
`127.0.0.1` numa máquina de desenvolvimento — quase tudo aqui só vira problema de verdade
na migração para VPS. É exatamente por isso que precisa estar escrito antes.

## Situação

| # | Item | Sev | Status |
|---|---|---|---|
| 1 | [Web auth token desligado](#1--web-auth-token-desligado) | média | mitigado / a reavaliar |
| 2 | [MariaDB publicado no host](#2--mariadb-publicado-no-host) | alta | a analisar |
| 3 | [Senhas default no compose versionado](#3--senhas-default-no-compose-versionado) | alta | a analisar |
| 4 | [Credenciais inter-server `s1`/`p1`](#4--credenciais-inter-server-s1p1) | alta | a analisar |
| 5 | [Web-server em HTTP puro](#5--web-server-em-http-puro-sem-tls) | alta | a analisar |
| 6 | [Token gravado em claro no banco](#6--token-gravado-em-claro-no-banco) | média | a analisar |
| 7 | [Fallback de geração sem hash](#7--fallback-de-geração-sem-hash) | média | a analisar |
| 8 | [Loop de retry que não conta](#8--loop-de-retry-que-não-conta-defeito-upstream) | baixa | a analisar |
| 9 | [Token de 16 chars](#9--token-de-16-chars) | baixa | provavelmente aceitar |
| 10 | [`allowed_origin_cors` vazio](#10--allowed_origin_cors-vazio) | info | a analisar |
| 11 | [Login publicado em duas portas](#11--login-publicado-em-duas-portas) | baixa | a analisar |

Severidade é **para produção em VPS**, não para o ambiente atual.

---

### 1 — Web auth token desligado

`use_web_auth_token: no` em [conf/import/login_conf.txt](../conf/import/login_conf.txt).

Contorno para o bloqueio de login causado pelo conflito de porta. É *fail-closed*:
`isAuthorized()` ([src/web/auth.cpp:35](../src/web/auth.cpp#L35)) exige
`web_auth_token_enabled = '1'`, e sem geração a coluna fica `0` — o web-server rejeita
tudo em vez de liberar. **Não abre buraco de autenticação**, mas deixa inoperantes
emblema de guild, configs de char/conta, party booking e busca de lojas.

**Correção:** liberar a 8888 e religar. Passo a passo em [auth-token.md](auth-token.md#como-religar).
**Prazo:** antes de abrir para jogadores.

### 2 — MariaDB publicado no host

[docker-compose.yml:17](../docker-compose.yml#L17) → `"3307:3306"`.

O Docker publica em `0.0.0.0` por padrão. Numa VPS isso expõe o banco à internet, e o
banco tem as contas dos jogadores (tabela `login`) e todos os logs. Um `iptables` mal
configurado ou um firewall de nuvem esquecido basta.

Hoje o mapeamento não é necessário para o servidor funcionar — os quatro serviços falam
com o host `db` pela rede interna do compose ([conf/inter_athena.conf:34-75](../conf/inter_athena.conf#L34-L75)).
Só existe para acesso de ferramenta externa.

**Correção:** trocar por `"127.0.0.1:3307:3306"` (bind só no loopback), ou remover a
publicação e acessar via `docker compose exec db mysql`.
**Prazo:** antes da migração para VPS. Barato de fazer agora.

### 3 — Senhas default no compose versionado

[docker-compose.yml:7-10](../docker-compose.yml#L7-L10) — `MYSQL_ROOT_PASSWORD`,
`MYSQL_USER` e `MYSQL_PASSWORD` todos `ragnarok`, em texto, num arquivo commitado.
As mesmas credenciais se repetem 6 vezes em
[conf/inter_athena.conf](../conf/inter_athena.conf) (login, ipban, char, map, web, log).

Combinado com o item 2, é acesso root ao banco para quem alcançar a porta. E como está
em git, trocar a senha depois não apaga o histórico.

**Correção:** mover para um `.env` fora do git (`env_file:` no compose, `.env` no
`.gitignore`), com um `.env.example` versionado documentando as chaves. O
`inter_athena.conf` precisa mudar junto — e o override dele vai em `conf/import/inter_conf.txt`,
não no arquivo do upstream.
**Prazo:** junto com o item 2.

### 4 — Credenciais inter-server `s1`/`p1`

[conf/char_athena.conf:8-9](../conf/char_athena.conf#L8-L9) e
[conf/map_athena.conf:13-14](../conf/map_athena.conf#L13-L14) — `userid: s1`, `passwd: p1`.

São as credenciais **default do rAthena**, públicas e conhecidas por qualquer pessoa que
já tenha visto o projeto. É com elas que o char-server e o map-server se autenticam no
login-server, e a conta correspondente existe no banco com `sex = 'S'`
([sql-files/main.sql](../sql-files/main.sql)).

O risco concreto: com a porta do login-server alcançável (6900 e 6951, item 11), alguém
pode se conectar apresentando `s1`/`p1` e se registrar como um char-server. A partir daí
recebe o tráfego inter-server. É o item de hardening mais clássico do rAthena, e o
`char_athena.conf` traz o aviso "**Do not forget to change**" no próprio comentário.

**Correção:** trocar `userid`/`passwd` nos dois arquivos, atualizar a linha correspondente
na tabela `login`, e usar `conf/import/char_conf.txt` e `conf/import/map_conf.txt` para o
override — assim não conflita no merge e não vai para o git (a pasta é ignorada, exceto
pelas exceções explícitas do [.gitignore](../.gitignore)).
**Prazo:** antes de qualquer exposição fora do localhost. É o item mais barato e mais
importante desta lista.

### 5 — Web-server em HTTP puro, sem TLS

[src/web/web.cpp:504](../src/web/web.cpp#L504) — `http_server->listen(...)`. O rAthena
não implementa HTTPS aqui.

O token de autenticação trafega em claro no corpo multipart de cada requisição
([src/web/auth.cpp:23](../src/web/auth.cpp#L23)). Em rede local não importa; entre o
jogador e uma VPS, qualquer intermediário lê. Com o token e o `AID` capturados, dá para
falar com os endpoints do web-server como se fosse o jogador enquanto ele está online.

**Correção:** pôr um reverse proxy com TLS (nginx / Caddy) na frente do web-server e
publicar só ele. Depende de o cliente aceitar `https://` para esse endpoint — **não
verificado**, e o item 1 precisa estar resolvido antes de dar para testar.
**Prazo:** antes de expor o web-server fora do localhost.

### 6 — Token gravado em claro no banco

[sql-files/main.sql:789](../sql-files/main.sql#L789) — `web_auth_token varchar(17)`, valor
utilizável direto.

Quem lê a tabela `login` consegue se passar por qualquer jogador online no web-server, sem
precisar da senha. O token é rotacionado a cada login e revogado 10 s após o logout
([src/login/account.cpp:935](../src/login/account.cpp#L935)), o que limita a janela —
mas dentro dela é uma credencial válida em texto puro.

Note que a coluna `user_pass` da mesma tabela pode estar em MD5 ou em claro conforme
`use_MD5_passwords` em [conf/login_athena.conf](../conf/login_athena.conf); vale auditar
as duas juntas.

**Correção:** é comportamento do upstream. Mudar exigiria patch em `account.cpp` +
`auth.cpp` (gravar hash, comparar hash) e sairia da compatibilidade com o rAthena.
Provavelmente o certo é **aceitar e restringir o acesso ao banco** (itens 2 e 3), não patchar.

### 7 — Fallback de geração sem hash

[src/login/account.cpp:669-671](../src/login/account.cpp#L669-L671):

```sql
UPDATE `login` SET `web_auth_token` = LEFT( CONCAT( UUID(), RAND() ), 16 ) ...
```

Usado quando o MySQL não tem `SHA2` nem `MD5`. Sem hash, os 16 chars são o **prefixo do
`UUID()`** — que no MySQL é UUID v1, derivado de timestamp e endereço MAC. Os primeiros
16 caracteres de um UUID v1 são quase inteiramente o timestamp: previsíveis por quem
sabe a hora aproximada do login. O `RAND()` fica depois do corte e não entra.

Só dispara em MySQL antigo, e o código emite `ShowWarning` quando cai nesse caminho.
Nosso MariaDB 10.5 tem SHA2 — **não estamos nesse cenário hoje**.

**Correção:** conferir no boot que o warning não aparece; se um dia aparecer, tratar como
incidente, não como aviso. A versão do MariaDB já está fixada em
[docker-compose.yml:4](../docker-compose.yml#L4), o que ajuda a manter isso estável.

### 8 — Loop de retry que não conta (defeito upstream)

[src/login/account.cpp:676-691](../src/login/account.cpp#L676-L691):

```cpp
const int32 MAX_RETRIES = 20;
int32 i = 0;
do{
    if( SQL_SUCCESS == Sql_Query( ... ) ){ success = true; break; }
}while( i < MAX_RETRIES && Sql_GetError( sql_handle ) == 1062 );
```

**`i` nunca é incrementado.** Consequências: `i < MAX_RETRIES` é sempre verdadeiro, então
o "máximo de 20 tentativas" não existe — o loop repete enquanto o erro for 1062
(violação da UNIQUE KEY do token). E o `if( i == MAX_RETRIES )` logo abaixo nunca é
verdadeiro, então a mensagem de erro específica jamais é emitida.

Na prática exige uma colisão persistente de token para travar, o que é improvável com
SHA2. Mas é um laço sem limite real dentro do save de conta — bloquearia o login-server.

**Correção:** é bug do upstream `rathena/rathena`, não nosso. Vale reportar lá. Um patch
local em `src/custom/` custaria mais em conflito de merge do que o risco justifica.

### 9 — Token de 16 chars

[src/common/mmo.hpp:121](../src/common/mmo.hpp#L121) — `WEB_AUTH_TOKEN_LENGTH 16+1`.

O SHA2-256 é truncado em 16 caracteres hex ≈ 64 bits. Não é adivinhável por força bruta
online, e o campo é ditado pelo tamanho fixo no pacote `AC_ACCEPT_LOGIN`
([src/common/packets.hpp:195](../src/common/packets.hpp#L195)) — mudar quebraria o
protocolo com o cliente.

**Correção:** nenhuma viável. Registrar e seguir.

### 10 — `allowed_origin_cors` vazio

[conf/web_athena.conf:65](../conf/web_athena.conf#L65).

Vazio significa que o web-server não emite header CORS, o que **bloqueia** chamadas de
navegador de outra origem. É o default seguro. Vira item quando o `ragna-site` precisar
falar com o web-server pelo browser — aí a tentação será liberar `*`.

**Correção:** quando chegar a hora, listar a origem exata do site, nunca `*`.
Note que [conf/web_athena.conf:67](../conf/web_athena.conf#L67) importa
`conf/import/web_conf.txt`, **que não existe** — é o lugar certo para esse override.

### 11 — Login publicado em duas portas

[docker-compose.yml:28,34](../docker-compose.yml#L28) — `6900:6900` e `6951:6900`.

A 6951 existe porque o cliente 2025-04-16 deriva essa porta em código
(ver [cliente/leia-me.md](cliente/leia-me.md)). A 6900 é a original. Duas portas para o
mesmo serviço é superfície de ataque duplicada de graça — e a 6900 provavelmente não é
mais usada por ninguém.

**Correção:** verificar se algum cliente ainda usa a 6900; se não, remover a publicação
e deixar só a 6951.
**Prazo:** limpeza, sem urgência.

---

## Fora deste documento

- **Segurança de gameplay** (exploits de script, dupe, `@commands` liberados demais em
  [conf/groups.yml](../conf/groups.yml)) — é outra categoria de risco. Vale um documento
  próprio quando o servidor tiver jogadores.
- **Segurança do cliente** (patches do WARP, GameGuard, integridade do GRF) — ver
  [cliente/leia-me.md](cliente/leia-me.md).
- **Backup** — está na Fase 5 do [ROADMAP.md](../ROADMAP.md). Perda de dados não é
  ataque, mas mata um servidor do mesmo jeito.
