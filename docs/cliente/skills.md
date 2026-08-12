# Skills em PT-BR

Instalado em 11/ago/2026, com uma correção no caminho.

---

## Os três arquivos

Vão em `data\luafiles514\lua files\skillinfoz\`, onde vencem o GRF:

| Arquivo | Origem | Tam |
|---|---|---|
| `skilldescript.lub` | LATAM, tabela `SKILL_DESCRIPT` | 871.556 |
| `skillinfolist.lub` | LATAM, tabela `SKILL_INFO_LIST` | 546.757 |
| `skillid.lub` | **o nosso**, decompilado + 3 apelidos | 48.057 |

O exe lê `Lua Files\SkillInfoz\SkillDescript`, `...\SkillInfoList` e `...\SkillID`.

## O erro que a troca ingênua causou

Instalar só os dois arquivos do LATAM quebra o cliente:

```
...\SkillInfoList.lua:3557: table index is nil
...\SkillDescript.lua:4911: table index is nil
```

**Causa:** os arquivos do LATAM indexam skills por `SKID.NOME`. Três nomes que eles usam
não existem no **nosso** `skillid.lub` (kRO 2024-10-16), então `SKID.NOME` devolve `nil`,
e `tabela[nil]` é erro em Lua.

| O LATAM usa | O nosso define | O que houve |
|---|---|---|
| `BA_FROSTJOKER` | `BA_FROSTJOKE` = 318 | digitação corrigida entre versões |
| `MH_SONIC_CLAW` | `MH_SONIC_CRAW` = 8028 | idem |
| `ALL_LIGHTHALZEN_RECALL` | — | não existe mais; o LATAM usa 3045 |

## A correção — apelidos, não substituição

Trocar o `skillid.lub` inteiro pelo do LATAM **não serve**: ele tem 1807 constantes contra
as nossas 1840, então perderíamos 36 que outros arquivos referenciam — o mesmo erro, só que
em outro lugar.

A saída é cirúrgica: manter o nosso (superconjunto) e acrescentar três linhas. O
`skillid.lub` foi decompilado com o `unluac.jar`, e o resultado — texto Lua puro,
`SKID = { NOME = id }` — recebeu no fim:

```lua
SKID.BA_FROSTJOKER          = SKID.BA_FROSTJOKE   -- 318
SKID.MH_SONIC_CLAW          = SKID.MH_SONIC_CRAW  -- 8028
SKID.ALL_LIGHTHALZEN_RECALL = 3045
```

O cliente aceita Lua em texto tão bem quanto bytecode, então não é preciso recompilar.

**Verificação automatizável:** extrair todos os tokens `[A-Z][A-Z0-9_]{2,40}` dos dois
arquivos do LATAM, cruzar com os definidos no `skillid.lub`, e a diferença tem que ser
vazia. Foi assim que os três foram achados, e é o teste a repetir se um dia trocarmos de
versão.

## Cobertura

O LATAM traz 1805 skills contra 1838 nossas. As 41 que faltam são todas de 4ª classe
(`ABC_`, `AG_`, `DK_`, `EM_`, `IG_`, `MT_`…) — **não existem num pre-renewal 99/70**, então
a perda é teórica.

## Armadilha

Existe um segundo `skilldescript.lub` em `DEVTOOLS\PTBR\latam\lua files\skillinfoz\`
(585.174 bytes). **Não use:** é bytecode **Lua 5.0** (`\x1bLuaP`), legado. O correto é o de
`latam\luafiles514\lua files\skillinfoz\` (`\x1bLuaQ`, Lua 5.1).

## Não foram tocados

`skilltreeview.lub`, `skillinfo_f.lub`, `skilldelaylist.lub` e `jobinheritlist.lub`
continuam os do GRF. Só as duas tabelas de texto e o `skillid.lub` mudaram — quanto menos
superfície, menor a chance de quebrar a árvore de skills.

---

## Corrigindo descrições para pre-renewal

Os arquivos do LATAM descrevem o **renewal**. Onde o comportamento diverge, a descrição
mente para o jogador. Duas já foram corrigidas, com a fonte da verdade sendo o código
deste repositório — não a wiki.

### Impacto Explosivo (`SM_MAGNUM`)

| | LATAM (renewal) | Corrigido (pre-renewal) |
|---|---|---|
| Dano | ATQ único, 120% → 300% | **depende da distância**: 3x3 interno `100+20×Nv`, anel 5x5 `100+10×Nv` |
| Efeito | "o dano físico do usuário é aumentado em 20%" | 20% do ataque passa a ter **propriedade Fogo** |
| Precisão | não mencionava | **+10% por nível** |
| HP | não mencionava | exige 20→16, **mas não consome** |

Fontes: [magnum.cpp:17-30](../../src/map/skills/swordman/magnum.cpp#L17) (os dois ratios e o
hit rate), [magnum.cpp:52-57](../../src/map/skills/swordman/magnum.cpp#L52) (`SC_WATK_ELEMENT`
no ramo `#else`, ou seja pre-renewal), [skill.cpp:3538](../../src/map/skill.cpp#L3538)
(`hp = 0` antes do `status_zap`).

### Angelus (`AL_ANGELUS`)

| | LATAM (renewal) | Corrigido |
|---|---|---|
| DEF | +5%×Nv | igual |
| **HP máx.** | **+50×Nv** | **não existe** |

O bônus de HP está dentro de `#ifdef RENEWAL` em
[status.cpp:3187](../../src/map/status.cpp#L3187). No pre-renewal só vale
[status.cpp:11620](../../src/map/status.cpp#L11620) (`val2 = 5*val1`) aplicado em
[status.cpp:7882](../../src/map/status.cpp#L7882), o ramo `#else`.

### Como editar outras

O `skilldescript.lub` é bytecode. O fluxo é decompilar → editar texto → gravar como texto
(o cliente aceita os dois):

```
java -jar unluac.jar <skilldescript.lub> > skilldescript.PTBR.lua
python editar-skills-prere.py      # reescreve os blocos e grava direto no data\
python ver-skill.py SM_MAGNUM      # confere, resolvendo os escapes e tirando as cores
```

Dois cuidados:

- **Escapes.** O `unluac` emite não-ASCII como `\ddd` decimal em cp1252 (`\237` = í,
  `\231` = ç). O `editar-skills-prere.py` converte sozinho — escreva o texto normal.
- **Validar as chaves.** Depois de editar, `{` e `}` têm que continuar batendo. O script
  aborta se não baterem; o arquivo tem 1.427 pares e 1.426 entradas.

O original do LATAM fica em `DEVTOOLS/PTBR/_extraido/skilldescript.LATAM-original.lub`.

---

## Ícones de estado (buffs) — e a descoberta do encoding misto

Instalados em 11/ago/2026, em `data\luafiles514\lua files\stateicon\`:
`stateiconinfo.lub` (204 KB, do LATAM) e `efstids.lub` (o nosso, decompilado, mais
15 apelidos).

Mesmo padrão das skills — os arquivos do LATAM indexam por constante `EFST_*`, e a nossa
versão (kRO 2024) não define 15 delas. Diferente das skills, **nenhuma é erro de
digitação**: são efeitos regionais (`HELM_*` das runas, `JPNONLY_*`, `OVERSEA_BUFF_*`) que
só existem na build do LATAM. Recebem o valor de lá, depois de conferir que **nenhum
colide** com efeito nosso.

> A tabela chama-se **`EFST_IDs`**, com sublinhado. Escrevi `EFSTIDs` na primeira
> tentativa e o override não teria efeito nenhum — sem erro, só silêncio.

### Os arquivos do LATAM não têm encoding uniforme

Esta é a descoberta que vale para todo o resto da tradução:

| Arquivo | Bytes de `á` / `ã` | Encoding |
|---|---|---|
| `skilldescript.lub` | `e1` | **cp1252** |
| `stateiconinfo.lub` | `c3 a3` | **UTF-8** |

Instalar o segundo como veio produziria o mesmo mojibake da curandeira. **Não assuma o
encoding — meça**, com o arquivo que você vai instalar.

Como `.lub` é bytecode com strings de tamanho prefixado, não dá para trocar os bytes no
lugar: encolher a string quebra o formato. O caminho é decompilar, converter, e gravar
como texto:

```
java -jar unluac.jar <arquivo.lub> > fonte.lua
python utf8-para-cp1252.py fonte.lua <destino.lub>
python ver-perdidos.py fonte.lua        # o que não coube em cp1252
```

Resultado aqui: **928 sequências convertidas**, e 109 mantidas — são 39 frases em
**coreano** que o próprio LATAM nunca traduziu. Sem equivalente em cp1252, e ilegíveis de
qualquer forma.

O conversor aborta se a contagem de chaves mudar.
