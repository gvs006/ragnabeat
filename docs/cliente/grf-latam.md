# A GRF do LATAM: o que ela tem que a nossa não tem

Levantado em 03/set/2026, ao investigar por que trajes com sprite existente
apareciam como `SEM SPRITE`.

Arquivo: `C:\RagnaClient\old-client-apagar-dps\data.grf` — 4,4 GB, 268.764
arquivos. A pasta se chama "apagar-dps". **Não apague.**

---

## Que GRF é essa

É do **RO LATAM / bRO**, não do kRO. O `data\clientinfo.xml` de dentro dela diz:

```xml
<servicetype>brazil</servicetype>
<taaddress>lt-account-01.gnjoylatam.com:6951</taaddress>
```

Formato GRF **v0x300** ("Event Horizon"), contra o v0x200 ("Master of Magic")
do kRO — o `grf_listar.py` já lê os dois.

## Nenhuma das duas é superconjunto da outra

Esta era a suposição errada. A comparação:

| | arquivos |
|---|---|
| em comum | 182.992 |
| só no build (kRO 2025-04-16) | 31.232 |
| **só no LATAM** | **85.772** |

O GRF do build é mais **novo** — trouxe mapas, modelos e efeitos que o LATAM
não tem (`issgard`, `heroage`, `undying`, `aurora`, `invasion`,
`20th_firework`). O do LATAM é mais **completo em traje**: sozinho ele tem
71.083 arquivos de sprite de capa, 3.084 de ícone de item e 2.929 de acessório
de cabeça que o build não tem.

Foi isso que reprovava centenas de visuais: o sprite existe, só não está
*naquele* GRF.

## O que já foi aproveitado

`docs/cliente/importar-sprites-latam.py` copia o que falta para a pasta `data/`
solta do cliente, que vence o GRF pelo patch `DataFolderFirst`.

| grupo | itens | arquivos | solto em `data/` |
|---|---|---|---|
| cabeça | 337 | 2.002 | **89 MB** ← importado na 0.0.11 |
| capa | 150 | 48.632 | 2.157 MB ← **fora**, por enquanto |

A capa custa 300× mais por item por um motivo estrutural: **o sprite de capa é
por classe**. Um traje de cabeça são 6 arquivos; uma capa são todos os jobs
vezes os dois sexos vezes as evoluções — o Escudo do Senhor dos Mortos sozinho
são 1.037 arquivos. Trazer as 150 multiplicaria o download do tester por quatro
para ganhar 150 itens.

Rodar `python docs/cliente/importar-sprites-latam.py --dry` para reavaliar.

---

## O achado grande: 273.085 strings PT-BR oficiais

A GRF do LATAM carrega a **localização brasileira oficial do Ragnarok**, em
dois arquivos que o GRF do kRO não tem:

| Onde | O quê | Linhas com PT |
|---|---|---|
| `data\msgstringtable_ml.csv` | mensagens de sistema do cliente | **4.362** |
| `data\i18n\sc\*.csv` (1.496 arquivos) | **diálogo de NPC** | **268.723** |

Formato: CSV, uma chave por linha, **cada campo em Base64**. As colunas:

| coluna | idioma |
|---|---|
| 0 | chave (ex.: `MSI_SERVER_CONNECTION_FAILED`) |
| 1 | coreano |
| 2 | inglês |
| 3–6 | vazias |
| **7** | **português** |
| 8 | vazia |
| 9 | espanhol |

Amostra, já decodificada:

```
EN: Failed to Connect to Server.
PT: Não foi possível conectar-se ao servidor.

EN: You are carrying too many items. Come back after taking off ...
PT: Você está carregando muitos itens. Volte depois de retirar ...

EN: Eden Group Jeweler
PT: Joalheiro do Grupo Eden
```

### Por que isso importa, e onde não importa

O `msgstringtable_ml.csv` é **diretamente aproveitável**: são as mesmas
mensagens de sistema que hoje traduzimos à mão em `msgstringtable.csv`, e a
coluna 7 traz a tradução oficial de 4.362 delas. Ver
[../traducao.md](../traducao.md) e [acentuacao.md](acentuacao.md) — o encoding
de saída continua sendo cp1252.

O `i18n\sc` **não** se aplica direto. Ele é o diálogo dos NPCs do cliente
LATAM, chaveado por hash do servidor deles; o nosso rAthena manda o texto do
NPC pelo pacote, vindo dos scripts em `npc/`. O valor dele é como **corpus de
referência**: 268 mil linhas de tradução oficial para consultar ao traduzir
quest, item e nome próprio, em vez de inventar terminologia. É a fonte que
resolve "como o RO oficial chamou isso em português".

Nada disso foi extraído ainda para o repo. É trabalho de um ciclo próprio.
