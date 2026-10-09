"""
Script de Teste End-to-End (E2E) para o Jogo da Forca Multi-Banco.

Valida o fluxo completo de ponta a ponta:
1. Conectividade e saúde dos 3 bancos: MySQL (Auth/Stats), MongoDB (Vocab/Logs), Neo4j (Dicas de Grafo).
2. Registro e autenticação de múltiplos usuários (Alice, Bob, Charlie).
3. Simulação de partidas reais via ForcaEngine, consumindo palavras do MongoDB e dicas do Neo4j.
4. Registro de resultados, pontuações e histórico detalhado.
5. Verificação de posições e mudanças dinâmicas no ranking (ultrapassagens).
6. Validação de auditoria dos logs de partidas no MongoDB.
"""

from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import DatabaseManager
from core.auth_service import AuthService
from core.ranking_service import RankingService
from core.mongo_word_repository import MongoWordRepository
from core.neo4j_hint_repository import Neo4jHintRepository
from core.engine import ForcaEngine
from core.models import Categoria


def print_section(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)


def cleanup_test_users(db: DatabaseManager, usernames: List[str]) -> None:
    """Limpa dados de testes anteriores para garantir idempotência."""
    with db.transaction() as conn:
        for u in usernames:
            cursor = conn.execute("SELECT id FROM users WHERE username = %s;", (u,))
            row = cursor.fetchone()
            if row:
                user_id = row["id"]
                conn.execute("DELETE FROM player_stats WHERE user_id = %s;", (user_id,))
                conn.execute("DELETE FROM users WHERE id = %s;", (user_id,))
    
    # Limpa logs do Mongo
    db.mongo_db.logs_partidas.delete_many({"username": {"$in": usernames}})


def run_e2e_tests() -> bool:
    print_section("1. Inicializando Conexões Multi-Banco")
    db = DatabaseManager()
    auth_service = AuthService(db)
    ranking_service = RankingService(db)
    word_repo = MongoWordRepository()
    hint_repo = Neo4jHintRepository()

    # Validação de disponibilidade
    print(" • MySQL Conectado: OK")
    print(f" • MongoDB Conectado ({db.mongo_db.name}): OK")
    neo4j_ok = hint_repo.is_available()
    print(f" • Neo4j Conectado: {'OK' if neo4j_ok else 'FALHA'}")
    assert neo4j_ok, "Neo4j deve estar acessível para o teste E2E"

    engine = ForcaEngine(word_repo=word_repo, hint_repo=hint_repo)

    test_users = ["alice_e2e", "bob_e2e", "charlie_e2e"]
    cleanup_test_users(db, test_users)

    print_section("2. Cadastro e Autenticação de Usuários (MySQL)")
    users = {}
    for name in test_users:
        ok, msg, user = auth_service.register_user(name, "senha123")
        assert ok, f"Falha ao registrar {name}: {msg}"
        assert user is not None
        users[name] = user
        print(f" • Usuário criado com sucesso: ID={user.id} | Username='{user.username}'")

        # Valida que o player_stats foi instanciado zerado
        player = ranking_service.get_player_by_id(user.id)
        assert player is not None
        assert player.score == 0
        assert player.partidas == 0
        assert player.vitorias == 0

    print_section("3. Simulação de Partidas via Engine + Mongo + Neo4j")

    # =========================================================================
    # PARTIDA 1: Alice joga categoria 'Paises'
    # =========================================================================
    print("\n--- Partida 1: Alice (Tema: Paises) ---")
    cat_paises = next((c for c in engine.categorias if "pais" in c.id.lower()), engine.categorias[0])
    state_alice = engine.novo_jogo(cat_paises)
    print(f"Palavra sorteada para Alice: '{state_alice.palavra_original}' (Normalizada: '{state_alice.palavra_normalizada}')")
    print(f"Total de Dicas Neo4j obtidas: {len(state_alice.dicas)}")
    assert len(state_alice.dicas) > 0, "Dicas do grafo devem ter sido geradas"
    for i, d in enumerate(state_alice.dicas, 1):
        print(f"  [Dica {i}] {d}")

    # Alice adivinha as letras da palavra (vitória com 5 vidas restantes)
    # Primeiro erra uma letra propositalmente para testar erro e avanço de dica
    state_alice, fb = engine.processar_tentativa(state_alice, "z" if "z" not in state_alice.palavra_normalizada else "w")
    assert fb == "erro"
    assert state_alice.tentativas_restantes == 5

    # Agora acerta todas as letras restantes
    letras_para_acertar = sorted(list(set(c for c in state_alice.palavra_normalizada if c.isalpha())))
    for l in letras_para_acertar:
        state_alice, fb = engine.processar_tentativa(state_alice, l)
    
    assert state_alice.venceu is True
    assert state_alice.fim_de_jogo is True
    print(f"Resultado: Venceu={state_alice.venceu} | Vidas={state_alice.tentativas_restantes} | Mensagem='{state_alice.mensagem}'")

    # Registra partida da Alice
    p_alice, pts_alice = ranking_service.record_match(
        user_id=users["alice_e2e"].id,
        won=state_alice.venceu,
        category_name=state_alice.categoria_nome,
        word=state_alice.palavra_original,
        attempts_left=state_alice.tentativas_restantes
    )
    print(f"Alice acumulou +{pts_alice} pontos! Pontuação total: {p_alice.score} (Streak: {p_alice.streak_atual})")

    # =========================================================================
    # PARTIDA 2: Bob joga categoria 'Estados Br'
    # =========================================================================
    print("\n--- Partida 2: Bob (Tema: Estados Br) ---")
    cat_estados = next((c for c in engine.categorias if "estado" in c.id.lower()), engine.categorias[0])
    state_bob = engine.novo_jogo(cat_estados)
    print(f"Palavra sorteada para Bob: '{state_bob.palavra_original}'")
    for i, d in enumerate(state_bob.dicas, 1):
        print(f"  [Dica {i}] {d}")

    # Bob comete 3 erros e acerta (vitória com 3 vidas)
    erros = ["x", "y", "w"]
    for err in erros:
        if err not in state_bob.palavra_normalizada:
            state_bob, _ = engine.processar_tentativa(state_bob, err)
    
    for l in sorted(list(set(c for c in state_bob.palavra_normalizada if c.isalpha()))):
        state_bob, _ = engine.processar_tentativa(state_bob, l)

    assert state_bob.venceu is True
    p_bob, pts_bob = ranking_service.record_match(
        user_id=users["bob_e2e"].id,
        won=state_bob.venceu,
        category_name=state_bob.categoria_nome,
        word=state_bob.palavra_original,
        attempts_left=state_bob.tentativas_restantes
    )
    print(f"Bob acumulou +{pts_bob} pontos! Pontuação total: {p_bob.score} (Streak: {p_bob.streak_atual})")

    # =========================================================================
    # PARTIDA 3: Charlie joga categoria 'Municipios Br' e perde
    # =========================================================================
    print("\n--- Partida 3: Charlie (Tema: Municipios Br) ---")
    cat_mun = next((c for c in engine.categorias if "municip" in c.id.lower()), engine.categorias[0])
    state_charlie = engine.novo_jogo(cat_mun)
    print(f"Palavra sorteada para Charlie: '{state_charlie.palavra_original}'")
    
    # Charlie erra 6 letras consecutivas
    erros_charlie = ["q", "w", "x", "y", "k", "z", "j"]
    for err in erros_charlie:
        if err not in state_charlie.palavra_normalizada and not state_charlie.fim_de_jogo:
            state_charlie, _ = engine.processar_tentativa(state_charlie, err)

    assert state_charlie.venceu is False
    assert state_charlie.fim_de_jogo is True
    assert state_charlie.tentativas_restantes == 0
    print(f"Resultado: Venceu={state_charlie.venceu} | Mensagem='{state_charlie.mensagem}'")

    p_charlie, pts_charlie = ranking_service.record_match(
        user_id=users["charlie_e2e"].id,
        won=state_charlie.venceu,
        category_name=state_charlie.categoria_nome,
        word=state_charlie.palavra_original,
        attempts_left=state_charlie.tentativas_restantes
    )
    print(f"Charlie acumulou +{pts_charlie} pontos de consolação! Pontuação total: {p_charlie.score}")

    print_section("4. Verificação do Ranking Inicial (Podium 1º, 2º, 3º)")
    ranking = [p for p in ranking_service.get_all_players() if p.name in test_users]
    for pos, p in enumerate(ranking, 1):
        print(f" {pos}º Lugar: {p.name:<15} | Score: {p.score:<5} | Vitórias: {p.vitorias}/{p.partidas} | Streak: {p.streak_atual}")

    assert ranking[0].name == "alice_e2e", f"1º lugar deveria ser alice_e2e, mas foi {ranking[0].name}"
    assert ranking[1].name == "bob_e2e", f"2º lugar deveria ser bob_e2e, mas foi {ranking[1].name}"
    assert ranking[2].name == "charlie_e2e", f"3º lugar deveria ser charlie_e2e, mas foi {ranking[2].name}"
    print(" -> Classificação inicial validada com sucesso!")

    print_section("5. Simulação de Ultrapassagem no Ranking (Bob vira o jogo)")
    print("Bob joga mais 2 partidas vitoriosas com pontuação perfeita (6 vidas e streak)...")
    
    for round_num in [2, 3]:
        p_bob, pts = ranking_service.record_match(
            user_id=users["bob_e2e"].id,
            won=True,
            category_name="Paises",
            word="Brasil",
            attempts_left=6
        )
        print(f"  • Partida {round_num} do Bob: +{pts} pts (Score Atual: {p_bob.score}, Streak: {p_bob.streak_atual})")

    # Reavalia o Ranking
    novo_ranking = [p for p in ranking_service.get_all_players() if p.name in test_users]
    print("\nNovo Ranking após as vitórias consecutivas de Bob:")
    for pos, p in enumerate(novo_ranking, 1):
        print(f" {pos}º Lugar: {p.name:<15} | Score: {p.score:<5} | Vitórias: {p.vitorias}/{p.partidas} | Streak: {p.streak_atual}")

    assert novo_ranking[0].name == "bob_e2e", f"Bob deveria ter assumido o 1º lugar, mas está {novo_ranking[0].name}"
    assert novo_ranking[1].name == "alice_e2e", f"Alice deveria estar em 2º lugar, mas está {novo_ranking[1].name}"
    assert novo_ranking[2].name == "charlie_e2e", f"Charlie deveria estar em 3º lugar, mas está {novo_ranking[2].name}"
    assert novo_ranking[0].score > novo_ranking[1].score > novo_ranking[2].score
    print(" -> Ultrapassagem dinâmica no ranking validada com sucesso!")

    print_section("6. Auditoria de Logs de Partida no MongoDB")
    mongo_logs = list(db.mongo_db.logs_partidas.find({"username": {"$in": test_users}}).sort("_id", 1))
    print(f"Total de registros de partidas auditados no MongoDB: {len(mongo_logs)}")
    assert len(mongo_logs) == 5, f"Esperava 5 partidas registradas, encontrou {len(mongo_logs)}"

    for log in mongo_logs:
        print(f" • [Log Mongo] User: {log['username']:<12} | Resultado: {log['resultado']:<8} | Pontos: {log['pontos']:<4} | Palavra: {log['palavra']} ({log['categoria']})")
        assert "data_partida" in log
        assert "attempts_left" in log or "tentativas_restantes" in log

    print_section("7. Resumo Final do Teste End-to-End")
    print("  Todas as asserções passaram com sucesso!")
    print("  MySQL (Users/Stats/Ranking): OK")
    print("  MongoDB (Dicionário/Logs):    OK")
    print("  Neo4j (Knowledge Graph Dicas): OK")
    print("  Regras de Negócio & Jogo:      OK")
    print("=" * 70 + "\n")

    hint_repo.close()
    db.close()
    return True


if __name__ == "__main__":
    success = run_e2e_tests()
    if not success:
        sys.exit(1)
