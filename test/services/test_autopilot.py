import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.asgi import app
from app.services.autopilot import AutopilotEngine


@pytest.fixture
def temp_autopilot_engine(tmp_path):
    """Fixture that initializes AutopilotEngine with a temporary storage directory."""
    with patch("app.utils.utils.storage_dir", return_value=str(tmp_path)):
        engine = AutopilotEngine()
        yield engine
        engine.stop()


def test_autopilot_initialization(temp_autopilot_engine):
    """Check storage creation and default profile."""
    engine = temp_autopilot_engine
    assert os.path.exists(engine._config_file)
    assert os.path.exists(engine._history_file)

    profiles = engine.get_profiles()
    assert len(profiles) >= 1
    default_p = profiles[0]
    assert default_p["enabled"] is True
    assert default_p["interval_hours"] == 24.0
    assert "tiktok" in default_p["platforms"]
    assert "youtube" in default_p["platforms"]


def test_autopilot_get_status(temp_autopilot_engine):
    """Check get_status output structure."""
    engine = temp_autopilot_engine
    status = engine.get_status()
    assert "running" in status
    assert "active_profiles" in status
    assert "next_run_timestamp" in status
    assert status["active_profiles"] == 1
    assert status["running"] is False


def test_autopilot_save_and_delete_profile(temp_autopilot_engine):
    """Check adding, updating and deleting profiles."""
    engine = temp_autopilot_engine

    new_profile = {
        "name": "Astronomy Quick Shorts",
        "category": "Espaço & Astrofísica",
        "interval_hours": 12.0,
        "voice": "pt-BR-AntonioNeural",
        "style": "viral_yellow",
        "source": "pexels",
        "duration": 60,
        "auto_publish": True,
        "platforms": ["tiktok", "youtube"],
    }
    saved = engine.save_profile(new_profile)
    assert saved["id"] is not None
    assert saved["name"] == "Astronomy Quick Shorts"
    assert saved["interval_hours"] == 12.0
    assert saved["auto_publish"] is True

    # Retrieve all
    profiles = engine.get_profiles()
    assert any(p["id"] == saved["id"] for p in profiles)

    # Delete
    deleted = engine.delete_profile(saved["id"])
    assert deleted is True

    # Confirm deletion
    profiles_after = engine.get_profiles()
    assert not any(p["id"] == saved["id"] for p in profiles_after)


def test_autopilot_custom_minutes(temp_autopilot_engine):
    """Check custom minutes conversion to hours."""
    engine = temp_autopilot_engine
    saved = engine.save_profile({
        "name": "Minute Runner",
        "interval_minutes": 30,
    })
    assert saved["interval_hours"] == 0.5


def test_autopilot_start_and_stop_worker(temp_autopilot_engine):
    """Check background worker thread lifecycle."""
    engine = temp_autopilot_engine
    assert not engine.is_running()

    engine.start()
    assert engine.is_running()

    # Re-starting should be idempotent
    engine.start()
    assert engine.is_running()

    engine.stop()
    assert not engine.is_running()


def test_autopilot_execute_profile_run(temp_autopilot_engine):
    """Check execution of profile run with mock task.start and upload_post."""
    engine = temp_autopilot_engine
    profiles = engine.get_profiles()
    profile_id = profiles[0]["id"]

    mock_result = {
        "videos": ["/mock/path/video_output.mp4"],
        "script": "Roteiro de teste da ciência",
    }

    with patch("app.services.task.start", return_value=mock_result) as mock_task_start, \
         patch("app.services.upload_post.cross_post_video") as mock_cross_post, \
         patch("app.services.upload_post.upload_post_service.is_configured", return_value=True), \
         patch("os.path.exists", return_value=True):

        mock_cross_post.return_value = {"success": True, "request_id": "req-123"}

        # Enable auto_publish for testing
        profiles[0]["auto_publish"] = True
        engine.save_profile(profiles[0])

        res = engine.execute_profile_run(profile_id)

        assert mock_task_start.called
        assert mock_cross_post.called
        assert res["status"] == "success"
        assert res["profile_id"] == profile_id
        assert len(res["published_platforms"]) >= 1

        history = engine.get_history()
        assert len(history) == 1
        assert history[0]["task_id"] == res["task_id"]


def test_saas_autopilot_api_endpoints():
    """Verify FastAPI integration for all /saas/autopilot/* routes."""
    client = TestClient(app)

    # 1. Status
    res = client.get("/api/v1/saas/autopilot/status")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert "running" in data["data"]

    # 2. Profiles list
    res = client.get("/api/v1/saas/autopilot/profiles")
    assert res.status_code == 200
    profiles = res.json()["data"]
    assert isinstance(profiles, list)

    # 3. Save profile
    test_profile = {
        "name": "Integration Test Profile",
        "category": "Neurociência & Psicologia",
        "interval_hours": 6.0,
        "enabled": True,
        "voice": "pt-BR-FranciscaNeural",
        "style": "electric_cyan",
        "source": "hybrid",
        "duration": 60,
        "auto_publish": False,
        "platforms": ["tiktok"],
    }
    res = client.post("/api/v1/saas/autopilot/profiles", json=test_profile)
    assert res.status_code == 200
    saved = res.json()["data"]
    profile_id = saved["id"]
    assert saved["name"] == "Integration Test Profile"

    # 4. Trigger profile (async)
    with patch("app.services.autopilot.autopilot_engine.execute_profile_run"):
        res = client.post(f"/api/v1/saas/autopilot/trigger/{profile_id}")
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "processing"

    # 5. History
    res = client.get("/api/v1/saas/autopilot/history")
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)

    # 6. Toggle
    res = client.post("/api/v1/saas/autopilot/toggle", json={"enabled": False})
    assert res.status_code == 200
    assert res.json()["data"]["enabled"] is False

    # 7. Delete profile
    res = client.delete(f"/api/v1/saas/autopilot/profiles/{profile_id}")
    assert res.status_code == 200
    assert res.json()["data"]["deleted"] is True


@pytest.mark.anyio
async def test_autopilot_lifespan_integration():
    """Verify that autopilot_engine.start() is invoked when profiles are enabled, and stopped on shutdown."""
    from app.asgi import application_lifespan

    with patch("app.services.autopilot.autopilot_engine.has_enabled_profiles", return_value=True), \
         patch("app.services.autopilot.autopilot_engine.start") as mock_start, \
         patch("app.services.autopilot.autopilot_engine.stop") as mock_stop:

        async with application_lifespan(app):
            mock_start.assert_called_once()
            assert not mock_stop.called

        mock_stop.assert_called_once()

