# Thor Patcher do Midgard Eternal

Escrito em 03/set/2026, junto com a 0.0.11 — a primeira versão distribuída a
testers. O patcher é o que o tester abre; ele confere se há atualização, aplica,
e chama o cliente.

Base: **Thor Patcher 2.6.4.8**, que já estava em `DEVTOOLS/Thor Patcher/`.

---

## ⚠ O IP MUDA. Leia isto antes de qualquer outra coisa

Tudo aponta hoje para **100.76.66.99**, que é o endereço desta máquina na
tailnet do Tailscale. Esse endereço **não é estável**: ele muda se a máquina
sair e voltar para a tailnet, se o servidor mudar de host, ou no dia em que
isso virar um domínio público.

O endereço está em **cinco** lugares, e três deles exigem redistribuir o
cliente:

| Onde | O quê | Muda como |
|---|---|---|
| `patcher/config.ini` | `RootURL` e a URL dos dois `NoticeBox` | edita, **regera** e redistribui |
| `patcher/web/main.ini` | `file_url` | edita **no servidor**, vale na hora |
| `conf/import/char_conf.txt` | `char_ip` | edita e reinicia o char-server |
| `conf/import/map_conf.txt` | `map_ip` | edita e reinicia o map-server |
| `<cliente>/data/clientinfo.xml` | `<address>` | edita e **redistribui** |
| `MidgardEternal.exe` | 6 endereços **compilados no binário** | `pos-warp.py` e **redistribui** |

O `.exe` é o traiçoeiro: **o cliente 2025 não lê o `clientinfo.xml` para achar
o login**, ele usa uma tabela em `.rdata`. Trocar só o XML não adianta. Ver
[pos-warp.py](pos-warp.py).

Receita completa quando o IP mudar:

```
# 1. servidor
sed -i 's/100.76.66.99/<novo>/' conf/import/char_conf.txt conf/import/map_conf.txt
# 2. patcher (config local e config remota)
sed -i 's/100.76.66.99/<novo>/' patcher/config.ini patcher/web/main.ini
# 3. cliente
sed -i 's/100.76.66.99/<novo>/' C:/RagnaClient/RagnaBeat.Dev/data/clientinfo.xml
#    e o endereco dentro de cada exe:
cd C:/RagnaClient/RagnaBeat.Dev
python pos-warp.py MidgardEternal.exe   # o SERVIDOR no topo do pos-warp.py tambem muda
# 4. build novo + patcher dentro dele
python build.py
python patcher/gerar-visual.py    # reescreve o config.ini com o endereco novo
python patcher/montar.py
```

> O `build.py` **barra o build** se qualquer exe do tamanho do cliente
> (14.987.776 bytes) não contiver o `<address>` do `clientinfo.xml` que está
> indo junto. O critério é o tamanho e não o nome porque um glob
> `RagnaBeat*.exe` pegava junto o patcher, que é o Thor e não tem endereço
> nenhum dentro. Essa checagem entrou porque um dos exes secundários foi para a
> 0.0.11 ainda apontando para `127.0.0.1`:
> fora desta máquina ele conectaria em si mesmo e travaria em "Please wait",
> sem deixar rastro no log do servidor. Só o `MidgardEternal.exe` era conferido.

---

## As peças

```
patcher/
  gerar-visual.py     desenha bg.bmp e os botoes E GERA o config.ini
  baixar-fontes.py    baixa Cinzel e Barlow para fontes/
  montar.py           poe o patcher dentro de um build do cliente
  servir.py           publica web/ na tailnet
  config.ini          GERADO - config LOCAL, vai para a maquina do tester
  fontes/             GERADO por baixar-fontes.py
  images/             GERADO por gerar-visual.py
  Scripts/main.js     obrigatorio: sem ele o Thor nem abre
  Languages/          mensagens em PT-BR
  web/                o que fica no SERVIDOR
    main.ini          config remota
    plist.txt         lista de patches
    notice.html       abas + noticias (NoticeBox 0)
    status.html       status do mundo (NoticeBox 1)
    style.css
    data/             os .thor
```

Fluxo: `baixar-fontes.py` (uma vez) → `gerar-visual.py` → `build.py` →
`montar.py`. O `web/` e servido pela tarefa agendada, sem passo manual.

## Configuração de vídeo: fica no `savedata`, não no registro

**Eu errei isto na primeira volta e vale registrar o erro.** Os nomes
`ISFULLSCREENMODE`, `WIDTH`, `HEIGHT` e `DEVICECNT` estão dentro do binário e
existem em `HKLM\SOFTWARE\WOW6432Node\Gravity Soft\Ragnarok`, então parecia
óbvio que era de lá que o cliente lia. Cheguei a entregar um `Padrao-Video.reg`
baseado nisso.

**Não é.** Testei quatro resoluções escritas no registro — 1366×768, 1280×720,
1280×1024 e 1600×900 — e o cliente abriu em **1024×768 nas quatro**. Aquela
chave é do setup legado. Quem manda no cliente 2025 é o
`savedata/OptionInfo.lua`:

```lua
OptionInfoList["ISFULLSCREENMODE"] = 0
OptionInfoList["WIDTH"]  = 1366
OptionInfoList["HEIGHT"] = 768
```

Com essas três linhas em `savedata-padrao/OptionInfo.lua`, que o `build.py`
entrega como `savedata/OptionInfo.lua`, o cliente abriu em 1366×768 na
primeira. O `.reg` foi removido.

O que **não** pode entrar ali junto: `DX9DEVICEID` e `DX9DEVICENAME`. Esses
identificam a placa e o monitor de quem gerou o build; o cliente do tester
descobre os dele sozinho.

O `RagnarokKR.ini` que ainda vai no build é peso morto: a string
`RagnarokKR.ini` não aparece em lugar nenhum do binário. O patch
`LoadKrExtSettings`, que parecia candidato a lê-lo, é sobre o lua de
`ExternalSettings` — outra coisa.

### O cap de 60 FPS

É o **VSync**, e a opção é do `opensetup.exe` (RO OpenSetup 3.4.0.680, do
Ai4rei): a caixa **Disable VSync**, cuja própria descrição diz *"Disable VSync
so RO can properly utilize modern GPUs"*. A chave se chama `DisableVSync` e
**não existe no registro** desta máquina, ou seja, está no padrão — travado na
taxa do monitor.

Não é patch do WARP: não há nenhum patch de frame rate na lista. O único
parente, `SLEEP DELAY CUSTOMIZATION` → `CustomGameLoopDelay`, intercepta o
`Sleep()` do KERNEL32 para **aumentar** o delay do loop — serve para baixar
consumo de CPU e faz o oposto.

### DirectX 7 e DirectX 9

Os dois caminhos existem de verdade no binário — estão na tabela de imports:

| | DLL | Init |
|---|---|---|
| DirectX 7 | `DDraw.dll` | `DirectDrawCreateEx` |
| DirectX 9 | `D3D9.dll` + `D3DX9_43.dll` | `Direct3DCreate9` |

O opensetup escolhe qual API o cliente inicializa. O caminho DX7 é DirectDraw,
que no Windows moderno roda emulado por cima do DWM. **Não foi identificado
qual dos dois está selecionado hoje** — as chaves visíveis (`GUIDDRIVER`,
`GUIDDEVICE`, `DEVICECNT`, `ISVOODOO`) são todas da enumeração DirectDraw e não
há chave explícita de versão. Confere-se abrindo o opensetup.

## O servidor web (e por que ele é inevitável)

O Thor busca a config remota (`main.ini`) e a lista de patches por HTTP. **Não
há como não ter servidor**: sem ele o patcher não passa da tela inicial.

O que dá para fazer, e está feito, é o `FinishOnConnectionFailure=true` no
`config.ini`: se o servidor estiver fora, o tester ainda entra no jogo. Ele
perde o aviso e o patch, não a sessão.

> `tailscale serve` **serviria uma pasta** e viveria dentro do `tailscaled`,
> sem processo extra — seria melhor. Mas serve por HTTPS no nome MagicDNS, e o
> Thor é de 2014: não dá para contar com TLS moderno nele. Se o patcher um dia
> for trocado, vale revisitar.

Ele roda como **tarefa agendada**, igual à ponte de portas:

| Tarefa | O quê |
|---|---|
| `RagnaBeat - ponte de portas` | `docs/ponte-portas.py --quieto` — 6900/6121/5121 |
| `RagnaBeat - patcher HTTP` | `patcher/servir.py --quieto` — 8099 |

A do patcher sobe no logon do `huds` **e tenta subir de novo a cada 5 minutos**,
para sempre. Parece desperdício e não é: com
`MultipleInstances = IgnoreNew`, a tentativa é descartada se o processo já
estiver de pé, e vira ressurreição se ele tiver morrido.

> **O "Reiniciar se a tarefa falhar" do Agendador não funciona para isto.** A
> primeira versão desta tarefa usava `RestartCount=3` / `RestartInterval=1min`,
> que é o caminho óbvio. Matei o processo para testar e ele **não voltou** — a
> tarefa foi para `Ready` com `LastResult=0xFFFFFFFF` e ficou lá. O gatilho
> repetido é o que realmente traz de volta. Ver a mesma ressalva em
> [../infra-docker.md](../infra-docker.md).

Conferir com:

```powershell
Get-ScheduledTask -TaskName 'RagnaBeat*' | Select-Object TaskName, State
```

Para rodar na mão (com log na tela, para depurar):

```
python patcher/servir.py
```

O log fica em `patcher/_servir.log` — é por onde se vê se um tester chegou a
falar com o servidor.

> **Não é `python -m http.server`.** Aquele atende uma conexão por vez; com
> vários testers abrindo o patcher junto, um espera o outro e o Thor estoura o
> TimeOut dele. O sintoma seria "às vezes não abre", que é o pior tipo de bug
> para depurar. O `servir.py` usa `ThreadingHTTPServer`.

A porta **8099** foi somada à regra de firewall `RagnaBeat - rAthena via
Tailscale`, que continua limitada a `100.64.0.0/10` — só a tailnet alcança,
nada fica exposto na internet. A regra cobre hoje:

```
6900, 6121, 5121, 6950-6960, 8099
```

Se um dia a porta mudar, a regra tem que mudar junto:

```powershell
# PowerShell como administrador
Set-NetFirewallRule -DisplayName 'RagnaBeat - rAthena via Tailscale' `
  -LocalPort 6900,6121,5121,6950-6960,<nova>
```

> O range 6950-6960 já está **todo ocupado** por scripts Python do host — foi
> por isso que a 8099 precisou entrar em vez de reaproveitar uma porta livre
> lá dentro. E a 8080, que é o padrão do Thor, é do VLC nesta máquina.

## O visual: do design ao Thor

A partir de 03/set/2026 o visual vem do design **"Launcher Midgard"**, feito no
Claude Design e entregue como bundle de handoff. O `gerar-visual.py` implementa
esse design; o `.dc.html` original é um protótipo HTML/CSS.

O Thor não tem nada do que o protótipo usa. Ele sabe desenhar **uma imagem de
fundo** e posicionar quatro tipos de widget por cima. A tradução é sempre a
mesma pergunta — *isto muda em tempo de execução?*

| No design | No Thor |
|---|---|
| moldura, gradiente, véu, nome, selo, redes, painéis | assado no `bg.bmp` |
| START, fechar, engrenagem, barra, status | widget (Button / ProgressBar / Label) |
| abas, banner do evento, status do mundo | `NoticeBox` — é um controle do IE, então aceita HTML de verdade |

**São dois NoticeBox**, e isso é deliberado. O painel "status do mundo" podia
ter ido assado no bitmap, mas aí ele mentiria: diria "Online" com o servidor
fora do ar, e as taxas ficariam congeladas na imagem do dia em que o bitmap foi
gerado. Sendo HTML servido por nós, muda sem cliente novo.

### O que foi cortado do design, e por quê

- **abas de idioma** (Português / Español / English): só entregamos PT-BR. Botão
  que não faz nada é pior que botão ausente.
- **botão RE/PLAY**: não há o que ele abra hoje. O Thor só sabe "abrir URL" ou
  "executar arquivo", e nenhum dos dois serve para "ver replays".
- **animações** (shine na barra, pulse no START, bob no logo): o Thor desenha
  bitmap parado. O brilho do START virou gradiente fixo.
- **o logo transbordando a moldura**: no design ele fica em (-34,-74), metade
  fora. Aqui ficou dentro, ocupando o `padding-top` de 108px que existe
  justamente para ele. O motivo é o chroma key — ver abaixo. Com o PNG do logo
  pronto dá para tentar o transbordo de novo, recortando a silhueta pelo alfa.

### As regras do Thor que mandam no desenho

1. **O fundo em BMP usa o pixel do canto superior esquerdo como cor
   transparente** (chroma key do Win32). É o que dá a moldura arredondada e
   deixa o botão de fechar sair da janela. A chave é uma magenta que não
   aparece no tema. **A máscara tem que ser dura, sem antialias**: a chave
   compara cor exata, então pixel meio-transparente vira franja magenta. Foi
   por isso que o logo não pôde flutuar fora da moldura.
2. **As coordenadas existiam em dois lugares** — as constantes do script e os
   `Left`/`Top` do `config.ini` — e era só questão de tempo até desencontrarem.
   Agora **o `config.ini` é gerado pelo `gerar-visual.py`**, das mesmas
   constantes que desenham o bitmap. Não edite o `config.ini` à mão; o endereço
   do servidor é preservado a cada geração.
3. A barra de progresso recebe `FrontImage`/`BackImage`. Sem elas o Thor desenha
   a barra padrão do Windows, branca e chapada. O `BackImage` aqui é
   **transparente** de propósito: o trilho já está pintado no `bg.bmp`.

### Escala

O design tem 1170×790 contando o que transborda a moldura. Isso **não cabe em
1366×768**, que é a resolução que o `Padrao-Video.reg` entrega ao tester. Daí a
constante `ESCALA = 0.85`, que dá **994×672**. Tudo é desenhado em coordenadas
do design e convertido na hora, então mudar a escala não exige remexer em
número nenhum.

### As fontes

O design pede **Cinzel** e **Barlow / Barlow Condensed**, que não existem no
Windows. `python patcher/baixar-fontes.py` as baixa para `patcher/fontes/` — são
Open Font License. Como o fundo é uma imagem que **nós** geramos, o tester não
precisa ter nada instalado.

Sem a pasta, o gerador cai para fontes do Windows e **avisa**: o desenho sai
diferente do design aprovado.

## O notice roda dentro do Internet Explorer

`notice.html` é renderizado pelo controle IE embutido, **não** por um navegador
moderno. Nada de flexbox, grid, `var()` ou fonte web: o `style.css` usa float e
margem de propósito. Se abrir bonito no Chrome e torto no patcher, foi por ter
esquecido disso.

## Por que o JOGAR não abria o jogo: elevação

O sintoma era "clico e não acontece nada". A causa:

| | manifesto |
|---|---|
| `MidgardEternal.exe` (Ragexe) | `requireAdministrator` |
| `Thor.exe` (o patcher) | `asInvoker` |

O Thor lança o cliente com `CreateProcess`, e **`CreateProcess` não eleva**: ela
falha com `ERROR_ELEVATION_REQUIRED` quando o alvo pede admin e o pai não tem.
Só `ShellExecute` com o verbo `runas` eleva, e o Thor não usa. O resultado é uma
falha silenciosa — e o Thor fecha a própria janela logo em seguida, então nem
resta a tela para dizer o que houve.

### Por que meus primeiros testes não pegaram isso

**A sessão em que eu testava era elevada.** O patcher lançado por ela herdava o
token de admin, o `CreateProcess` passava, e eu concluí quatro vezes que o botão
funcionava. Funcionava — só que num ambiente que o tester não tem.

Reproduzi com o patcher rodando por uma tarefa agendada com
`RunLevel Limited`: cliente não abre, patcher fecha. Igualzinho ao relato.

### A correção

Tirei a exigência de admin **do cliente**, trocando o manifesto de
`requireAdministrator` para `asInvoker`. É uma troca do mesmo tamanho em bytes —
`"requireAdministrator"` tem 22 caracteres com as aspas, e `"asInvoker"` mais 11
espaços também: espaço entre atributos é XML válido, então o recurso não muda de
tamanho e o exe continua com 14.987.776 bytes.

Testado sem elevação: **cliente abre, em 1366×768.** Nenhum UAC em lugar
nenhum — melhor do que rodar o patcher como admin, que resolveria pedindo uma
confirmação a cada abertura, para todo tester, para sempre.

> **No próximo rebuild no WARP, marque "Remove admin privilege requirement"**
> (em `Patches/Env.yml`). É exatamente este patch, e o rebuild apaga a alteração
> feita à mão. O WARP tem também "usar HKCU em vez de HKLM", pensado para o
> mesmo cenário; não foi preciso porque a resolução vem do `savedata`, não do
> registro.

## O botão JOGAR: o mecanismo

O hook em si sempre funcionou: clicando por automação, o cliente sobe e o
patcher fecha sozinho, que é o comportamento esperado. O que faltava era
elevação — ver a seção acima.

> **Hipótese que testei e descartei:** "o jogo já estava aberto e o mutex mata a
> segunda instância". Abri o cliente, abri o patcher por cima e cliquei em
> START: subiu uma **segunda** instância normalmente. Este cliente aceita
> múltiplas janelas, então mutex não explicava nada.

Duas coisas mudaram no caminho:

- `ClientParameter` ficou **vazio**. Era `-1sak1`, que não serve para nada aqui:
  o perfil do WARP aplica `No1and1Arg`, cujo propósito é justamente desligar os
  argumentos `1rag1`/`1sak1` para o cliente abrir direto.
- Um teste anterior deu falso negativo porque eu reescrevi o `config.ini` com
  `Set-Content -Encoding UTF8` do PowerShell, que grava **BOM**. O Thor não leu
  a configuração e caiu numa janela padrão de 366×115. **Nunca grave o
  `config.ini` com BOM** — o `gerar-visual.py` grava sem.

## Som ao clicar: não dá

O Thor só tem `[Config:BGM]`, música de fundo. Não existe evento de áudio por
botão — nem no `config.ini` de exemplo, nem no changelog das 6 versões.

O `NoticeBox` é IE e *poderia* tocar som, mas o START não é HTML: é um `Button`
do Thor, e o clique nele não chega ao controle do navegador. Fazer o START
virar HTML resolveria o som e quebraria o que importa, porque só o hook do Thor
sabe lançar o cliente.

O que dá para ter é **BGM**: um tema tocando enquanto o patcher está aberto,
via `[Config:BGM]`. Não está ligado.

## O IE cacheia com entusiasmo

Depois de editar o `status.html` as linhas novas não apareceram — veio a versão
anterior. Para o tester seria pior: ele ficaria vendo o aviso da semana passada
sem jeito de forçar atualização.

O `servir.py` agora manda `Cache-Control: no-store`, `Pragma: no-cache` e
`Expires: 0` em toda resposta.

## Armadilhas que já custaram tempo

| Sintoma | Causa |
|---|---|
| `Exception EBESENError ... Could not load file "main.js"` | falta `Scripts/main.js`. O erro não diz que o arquivo ficou para trás na cópia |
| Patcher trava em "CANCELAR" para sempre, sem erro | `file_url` vazio no `main.ini` remoto. Ele **não** cai para o `RootURL`: lê o main.ini, não acha para onde ir e para ali. O log do servidor mostra o `main.ini` sendo baixado e o `plist.txt` nunca |
| Barra de progresso branca gritante | faltam `FrontImage`/`BackImage` |
| Buracos transparentes no meio da janela | a cor do canto superior esquerdo do `bg.bmp` aparece no desenho |

## Config solta, não embutida

O Thor tem o `ConfigGenerator.exe`, que embute o `config.ini` dentro do
`Thor.exe`. **Não usamos.** O `config.ini` vai como arquivo solto ao lado do
executável.

O motivo é o IP: embutido, trocar o endereço significa reembutir e
redistribuir o binário; solto, é editar uma linha de texto. O custo é que dá
para ler e alterar — o que, num teste fechado, não protege nada que já não
esteja no `clientinfo.xml` logo ao lado.

## Gerar um patch .thor

Ainda não foi preciso: a 0.0.11 vai como pasta completa e o `plist.txt` está
vazio de propósito. Quando for:

1. `DEVTOOLS/Thor Patcher/Tools/ThorGenerator.exe` (é GUI) monta o `.thor`
2. o arquivo vai para `patcher/web/data/`
3. acrescente a linha em `patcher/web/plist.txt`, com um número **maior que
   todos os anteriores**

O número é a memória do patcher: ele guarda o último aplicado no `server.dat`
do jogador e só baixa o que for maior. Por isso patch publicado **não se
edita** — corrige-se com um número novo.

## Estado em 03/set/2026

Testado nesta máquina: o patcher abre, baixa `main.ini`, `plist.txt` e
`notice.html` pela tailnet, conclui e mostra JOGAR e SAIR. **Não foi testado a
partir de outra máquina da tailnet**, nem o clique em JOGAR abrindo o cliente.
São os dois primeiros itens a confirmar com o primeiro tester.
