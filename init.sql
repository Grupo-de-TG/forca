USE forca_db;

-- ============================================================
-- TABELA DE USUÁRIOS
-- Dados permanentes e estruturados do jogador.
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    marca_paco TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================
-- ESTATÍSTICAS CONSOLIDADAS
-- Dados utilizados pelo ranking.
-- ============================================================

CREATE TABLE IF NOT EXISTS player_stats (
    user_id INT PRIMARY KEY,
    score INT NOT NULL DEFAULT 0,
    partidas INT NOT NULL DEFAULT 0,
    vitorias INT NOT NULL DEFAULT 0,
    streak_atual INT NOT NULL DEFAULT 0,
    best_streak INT NOT NULL DEFAULT 0,
    marca_paco TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_player_stats_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX idx_stats_score
    ON player_stats(score DESC, vitorias DESC, best_streak DESC);
