#!/bin/bash

preset_jogo() {
    db_palavras=()
    tentativas=()
    tentativas_restantes=6
    letras_certas=()
    letras_erradas=()
    mensagem="Bora começar! Digite uma letra."
    venceu=0

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LISTAS_DIR="$SCRIPT_DIR/listas"

    shopt -s globstar nullglob
    arquivos=("$LISTAS_DIR"/**/*.txt)

    if [[ ${#arquivos[@]} -eq 0 ]]; then
        echo "Erro: Nenhuma lista de palavras encontrada em $LISTAS_DIR"
        exit 1
    fi

    # Random para pegar o arquivo
    indice=$(($RANDOM % ${#arquivos[@]}))
    arquivo_escolhido=${arquivos[$indice]}

    # DB de palavras recebe 10 palavras aleatórias do arquivo
    mapfile -t db_palavras < <(shuf -n 10 "$arquivo_escolhido")
    palavra=${db_palavras[$RANDOM % ${#db_palavras[@]}]}

    # normaliza palavra (minúsculas, remove acentos e caracteres especiais)
    palavra=$(sed 'y/áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ/aaaaeeiooouucAAAAEEIOOOUUC/' <<< "$palavra" | tr '[:upper:]' '[:lower:]' | tr -d '\r')

    # split da palavra em caracteres
    palavra_split=()
    for (( i=0; i<${#palavra}; i++ )); do
        palavra_split+=("${palavra:$i:1}")
    done
}

## Cores e Estilos
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
    echo -e " STATUS: ${YELLOW}${BOLD}$mensagem${RESET}"
    echo -e "-----------------------------------------"
    echo -e "${BOLD}Digite '!' para tentar a palavra toda.${RESET}"
    echo ""
}

processar_tentativa() {
    local tentativa="$1"
    tentativa=$(sed 'y/áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ/aaaaeeiooouucAAAAEEIOOOUUC/' <<< "$tentativa" | tr '[:upper:]' '[:lower:]' | tr -d '\r')

    if [[ ${#tentativa} -ne 1 ]]; then
        mensagem="Digite uma letra única."
        return 2
    fi

    if [[ ! "$tentativa" =~ ^[a-z]$ ]]; then
        mensagem="Digite apenas letras."
        return 2
    fi

    if [[ " ${tentativas[*]} " =~ " ${tentativa} " ]]; then
        mensagem="Você já tentou a letra '$tentativa'."
        return 2
    fi

    tentativas+=("$tentativa")

    for letra in "${palavra_split[@]}"; do
        if [[ "$letra" == "$tentativa" ]]; then
            mensagem="Boa! Você acertou a letra '$tentativa'."
            return 0
        fi
    done

    mensagem="Ops! A letra '$tentativa' não está na palavra."
    return 1
}

processar_chute() {
    read -p 'Digite a palavra completa: ' chute
    chute=$(sed 'y/áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ/aaaaeeiooouucAAAAEEIOOOUUC/' <<< "$chute" | tr '[:upper:]' '[:lower:]' | tr -d '\r')

    if [[ "$chute" == "$palavra" ]]; then
        desenhar_header "$tentativas_restantes" "$palavra" "${letras_certas[*]}" "${letras_erradas[*]}"
        echo -e "${GREEN}${BOLD}🎯 Você acertou a palavra inteira! ($palavra)${RESET}"
        return 0
    else
        echo -e "${RED}${BOLD}❌ Errou o chute! ($chute)${RESET}"
        return 1
    fi
}

gerar_progresso() {
    local progresso=""
    for letra in "${palavra_split[@]}"; do
        if [[ "$letra" == " " ]]; then
            progresso+="  "
        elif [[ "$letra" == "-" ]]; then
            progresso+="- "
        elif [[ " ${letras_certas[*]} " =~ " ${letra} " ]]; then
            progresso+="$letra "
        else
            progresso+="_ "
        fi
    done
    echo "$progresso"
}

# INICIALIZAÇÃO
preset_jogo

# ===== LOOP Principal =====
while true; do
    venceu=0
    while ((tentativas_restantes > 0)); do
        progresso=$(gerar_progresso)
        desenhar_header "$tentativas_restantes" "$progresso" "${letras_certas[*]}" "${letras_erradas[*]}"

        read -p 'Digite uma letra: ' tentativa

        if [[ "$tentativa" == "!" ]]; then
            if processar_chute; then
                venceu=1
            fi
            tentativas_restantes=0
            break
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
            desenhar_header "$tentativas_restantes" "$progresso" "${letras_certas[*]}" "${letras_erradas[*]}"
            echo -e "${GREEN}${BOLD}🎉 Você venceu! Palavra: $palavra${RESET}"
            tentativas_restantes=0
            venceu=1
            break
        fi
    done

    if [[ $venceu -ne 1 ]]; then
        desenhar_header "$tentativas_restantes" "$progresso" "${letras_certas[*]}" "${letras_erradas[*]}"
        echo -e "${RED}${BOLD}💀 Fim de jogo! A palavra era: $palavra${RESET}"
    fi

    echo ""
    read -p "Bora jogar forca novamente? (s/n): " bora
    bora=$(tr '[:upper:]' '[:lower:]' <<< "$bora")

    if [[ "$bora" == "s" ]]; then
        preset_jogo
        continue
    else
        echo -e "${CYAN}Valeu por jogar!${RESET}"
        break
    fi
done
