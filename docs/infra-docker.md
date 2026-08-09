# Infra — Docker, portas e banco

Como a stack sobe e por que cada porta existe. Escrito em 09/ago/2026.

---

## A stack

Dois serviços em [docker-compose.yml](../docker-compose.yml):

| Serviço | Container | Imagem |
|---|---|---|
| `db` | `ragnabeat_db` | `mariadb:10.5` |
| `rathena` | `ragnabeat_server` | build local do [Dockerfile](../Dockerfile) (Ubuntu 22.04 + toolchain) |

O `rathena` roda os **quatro** servidores num container só
([docker-compose.yml:42](../docker-compose.yml#L42)):

```
./login-server & ./char-server & ./map-server & ./web-server & wait
```

O repositório inteiro é montado em `/server` (`.:/server`,
[docker-compose.yml:26](../docker-compose.yml#L26)). Consequência prática: **editar conf,
db ou npc no host altera o que o container lê** — sem rebuild de imagem. Só mudança em
`src/` exige recompilar.

## Portas

| Publicação | Serviço | Por quê |
|---|---|---|
| `3307:3306` | MariaDB | acesso de ferramenta externa. Não é necessário para o servidor funcionar — ver [seguranca.md item 2](seguranca.md#2--mariadb-publicado-no-host) |
| `6900:6900` | login-server | porta padrão do rAthena |
| `6951:6900` | login-server | **o cliente 2025-04-16 conecta aqui.** A porta é derivada em código, não vem do `clientinfo.xml`. Encaminhamos para a 6900 em vez de mexer na config do rAthena |
| `6121:6121` | char-server | |
| `5121:5121` | map-server | |
| `8889:8888` | web-server | **a 8888 do host está ocupada pelo OpenTelemetry Collector.** É a origem do bloqueio de login — ver [auth-token.md](auth-token.md) |

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
