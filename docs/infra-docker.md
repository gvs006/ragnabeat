# Infra — Docker, portas e banco

Como a stack sobe e por que cada porta existe. Escrito em 09/ago/2026.

---

## A stack

Dois serviços em [docker-compose.yml](../docker-compose.yml):

| Serviço | Container | Imagem |
|---|---|---|
| `db` | `ragnabeat_db` | `mariadb:10.5` |
| `rathena` | `ragnabeat_server` | build local do [Dockerfile](../Dockerfile) (Ubuntu 22.04 + toolchain) |

O `rathena` roda os **quatro** servidores num container só:

```
until (echo > /dev/tcp/db/3306) 2>/dev/null; do sleep 2; done
./login-server & ./char-server & ./map-server & ./web-server & wait -n; exit 1
```

As duas linhas parecem ruído e não são — cada uma existe por causa de uma falha
que já aconteceu. Ver [Boot: as duas travas](#boot-as-duas-travas).

O repositório inteiro é montado em `/server` (`.:/server`,
[docker-compose.yml:26](../docker-compose.yml#L26)). Consequência prática: **editar conf,
db ou npc no host altera o que o container lê** — sem rebuild de imagem. Só mudança em
`src/` exige recompilar.

## Boot: as duas travas

### 1. Esperar o MariaDB — o `depends_on` não cobre o boot do Windows

`login-server`, `char-server` e `web-server` chamam `Sql_Connect` no início e
**saem se falhar**. Não há retentativa. O `map-server` demora mais para chegar
no banco (carrega 13 mil NPCs antes), então ele sobrevive — e fica sozinho,
tentando a 6121 para sempre:

```
[Error]: Couldn't connect with uname='ragnarok',host='db',port='3306'
...
[Status]: Connecting to 127.0.0.1:6121
[Error]: make_connection: connect failed (socket #7, error 111: Connection refused)!
```

O compose tem `depends_on: db: condition: service_healthy`, e ainda assim isso
aconteceu em 10/ago/2026, depois de reiniciar o PC. O motivo:

> **`depends_on` só vale quando *você* roda `docker compose up`.** Quando o
> Docker Desktop religa os containers sozinho — boot do Windows, `restart:
> always` —, quem sobe é o daemon, e o daemon não conhece `depends_on`. Ele
> reinicia os dois em paralelo, e num boot frio o MariaDB ainda está em
> recuperação.

Por isso a espera vive **dentro do container**, no `command`: é o único ponto
que funciona nos dois caminhos. O `/dev/tcp` é do próprio bash — não exige
`mysql-client` na imagem.

### 2. `wait -n` — para a stack não ficar meio morta em silêncio

Com o `wait` seco, o bash só retorna quando **todos** os filhos acabam. Com um
único servidor vivo o container seguia `Up`, o `restart: always` nunca
disparava, e o servidor ficava inacessível sem nada indicar problema.

Com `wait -n` o bash volta assim que **qualquer** um sai; o `exit 1` derruba o
container de propósito e o `restart: always` sobe os quatro de novo. Testado:
matar o `char-server` derruba e recompõe a stack em menos de um minuto.

Efeito colateral aceito: se um servidor não conseguir subir por erro de config,
o container entra em ciclo de restart. É barulhento — e é melhor que meio morto
em silêncio.

## Portas

| Publicação | Serviço | Por quê |
|---|---|---|
| `3307:3306` | MariaDB | acesso de ferramenta externa. Não é necessário para o servidor funcionar — ver [seguranca.md item 2](seguranca.md#2--mariadb-publicado-no-host) |
| `6900:6900` | login-server | porta padrão do rAthena |
| `6950:6900` … `6960:6900` | login-server | **o cliente não usa porta fixa** — ver abaixo |
| `6121:6121` | char-server | |
| `5121:5121` | map-server | |
| `8888:8888` | web-server | o cliente monta a URL a partir do endereço do servidor mais a **porta 8888, fixa em código** — não há campo para ela no `clientinfo.xml`. A 8888 do host estava com o OpenTelemetry Collector, movido para a 8890 em 10/ago — ver [auth-token.md](auth-token.md) |

> ⚠ **Todos os clientes chegam ao container como `172.18.0.1`** (gateway da rede do
> compose), porque o Docker faz NAT. Isso quebrou a proteção anti-DDoS do rAthena e
> causou o login intermitente — ver [seguranca.md item 12](seguranca.md#12--proteção-anti-ddos-desligada--o-docker-colapsa-todos-os-ips).
> Qualquer coisa que dependa de distinguir jogadores por IP (antifraude, cooldown por
> IP do Vote4Points) **não vai funcionar** enquanto isso valer.

### A porta do login não é fixa — a causa do "Please wait"

De 08 a 11/ago/2026 o login travava e exigia abrir o cliente 2 a 4 vezes. A captura
que fechou o caso, com rastreio de socket do processo do cliente numa tentativa
travada:

```
12:14:51.377  0.0.0.0     0     Bound
12:14:51.380  127.0.0.1  6952   SynSent
```

`SynSent` = SYN enviado, ninguém respondeu. E o log do servidor, com `debug: yes`
ligado, **não registrou conexão nenhuma** naquele minuto.

**O cliente 2025 deriva a porta de login em runtime**, de um bloco de agency — não
usa a do `clientinfo.xml` nem uma fixa. Publicávamos só a 6900 e a 6951, então era
sorte: caindo numa dessas, entrava; caindo na 6952, travava até o TCP desistir.

Por isso todas as medições anteriores davam 30/30 e mesmo assim o cliente falhava —
testávamos as portas publicadas, e o cliente ia para outra.

Correção: publicar **6950 a 6960** apontando para o login-server.

> ⚠ **`"6950-6960:6900"` não funciona.** O compose aceita sem erro e depois ignora
> em silêncio: `docker port` não mostra nada e as portas ficam fechadas. Faixa no
> host exige faixa do mesmo tamanho no container. Por isso as onze estão listadas
> uma a uma.

Se um dia o sintoma voltar, o roteiro é este: ligar `debug: yes` em
[conf/import/packet_conf.txt](../conf/import/packet_conf.txt), rastrear
`Get-NetTCPConnection -OwningProcess <pid do cliente>` durante uma tentativa que
falhe, e ver em que porta ele parou.

O `bind_ip: 0.0.0.0` está ativo em [conf/char_athena.conf:31](../conf/char_athena.conf#L31)
e [conf/map_athena.conf:27](../conf/map_athena.conf#L27) — necessário dentro do container,
já que o Docker faz NAT da porta publicada para a interface interna.

Os IPs anunciados aos clientes são `127.0.0.1`
([char_athena.conf:24](../conf/char_athena.conf#L24),
[map_athena.conf:20,35](../conf/map_athena.conf#L20)). **Isso muda na migração para VPS** —
esses campos precisam do IP público, senão o cliente recebe o endereço errado depois do
login e trava.

## Banco

Todos os cinco pares de credenciais em
[conf/inter_athena.conf:34-75](../conf/inter_athena.conf#L34-L75) apontam para o host `db`,
resolvido pela rede interna do compose. Nenhum serviço usa a 3307.

Na primeira subida o MariaDB carrega os schemas automaticamente
([docker-compose.yml:14-15](../docker-compose.yml#L14-L15)):

```
./sql-files/main.sql  ->  /docker-entrypoint-initdb.d/1-main.sql
./sql-files/logs.sql  ->  /docker-entrypoint-initdb.d/2-logs.sql
```

> ⚠ Isso só roda com o volume **vazio**. Com `ragnabeat_data` já criado, alterar os `.sql`
> não tem efeito nenhum — é preciso aplicar a migração à mão, ou destruir o volume
> (`docker compose down -v`, **apaga tudo**).

Dados persistem no volume nomeado `ragnabeat_data`. Backup automático ainda não existe —
está na Fase 5 do [ROADMAP.md](../ROADMAP.md).

## Comandos

```bash
docker compose up -d              # sobe
docker compose logs -f rathena    # acompanha os 4 servidores (saída intercalada)
docker compose restart rathena    # recarrega conf/db/npc alterados no host
docker compose config             # valida o YAML sem subir nada
docker compose down               # derruba, preserva o volume
docker compose down -v            # derruba E APAGA O BANCO
```

Como os quatro servidores compartilham stdout, filtrar ajuda:

```bash
docker compose logs rathena | grep -i "login\|web auth"
```

## Config por instalação × config versionada

O rAthena trata `conf/import/` e `db/import/` como config local de cada instalação.
**Neste projeto é o oposto** — `import/` é onde vive toda a customização, justamente
para não conflitar no merge com o upstream.

Por isso o [.gitignore](../.gitignore) inverte a regra: ignora `/conf/import/*`
(linha 73) e depois abre **exceção por arquivo** no bloco do fim. Arquivo custom novo
precisa ser adicionado lá conscientemente, senão some no clone.

Versionados hoje:

| Arquivo | O que carrega |
|---|---|
| `conf/import/battle_conf.txt` | rates, limites |
| `conf/import/login_conf.txt` | `use_web_auth_token: no` — ver [auth-token.md](auth-token.md) |

## Rotina depois de um clone limpo

1. `docker compose up -d` — na primeira vez o MariaDB carrega os schemas e demora
2. `docker compose logs -f rathena` até ver os quatro servidores prontos
3. Conferir que `use_web_auth_token: no` está valendo:
   `grep use_web_auth_token conf/import/login_conf.txt`
4. Cliente: ver [cliente/leia-me.md](cliente/leia-me.md) — o `.exe` precisa dos patches
   de pós-build, que não vêm do repo

## Pendências

- **Migração para VPS**: trocar os `127.0.0.1` anunciados, restringir a 3307 ao loopback,
  trocar as credenciais default. Ver [seguranca.md](seguranca.md) itens 2, 3 e 4.
- **Backup do volume** — Fase 5 do [ROADMAP.md](../ROADMAP.md).
- **Ambiente de teste separado do de produção** — Fase 5.
- O `Dockerfile` tem um `CMD` antigo comentado com `-DENABLE_PACKETVER=20211103`, que não
  bate mais com o `PACKETVER 20250416` em uso. É comentário morto, mas confunde — vale
  limpar quando alguém mexer no build.
