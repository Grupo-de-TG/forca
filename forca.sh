#!/bin/bash

preset_jogo() {
    db_palavras=()
    tentativas=()
    tentativas_restantes=6
    letras_certas=()
    letras_erradas=()
    mensagem="Bora começar! Digite uma letra."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LISTAS_DIR="$SCRIPT_DIR/listas"

    shopt -s globstar
    arquivos=("$LISTAS_DIR"/**/*.txt)
#random para pegar o file
    indice=$(($RANDOM % ${#arquivos[@]}))
    arquivo_escolhido=${arquivos[$indice]}
# DB de palavras recebe uma palavra de 10 randomicas escolhidas de 6 ou 7 files
    db_palavras=($(shuf -n 10 "$arquivo_escolhido"))
    palavra=${db_palavras[$RANDOM % ${#db_palavras[@]}]}

    # normaliza palavra
    palavra=$(tr '[:upper:]' '[:lower:]' <<< "$palavra")

    palavra_split=($(grep -o . <<< "$palavra"))
}

## tudo front end
BOLD="\e[1m"
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
CYAN="\e[36m"
RESET="\e[0m"

desenhar_header() {
    clear
    echo -e "${CYAN}${BOLD}=========================================${RESET}"
    echo -e "         JOGO DA FORCA - SYSOPS          "
    echo -e "${CYAN}${BOLD}=========================================${RESET}"
    echo -e " Tentativas restantes: ${RED}$1${RESET} | Progresso: ${GREEN}$2${RESET}"
    echo -e " Letras certas: ${GREEN}${3:-Nenhuma}${RESET}"
    echo -e " Letras erradas: ${YELLOW}${4:-Nenhuma}${RESET}"
    echo -e " Letras erradas: ${YELLOW}${4:-Nenhuma}${RESET}"
    echo -e " STATUS: ${YELLOW}${BOLD}$mensagem${RESET}"
    echo -e "-----------------------------------------"
    echo -e "${BOLD}Digite '!' para tentar a palavra toda.${RESET}"
    echo ""
}
# uma var local para tentativa, com tratamento de entrada, apenas letras, letra unicas e letras novas.
#letra unica e nao pode repetir
processar_tentativa() {
    local tentativa="$1"
    tentativa=$(tr '[:upper:]' '[:lower:]' <<< "$tentativa")

    if [[ ${#tentativa} -ne 1 ]]; then
        mensagem= "Digite uma letra unica."
        return 2
    fi

    if [[ ! "$tentativa" =~ ^[a-z]$ ]]; then
        mensagem= "Digite apenas letras."
        return 2
    fi

    if [[ " ${tentativas[*]} " =~ " ${tentativa} " ]]; then
        mensagem= "Você ja tentou essa letra."
        return 2
    fi

    tentativas+=("$tentativa")## update no array de Tentativas
## geral ta certo? parebens então ta certo!

    for letra in "${palavra_split[@]}"; do
        if [[ "$letra" == "$tentativa" ]]; then
            mensagem= "Você acertou!"
            return 0
        fi
    done

    mensagem= "Você errou!"
    return 1
}
##mecanica do chute! Vai daqui mesmo! apenas "!" ativa isso aqui
processar_chute() {
    read -p 'Digite a palavra completa: ' chute
    chute=$(tr '[:upper:]' '[:lower:]' <<< "$chute")

    if [[ "$chute" == "$palavra" ]]; then
        desenhar_header "$tentativas_restantes" "$palavra" "${letras_certas[*]}" "${letras_erradas[*]}"
        mensagem= " Você acertou a palavra inteira!"
        return 0
    else
        mensagem= " Errou o chute! Fim de jogo."
        return 1
    fi
}
#aqui é pra atualizar o placaar,
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

#INICIALIZAÇÃO
preset_jogo

# ===== LOOP Principal =====
while true; do## esse ta aqui para garantir o rerun
    while ((tentativas_restantes > 0)); do ## esse aqui é par rodar o jogo em sí
        progresso=$(gerar_progresso)
        desenhar_header "$tentativas_restantes" "$progresso" "${letras_certas[*]}" "${letras_erradas[*]}"

        read -p 'Digite uma letra: ' tentativa

        if [[ "$tentativa" == "!" ]]; then
            processar_chute
            tentativas_restantes=0
        else
            processar_tentativa "$tentativa"
            resultado=$?

            if [[ $resultado -eq 0 ]]; then
                [[ ! " ${letras_certas[*]} " =~ " ${tentativa} " ]] && letras_certas+=("$tentativa")
            elif [[ $resultado -eq 1 ]]; then
                letras_erradas+=("$tentativa")
                ((tentativas_restantes--))
            fi
        fi

        progresso=$(gerar_progresso)

        if [[ ! "$progresso" =~ "_" ]]; then
            echo " Você venceu! Palavra: $palavra"
            tentativas_restantes=0
        fi
    done

    echo " Fim de jogo! A palavra era: $palavra"

    echo ""
    read -p "Bora jogar forca? (s/n): " bora
    bora=$(tr '[:upper:]' '[:lower:]' <<< "$bora")

    if [[ "$bora" == "s" ]]; then
        preset_jogo
        continue
    else
        echo "Valeu por jogar!"
        break
    fi
done
