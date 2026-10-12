"""Unit and Integration Tests for Incompetech Royalty-Free BGM Service and API.

Covers:
- Attribution generator (get_cc_attribution and get_attribution)
- Bundled curated fallback library (~22 iconic Kevin MacLeod tracks)
- Manifest loading, disk caching in storage/cache/incompetech_pieces.json, and network resilience
- Multi-criteria filtering (feel, genre, min_bpm, max_bpm, query, limit)
- Track downloading with streaming, safe naming, cache reuse, retries, and errors
- FastAPI endpoint GET /api/v1/saas/bgm/incompetech
- Attribution integration in generate_viral_metadata and POST /api/v1/saas/metadata
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi.testclient import TestClient

from app.asgi import app
from app.controllers.v1.saas import generate_viral_metadata
from app.services import incompetech_bgm


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Overrides storage_dir to use a temporary directory for isolation."""
    cache_path = tmp_path / "cache"
    cache_path.mkdir(parents=True, exist_ok=True)
    # Pre-populate disk cache with fallback tracks so search tests don't hit live internet
    default_cache = cache_path / incompetech_bgm.CACHE_FILENAME
    with open(default_cache, "w", encoding="utf-8") as f:
        json.dump(incompetech_bgm.TOP_TRACKS_FALLBACK, f, ensure_ascii=False)

    with patch("app.utils.utils.storage_dir", return_value=str(cache_path)):
        # Reset memory cache before and after test
        incompetech_bgm._MANIFEST_MEMORY_CACHE = None
        yield cache_path
        incompetech_bgm._MANIFEST_MEMORY_CACHE = None


# =========================================================================
# 1. Attribution Tests
# =========================================================================

def test_get_cc_attribution_formatting():
    """Verify standard CC-BY 4.0 attribution output."""
    credit = incompetech_bgm.get_cc_attribution("Sneaky Snitch")

    assert '"Sneaky Snitch"' in credit
    assert "Kevin MacLeod" in credit
    assert "(incompetech.com)" in credit
    assert "Licensed under Creative Commons: By Attribution 4.0 License" in credit
    assert "http://creativecommons.org/licenses/by/4.0/" in credit


def test_get_cc_attribution_strips_mp3_extension():
    """Verify that .mp3 extension in title is cleanly stripped."""
    credit = incompetech_bgm.get_cc_attribution("Carefree.mp3")
    assert '"Carefree"' in credit
    assert ".mp3" not in credit


def test_get_cc_attribution_custom_artist_and_alias():
    """Verify alias get_attribution and custom artist parameter."""
    credit = incompetech_bgm.get_attribution("Cipher", artist="Kevin MacLeod & Collaborator")
    assert '"Cipher"' in credit
    assert "Kevin MacLeod & Collaborator" in credit


# =========================================================================
# 2. Bundled Curated Fallback Library Tests
# =========================================================================

def test_bundled_fallback_catalog_completeness():
    """Verify curated fallback contains at least 20 iconic Kevin MacLeod tracks with valid fields."""
    fallback = incompetech_bgm.TOP_TRACKS_FALLBACK
    assert len(fallback) >= 20

    titles = [t["title"] for t in fallback]
    required_tracks = [
        "Sneaky Snitch",
        "Cipher",
        "Carefree",
        "The Complex",
        "Darkest Child",
        "Heartbreaking",
        "Monkeys Spinning Monkeys",
        "Scheming Weasel",
        "Volatile Reaction",
        "Pop Goes the Weasel",
    ]
    for required in required_tracks:
        assert required in titles, f"Expected '{required}' in fallback catalog"

    for track in fallback:
        assert track["id"]
        assert track["title"]
        assert track["filename"].endswith(".mp3")
        assert isinstance(track["bpm"], (int, float))
        assert track["genre"]
        assert track["feel"]
        assert track["length"]


def test_normalize_track():
    """Verify normalization handles diverse formats and missing attributes."""
    raw = {
        "uuid": "custom-uuid-123",
        "title": "A Great Piece",
        "filename": "great.mp3",
        "bpm": "128",
        "genre": "Soundtrack",
        "mood": "Epic",
        "length": "03:12",
    }
    normalized = incompetech_bgm.normalize_track(raw)

    assert normalized["id"] == "custom-uuid-123"
    assert normalized["title"] == "A Great Piece"
    assert normalized["filename"] == "great.mp3"
    assert normalized["bpm"] == 128
    assert normalized["feel"] == "Epic"
    assert normalized["genre"] == "Soundtrack"
    assert normalized["download_url"] == "https://incompetech.com/music/royalty-free/mp3-royaltyfree/great.mp3"


# =========================================================================
# 3. Manifest Loading & Cache Tests
# =========================================================================

def test_load_manifest_fallback_when_network_fails(temp_cache_dir):
    """When network fails and no cache exists, must fall back to bundled library and cache it."""
    cache_file = os.path.join(temp_cache_dir, incompetech_bgm.CACHE_FILENAME)
    if os.path.exists(cache_file):
        os.remove(cache_file)
    with patch("requests.get", side_effect=requests.RequestException("Connection refused")):
        tracks = incompetech_bgm.load_manifest(force_refresh=True)

        assert len(tracks) >= 20
        assert any(t["title"] == "Sneaky Snitch" for t in tracks)

        assert os.path.exists(cache_file)


def test_load_manifest_reads_existing_disk_cache(temp_cache_dir):
    """When disk cache exists and force_refresh is False, load without network request."""
    cache_file = os.path.join(temp_cache_dir, incompetech_bgm.CACHE_FILENAME)
    custom_cached = [
        {
            "id": "cached-one",
            "title": "Cached Track",
            "filename": "cached.mp3",
            "bpm": 110,
            "genre": "Ambient",
            "feel": "Peaceful",
            "length": "02:00",
        }
    ]
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(custom_cached, f)

    with patch("requests.get") as mock_get:
        tracks = incompetech_bgm.load_manifest(force_refresh=False)
        mock_get.assert_not_called()
        assert len(tracks) == 1
        assert tracks[0]["title"] == "Cached Track"


def test_load_manifest_from_remote_success(temp_cache_dir):
    """When remote fetch succeeds, parse tracks and update disk cache."""
    remote_data = [
        {
            "uuid": "remote-1",
            "title": "Remote Harmony",
            "filename": "harmony.mp3",
            "bpm": 95,
            "genre": "Acoustic",
            "feel": "Warm",
            "length": "01:45",
        }
    ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = remote_data

    with patch("requests.get", return_value=mock_resp):
        tracks = incompetech_bgm.load_manifest(force_refresh=True)
        assert len(tracks) == 1
        assert tracks[0]["id"] == "remote-1"
        assert tracks[0]["title"] == "Remote Harmony"
        assert tracks[0]["download_url"] == "https://incompetech.com/music/royalty-free/mp3-royaltyfree/harmony.mp3"

        cache_file = os.path.join(temp_cache_dir, incompetech_bgm.CACHE_FILENAME)
        assert os.path.exists(cache_file)


# =========================================================================
# 4. Search & Filtering Tests
# =========================================================================

def test_search_tracks_by_genre(temp_cache_dir):
    """Filter tracks by genre."""
    humorous = incompetech_bgm.search_incompetech_tracks(genre="Humorous")
    assert len(humorous) > 0
    for t in humorous:
        assert "humorous" in t["genre"].lower() or "humorous" in t["feel"].lower()


def test_search_tracks_by_feel(temp_cache_dir):
    """Filter tracks by feel / mood."""
    dark_tracks = incompetech_bgm.search_incompetech_tracks(feel="Dark")
    assert len(dark_tracks) > 0
    for t in dark_tracks:
        assert "dark" in t["feel"].lower()

    darkest = incompetech_bgm.search_incompetech_tracks(feel="Dark", query="Darkest Child")
    assert len(darkest) > 0
    assert any("Darkest Child" in t["title"] for t in darkest)


def test_search_tracks_by_bpm_range(temp_cache_dir):
    """Filter tracks by min_bpm and max_bpm."""
    filtered = incompetech_bgm.search_incompetech_tracks(min_bpm=120, max_bpm=135)
    assert len(filtered) > 0
    for t in filtered:
        assert t["bpm"] is not None
        assert 120 <= t["bpm"] <= 135


def test_search_tracks_by_query_and_limit(temp_cache_dir):
    """Search tracks by keyword with limit constraint."""
    monkeys = incompetech_bgm.search_tracks(query="Monkeys", limit=1)
    assert len(monkeys) == 1
    assert "Monkeys" in monkeys[0]["title"]


# =========================================================================
# 5. Download Tests
# =========================================================================

def test_download_track_success(tmp_path):
    """Verify safe track download and local storage."""
    dest_dir = tmp_path / "bgm"
    fake_mp3_content = b"ID3\x03\x00\x00\x00\x00\x00#FAKE_MP3_STREAM"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [fake_mp3_content]

    with patch("requests.get", return_value=mock_resp):
        saved_path = incompetech_bgm.download_incompetech_track("Sneaky Snitch.mp3", dest_dir=str(dest_dir))

        assert os.path.exists(saved_path)
        assert os.path.basename(saved_path) == "Sneaky Snitch.mp3"
        with open(saved_path, "rb") as f:
            assert f.read() == fake_mp3_content

        # Second download must use existing file without network request
        with patch("requests.get") as mock_get:
            cached_path = incompetech_bgm.download_track("Sneaky Snitch.mp3", destination_dir=str(dest_dir))
            mock_get.assert_not_called()
            assert cached_path == saved_path


def test_download_track_unsafe_filename():
    """Verify directory traversal is strictly blocked."""
    with pytest.raises(ValueError):
        incompetech_bgm.download_incompetech_track("../../unsafe.mp3")


def test_download_track_retry_and_failure(tmp_path):
    """Verify download retries on network error and raises RuntimeError on persistent failure."""
    dest_dir = tmp_path / "bgm"
    with patch("requests.get", side_effect=requests.RequestException("Timeout")):
        with patch("time.sleep"):  # Avoid real backoff delays
            with pytest.raises(RuntimeError):
                incompetech_bgm.download_incompetech_track("Carefree.mp3", dest_dir=str(dest_dir))


# =========================================================================
# 6. Controller & API Integration Tests
# =========================================================================

def test_api_get_incompetech_bgm(api_client, temp_cache_dir):
    """Verify GET /api/v1/saas/bgm/incompetech returns 200 and list of tracks."""
    res = api_client.get("/api/v1/saas/bgm/incompetech?feel=Bouncy&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    tracks = data["data"]
    assert isinstance(tracks, list)
    assert len(tracks) > 0
    assert len(tracks) <= 5

    first = tracks[0]
    assert "id" in first
    assert "title" in first
    assert "download_url" in first
    assert "bpm" in first


def test_generate_viral_metadata_with_incompetech_attribution():
    """Verify seamless appending of CC-BY attribution to viral metadata description."""
    meta = generate_viral_metadata(
        subject="Mistérios do Oceano",
        script="Nas profundezas mais escuras do oceano...",
        bgm_track="Sneaky Snitch",
    )

    assert "attribution" in meta
    assert '"Sneaky Snitch"' in meta["attribution"]
    assert "Kevin MacLeod" in meta["attribution"]
    assert "incompetech.com" in meta["attribution"]

    # Attribution should be present in both description and clipboard text
    assert meta["attribution"] in meta["description"]
    assert meta["attribution"] in meta["clipboard_text"]


def test_api_post_viral_metadata_with_bgm_track(api_client):
    """Verify POST /api/v1/saas/metadata appends attribution when bgm_track is specified."""
    payload = {
        "video_subject": "A Gravidade Quântica",
        "video_script": "A gravidade na escala quântica se comporta de forma inesperada.",
        "bgm_track": "Cipher.mp3",
    }
    res = api_client.post("/api/v1/saas/metadata", json=payload)
    assert res.status_code == 200
    body = res.json()["data"]

    assert "attribution" in body
    assert '"Cipher"' in body["attribution"]
    assert "Kevin MacLeod" in body["attribution"]
    assert body["attribution"] in body["description"]
