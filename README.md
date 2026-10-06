# 🎮 Jogo da Forca - SysOps Edition

> Uma evolução moderna do clássico jogo de forca em terminal: de um script monolítico em **Bash** para uma aplicação **TUI orientada a objetos com Python e Textual**.

---

## 📑 Sumário

- [Visão Geral](#-visão-geral)
- [Evolução: Do Bash (.sh) ao Textual (Python POO)](#-evolução-do-bash-sh-ao-textual-python-poo)
- [Novas Funcionalidades e Telas](#-novas-funcionalidades-e-telas)
- [Arquitetura do Projeto](#-arquitetura-do-projeto)
- [Sistema de Pontuação e Ranking](#-sistema-de-pontuação-e-ranking)
- [Controles e Navegação por Teclado](#-controles-e-navegação-por-teclado)
- [Como Executar](#-como-executar)
- [Histórico do Projeto Original (Bash)](#-histórico-do-projeto-original-bash)

---

## 🎯 Visão Geral

O **Jogo da Forca - SysOps Edition** é um jogo de terminal interativo com estética *SysOps / Dark Terminal*, desenvolvido com foco em alta responsividade, navegação 100% via teclado físico (sem necessidade de mouse) e código modularizado seguindo princípios rígidos de POO (Programação Orientada a Objetos).

---

## 🚀 Evolução: Do Bash (`.sh`) ao Textual (Python POO)

| Característica | Versão Original (`forca.sh`) | Versão Atual (Textual POO) |
| :--- | :--- | :--- |
| **Linguagem / Stack** | Bash CLI (`echo`, `sed`, `tr`, `read`) | Python 3 + Textual Framework |
| **Arquitetura** | Monolítico procedural em arquivo único | Arquitetura POO modular (Controllers, Interfaces, Screens, Modals, Models, Services) |
| **Interface / TUI** | Saída estática via `clear` + `echo` sequencial | TUI reativa com widgets, layout CSS (`.tcss`) e redimensionamento dinâmico |
| **Layout Responsivo** | Rígido (tamanho fixo de linhas de terminal) | **Detecção de Aspect Ratio**: alterna dinamicamente entre **Horizontal** e **Vertical** respeitando a regra de **40/60** (View da Forca / Painel de Jogo) |
| **Navegação** | Apenas digitação sequencial no `read` | **100% Teclado Físico**: Setas, atalhos de acorde (`Ctrl+F`, `Ctrl+R`, `Ctrl+M`, `Ctrl+Esc`) e slot de letra dedicado |
| **Perfis de Jogador** | Inexistente (sessão volátil) | **Sistema de Jogadores**: Cadastro, seleção rápida de perfis recentes e histórico |
| **Persistência / Ranking** | Sem persistência | **Ranking Geral (Leaderboard)** persistido em JSON com pontuações, vitórias, taxa de acerto e *streaks* |
| **Normalização** | `sed` básico substituindo caracteres | Normalização Unicode NFKD completa (suporte a acentos, cedilha e maiúsculas/minúsculas) |

---

## 🖥️ Novas Funcionalidades e Telas

A aplicação conta com 4 telas principais e 2 modais contextuais sobrepostos:

### 1. 🏠 Menu Principal (`MenuScreen`)
- Logo em arte ASCII estilizada.
- Botões de navegação rápida:
  - `Iniciar Jogo [Enter]` ➡️ Abre a Seleção de Jogador.
  - `Ranking [R]` ➡️ Abre o Leaderboard Geral.
  - `Sair do Jogo [Ctrl+Esc]`.

### 2. 👤 Seleção de Jogador (`SelectPlayerScreen`)
- Identificação por apelido/tag.
- Seleção direta via lista rápida de jogadores recentes (`OptionList`).
- Criação e carregamento transparente de perfil.

### 3. 🎮 Tela de Jogo (`GameScreen`)
- **Grid Adaptativo 40/60:** A View da Forca (desenho ASCII dos 6 estágios + vidas) e o Painel de Interação se reorganizam em coluna ou linha dependendo da proporção da janela do terminal.
- **Slot de Letra Centralizado:** Exibe `Letra: _` inline, atualizando em tempo real conforme a letra física é digitada.
- **Prevenção de Colisão:** O slot é focável e isolado para que o `Enter` envie apenas a letra sem acionar botões indesejados.
- **Ações Inferiores Proporcionais:** 3 botões em texto limpo dividindo igualmente o rodapé (`Chutar [Ctrl+F]`, `Refresh [Ctrl+R]`, `Menu [Ctrl+M]`).

### 4. 🏆 Ranking Geral (`RankingScreen`)
- Tabela interativa (`DataTable`) com ordenação automática dos melhores jogadores:
  - Posição com pódio visual (🥇 1º, 🥈 2º, 🥉 3º).
  - Nome do Jogador, Pontuação Acumulada, Vitórias, Total de Partidas, Taxa de Vitória (%) e Maior Sequência de Vitórias (*Best Streak*).

### 🪟 Modais Contextuais
- **Modal de Chute (`ChuteModal`):** Permite arriscar a palavra completa digitando o termo completo (`Ctrl+F`).
- **Modal de Fim de Jogo (`GameOverModal`):** Apresenta vitória/derrota, palavra revelada, estatísticas da rodada, pontos obtidos (`+180 pts`) e ações de revanche rápida (`Replay` ou `Menu`).

---

## 🏗️ Arquitetura do Projeto

```text
forca_zipada/
├── core/                         # Núcleo de Domínio e Lógica de Negócio
│   ├── engine.py                 # Mecânica de sorteio de palavras e validação da forca
│   ├── models.py                 # Dataclasses (Categoria, GameState)
│   ├── normalizer.py             # Normalizador de strings e caracteres (NFKD)
│   ├── orientation.py            # Detector de aspect ratio para layouts dinâmicos
│   └── ranking_service.py        # Serviço de persistência JSON e cálculo de pontos
├── controllers/                  # Controladores de Navegação e Foco
│   ├── letter_buffer_controller.py  # Gerencia buffer de digitação e navegação 2-níveis
│   └── menu_controller.py        # Navegação linear em menus e modais
├── interfaces/                   # Contratos e Classes Base
│   ├── base_screen.py            # BaseGameScreen (Screen com ciclo de vida customizado)
│   ├── base_modal.py             # BaseGameModal (ModalScreen com navegação)
│   └── controller.py             # Interface IController
├── screens/                      # Telas da Aplicação com TCSS isolados
│   ├── menu/                     # Menu Principal (screen.py, menu.tcss)
│   ├── player_select/            # Seleção de Jogador (screen.py, player_select.tcss)
│   ├── game/                     # Tela Principal da Partida (screen.py, game.tcss)
│   ├── ranking/                  # Ranking / Leaderboard (screen.py, ranking.tcss)
│   └── modals/                   # Modais (chute_modal, game_over_modal)
├── styles/
│   └── global.tcss               # Variáveis de cor e design tokens globais
├── data/
│   └── ranking.json              # Persistência de perfis e pontuações
├── listas/                       # Dicionários de palavras por categoria
├── forca_app.py                  # Ponto de entrada Textual (App Orchestrator)
├── run.sh                        # Script de inicialização com auto-ativação de venv
└── forca.sh                      # Versão legada original em Shell Script
```

---

## 📊 Sistema de Pontuação e Ranking

A pontuação de cada partida é calculada dinamicamente:
* **Vitória:**
  $$\text{Pontos} = 100 \text{ (base)} + (20 \times \text{tentativas restantes}) + \min(\text{streak} \times 10, 100)$$
* **Derrota:**
  $$\text{Pontos} = 10 \text{ (participação)}, \quad \text{streak} = 0$$

Os dados ficam salvos em `data/ranking.json` e são carregados a cada inicialização.

---

## ⌨️ Controles e Navegação por Teclado

| Ação | Teclas |
| :--- | :--- |
| **Digitar Letra** | Qualquer tecla `A-Z` ou `Ç` |
| **Limpar Letra** | `Backspace` / `Delete` |
| **Enviar Letra** | `Enter` (com o slot de letra focado) |
| **Navegar Foco** | `↑` / `↓` / `←` / `→` |
| **Chutar Palavra Toda** | `Ctrl + F` |
| **Nova Palavra / Reiniciar** | `Ctrl + R` |
| **Menu Principal** | `Ctrl + M` |
| **Voltar (em telas/modais)** | `Esc` |
| **Sair da Aplicação** | `Ctrl + Esc` ou `Ctrl + Q` |

---

## 🛠️ Como Executar

### Pré-requisitos
* Python 3.10 ou superior
* Terminal com suporte a cores e UTF-8

### Execução Direta via Launcher:
```bash
chmod +x run.sh
./run.sh
```

*(O script cria e ativa o ambiente virtual `.venv`, instala as dependências do `textual` se necessário e inicia o jogo).*

---

## 📜 Histórico do Projeto Original (Bash)

<details>
<summary><b>Clique para expandir as notas do projeto acadêmico original (Sistemas Operacionais II - 2026)</b></summary>

### Descrição Original
O projeto inicial foi o desenvolvimento de um jogo CLI de forca em Bash, visando prática e aprofundamento no uso de Shell Script e terminal Linux.

**Comandos e utilitários principais utilizados no script original:**
* `$echo` e sequências ANSI de escape para formatação no terminal
* `$RANDOM` para sorteio de palavras e índices
* Laço `while` para o loop principal da sessão
* `shopt -s globstar` para indexação recursiva de arquivos de palavras em `listas/`
* `sed` e `tr` para tratamento de strings e remoção de acentuação

**Estrutura de funções no Bash:**
* `preset_jogo()`: Pré-carregamento do banco de palavras e sorteio
* `desenhar_header()`: Renderização do estado do jogo no terminal
* `gerar_progresso()`: Verificação de letras acertadas vs ocultas
* `processar_tentativa()`: Validação e contabilização da letra digitada
* `processar_chute()`: Modo *all-in* para adivinhar a palavra completa

</details>

---

Desenvolvido por **Ryan Henrique Bezerra da Silva (Ryse)**.