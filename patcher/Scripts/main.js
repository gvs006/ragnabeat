// Script do Thor Patcher. Carregado na abertura, obrigatorio: sem este
// arquivo o patcher morre com "Could not load file main.js" antes de desenhar
// a janela - e o erro nao diz que o arquivo ficou para tras na copia.
//
// Nao temos nada a automatizar aqui. O padrao do Thor fazia require('test.js')
// para um arquivo que so tinha um alert() comentado; ficar sem o require e uma
// dependencia a menos para esquecer.
