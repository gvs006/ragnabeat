# Builder de release do cliente

Escrito em 10/ago/2026. O `build.py` monta a pasta que vai ser entregue aos jogadores.

---

## Como rodar

Fica na raiz da pasta de desenvolvimento (hoje `C:\RagnaClient\RagnaBeat.Dev`).

```
python build.py                  proxima versao, patch +1
python build.py --minor          0.0.7 -> 0.1.0
python build.py --major          0.4.2 -> 1.0.0
python build.py --version 2.0.0  forca um valor
python build.py --dry            lista o que faria, nao escreve nada
```

Saída em `builds/<servidor>ProdV<versao>/`. Recusa sobrescrever build existente, e
**só grava o `version.txt` depois que a verificação passa** — build com problema não
consome número de versão.

| Arquivo | Papel |
|---|---|
| `config.yml` | `servidor:` (compõe o nome da pasta) e `padrao_pasta:` |
| `version.txt` | uma linha, `X.Y.Z`. O builder incrementa sozinho |
| `build.py` | o builder |

> **Nada depende do nome da pasta de desenvolvimento.** O `build.py` se localiza por
> `Path(__file__).parent`. Renomear a pasta não quebra o builder. O que *não* é
> imune ao rename está em [Ao renomear a pasta](#ao-renomear-a-pasta-de-desenvolvimento).

## O que ele faz — e o que não faz

**Faz:** seleciona arquivos, copia, cria três pastas vazias, verifica o resultado.

**Não faz** — deliberadamente, para este ciclo: não reescreve `clientinfo.xml`, não
recompila lua, não encripta GRF, não empacota em zip, não roda o `pos-warp.py`.
As opções estão em [Endurecimento futuro](#endurecimento-futuro).

O `config.yml` define o nome do servidor mas **não o aplica** ao `clientinfo.xml` —
ele só compõe o nome da pasta. Se os dois divergirem, o builder emite um **aviso**,
não um erro.

## GRFs entram por hardlink

`data.grf` (4,0 GB) e `en.grf` entram com `os.link`, não cópia. O build fica com
4,5 GB lógicos ocupando **570 MB reais**.

Não é otimização, é requisito: o disco está a 99%, com ~19 GB livres. Cópia real
permitiria 4 builds antes de encher.

> ⚠ **Hardlink compartilha o conteúdo.** Editar o `data.grf` de um build *in-place*
> altera o da pasta de desenvolvimento junto. Para GRF, que é só leitura em uso,
> isso é seguro. **Não use hardlink para o `.exe` nem para os lua** — esses o
> processo de build modifica.

Só funciona no mesmo volume NTFS. Se falhar, o builder cai para cópia real e
**avisa em voz alta** — nunca em silêncio. Ao compactar em `.zip`, o hardlink é
resolvido e o conteúdo é lido inteiro; a economia é em disco, não no zip.

## O que fica de fora, e por quê

Deny-list por padrão de nome, não lista fixa — arquivo novo de trabalho já nasce
excluído. Resultado atual: **3.043 arquivos, 570 MB** copiados dos 4,7 GB da pasta.

| Excluído | Motivo |
|---|---|
| `savedata/`, `Replay/`, `memo/` | **criadas vazias.** O `savedata/` tem a UI, os atalhos e as janelas de chat **do desenvolvedor** |
| `DEVTOOLS/` | WARP, patchers, decompiladores, exes candidatos — 602 MB. Mora dentro da pasta de desenvolvimento desde 10/ago |
| `_tmpEmblem/` | emblemas de guilda baixados na sessão do desenvolvedor |
| `BASE_*.exe` | a fonte de todo rebuild. Entregar isso é entregar o cliente sem nenhum patch |
| `*.epi`, `*.secure.txt`, `*PROFILE.yml` | artefatos do WARP — **revelam exatamente quais patches foram aplicados** |
| `*.py`, `*.bat`, `*.ps1`, `*.md` | ferramentas e documentação interna |
| `*.antes-*`, `*.TESTE-*`, `*.bak`, `*.old*` | backups; só no `SystemEN` eram 7,5 MB |
| `*.servicetype-korea` | variantes de teste do `clientinfo.xml` |
| `GameGuard/`, `GameGuard.des`, `v3hunt.dll` | anticheat desativado pelo patch `NoGGuard`. 45 MB inúteis |
| `PatchClient/`, `Patch.inf`, `patch_allow.txt`, `patch2.txt`, `RagHash.dat` | resíduos do patcher oficial kRO |
| `Ragnarok.exe`, `Setup.exe`, `unins000.*` | launcher, setup de vídeo e desinstalador do kRO. O jogador usa `RagnaBeat.exe` e `opensetup.exe` |
| `_exes_antigos/`, `RagnaBeat-*.exe`, `RagnaBeat.exe.*` | exes descartados e backups |
| `msgstringtable_EN.txt` | dump de trabalho da tradução; o cliente lê do GRF |

**Candidatos a revisão:** `Setup.exe` foi excluído por ser redundante com o
`opensetup.exe`. `RagnarokKR.ini` ficou — é config gráfica do kRO, inofensiva. Se
algum jogador reclamar de configuração de vídeo, comece por aí.

## Verificação

Roda sozinha ao fim de cada build. Um cliente entregue quebrado é pior que um build
que falha.

| Checagem | Erro ou aviso |
|---|---|
| `RagnaBeat.exe` presente, 14.987.776 bytes | erro |
| Zero constantes cp949 abertas — senão os acentos falham | erro |
| `_setmbcp` preservado em cp949 | erro |
| Zero endereços `*.ragnarok.co.kr` — senão não conecta | erro |
| `itemInfo_C.lua` com chaves balanceadas | erro |
| GRFs presentes e do mesmo tamanho da origem | erro |
| Nenhum arquivo da deny-list vazou | erro |
| `itemInfo_C.lua` com 5.296 itens | aviso |
| Itens com `resourceName` vazio (ficam sem sprite) | aviso |
| `config.yml` divergindo do `<display>` do `clientinfo.xml` | aviso |

As duas primeiras checagens do exe usam as mesmas assinaturas de byte do
[pos-warp.py](pos-warp.py) — se elas mudarem lá, mudam aqui. Ver [acentuacao.md](acentuacao.md).

## Ao renomear a pasta de desenvolvimento

O builder e o `pos-warp.py` são imunes. Estes **não** são, porque guardam caminho absoluto:

| Onde | O quê |
|---|---|
| `DEVTOOLS/WARP-2025/LastSession.yml` | campos `from:` / `to:` |
| `<pasta>/BASE_*_PROFILE.yml` | idem |
| WARP, campos Source/Target na tela | e clicar em **recarregar** |

O `DEVTOOLS/PTBR/gen_item_ptbr.py` foi tornado imune: ele sobe a partir do próprio
arquivo até achar a pasta que tem `DATA.ini` e `SystemEN/`, em vez de fixar o nome.

---

## Endurecimento futuro

O que o builder **poderia** passar a fazer para dificultar extração de conteúdo.
Nada disto está implementado.

> **A ressalva que vale para a lista inteira:** proteção do lado do cliente é
> lombada, não muro. Tudo que o cliente renderiza, ele precisa decifrar primeiro —
> e o que ele decifra, alguém extrai. A pergunta útil não é "como impedir", é
> "quanto trabalho isso dá para quem quer copiar". O que **não pode** vazar
> (dados de item, taxas de drop, preços, lógica de quest) mora no servidor, e
> nenhuma dessas medidas deve virar desculpa para mover isso para o cliente.

### Encriptar o `data.grf`

O GRF Editor (já em `DEVTOOLS/`) suporta GRF encriptado, e o cliente precisa de um
patch para ler com a chave.

- **Resolve:** abrir o GRF com ferramenta comum deixa de funcionar
- **Limite:** a chave fica embutida no exe. Quem desmonta o binário a extrai — e o
  procedimento é conhecido e publicado
- **Custo:** repackar a cada mudança de asset; um passo a mais no builder

### Compilar os lua para `.lub` e remover debug info

Hoje o `itemInfo_C.lua` vai como texto puro — 3,7 MB de tradução legível e copiável.

- **Resolve:** cópia trivial do trabalho de tradução
- **Limite:** o `unluac` (que nós mesmos usamos para extrair do LATAM) decompila
  `.lub` de volta. Sem os nomes originais, mas com toda a string legível — que é
  justamente o que se queria proteger
- **Custo:** baixo. É um passo de compilação no builder

### Absorver os overrides de `data/` para dentro do GRF

Hoje o patch `DataFolderFirst` faz a pasta `data\` vencer o GRF. É uma via de mão
dupla: nós usamos para sobrescrever, e **o jogador também pode**.

- **Resolve:** injeção de arquivo pelo jogador (sprite, lua, clientinfo alterado)
- **Limite:** só fecha a porta fácil; com GRF não encriptado, repackar é possível
- **Custo:** perde a conveniência de editar sem repackar. **Provavelmente o item de
  melhor relação custo-benefício da lista**, e o único que fecha uma porta de
  verdade em vez de só atrasar

### Manifesto de hashes + verificação

Gerar um `.json` com o hash de cada arquivo entregue, e o patcher recusar cliente
adulterado.

- **Resolve:** detecta modificação — inclusive de quem tenta injetar sprite ou lua
- **Limite:** verificação do lado do cliente é contornável por quem patcha o cliente
- **Custo:** exige um patcher. O `Thor Patcher` já está em `DEVTOOLS/`

### Empacotar o exe (Themida ou similar)

- **Resolve:** dificulta achar as constantes de codepage, os endereços redirecionados e os patches
- **Limite:** desempacotadores existem para todos os packers populares. O Ragexe
  original vinha empacotado com Themida e **foi desempacotado justamente para
  poder ser patchado** — o `Ragexe.exe.themida-original` está lá
- **Custo:** alto. Complica todo rebuild e todo diagnóstico. **Não recomendado**
  enquanto o cliente ainda estiver sendo alterado com frequência

### Distribuir por patcher em vez de pasta/zip

- **Resolve:** entrega incremental, controle de versão do lado do jogador, e o
  ponto natural para o manifesto de hashes
- **Custo:** é um projeto próprio, não um passo do builder

### Ordem sugerida, se isso virar prioridade

1. **Absorver `data/` no GRF** — fecha a porta de injeção, custo baixo
2. **Compilar os lua** — protege a tradução, custo baixo
3. **Manifesto de hashes** (junto com o patcher, quando existir)
4. **Encriptar o GRF** — só depois dos anteriores; sozinho protege pouco
5. **Empacotar o exe** — só quando o cliente estabilizar, se é que vale

Ver também [seguranca.md](../seguranca.md), que cobre o lado do servidor.
