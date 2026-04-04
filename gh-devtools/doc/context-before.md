# Contexto atual do projeto rAthena em Docker

## Objetivo
Estou tentando subir um servidor **rAthena** em **Docker Desktop no Windows**, usando:
- **Ubuntu 22.04** na imagem do servidor
- **MariaDB 10.5** no container do banco
- Projeto local em: `C:\IT\repo\ragnabeat`
- Nome do container do servidor: `ragnabeat_server`
- Nome do serviço do banco no compose: `db`

## Situação atual
O servidor **já compilou com sucesso** e os binários do rAthena foram gerados.
Também já consegui:
- fazer o container do rAthena parar de recompilar infinitamente
- fazer login no cliente
- chegar ao ponto em que o servidor sobe e o map-server fica ativo

Mas ainda existe problema de **conexão entre login/char/map/client**, especialmente na transição do login para a tela de personagens.

---

## Problemas que já aconteceram

### 1. Conflito de dependências na build
No começo, a imagem Ubuntu dava erro de apt:
- `libmariadb-dev` conflitava com `libmysqlclient-dev`
- isso quebrava a compilação no Dockerfile

Depois isso foi contornado, e o CMake passou a encontrar o MySQL corretamente.

### 2. CMake não encontrava MYSQL
Depois do conflito de pacotes, o CMake dava erro:
- `Stopping target common (requires common_base and MYSQL)`

Isso foi resolvido depois que o ambiente achou corretamente:
- `MYSQL`
- `PCRE`
- `ZLIB`

### 3. Comando `make server` não existia
Depois que o CMake funcionou, o build falhava com:
- `make: *** No rule to make target 'server'. Stop.`

Foi necessário mudar a forma de build para usar `make` normal.

### 4. Loop de recompilação / restart infinito
Depois de compilar 100%, o container ficava entrando em loop:
- compilava
- iniciava o rAthena
- saía com `code 0`
- Docker reiniciava tudo

Isso acontecia porque o script `./athena-start start` soltava os processos em background e o processo principal do container morria.

### 5. `tail -f log/map-server.log` falhava
Foi tentado segurar o container com:
```yaml
command: /bin/bash -c "./athena-start start && tail -f log/map-server.log"
```

Mas falhou porque:
- `log/map-server.log` não existia
- então o `tail` fechava
- o container reiniciava com `code 1`

### 6. Subida manual dos executáveis
Depois foi usado algo como:
```yaml
command: /bin/bash -c "./login-server & ./char-server & ./map-server & ./web-server & wait"
```

Isso fez os processos ficarem ativos no container, o que foi melhor para o Docker.

---

## Estado atual do docker-compose

Compose atual base:

```yaml
version: '3.8'
services:
  db:
    image: mariadb:10.5
    container_name: ragnabeat_db
    environment:
      MYSQL_ROOT_PASSWORD: ragnarok
      MYSQL_USER: ragnarok
      MYSQL_PASSWORD: ragnarok
      MYSQL_DATABASE: ragnarok
    volumes:
      - ragnabeat_data:/var/lib/mysql
      - ./sql-files/main.sql:/docker-entrypoint-initdb.d/1-main.sql
      - ./sql-files/logs.sql:/docker-entrypoint-initdb.d/2-logs.sql
    ports:
      - "3307:3306"
    restart: always

  rathena:
    build: .
    container_name: ragnabeat_server
    depends_on:
      - db
    volumes:
      - .:/server
    ports:
      - "6900:6900"
      - "6121:6121"
      - "5121:5121"
    restart: always
```

Em algum momento o `command` foi alterado para iniciar os executáveis manualmente, para evitar o container fechar.

---

## Estado atual do banco
O banco MariaDB aparentemente já está funcional.
Antes havia erro de conexão:
- `Can't connect to MySQL server on 'db:3306' (111)`

Mas depois isso foi resolvido, e o servidor conseguiu continuar.
Então **o banco não parece mais ser o principal problema**.

---

## Logs importantes já vistos

### Conexão com DB falhando no passado
```text
[SQL]: Can't connect to MySQL server on 'db:3306' (111)
[Error]: Couldn't connect with uname='ragnarok',host='db',port='3306',database='ragnarok'
```

### Map-server pronto
Também já apareceu algo como:
```text
[Status]: Server is 'ready' and listening on port '5121'.
```

### Falha do map-server para conectar no char-server
O erro atual/recorrente mais importante foi:
```text
[Status]: Attempting to connect to Char Server. Please wait.
[Status]: Connecting to 172.18.0.3:6121
[Error]: make_connection: connect failed (socket #7, error 111: Connection refused)!
```

Ou seja:
- o **map-server está tentando conectar no char-server usando IP interno do Docker (`172.18.0.3`)**
- isso indica que **o IP anunciado/configurado ainda está errado para esse fluxo**

---

## Arquivos de configuração já analisados

### `inter_athena.conf`
Já estava configurado com:
- `db` como host do MySQL
- porta `3306`
- usuário/senha/db = `ragnarok`

Ou seja, este arquivo **já estava correto** para banco.

### `char_athena.conf`
Arquivo enviado e analisado.
Pontos relevantes:
- `loginip 127.0.0.1`
- `bindip 127.0.0.1`
- `charip 127.0.0.1`

Mas no arquivo original essas configs estavam **comentadas** no formato padrão do rAthena, ou seja, existe a suspeita de que:
- o servidor está ignorando os valores esperados
- ou está usando autodetect
- ou algum `conf/import/*.txt` está sobrescrevendo tudo

### `map_athena.conf`
Também havia indicação de:
- `charip 127.0.0.1`
- `bindip 127.0.0.1`
- `mapip 127.0.0.1`

Mesmo assim, o servidor continuou tentando usar `172.18.0.3`, então a suspeita atual é:
- autodetect de IP interno
- override por `conf/import`
- ou ordem/forma de subida dos processos causando anúncio incorreto entre os servers

---

## Arquivos `conf/import`
Nos logs apareceram vários avisos/erros como:
```text
File not found: conf/import/inter_conf.txt
File not found: conf/import/packet_conf.txt
Configuration file not found: conf/import/char_conf.txt
Configuration file not found: conf/import/login_conf.txt
Configuration file not found: conf/import/web_conf.txt
Configuration file not found: conf/import/map_conf.txt
```

Esses erros não impediram totalmente o boot, mas levantaram a suspeita de que:
- a pasta `conf/import` pode não estar pronta
- pode existir necessidade de criar os arquivos de override explicitamente
- o rAthena pode estar caindo em autodetect por falta desses imports

---

## Sobre o cliente / Hexed
Situação atual:
- **Packet Obfuscation foi desativado no server**
- O servidor mostrou algo como:
```text
Packet Obfuscation: Disabled.
Using packet version: 20211103.
```

Ainda não foi confirmado se o Hexed está 100% alinhado com isso.
Mas o usuário **já conseguiu logar**, então pelo menos a parte de login está funcional.

---

## Sobre Pre-Renewal
Ainda **não foi configurado de verdade**.
O ambiente ainda parece estar com comportamento padrão mais próximo de Renewal.
Também apareceu warning de packet/feature moderna.

Então o problema de **entrar na tela de personagens NÃO parece ser por pre-renewal**.
Pre-renewal ainda é uma tarefa separada para depois estabilizar login/char/map.

---

## Sintoma atual principal
Resumo do problema atual:

- O servidor compila
- O container sobe
- O banco conecta
- O login funciona
- O usuário consegue autenticar no login-server
- Mas a transição para char-server / tela de personagens está inconsistente
- O sistema ainda tenta usar IP interno do Docker (`172.18.0.3`) em algum ponto
- Mesmo após editar configs e reiniciar, ele continua usando o mesmo IP

---

## O que já foi tentado
- editar `inter_athena.conf`
- editar `char_athena.conf`
- editar `map_athena.conf`
- reiniciar o container
- usar `docker-compose restart rathena`
- subir os servidores manualmente com `login-server`, `char-server`, `map-server`, `web-server`
- evitar o script `athena-start` por causa do comportamento em background
- segurar o container com `wait`
- verificar logs de conexão entre serviços

---

## Hipótese mais forte no momento
A hipótese principal é uma destas:

1. **`char_athena.conf` / `map_athena.conf` não estão sendo aplicados como esperado**
2. **algum arquivo em `conf/import` está faltando e o rAthena entra em autodetect**
3. **os IPs `bindip`, `charip`, `mapip`, `loginip` estão corretos para cliente local, mas não para a comunicação interna entre os próprios servers**
4. **o char-server pode não estar realmente escutando de forma acessível ao map-server quando os processos são lançados manualmente**
5. **a forma de iniciar todos os executáveis com `& ... & wait` pode estar gerando race condition ou anúncio errado de IP**

---

## O que preciso descobrir agora
Quero ajuda para identificar a forma correta de rodar o rAthena em Docker no Windows, garantindo:
- comunicação correta entre login-server, char-server e map-server
- cliente local conectando via `127.0.0.1`
- sem autodetect em `172.18.0.x`
- sem precisar recompilar toda hora
- sem loop de restart do container

Também quero saber:
- qual é a configuração certa de `loginip`, `bindip`, `charip`, `mapip`
- se devo usar `127.0.0.1`, `0.0.0.0`, nome do serviço Docker (`db`, `rathena`) ou IP da máquina host
- se preciso criar manualmente os arquivos em `conf/import/`
- se a forma atual de iniciar os executáveis está correta

---

## Extra
Depois que essa parte estabilizar, o próximo passo será:
- converter/configurar corretamente o servidor para **Pre-Renewal**
- alinhar isso com o cliente/Hexed
- ajustar criação de contas GM e grupos