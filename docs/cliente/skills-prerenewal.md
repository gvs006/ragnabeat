# Descrições de skill — corrigindo para pre-renewal

Os arquivos de skill vêm do RO LATAM, que é **renewal**. Onde o comportamento diverge do
nosso servidor, a descrição mente para o jogador.

Isto **não é tradução** — é precisão de dados. A fonte da verdade é o código deste
repositório, não a wiki. A instalação dos arquivos está em [../traducao.md](../traducao.md).

---

## Já corrigidas

### Impacto Explosivo (`SM_MAGNUM`)

| | LATAM (renewal) | Corrigido (pre-renewal) |
|---|---|---|
| Dano | ATQ único, 120% → 300% | **depende da distância**: 3x3 interno `100+20×Nv`, anel 5x5 `100+10×Nv` |
| Efeito | "o dano físico do usuário é aumentado em 20%" | 20% do ataque passa a ter **propriedade Fogo** |
| Precisão | não mencionava | **+10% por nível** |
| HP | não mencionava | exige 20→16, **mas não consome** |

Fontes: [magnum.cpp:17-30](../../src/map/skills/swordman/magnum.cpp#L17) (os dois ratios e
o hit rate), [magnum.cpp:52-57](../../src/map/skills/swordman/magnum.cpp#L52)
(`SC_WATK_ELEMENT` no ramo `#else`, ou seja pre-renewal),
[skill.cpp:3538](../../src/map/skill.cpp#L3538) (`hp = 0` antes do `status_zap`).

### Angelus (`AL_ANGELUS`)

| | LATAM (renewal) | Corrigido |
|---|---|---|
| DEF | +5%×Nv | igual |
| **HP máx.** | **+50×Nv** | **não existe** |

O bônus de HP está dentro de `#ifdef RENEWAL` em
[status.cpp:3187](../../src/map/status.cpp#L3187). No pre-renewal só vale
[status.cpp:11620](../../src/map/status.cpp#L11620) (`val2 = 5*val1`) aplicado em
[status.cpp:7882](../../src/map/status.cpp#L7882), o ramo `#else`.

---

## Como corrigir outras

O `skilldescript.lub` é bytecode. O fluxo é decompilar → editar texto → gravar como texto
(o cliente aceita os dois):

```
java -jar unluac.jar <skilldescript.lub> > skilldescript.PTBR.lua
python editar-skills-prere.py      # reescreve os blocos e grava direto no data\
python ver-skill.py SM_MAGNUM      # confere, resolvendo escapes e tirando as cores
```

Dois cuidados:

- **Escapes.** O `unluac` emite não-ASCII como `\ddd` decimal em cp1252 (`\237` = í,
  `\231` = ç). O `editar-skills-prere.py` converte sozinho — escreva o texto normal.
- **Validar as chaves.** Depois de editar, `{` e `}` têm que continuar batendo. O script
  aborta se não baterem; o arquivo tem 1.427 pares e 1.426 entradas.

O original do LATAM fica em `DEVTOOLS/PTBR/_extraido/skilldescript.LATAM-original.lub`.

---

## Candidatas a revisar

O arquivo inteiro descreve renewal, então provavelmente há várias. As mais prováveis são
as que mudaram de fórmula entre as versões:

- **Bênção**, **Aumentar DEX/AGI** — os bônus escalam diferente
- **Habilidades de Mercador** — Overcharge e Discount mudaram
- **Linhas de dano dos 2ª classe** — a maioria teve ratio revisto no renewal

O jeito prático é ir corrigindo conforme aparecerem no jogo. Cada uma leva poucos minutos
pelo fluxo acima.
