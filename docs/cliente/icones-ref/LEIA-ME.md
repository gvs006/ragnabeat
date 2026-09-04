# Ícones de status (buff) — como criar

Os arquivos `.tga` desta pasta são **referências extraídas da nossa `data.grf`**.
Servem para abrir no Photoshop e usar de molde: tamanho, canal alfa e estilo já
estão certos.

---

## O que dá para criar

| Peça | Dificuldade | O que é |
|---|---|---|
| **Ícone de status** | fácil | O quadradinho na barra de buffs, canto superior direito. É um `.tga` de 32x32. **É este o do ROTD.** |
| Ícone de item | fácil | `.bmp` de 24x24, em `data\texture\<ui>\item\` |
| Efeito no personagem | difícil | Animação `.str` + várias texturas. Não é imagem única; é um formato próprio da Gravity com quadros, camadas e blending |
| Sprite de chapéu/visual | médio | Par `.spr` + `.act`, precisa de ferramenta própria (ActOR) |

Este documento cobre o **ícone de status**, que é o que o ROTD precisa.

---

## O formato, medido nos arquivos oficiais

Não é chute — foi lido do cabeçalho dos `.tga` da própria Gravity:

| Campo | Valor |
|---|---|
| Formato | TGA (Targa) |
| Tipo de imagem | **2** — RGB sem compressão (*não* use RLE) |
| Dimensões | **32 x 32** |
| Bits por pixel | **32** (BGRA, 8 bits de alfa) |
| Paleta | nenhuma |
| Origem | canto **inferior** esquerdo (padrão do Photoshop) |
| Tamanho final | ~4.140 bytes |

### Sobre a transparência

Os oficiais usam **dois estilos diferentes**, e os dois funcionam:

| Referência | Alfa |
|---|---|
| `swordclan.tga` | recorte duro — só 2 valores (0 e 255), 825 px transparentes |
| `kings_grace.tga` | borda suave — 138 valores distintos, **zero** px totalmente transparentes |
| `frigg_song.tga` | misto — 138 valores, 60 px transparentes |

Ou seja: o alfa gradiente é o estilo mais comum da Gravity. O ícone quase
sempre ocupa os 32x32 inteiros, com a borda desbotando em vez de recortar.

---

## Photoshop 2022 — parâmetros exatos

**Documento novo:**

| Campo | Valor |
|---|---|
| Largura x Altura | **32 x 32 pixels** |
| Resolução | 72 ppi (irrelevante para TGA, mas evita surpresa) |
| Modo de cores | **RGB, 8 bits/canal** |
| Conteúdo do fundo | **Transparente** |

> ⚠ Se o modo estiver em 16 bits/canal, a opção de 32 bits/pixel some na hora
> de exportar. `Imagem > Modo > 8 Bits/Canal`.

**Desenhe com o fundo transparente.** Não coloque camada de fundo branca — o
branco viraria pixel opaco branco, não transparência.

**Exportar:**

1. `Arquivo > Salvar uma cópia` (ou `Salvar como`)
2. Formato: **Targa**
3. Na caixa de diálogo que abre:

| Opção | Valor |
|---|---|
| Resolução | **32 bits/pixel** |
| Compactar (RLE) | **desmarcado** |

O 32 bits/pixel é o que faz o Photoshop escrever o canal alfa a partir da
transparência das camadas. Com 24 bits/pixel a transparência é jogada fora e o
ícone sai com fundo preto no jogo.

> Se a opção **32 bits/pixel** aparecer cinza: o documento não tem
> transparência. Apague a camada "Plano de fundo" (ou converta em camada comum
> com duplo clique) e tente de novo.

**Conferir depois de salvar:** o arquivo tem que ficar com **~4 KB**. Se saiu
com ~3 KB, foi salvo em 24 bits (sem alfa). Se saiu bem menor, o RLE ficou
ligado.

---

## Onde o arquivo vai

```
C:\RagnaClient\RagnaBeat.Dev\data\texture\effect\<NOME>.tga
```

A pasta `data\texture\effect\` **ainda não existe solta** — é só criar. O patch
`DataFolderFirst` está ligado, então arquivo solto ganha do que está dentro da
GRF, e nada precisa ser reempacotado.

---

## Como ligar o ícone ao status

São três tabelas, todas em
`data\luafiles514\lua files\stateicon\`. As duas primeiras já estão **soltas e
em texto** na nossa instalação, então é só editar.

| Arquivo | O que faz | Estado |
|---|---|---|
| `efstids.lub` | nome do EFST → número | solto, texto |
| `stateiconinfo.lub` | texto do balão | solto, texto |
| `stateiconimginfo.lub` | EFST → nome do `.tga` | **só na GRF, em bytecode** |

### O atalho que evita mexer no bytecode

**Não precisamos criar um EFST novo.** O ROTD hoje já usa um emprestado:

```yaml
# db/import/status.yml
- Status: Time_Accessory
  Icon: EFST_AID_PERIOD_PLUSEXP
```

Então basta **trocar a imagem que esse EFST aponta**. Como o cliente aceita
`.lub` em Lua de texto (o nosso `efstids.lub` solto é a prova), dá para gerar
uma versão em texto do `stateiconimginfo.lub` com as 397 entradas originais e a
nossa linha alterada, e soltar em `data\`.

As 397 entradas saem do bytecode atual — são pares `EFST_X` / `X.TGA` em
sequência, extraíveis por script. Não é trabalho manual.

---

## Os arquivos desta pasta

| Arquivo | Por que está aqui |
|---|---|
| `kings_grace.tga` | borda suave, dourado. **É o ícone que o VIP usa hoje** |
| `frigg_song.tga` | misto, com alguma transparência dura |
| `full_throttle.tga` | borda suave, vermelho |
| `swordclan.tga` | recorte duro — o único do conjunto |
| `unlimit.tga` | borda suave, azul |
