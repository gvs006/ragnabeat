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
