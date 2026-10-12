"""Unit and Integration Tests for Monetization Funnel & Pinned Comment Engine.

Covers:
- generate_monetization_pack generation and dictionary keys
- ManyChat pinned comment DM trigger copy and trigger word extraction
- YouTube Shorts / TikTok to Longform conversion bridge
- CONAR (Brazil) and FTC (USA) affiliate disclosure compliance
- Lead magnet hook overlays and verbal callout scripts at second 50
- Multi-tier RPM revenue calculations (Tier 1 vs Brazil/Tier 3 at 100k, 500k, 1M views)
- Custom lead magnet and niche topic auto-detection
- FastAPI POST /api/v1/saas/monetization/funnel endpoint
- Seamless integration into generate_viral_metadata
"""

import pytest
from fastapi.testclient import TestClient

from app.asgi import app
from app.services.monetization_funnel import (
    calculate_projected_earnings,
    extract_trigger_word,
    generate_monetization_pack,
    get_affiliate_disclosures,
    get_affiliate_recommendations,
)
from app.controllers.v1.saas import generate_viral_metadata


@pytest.fixture
def api_client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests: Core Monetization Generator
# ---------------------------------------------------------------------------

def test_generate_monetization_pack_keys():
    """Pack must contain all required monetization funnel keys."""
    pack = generate_monetization_pack(
        subject="O Mistério do Bloop",
        script="Um som subaquático misterioso detectado no Pacífico...",
        lead_magnet="Dossiê Secreto das Profundezas em PDF",
        affiliate_category="livros_educacao",
    )

    required_keys = [
        "pinned_comment_dm_trigger",
        "pinned_comment_longform_bridge",
        "affiliate_disclosures",
        "lead_magnet_callouts",
        "estimated_earnings",
        "revenue_estimator",
        "trigger_word",
        "lead_magnet",
        "affiliate_category",
        "affiliate_recommendations",
        "clipboard_comment",
    ]
    for key in required_keys:
        assert key in pack, f"Missing key {key} in monetization pack"

    # revenue_estimator must match estimated_earnings
    assert pack["revenue_estimator"] == pack["estimated_earnings"]


def test_pinned_comment_dm_trigger_manychat():
    """DM trigger comment must contain trigger word, direct call to action, and emoji."""
    pack = generate_monetization_pack(
        subject="O que acontece se você cair em um buraco negro?",
        lead_magnet="Dossiê da Singularidade em PDF",
    )
    dm_trigger = pack["pinned_comment_dm_trigger"]

    assert "DOSSIE" in dm_trigger
    assert "direct" in dm_trigger.lower() or "link" in dm_trigger.lower()
    assert pack["trigger_word"] == "DOSSIE"


def test_trigger_word_extraction():
    """Extracts trigger words from explicit lead magnet titles."""
    assert extract_trigger_word(lead_magnet="Planilha de Gastos Mensais") == "PLANILHA"
    assert extract_trigger_word(lead_magnet="Guia Definitivo do Cosmos") == "GUIA"
    assert extract_trigger_word(lead_magnet="Ebook Secreto de Astrofísica") == "EBOOK"
    assert extract_trigger_word(lead_magnet="Mega Pack de Prompts IA") == "PACK"
    assert extract_trigger_word(lead_magnet="Acesse a Aula Completa") == "AULA"

    # Niche fallback
    assert extract_trigger_word(lead_magnet="", subject="Buraco Negro no Espaço") == "COSMOS"
    assert extract_trigger_word(lead_magnet="", subject="Fossa das Marianas e o Bloop") == "ABISMO"
    assert extract_trigger_word(lead_magnet="", subject="Como ganhar dinheiro e investir") == "LUCRO"


def test_pinned_comment_longform_bridge():
    """Longform bridge must encourage Shorts viewers to watch 20min longform video."""
    pack = generate_monetization_pack(subject="Buraco Negro")
    bridge = pack["pinned_comment_longform_bridge"]

    assert "20min" in bridge or "completa" in bridge.lower()
    assert "link fixado" in bridge.lower()
    assert "[LINK DO VÍDEO COMPLETO" in bridge


def test_affiliate_disclosures_compliance():
    """Affiliate disclosures must include both CONAR (Brazil) and FTC (USA) notices."""
    disclosures = get_affiliate_disclosures()

    assert "conar_br" in disclosures
    assert "ftc_us" in disclosures
    assert "full_text" in disclosures

    # CONAR transparency
    assert "CONAR" in disclosures["conar_br"]
    assert "afiliado" in disclosures["conar_br"].lower()
    assert "sem nenhum custo adicional" in disclosures["conar_br"].lower()

    # FTC transparency
    assert "FTC" in disclosures["ftc_us"]
    assert "commission" in disclosures["ftc_us"].lower()


def test_lead_magnet_callouts_50s():
    """Callouts must contain 50-second verbal script and visual hook banner."""
    pack = generate_monetization_pack(
        subject="Inteligência Artificial",
        lead_magnet="Prompt Pack de IA",
    )
    callouts = pack["lead_magnet_callouts"]

    assert callouts["second"] == 50
    assert "verbal_script_50s" in callouts
    assert "visual_overlay_text" in callouts
    assert "comentário fixado" in callouts["verbal_script_50s"].lower()
    assert "COMENTÁRIO FIXADO" in callouts["visual_overlay_text"]


def test_projected_rpm_revenue_calculations():
    """Verifies math for Tier 1 and Brazil/Tier 3 RPM projections at 100k, 500k, 1M views."""
    # Tier 1 arbitrary calculation
    t1_100k = calculate_projected_earnings(100_000, "tier_1")
    assert t1_100k["min_usd"] == 15.00
    assert t1_100k["max_usd"] == 35.00

    t1_1m = calculate_projected_earnings(1_000_000, "tier_1")
    assert t1_1m["min_usd"] == 150.00
    assert t1_1m["max_usd"] == 350.00

    # Brazil / Tier 3 calculation
    br_100k = calculate_projected_earnings(100_000, "brazil_tier_3")
    assert br_100k["min_usd"] == 3.00
    assert br_100k["max_usd"] == 7.00
    assert br_100k["min_brl"] >= 15.00

    # Full table in monetization pack
    pack = generate_monetization_pack(subject="Astrofísica")
    rev = pack["revenue_estimator"]

    assert "tier_1" in rev
    assert "brazil_tier_3" in rev
    assert "longform_bridge_extra" in rev
    assert "lead_capture_potential" in rev

    assert rev["tier_1"]["projections"]["100k"]["min_usd"] == 15.00
    assert rev["tier_1"]["projections"]["500k"]["min_usd"] == 75.00
    assert rev["tier_1"]["projections"]["1m"]["min_usd"] == 150.00

    assert rev["brazil_tier_3"]["projections"]["100k"]["min_usd"] == 3.00
    assert rev["brazil_tier_3"]["projections"]["500k"]["min_usd"] == 15.00
    assert rev["brazil_tier_3"]["projections"]["1m"]["min_usd"] == 30.00


def test_affiliate_recommendations_catalog():
    """Curated recommendations must match category or fallback sensibly."""
    books = get_affiliate_recommendations("livros_educacao")
    assert len(books) > 0
    assert any("Livro" in b["name"] or "Kindle" in b["name"] for b in books)

    saas = get_affiliate_recommendations("softwares_ia")
    assert len(saas) > 0
    assert any("ElevenLabs" in s["name"] or "VPN" in s["name"] for s in saas)

    finance = get_affiliate_recommendations("financas_investimentos")
    assert len(finance) > 0
    assert any("Ledger" in f["name"] or "Psicologia Financeira" in f["name"] for f in finance)


def test_empty_and_graceful_inference():
    """Engine must infer valid lead magnets and triggers without errors for empty inputs."""
    pack = generate_monetization_pack("", script="")
    assert pack["trigger_word"] == "DOSSIE"
    assert len(pack["pinned_comment_dm_trigger"]) > 10
    assert len(pack["pinned_comment_longform_bridge"]) > 10
    assert len(pack["clipboard_comment"]) > 20


# ---------------------------------------------------------------------------
# Integration Tests: Controller & Metadata Engine
# ---------------------------------------------------------------------------

def test_api_endpoint_monetization_funnel(api_client):
    """POST /api/v1/saas/monetization/funnel must return 200 with full monetization pack."""
    payload = {
        "subject": "O Paradoxo de Fermi",
        "script": "Onde estão todas as civilizações alienígenas?",
        "lead_magnet": "Dossiê Fermi em PDF",
        "affiliate_category": "livros_educacao",
    }
    response = api_client.post("/api/v1/saas/monetization/funnel", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    data = body["data"]

    assert "pinned_comment_dm_trigger" in data
    assert "pinned_comment_longform_bridge" in data
    assert "affiliate_disclosures" in data
    assert "lead_magnet_callouts" in data
    assert "estimated_earnings" in data
    assert "revenue_estimator" in data
    assert data["trigger_word"] == "DOSSIE"


def test_api_endpoint_root_alias_and_field_aliases(api_client):
    """Direct /saas/monetization/funnel root alias and parameter aliases must be accepted."""
    payload = {
        "video_subject": "O Telescópio James Webb",
        "video_script": "Galáxias que desafiam a física moderna.",
        "lead_magnet_topic": "Guia Ilustrado James Webb",
    }
    # Direct alias
    response = api_client.post("/saas/monetization/funnel", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    data = body["data"]

    assert data["trigger_word"] == "GUIA"
    assert "GUIA" in data["pinned_comment_dm_trigger"]


def test_generate_viral_metadata_includes_monetization():
    """generate_viral_metadata must automatically integrate pinned comments and disclosures."""
    meta = generate_viral_metadata(
        subject="O Mecanismo de Anticítera",
        script="Em 1901, mergulhadores gregos acharam uma máquina de mais de dois mil anos...",
    )

    assert "monetization" in meta
    assert "pinned_comment" in meta
    assert "pinned_comment_dm_trigger" in meta
    assert "pinned_comment_longform_bridge" in meta
    assert "affiliate_disclosures" in meta
    assert "estimated_earnings" in meta

    # Clipboard text must contain the pinned comment and CONAR disclosure
    assert "COMENTARIO FIXADO" in meta["clipboard_text"]
    assert "DIVULGACAO DE AFILIADOS" in meta["clipboard_text"]
    assert "CONAR" in meta["description"]
