-98as Operacionais II
Turma 2026 1º Semestre de Analise e Desenvolvimento de Sistemas
Ryan Henrique Bezerra da Silva

Data 09 de abril de 2026

___

O projeto proposto é o desenvolvimento de um jogo CLI de forca em bash, visando pratica e aprofundamento no uso de Shell Script e terminal linux. Os principais comandos e tecnologias utilizadas:
* $echo para output no terminal, 
* $RAMDON para escolha aleatoria de palavras
* While para o controle de sessão principal, cada rodada é feita dentro de um while
* shopt -S para o set de arquivos recursivamente

# Como foi construido
Como base eu utilizei o projeto Termonal[https://github.com/viniciuskant/termonal/tree/main], que é uma implementação do jogo de adivinhação de palavras Termo para linha de comando.
O projeto foi minha principal fonte de palavras em arquivos .txt e como pricipal estrategia eu listei um numero x de palavras por sessao aleatoriamente, isso foi definido no esboço do projeto junto do que deveria ser o frontend em um file separado, ainda sobre esse esboço eu defini que a sessao seria dentro de um while e que coisas como definir qual palavra seria escolhida e sua divisao em letras seria feita pre-carregadas.

A montagem do DB de palavras se resume em usar o `shopt -S globstar`  puxando todos os txt para uma var de arquivos e construir o db com um indice randomico de 10 palavras, depois fazer o split de uma entre as 10 definida também com `$RANDOM` para termos a palavra da vez. 

## Como foram separadas as funções
Aqui foi onde eu gastei um tempo refazendo, porque minha definição de qual parte do codigo merecia ter uma função própria foi refeita algumas vezes, por exemplo o $desenhar_header faria apenas a introdução do jogo e os updates seriam feitos por outra função que chamaria a $desenhar_hader quantas vezes fossem nescessarias. 

\$desenhar_header() é responsavel por fazer o frontend e atualizar visualmente o andamento ta partida. Aqui eu apanhei bastante porque eu não consegui passar direito os novos valores quando o jogador acertava as letras, atualizar os arrays era ok mas atualizar os underlines conforme ele acertava deu um trabalho, isso inclusive me fez refazer o gerar_progresso.

\$gerar_progresso() esta la para atualizar os arrays de letras certas e erradas conforme a comparação com o array da palavra da vez.

\processar_chute() É uma função para _All win_ onde o jogador pode gastar todos os trials e dizer qual é a palavra. Funciona dependente da dica (uma das ultimas a serem desenvolvidas) porque fazer o set de dicas para files de palavras foi volumoso e demorado, para o meu azar o dict - Dicionario CLI, só funciona bem em ingles então todas as palavras precisaram de uma linha em outro file correspondente com as dicas.

\processar_tentativa() faz a tratativa de entrada, nele tem tratamento para input apenas de letras, verificação de tentativas repetidas, letras unicas e por fim se a letra está na palavra ou não. Aqui eu apanhei para definir os retornos, durante um tempo voce só sairia do jogo se forçasse um chute, como saida eu utilizei numeros diferentes para cada estagio onde teria uma verificação e dentro do while principal defini o valor de return que deveria "quebrar" a sessão com -eq.

## Melhorias
Dicas de palavra, isso deve reutilizar a estrutura atual mas vai acrescentar o trabalho de duplicar a base atual de palavras mas relacionando cada uma ao indice da sua dica correspondente. Deve ter jeito melhor de fazer.

Rerun, eu não fiz um bom rerun, ele no maximo vai rodar tudo de novo sem evitar que a mesma sessão seja repetida logo na sequencia por exemplo.


# Perguntas de Verificação ( I'm not a robot?)

P1- O esboço foi definido com preciso de um DB de palavras partindo de um file ou do dict que eu sabia que poderia usar para me retornar uma palavra com alguns parametros. O que mudou muito foi a estrutura do codigo em sí, tinha menos funções e o set da palavra era feito dentro do while a principio.
Acho que a principal motivação foi eu ter jogado o "frontend" para outro file então eu tinha mais espaço para organizar as coisas fora do meu main e botar pra rodar no while (eu puxei o front de volta par um file só na revisão para me enquadrar na regra do file unico)

P2-  
* Busca recursiva de files em um dir com globstar e filtro pela extensão do file, todos para o array de arquivos.
* Escolha de um file com `$RANDOM` que gera apenas um int aleatório a principio, mas com o uso do modulo eu posso limitar o escopo do random para algo valido dividindo esse numero aleatorio por um valor fixo e usando o resto dessa divisão como o meu numero escolhido.

P3-
## While e if
``` Shell
while ((tentativas_restantes>0)); do
    progresso=$(gerar_progresso)
    desenhar_header "$tentativas_restantes" "$progresso" "${letras_certas[*]}" "${letras_erradas[*]}"
    read -p 'Digite uma letra: ' tentativa
    if [[ "$tentativa" == "!" ]]; then
        processar_chute
        resultado=$?
        if [[ $resultado -eq 0 ]]; then
            break
        else
            tentativas_restantes=0
            break
        fi
    else
        processar_tentativa "$tentativa"
        resultado=$?
        if [[ $resultado -eq 0 ]]; then
            letras_certas+=("$tentativa")
        elif [[ $resultado -eq 1 ]]; then
            letras_erradas+=("$tentativa")
            ((tentativas_restantes--))
        fi
    fi
    progresso=$(gerar_progresso)
    #desenhar_header "$tentativas_restantes" "$progresso" "${letras_certas[*]}" "${letras_erradas[*]}"
    if [[ ! "$progresso" =~ "_" ]]; then
        echo " Você venceu! Palavra: $palavra"
        break
    fi
done
```

Ele faz o chamado de todas as funções e o jogo mesmo rola aqui, enquanto o player tem tentativas restantes o jogo rola. Provabelmente um switch case seria mais clean mas como eu ja tinha pré-definido para os breaks um numero pequeno de saidas eu fui de if aninnhado mesmo.

tem as saidas definidas nos ifs e elifs msa no processar chute também por exemplo, onde se o input for igual a palavra (input tratado com o | tr inclusive) valida e encerra a partida.
se a função retorna a em `$?` tem um if para cada caso,  if para ! que chama o processa chute, um que derruba a sessão se for zero e outro que chama o processa tentativas e dentro dessa função direciona o acerto ou erro da letra em um array que vai para o placar. 
 
```
processar_chute() {
    read -p 'Digite a palavra completa: ' chute
    chute=$(echo "$chute" | tr '[:upper:]' '[:lower:]')
    if [[ "$chute" == "$palavra" ]]; then
        desenhar_header "$tentativas_restantes" "$palavra" "${letras_certas[*]}" "${letras_erradas[*]}"
        echo " Você acertou a palavra inteira!"
        return 0
    else
        echo " Errou o chute! Fim de jogo."
        return 1
    fi
}
```

## For
```
gerar_progresso() {
    local progresso=""
    for letra in "${palavra_split[@]}"; do
        if [[ " ${letras_certas[*]} " =~ " ${letra} " ]]; then
            progresso+="$letra "
        else
            progresso+="_ "
        fi
    done
    echo "$progresso"
}
```

aqui usei o for para atualizar o placar de letras la na header, ele faz a verificação que tem no if passar por todas as letras da palavra que dividimos.

# P5 
Definir o que interfere no placar e como atualizar ele foi trabalhoso, de primeira eu iria chamar os processadores de tentativa e direcionar um return em cada para mandar direto para o placar, mas agrupar isso em uma unica função que verifica o status da palavra com o input direto foi melhor, eu tenho uma area menor para lidar, um array a mais apenas.