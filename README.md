# 🎮 Jogo da Forca - SysOps Edition

> Uma evolução moderna do clássico jogo de forca em terminal: de um script monolítico em **Bash** para uma aplicação **TUI orientada a objetos com Python, Textual, Neo4j Graph Database e Delivery Multi-Container**.

---

## 📑 Sumário

- [Visão Geral](#-visão-geral)
- [Evolução: Do Bash (.sh) ao Grafo Neo4j e Multi-Container](#-evolução-do-bash-sh-ao-grafo-neo4j-e-multi-container)
- [Novas Funcionalidades e Telas](#-novas-funcionalidades-e-telas)
- [Arquitetura de Repositórios e Domínio](#-arquitetura-de-repositórios-e-domínio)
- [Grafo Geográfico no Neo4j (Taxonomia & Conexões)](#-grafo-geográfico-no-neo4j-taxonomia--conexões)
- [Delivery e Execução em Containers](#-delivery-e-execução-em-containers)
- [Sistema de Pontuação e Ranking](#-sistema-de-pontuação-e-ranking)
- [Controles e Navegação por Teclado](#-controles-e-navegação-por-teclado)
- [Histórico do Projeto Original (Bash)](#-histórico-do-projeto-original-bash)

---

## 🎯 Visão Geral

O **Jogo da Forca - SysOps Edition** é um jogo de terminal interativo com estética *SysOps / Dark Terminal*, desenvolvido com foco em alta responsividade, navegação 100% via teclado físico (sem necessidade de mouse), código modularizado (SOLID / Clean Architecture) e suporte a múltiplos backends de armazenamento (**Neo4j Graph Database**, **SQL Relacional** e **Arquivos Locais**).

---

## 🚀 Evolução: Do Bash (`.sh`) ao Grafo Neo4j e Multi-Container

| Característica | Versão Original (`forca.sh`) | Versão Atual (Textual + Neo4j + Docker) |
| :--- | :--- | :--- |
| **Linguagem / Stack** | Bash CLI (`echo`, `sed`, `tr`, `read`) | Python 3 + Textual Framework |
| **Arquitetura** | Monolítico procedural em arquivo único | Arquitetura POO modular com **Interfaces Desacopladas** (`IWordRepository`, `IPlayerRepository`, `WordRepositoryFactory`) |
| **Banco de Vocabulário** | Leitura direta de `.txt` em disco | **Neo4j Graph Database** com taxonomia hierárquica e relações semânticas (`LOCATED_IN`, `BELONGS_TO`) |
| **Persistência de Usuários** | Sem persistência | **Banco SQL Relacional** (`users`, `player_stats`, `partidas`) |
| **Layout Responsivo** | Rígido (tamanho fixo de linhas de terminal) | **Detecção de Aspect Ratio**: alterna dinamicamente entre **Horizontal** e **Vertical** respeitando a regra de **40/60** |
| **Navegação** | Apenas digitação sequencial no `read` | **100% Teclado Físico**: Setas, atalhos de acorde (`Ctrl+F`, `Ctrl+R`, `Ctrl+M`, `Ctrl+Esc`) e slot de letra dedicado `Letra: _` |
| **Delivery / Execução** | Script bash local | **Multi-Container Docker**: `./setup.sh` (com flags `--grafo` / `--arquivo`) e `./run.sh` |

---

## 🖥️ Telas e Recursos da Aplicação

1. **🏠 Menu Principal (`MenuScreen`):** Logo em arte ASCII estilizada e botões diretos: `Iniciar Jogo [Enter]`, `Ranking [R]` e `Sair [Ctrl+Esc]`.
2. **👤 Seleção de Jogador (`SelectPlayerScreen`):** Identificação por apelido/tag com histórico e seleção rápida via `OptionList`.
3. **🎮 Tela de Jogo (`GameScreen`):**
   - **Grid Adaptativo 40/60:** A View da Forca (desenho ASCII dos 6 estágios + vidas) e o Painel de Interação se reorganizam dinamicamente em linha ou coluna.
   - **Slot de Letra Centralizado:** Exibe `Letra: _` inline, atualizando em tempo real com digitação direta e sem colisão de foco com botões.
   - **Ações Inferiores Proporcionais:** 3 botões em texto limpo dividindo igualmente o rodapé (`Chutar [Ctrl+F]`, `Refresh [Ctrl+R]`, `Menu [Ctrl+M]`).
4. **🏆 Ranking Geral (`RankingScreen`):** Tabela interativa (`DataTable`) com pódio visual (🥇 1º, 🥈 2º, 🥉 3º), pontuação acumulada, vitórias, partidas, taxa de vitória e maior sequência (*Best Streak*).
5. **🪟 Modais Contextuais:** Modal de chute de palavra completa (`ChuteModal`) e tela de vitória/derrota com revanche rápida (`GameOverModal`).

---

## 🏗️ Arquitetura de Repositórios e Domínio

O motor do jogo ([`ForcaEngine`](file:///home/ryse/Documentos/forca_zipada/core/engine.py)) é **100% agnóstico e desacoplado**, comunicando-se exclusivamente através de interfaces:

```text
forca_zipada/
├── core/
│   ├── engine.py                  # Motor central de regras da forca
│   ├── models.py                  # Dataclasses de domínio (WordData, Categoria, Player, GameState)
│   ├── normalizer.py              # Normalizador Unicode NFKD
│   ├── orientation.py             # Detector de aspect ratio para layouts dinâmicos
│   ├── database.py                # DatabaseManager (SQLite / Postgres)
│   ├── ranking_service.py         # RankingService (Implementa IPlayerRepository)
│   ├── neo4j_word_repository.py   # Neo4jWordRepository (Implementa IWordRepository)
│   ├── file_word_repository.py    # FileWordRepository (Implementa IWordRepository fallback)
│   └── word_repository_factory.py # Fábrica de instanciação por ambiente (WORD_BACKEND)
├── interfaces/
│   ├── word_repository.py         # Interface IWordRepository (Vocabulário e Temas)
│   ├── player_repository.py       # Interface IPlayerRepository (Usuários e Ranking)
│   ├── base_screen.py             # BaseGameScreen (Textual Screen com ciclo de vida)
│   ├── base_modal.py              # BaseGameModal (ModalScreen)
│   └── controller.py              # Interface IController
├── screens/                       # Telas e Stylesheets isolados (TCSS)
│   ├── menu/                      # Menu Principal (screen.py, menu.tcss)
│   ├── player_select/             # Seleção de Jogador (screen.py, player_select.tcss)
│   ├── game/                      # Partida (screen.py, game.tcss)
│   ├── ranking/                   # Leaderboard (screen.py, ranking.tcss)
│   └── modals/                    # Modais (chute, game_over)
├── styles/
│   └── global.tcss                # Design system global e paleta de cores
├── scripts/
│   └── populate_graph_geography.py # Script de população do grafo no Neo4j
├── listas/                        # Dicionários de palavras por categoria
├── Dockerfile                     # Imagem Docker multi-backend otimizada
├── docker-compose.yml             # Orquestrador multi-container
├── setup.sh                       # Script de provisionamento configurável
├── run.sh                         # Launcher de execução interativa (Docker ou Local)
└── forca_app.py                   # Ponto de entrada Textual
```

---

## 🌐 Grafo Geográfico no Neo4j (Taxonomia & Conexões)

O vocabulário geográfico está estruturado em um grafo de conhecimento no **Neo4j**:

```mermaid
graph TD
    Geo["🌍 Tema: Geografia Geral"]
    Cont["🌐 Tema: Continentes"]
    Pais["🏳️ Tema: Países"]
    Est["🗺️ Tema: Estados do Brasil"]
    Mun["🏙️ Tema: Municípios Brasileiros"]

    Cont -->|"[:SUBTHEME_OF]"| Geo
    Pais -->|"[:SUBTHEME_OF]"| Geo
    Est -->|"[:SUBTHEME_OF]"| Geo
    Mun -->|"[:SUBTHEME_OF]"| Est

    W_Mun["Word: Campinas"] -->|"[:LOCATED_IN]"| W_SP["Word: São Paulo"]
    W_Mun -->|"[:BELONGS_TO]"| Mun

    W_SP -->|"[:LOCATED_IN]"| W_Brasil["Word: Brasil"]
    W_SP -->|"[:BELONGS_TO]"| Est

    W_Brasil -->|"[:LOCATED_IN]"| W_Am["Word: América"]
    W_Brasil -->|"[:BELONGS_TO]"| Pais
```

* **5.520 Nós de Palavras** indexados com normalização NFKD.
* **5.544 Relações `[:BELONGS_TO]`** vinculando palavras às suas categorias.
* **5.530 Relações `[:LOCATED_IN]`** mapeando rotas geográficas (*Município $\rightarrow$ Estado $\rightarrow$ País $\rightarrow$ Continente*).

---

## 🐳 Delivery e Execução em Containers

A aplicação roda em containers Docker interativos com suporte a cores 24-bit (TrueColor) e TTY:

### 1. Provisionamento e Configuração (`./setup.sh`)
O script de setup aceita flags para definir qual backend ativar:

```bash
# Provisiona com Neo4j Graph Database e popula o grafo (Padrão):
./setup.sh --grafo

# Provisiona para uso com arquivos locais:
./setup.sh --arquivo
```

### 2. Iniciar o Jogo (`./run.sh`)
```bash
# Executa via Docker Container:
./run.sh

# Ou executa em modo Python Local (sem Docker):
./run.sh --local
```

---

## 📊 Sistema de Pontuação e Ranking

A pontuação de cada partida é calculada dinamicamente:
* **Vitória:**
  $$\text{Pontos} = 100 \text{ (base)} + (20 \times \text{tentativas restantes}) + \min(\text{streak} \times 10, 100)$$
* **Derrota:**
  $$\text{Pontos} = 10 \text{ (participação)}, \quad \text{streak} = 0$$

---

## ⌨️ Controles e Navegação por Teclado

| Ação | Teclas |
| :--- | :--- |
| **Digitar Letra** | Qualquer tecla `A-Z` ou `Ç` |
| **Limpar Letra** | `Backspace` / `Delete` |
| **Enviar Letra** | `Enter` (com o slot de letra focado) |
| **Navegar Foco** | `↑` / `↓` / `←` / `→` |
| **Chutar Palavra Toda** | `Ctrl + F` |
| **Nova Palavra / Refresh** | `Ctrl + R` |
| **Menu Principal** | `Ctrl + M` |
| **Voltar (em telas/modais)** | `Esc` |
| **Sair da Aplicação** | `Ctrl + Esc` ou `Ctrl + Q` |

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

</details>

---

Desenvolvido por **Ryan Henrique Bezerra da Silva (Ryse)**.