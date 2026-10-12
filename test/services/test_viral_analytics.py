"""Unit and Integration Tests for Viral Retention Analytics & Hook A/B Engine.

Covers:
- analyze_script_virality calculations and constraints
- Word count, character count, and 1.15x neural cadence duration
- Hook score and Pacing score algorithms
- Retention simulation milestones [0s, 15s, 30s, 45s, 60s]
- Actionable recommendations (2-4 items)
- 3 Hook A/B variations (Curiosity Gap, Shock & High Stakes, Counter-Intuitive Fact)
- Edge cases (empty, single-sentence, fluff-heavy)
- FastAPI POST /api/v1/saas/script/analyze endpoint
"""

import pytest
from fastapi.testclient import TestClient

from app.asgi import app
from app.services.viral_analytics import (
    NEURAL_CADENCE_WORDS_PER_SEC,
    analyze_script_virality,
)


@pytest.fixture
def api_client():
    return TestClient(app)


def test_neural_cadence_constant():
    """Verify that neural cadence is set to ~2.65 words/sec (1.15x speech rate)."""
    assert NEURAL_CADENCE_WORDS_PER_SEC == 2.65


def test_empty_script_handling():
    """Empty script should return safe zeroed metrics without throwing exceptions."""
    result = analyze_script_virality("", subject="Física Quântica")

    assert result["word_count"] == 0
    assert result["character_count"] == 0
    assert result["estimated_duration_seconds"] == 0.0
    assert result["cadence_words_per_second"] == 2.65
    assert result["hook_score"] == 0
    assert result["pacing_score"] == 0
    assert result["overall_score"] == 0

    # Milestones must still exist
    milestones = result["retention_simulation"]
    assert len(milestones) == 5
    seconds = [m["second"] for m in milestones]
    assert seconds == [0, 15, 30, 45, 60]

    # Recommendations must contain 2-4 items
    assert 2 <= len(result["recommendations"]) <= 4

    # Variations must contain 3 items
    assert len(result["hook_variations"]) == 3
    var_types = [v["type"] for v in result["hook_variations"]]
    assert var_types == ["Curiosity Gap", "Shock & High Stakes", "Counter-Intuitive Fact"]


def test_duration_estimation_accuracy():
    """Duration must equal word count / 2.65 rounded to 1 decimal place."""
    script = "Um dois três quatro cinco seis sete oito nove dez."  # 10 words
    result = analyze_script_virality(script, subject="Teste")

    assert result["word_count"] == 10
    expected_duration = round(10 / 2.65, 1)  # 3.8s
    assert result["estimated_duration_seconds"] == expected_duration


def test_hook_scoring_curiosity_and_power_words():
    """Scripts with high curiosity questions and power words score higher."""
    strong_script = (
        "Por que o James Webb acaba de fotografar uma anomalia bizarra e impossível no cosmos? "
        "Astrônomos registraram um mistério que desafia tudo o que sabemos. "
        "Mas a verdadeira revelação só começou agora."
    )
    result = analyze_script_virality(strong_script, subject="James Webb")

    assert result["hook_score"] >= 75
    assert result["hook_analysis"]["has_question"] is True
    assert result["hook_analysis"]["has_curiosity_gap"] is True
    assert len(result["hook_analysis"]["power_words_detected"]) >= 1


def test_fluff_opener_penalized():
    """Scripts starting with conventional greeting fluff receive score penalties."""
    fluff_script = (
        "Olá a todos, sejam bem-vindos ao meu canal! No vídeo de hoje vamos falar sobre buracos negros. "
        "Eles são objetos espaciais com muita gravidade."
    )
    strong_script = (
        "Se você caísse em um buraco negro agora, seu corpo sofreria uma espaguetificação brutal. "
        "A gravidade nos seus pés seria trilhões de vezes mais intensa do que na sua cabeça."
    )
    fluff_result = analyze_script_virality(fluff_script, subject="Buracos Negros")
    strong_result = analyze_script_virality(strong_script, subject="Buracos Negros")

    assert fluff_result["hook_score"] < strong_result["hook_score"]
    # Fluff recommendation must appear
    assert any("saudações" in rec.lower() or "olá" in rec.lower() for rec in fluff_result["recommendations"])


def test_pacing_score_variance_and_transitions():
    """Rhythmic sentence variety and transition pivots increase pacing score."""
    monotonous_script = (
        "O universo é muito grande e infinito. "
        "Existem muitas galáxias no céu escuro. "
        "Os cientistas olham com telescópios. "
        "Nós não sabemos o que tem lá."
    )
    dynamic_script = (
        "O universo é um abismo silencioso. "
        "Mas em 1997, algo mudou completamente quando hidrofones militares detectaram um som colossal. "
        "Foi bizarro. "
        "Cientistas da marinha nunca tinham registrado uma frequência orgânica tão profunda. "
        "E no entanto, o mistério permanece vivo."
    )
    monotonous_result = analyze_script_virality(monotonous_script, subject="Universo")
    dynamic_result = analyze_script_virality(dynamic_script, subject="O Som Bloop")

    assert dynamic_result["pacing_score"] > monotonous_result["pacing_score"]
    assert dynamic_result["pacing_analysis"]["sentence_variance"] > 0
    assert dynamic_result["pacing_analysis"]["transition_markers_count"] >= 2


def test_retention_simulation_structure():
    """Retention milestones must strictly contain [0s, 15s, 30s, 45s, 60s] and decreasing decay."""
    script = (
        "Se você caísse em um buraco negro de massa estelar, a gravidade nos seus pés seria brutal. "
        "Esse fenômeno esticaria seu corpo como um fio fino antes do horizonte de eventos. "
        "Mas a verdadeira distorção acontece no tempo, que desacelera até o infinito."
    )
    result = analyze_script_virality(script, subject="Buraco Negro")
    milestones = result["retention_simulation"]

    assert len(milestones) == 5
    seconds = [m["second"] for m in milestones]
    assert seconds == [0, 15, 30, 45, 60]

    rates = [m["retention_rate"] for m in milestones]
    assert rates[0] == 100.0
    # Natural retention decay holds
    assert rates[0] >= rates[1] >= rates[2] >= rates[3] >= rates[4]
    for r in rates:
        assert 0.0 <= r <= 100.0


def test_recommendations_count():
    """Recommendations list must contain between 2 and 4 actionable tips."""
    samples = [
        "Curto.",
        "Se você caísse em um buraco negro agora, seu corpo sofreria espaguetificação brutal.",
        (
            "Durante a Guerra Fria, uma rede de hidrofones captou um ruído no fundo do Pacífico Sul. "
            "Batizado de Bloop, o som viajou cinco mil quilômetros. "
            "Mas o que impressionou foi sua intensidade orgânica. "
            "Será que uma criatura colossal ainda habita o abismo inexplorado da Terra?"
        ),
    ]
    for sample in samples:
        res = analyze_script_virality(sample)
        recs = res["recommendations"]
        assert 2 <= len(recs) <= 4, f"Recommendations count out of range: {len(recs)}"
        for tip in recs:
            assert isinstance(tip, str)
            assert len(tip.strip()) > 10


def test_hook_variations_three_categories():
    """Engine must return exactly 3 variations for Curiosity Gap, Shock & High Stakes, Counter-Intuitive Fact."""
    result = analyze_script_virality("Texto qualquer de teste", subject="A Fossa das Marianas")
    variations = result["hook_variations"]

    assert len(variations) == 3
    assert variations[0]["id"] == "hook_curiosity_gap"
    assert variations[0]["type"] == "Curiosity Gap"
    assert variations[0]["type_pt"] == "Lacuna de Curiosidade"
    assert len(variations[0]["hook"]) > 10

    assert variations[1]["id"] == "hook_shock_stakes"
    assert variations[1]["type"] == "Shock & High Stakes"
    assert variations[1]["type_pt"] == "Choque & Urgência"
    assert len(variations[1]["hook"]) > 10

    assert variations[2]["id"] == "hook_counter_intuitive"
    assert variations[2]["type"] == "Counter-Intuitive Fact"
    assert variations[2]["type_pt"] == "Verdade Contraintuitiva"
    assert len(variations[2]["hook"]) > 10


def test_subject_auto_detection():
    """When subject is omitted, the engine infers a sensible subject from the script opening."""
    script = "Se você caísse em um buraco negro de massa estelar, a gravidade nos seus pés seria brutal."
    result = analyze_script_virality(script, subject="")

    # Variations should still produce valid hooks
    assert len(result["hook_variations"]) == 3
    for v in result["hook_variations"]:
        assert len(v["hook"]) > 15


def test_api_endpoint_script_analyze(api_client):
    """POST /api/v1/saas/script/analyze must return 200 with full analysis payload."""
    payload = {
        "script": "Existem centenas de bilhões de planetas na nossa galáxia. Por que o universo está em silêncio absoluto?",
        "subject": "O Paradoxo de Fermi",
    }
    response = api_client.post("/api/v1/saas/script/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    data = body["data"]

    assert "word_count" in data
    assert "character_count" in data
    assert "estimated_duration_seconds" in data
    assert "hook_score" in data
    assert "pacing_score" in data
    assert "retention_simulation" in data
    assert "recommendations" in data
    assert "hook_variations" in data

    assert len(data["retention_simulation"]) == 5
    assert 2 <= len(data["recommendations"]) <= 4
    assert len(data["hook_variations"]) == 3


def test_api_endpoint_alias_fields(api_client):
    """POST /api/v1/saas/script/analyze must support video_script and video_subject aliases."""
    payload = {
        "video_script": "O telescópio James Webb acaba de fotografar estruturas que a física dizia serem impossíveis.",
        "video_subject": "James Webb",
    }
    response = api_client.post("/api/v1/saas/script/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    data = body["data"]
    assert data["word_count"] > 0
    assert data["estimated_duration_seconds"] > 0
