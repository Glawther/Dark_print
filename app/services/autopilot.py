"""Autopilot Engine Service

Autonomous background scheduling and orchestrator for unattended video generation
and automated social media delivery.
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger

from app.config import config
from app.models import const
from app.models.schema import VideoAspect, VideoParams
from app.utils import utils


class AutopilotEngine:
    """Thread-safe autonomous scheduling and task execution engine."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._storage_dir = utils.storage_dir("autopilot", create=True)
        self._config_file = os.path.join(self._storage_dir, "config.json")
        self._history_file = os.path.join(self._storage_dir, "history.json")
        self._ensure_storage_initialized()

    def _ensure_storage_initialized(self) -> None:
        """Initializes storage files with valid structures if they do not exist."""
        with self._lock:
            if not os.path.exists(self._config_file):
                default_config = {
                    "enabled": True,
                    "profiles": [
                        {
                            "id": "science-astrophysics-daily",
                            "name": "Ciência & Astrofísica Diário",
                            "category": "Espaço & Astrofísica",
                            "enabled": True,
                            "interval_hours": 24.0,
                            "next_run_timestamp": time.time() + 86400.0,
                            "last_run_timestamp": None,
                            "voice": "pt-BR-AntonioNeural",
                            "style": "viral_yellow",
                            "source": "hybrid",
                            "duration": 60,
                            "auto_publish": False,
                            "platforms": ["tiktok", "youtube"],
                        }
                    ],
                }
                self._write_json(self._config_file, default_config)

            if not os.path.exists(self._history_file):
                self._write_json(self._history_file, [])

    def _read_json(self, file_path: str, default_val: Any) -> Any:
        try:
            if not os.path.exists(file_path):
                return default_val
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Autopilot: failed reading {file_path}: {e}")
            return default_val

    def _write_json(self, file_path: str, data: Any) -> None:
        tmp_path = f"{file_path}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, file_path)
        except Exception as e:
            logger.error(f"Autopilot: failed writing {file_path}: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    def _load_config(self) -> Dict[str, Any]:
        return self._read_json(self._config_file, {"enabled": True, "profiles": []})

    def _save_config(self, cfg: Dict[str, Any]) -> None:
        self._write_json(self._config_file, cfg)

    def _load_history(self) -> List[Dict[str, Any]]:
        return self._read_json(self._history_file, [])

    def _save_history(self, hist: List[Dict[str, Any]]) -> None:
        self._write_json(self._history_file, hist)

    def _append_history(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            history = self._load_history()
            history.insert(0, entry)
            history = history[:100]  # Retain top 100 entries on disk
            self._save_history(history)

    def is_running(self) -> bool:
        with self._lock:
            return self._worker_thread is not None and self._worker_thread.is_alive()

    def has_enabled_profiles(self) -> bool:
        with self._lock:
            cfg = self._load_config()
            if not cfg.get("enabled", True):
                return False
            return any(bool(p.get("enabled", False)) for p in cfg.get("profiles", []))

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            running = self.is_running()
            cfg = self._load_config()
            global_enabled = cfg.get("enabled", True)
            profiles = cfg.get("profiles", [])

            active_profiles = [p for p in profiles if p.get("enabled", False)]
            active_count = len(active_profiles)

            upcoming_timestamps = [
                float(p["next_run_timestamp"])
                for p in active_profiles
                if p.get("next_run_timestamp") is not None
            ]
            next_run = min(upcoming_timestamps) if upcoming_timestamps else None
            next_run_iso = (
                datetime.fromtimestamp(next_run, tz=timezone.utc).isoformat()
                if next_run is not None
                else None
            )

            return {
                "running": running,
                "is_running": running,
                "enabled": global_enabled,
                "active_profiles": active_count,
                "total_profiles": len(profiles),
                "next_run_timestamp": next_run,
                "next_upcoming_execution_timestamp": next_run,
                "next_run_iso": next_run_iso,
            }

    def start(self) -> None:
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                logger.info("Autopilot engine worker thread is already running.")
                return

            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name="AutopilotEngineWorker",
            )
            self._worker_thread.start()
            logger.info("Autopilot engine started successfully.")

    def stop(self) -> None:
        with self._lock:
            if not self._worker_thread or not self._worker_thread.is_alive():
                return
            self._stop_event.set()

        logger.info("Signaling Autopilot engine worker thread to stop...")
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("Autopilot engine stopped.")

    def set_global_enabled(self, enabled: bool) -> None:
        with self._lock:
            cfg = self._load_config()
            cfg["enabled"] = bool(enabled)
            self._save_config(cfg)

        if enabled:
            self.start()
        else:
            self.stop()

    def get_profiles(self) -> List[Dict[str, Any]]:
        with self._lock:
            cfg = self._load_config()
            return list(cfg.get("profiles", []))

    def save_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            cfg = self._load_config()
            profiles = cfg.get("profiles", [])

            profile_id = str(data.get("id") or "").strip()
            if not profile_id:
                profile_id = f"auto-{str(uuid4())[:8]}"

            # Parse interval
            raw_interval = data.get("interval_hours")
            if raw_interval is None and "interval_minutes" in data:
                try:
                    interval_hours = max(float(data["interval_minutes"]) / 60.0, 0.05)
                except (ValueError, TypeError):
                    interval_hours = 24.0
            else:
                try:
                    interval_hours = max(float(raw_interval if raw_interval is not None else 24.0), 0.05)
                except (ValueError, TypeError):
                    interval_hours = 24.0

            # Determine next run
            now = time.time()
            next_run = data.get("next_run_timestamp")
            if next_run is not None:
                try:
                    next_run = float(next_run)
                except (ValueError, TypeError):
                    next_run = now + (interval_hours * 3600.0)
            else:
                next_run = now + (interval_hours * 3600.0)

            # Platforms normalization
            raw_platforms = data.get("platforms", ["tiktok", "youtube"])
            if isinstance(raw_platforms, str):
                platforms = [p.strip() for p in raw_platforms.split(",") if p.strip()]
            elif isinstance(raw_platforms, list):
                platforms = [str(p).strip() for p in raw_platforms if str(p).strip()]
            else:
                platforms = ["tiktok", "youtube"]

            normalized_profile: Dict[str, Any] = {
                "id": profile_id,
                "name": str(data.get("name") or "Autopilot Profile").strip(),
                "category": str(data.get("category") or "Espaço & Astrofísica").strip(),
                "enabled": bool(data.get("enabled", True)),
                "interval_hours": interval_hours,
                "next_run_timestamp": next_run,
                "last_run_timestamp": data.get("last_run_timestamp"),
                "voice": str(data.get("voice") or "pt-BR-AntonioNeural").strip(),
                "style": str(data.get("style") or "viral_yellow").strip(),
                "source": str(data.get("source") or "hybrid").strip(),
                "duration": int(data.get("duration") or 60),
                "auto_publish": bool(data.get("auto_publish", False)),
                "platforms": platforms,
            }

            # Optional extra fields preserved
            for extra_key in ("voice_rate", "voice_volume", "use_llm"):
                if extra_key in data:
                    normalized_profile[extra_key] = data[extra_key]

            # Update existing or append
            updated = False
            for idx, existing in enumerate(profiles):
                if existing.get("id") == profile_id:
                    profiles[idx] = normalized_profile
                    updated = True
                    break

            if not updated:
                profiles.append(normalized_profile)

            cfg["profiles"] = profiles
            self._save_config(cfg)
            logger.info(f"Autopilot profile saved: {profile_id} ('{normalized_profile['name']}')")
            return normalized_profile

    def delete_profile(self, profile_id: str) -> bool:
        with self._lock:
            cfg = self._load_config()
            profiles = cfg.get("profiles", [])
            initial_count = len(profiles)
            filtered = [p for p in profiles if p.get("id") != profile_id]

            if len(filtered) == initial_count:
                return False

            cfg["profiles"] = filtered
            self._save_config(cfg)
            logger.info(f"Autopilot profile deleted: {profile_id}")
            return True

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            history = self._load_history()
            history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return history[:50]

    def _worker_loop(self) -> None:
        logger.info("Autopilot worker loop active. Polling every 60 seconds.")
        while not self._stop_event.is_set():
            try:
                self._check_and_run_due_profiles()
            except Exception as e:
                logger.exception(f"Unexpected error in Autopilot worker loop: {e}")

            # Sleep 60 seconds; if stop_event is signaled, break early
            if self._stop_event.wait(timeout=60.0):
                break
        logger.info("Autopilot worker loop terminated.")

    def _check_and_run_due_profiles(self) -> None:
        with self._lock:
            cfg = self._load_config()
            if not cfg.get("enabled", True):
                return
            profiles = list(cfg.get("profiles", []))

        now = time.time()
        for profile in profiles:
            if not profile.get("enabled", False):
                continue

            next_run = profile.get("next_run_timestamp")
            if next_run is not None and now >= float(next_run):
                pid = profile.get("id")
                pname = profile.get("name")
                logger.info(f"Autopilot profile '{pname}' ({pid}) is due for execution.")

                # Schedule next run in advance to prevent concurrent triggers
                interval_hours = float(profile.get("interval_hours", 24.0))
                profile["last_run_timestamp"] = now
                profile["next_run_timestamp"] = now + (interval_hours * 3600.0)
                self.save_profile(profile)

                # Execute run in a dedicated thread to not block worker loop
                exec_thread = threading.Thread(
                    target=self.execute_profile_run,
                    args=(pid,),
                    daemon=True,
                    name=f"AutopilotRun-{pid}",
                )
                exec_thread.start()

    def _get_viral_idea(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Pulls a viral idea from SCIENCE_PRESETS or generates one via LLM."""
        from app.controllers.v1.saas import SCIENCE_PRESETS

        cat = (profile.get("category") or "").strip().lower()
        candidates = [
            p for p in SCIENCE_PRESETS
            if p.get("category", "").strip().lower() == cat
        ] if cat else list(SCIENCE_PRESETS)

        if not candidates:
            candidates = list(SCIENCE_PRESETS)

        recent_history = self.get_history()[:25]
        recent_topics = {
            h.get("topic", "").strip().lower()
            for h in recent_history
            if h.get("topic")
        }
        fresh_candidates = [
            p for p in candidates
            if p.get("title", "").strip().lower() not in recent_topics
        ]
        chosen = random.choice(fresh_candidates) if fresh_candidates else random.choice(candidates)

        # Check for optional LLM generation
        if profile.get("use_llm", False):
            try:
                from app.services import llm
                prompt = (
                    f"Gere um roteiro viral e hipnótico em português sobre '{profile.get('category') or 'Ciência Curiosa'}' para Shorts/TikTok.\n"
                    f"Duração de 60 segundos.\n"
                    f"Retorne apenas um JSON puro no formato: {{\"title\": \"Título\", \"script\": \"Roteiro narrativo\", \"terms\": [\"termo1 4k\", \"termo2\"]}}"
                )
                raw_response = llm._generate_response(prompt)
                import re
                match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if parsed.get("title") and parsed.get("script"):
                        return {
                            "title": parsed["title"],
                            "script": parsed["script"],
                            "terms": parsed.get("terms", chosen.get("terms", [])),
                            "voice": chosen.get("voice", "pt-BR-AntonioNeural"),
                            "voice_rate": chosen.get("voice_rate", 1.15),
                            "style": chosen.get("style", "viral_yellow"),
                        }
            except Exception as e:
                logger.warning(f"Autopilot LLM idea generation failed; falling back to preset: {e}")

        return chosen

    def _resolve_subtitle_style(self, style_id: str) -> Dict[str, Any]:
        """Resolves visual subtitle configuration based on style id."""
        from app.controllers.v1.saas import SUBTITLE_STYLES

        for s in SUBTITLE_STYLES:
            if s.get("id") == style_id:
                return s

        for s in SUBTITLE_STYLES:
            if s.get("id") == "viral_yellow":
                return s

        return SUBTITLE_STYLES[0] if SUBTITLE_STYLES else {}

    def execute_profile_run(self, profile_id: str) -> Dict[str, Any]:
        """Executes a complete autonomous production cycle for the specified profile.

        Pulls a viral idea, calls task.start() to render the video, logs history,
        and optionally publishes to social platforms via upload_post.cross_post_video().
        """
        profiles = self.get_profiles()
        profile = next((p for p in profiles if p.get("id") == profile_id), None)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        logger.info(f"=== Starting Autopilot run for profile '{profile.get('name')}' ({profile_id}) ===")

        # 1. Pull viral idea
        idea = self._get_viral_idea(profile)
        topic = idea.get("title") or "Mistérios da Ciência"
        script = idea.get("script", "")
        terms = idea.get("terms", [])

        voice_name = profile.get("voice") or idea.get("voice") or "pt-BR-AntonioNeural"
        voice_rate = float(profile.get("voice_rate") or idea.get("voice_rate") or 1.15)
        style_id = profile.get("style") or idea.get("style") or "viral_yellow"
        style_conf = self._resolve_subtitle_style(style_id)

        # 2. Build VideoParams
        video_source = profile.get("source") or "hybrid"

        params = VideoParams(
            video_subject=topic,
            video_script=script,
            video_terms=terms,
            video_aspect=VideoAspect.portrait.value,
            video_source=video_source,
            video_clip_duration=5,
            voice_name=voice_name,
            voice_rate=voice_rate,
            voice_volume=1.0,
            bgm_type="random",
            bgm_volume=0.2,
            subtitle_enabled=True,
            subtitle_position=style_conf.get("subtitle_position", "bottom"),
            subtitle_display_mode=style_conf.get("subtitle_display_mode", "word_by_word"),
            subtitle_animation=style_conf.get("subtitle_animation", "pop_spring"),
            font_name=style_conf.get("font_name", "BeVietnamPro-Bold.ttf"),
            font_size=int(style_conf.get("font_size", 70)),
            text_fore_color=style_conf.get("text_fore_color", "#FFE600"),
            stroke_color=style_conf.get("stroke_color", "#000000"),
            stroke_width=float(style_conf.get("stroke_width", 2.5)),
            text_background_color=style_conf.get("text_background_color", False),
            rounded_subtitle_background=bool(style_conf.get("rounded_subtitle_background", False)),
        )

        # 3. Create task and execute pipeline
        from app.services import state as sm
        from app.services import task as task_service

        task_id = utils.get_uuid()
        sm.state.update_task(task_id, params=params.model_dump())

        logger.info(f"Autopilot pipeline initiated: task_id={task_id}, topic='{topic}'")

        is_success = False
        video_paths: List[str] = []
        error_msg: Optional[str] = None

        try:
            task_result = task_service.start(task_id, params=params, stop_at="video")
            task_record = sm.state.get_task(task_id)

            if isinstance(task_result, dict) and task_result.get("videos"):
                video_paths = list(task_result["videos"])
            elif task_record:
                rec_videos = task_record.get("videos") if isinstance(task_record, dict) else getattr(task_record, "videos", None)
                if rec_videos:
                    video_paths = list(rec_videos)

            rec_state = task_record.get("state") if isinstance(task_record, dict) else getattr(task_record, "state", None) if task_record else None
            is_success = bool(video_paths) and (rec_state != const.TASK_STATE_FAILED)
            if not is_success:
                if isinstance(task_result, dict) and task_result.get("error"):
                    error_msg = str(task_result["error"])
                elif task_record:
                    rec_err = task_record.get("error") if isinstance(task_record, dict) else getattr(task_record, "error", None)
                    error_msg = str(rec_err) if rec_err else "Video generation pipeline failed"
                else:
                    error_msg = "Video generation pipeline failed"
                logger.error(f"Autopilot video generation failed: {error_msg}")
            else:
                logger.success(f"Autopilot video generated successfully: {video_paths}")
        except Exception as e:
            logger.exception(f"Autopilot error during task.start execution: {e}")
            is_success = False
            error_msg = str(e)

        # 4. Auto-publish if requested
        published_platforms: List[str] = []
        auto_publish = bool(profile.get("auto_publish", False))
        platforms = profile.get("platforms", ["tiktok", "youtube"])
        if isinstance(platforms, str):
            platforms = [p.strip() for p in platforms.split(",") if p.strip()]

        if is_success and auto_publish and video_paths and platforms:
            from app.services import upload_post
            from app.controllers.v1.saas import generate_viral_metadata

            target_video = video_paths[0]
            if not os.path.isabs(target_video):
                candidate = os.path.join(utils.task_dir(task_id), os.path.basename(target_video))
                if os.path.exists(candidate):
                    target_video = candidate

            if not upload_post.upload_post_service.is_configured():
                logger.warning(
                    f"Autopilot auto_publish requested for profile '{profile.get('name')}', "
                    "but Upload-Post credentials are not configured. Skipping cross-post."
                )
            elif not os.path.exists(target_video):
                logger.warning(f"Autopilot target video not found on disk: {target_video}")
            else:
                meta = generate_viral_metadata(subject=topic, script=script)
                post_title = meta["titles"][0] if meta.get("titles") else topic

                youtube_extra = None
                if any(p.startswith("youtube") for p in platforms):
                    yt_privacy = config.app.get("upload_post_youtube_privacy_status", "public")
                    made_for_kids = bool(config.app.get("upload_post_youtube_made_for_kids", False))
                    youtube_extra = {
                        "youtube_title": post_title[:100],
                        "youtube_description": f"{meta['description']}\n\n{meta['hashtags_text']}",
                        "tags": [tag.replace("#", "") for tag in meta["hashtags"][:10]],
                        "privacyStatus": yt_privacy,
                        "selfDeclaredMadeForKids": made_for_kids,
                        "containsSyntheticMedia": True,
                    }

                try:
                    logger.info(f"Autopilot publishing video {target_video} to {platforms}...")
                    pub_res = upload_post.cross_post_video(
                        video_path=target_video,
                        title=post_title,
                        platforms=platforms,
                        youtube_extra=youtube_extra,
                    )
                    if pub_res.get("success"):
                        published_platforms = list(platforms)
                        sm.state.update_task(
                            task_id,
                            cross_post_state=const.CROSS_POST_STATE_COMPLETE,
                            cross_post_results=[pub_res],
                        )
                        logger.success(f"Autopilot published to {platforms} successfully.")
                    else:
                        pub_err = pub_res.get("error") or "Upload-Post failure"
                        logger.warning(f"Autopilot cross-post failed: {pub_err}")
                        sm.state.update_task(
                            task_id,
                            cross_post_state=const.CROSS_POST_STATE_FAILED,
                            cross_post_error=pub_err,
                            cross_post_results=[pub_res],
                        )
                except Exception as pe:
                    logger.exception(f"Autopilot cross-post exception: {pe}")
                    sm.state.update_task(
                        task_id,
                        cross_post_state=const.CROSS_POST_STATE_FAILED,
                        cross_post_error=str(pe),
                    )

        # 5. Record run history
        run_record: Dict[str, Any] = {
            "task_id": task_id,
            "profile_id": profile["id"],
            "profile_name": profile.get("name", "Autopilot Profile"),
            "topic": topic,
            "status": "success" if is_success else "failed",
            "timestamp": time.time(),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "published_platforms": published_platforms,
            "error": error_msg,
            "video_path": video_paths[0] if video_paths else None,
        }
        self._append_history(run_record)

        # 6. Update profile's last_run and next_run timestamps
        now = time.time()
        interval_hours = float(profile.get("interval_hours", 24.0))
        profile["last_run_timestamp"] = now
        profile["next_run_timestamp"] = now + (interval_hours * 3600.0)
        self.save_profile(profile)

        logger.info(f"=== Completed Autopilot run for profile {profile_id}. Status: {run_record['status']} ===")
        return run_record


# Thread-safe Singleton
_autopilot_engine_lock = threading.Lock()
_autopilot_engine_instance: Optional[AutopilotEngine] = None


def get_autopilot_engine() -> AutopilotEngine:
    global _autopilot_engine_instance
    if _autopilot_engine_instance is None:
        with _autopilot_engine_lock:
            if _autopilot_engine_instance is None:
                _autopilot_engine_instance = AutopilotEngine()
    return _autopilot_engine_instance


autopilot_engine = get_autopilot_engine()
