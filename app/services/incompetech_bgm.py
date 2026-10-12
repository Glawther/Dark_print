"""Incompetech Royalty-Free BGM Service.

Provides seamless integration with Kevin MacLeod's Incompetech music catalog:
- Caching manifest in storage/cache/incompetech_pieces.json
- Resilient fallback list of iconic Kevin MacLeod tracks
- Multi-criteria filtering by mood, genre, BPM range, and query
- Safe download with streaming, retries, and local caching
- CC-BY 4.0 compliant attribution generator for video descriptions
"""

import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import requests
from loguru import logger

from app.config import config
from app.utils import utils

MANIFEST_URL = "https://incompetech.com/music/royalty-free/pieces.json"
DOWNLOAD_BASE_URL = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/"
CACHE_FILENAME = "incompetech_pieces.json"
DEFAULT_ARTIST = "Kevin MacLeod"

_MANIFEST_MEMORY_CACHE: Optional[List[Dict[str, Any]]] = None

# Curated library of 22 top Kevin MacLeod tracks used as fallback when offline or on network failure
TOP_TRACKS_FALLBACK: List[Dict[str, Any]] = [
    {
        "id": "sneaky-snitch",
        "title": "Sneaky Snitch",
        "filename": "Sneaky Snitch.mp3",
        "bpm": 120,
        "length": "02:15",
        "genre": "Humorous",
        "feel": "Bouncy, Bright, Humorous",
        "description": "Bouncy, playful, sneaky orchestral track with pizzicato strings and bassoon.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "cipher",
        "title": "Cipher",
        "filename": "Cipher.mp3",
        "bpm": 120,
        "length": "03:52",
        "genre": "Electronic",
        "feel": "Grooving, Mysterious, Driving",
        "description": "Mid-tempo electronic groove with synthesizers and subtle tension.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "carefree",
        "title": "Carefree",
        "filename": "Carefree.mp3",
        "bpm": 100,
        "length": "03:25",
        "genre": "Pop",
        "feel": "Happy, Cheerful, Uplifting",
        "description": "Lighthearted acoustic guitar and whistling tune.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "the-complex",
        "title": "The Complex",
        "filename": "The Complex.mp3",
        "bpm": 130,
        "length": "02:40",
        "genre": "Rock",
        "feel": "Aggressive, Driving, Intense",
        "description": "High-energy heavy rock track with electric guitars and driving drums.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "darkest-child",
        "title": "Darkest Child",
        "filename": "Darkest Child.mp3",
        "bpm": 85,
        "length": "04:10",
        "genre": "Horror",
        "feel": "Eerie, Dark, Mysterious",
        "description": "Creepy piano and ambient pads creating a haunting, suspenseful mood.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "heartbreaking",
        "title": "Heartbreaking",
        "filename": "Heartbreaking.mp3",
        "bpm": 60,
        "length": "03:15",
        "genre": "Classical",
        "feel": "Sad, Melancholic, Emotional",
        "description": "Somber piano and strings expressing profound grief and sorrow.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "monkeys-spinning-monkeys",
        "title": "Monkeys Spinning Monkeys",
        "filename": "Monkeys Spinning Monkeys.mp3",
        "bpm": 106,
        "length": "02:05",
        "genre": "Humorous",
        "feel": "Playful, Bouncy, Silly",
        "description": "Viral comedic circus and cartoon style flute and xylophone track.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "scheming-weasel",
        "title": "Scheming Weasel",
        "filename": "Scheming Weasel.mp3",
        "bpm": 135,
        "length": "01:32",
        "genre": "Humorous",
        "feel": "Mischievous, Sneaky, Fast",
        "description": "Fast-paced comedic caper track with quick pizzicato and woodwinds.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "volatile-reaction",
        "title": "Volatile Reaction",
        "filename": "Volatile Reaction.mp3",
        "bpm": 140,
        "length": "02:48",
        "genre": "Action",
        "feel": "Epic, Intense, Action",
        "description": "Urgent orchestral percussion and brass for high-stakes action scenes.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "pop-goes-the-weasel",
        "title": "Pop Goes the Weasel",
        "filename": "Pop Goes the Weasel.mp3",
        "bpm": 110,
        "length": "01:14",
        "genre": "Humorous",
        "feel": "Playful, Creepy, Whimsical",
        "description": "Classic whimsical music box and toy tune.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "local-forecast-elevator",
        "title": "Local Forecast - Elevator",
        "filename": "Local Forecast - Elevator.mp3",
        "bpm": 115,
        "length": "03:07",
        "genre": "Jazz",
        "feel": "Smooth, Relaxed, Groovy",
        "description": "Classic smooth bossa nova jazz elevator music with vibraphone.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "fluffing-a-duck",
        "title": "Fluffing a Duck",
        "filename": "Fluffing a Duck.mp3",
        "bpm": 132,
        "length": "01:07",
        "genre": "Humorous",
        "feel": "Goofy, Bouncy, Humorous",
        "description": "Quirky, goofy ragtime and tubas popular in comedic videos.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "investigations",
        "title": "Investigations",
        "filename": "Investigations.mp3",
        "bpm": 98,
        "length": "01:40",
        "genre": "Mystery",
        "feel": "Curious, Suspenseful, Inquisitive",
        "description": "Tiptoeing pizzicato and clarinet mystery solving theme.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "sneaky-adventure",
        "title": "Sneaky Adventure",
        "filename": "Sneaky Adventure.mp3",
        "bpm": 125,
        "length": "01:13",
        "genre": "Humorous",
        "feel": "Playful, Mischievous, Bouncy",
        "description": "Lighthearted comedic spy and stealth track.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "pixel-peeker-polka",
        "title": "Pixel Peeker Polka",
        "filename": "Pixel Peeker Polka.mp3",
        "bpm": 140,
        "length": "03:15",
        "genre": "Video Game",
        "feel": "Upbeat, Retro, Bouncy",
        "description": "Chiptune and polka retro 8-bit gaming background music.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "gymnopedie-no-1",
        "title": "Gymnopedie No 1",
        "filename": "Gymnopedie No 1.mp3",
        "bpm": 72,
        "length": "03:05",
        "genre": "Classical",
        "feel": "Calm, Relaxing, Peaceful",
        "description": "Erik Satie peaceful and meditative classic piano piece.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "the-builder",
        "title": "The Builder",
        "filename": "The Builder.mp3",
        "bpm": 110,
        "length": "01:58",
        "genre": "Pop",
        "feel": "Upbeat, Cheerful, Bright",
        "description": "Whistling and acoustic guitar energetic building track.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "killing-time",
        "title": "Killing Time",
        "filename": "Killing Time.mp3",
        "bpm": 90,
        "length": "03:26",
        "genre": "Rock",
        "feel": "Relaxed, Chill, Grooving",
        "description": "Laid-back rock rhythm with electric organ and guitar.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "meatball-parade",
        "title": "Meatball Parade",
        "filename": "Meatball Parade.mp3",
        "bpm": 130,
        "length": "01:25",
        "genre": "Humorous",
        "feel": "Bouncy, Festive, Silly",
        "description": "Festive brass polka parade comedic theme.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "hitman",
        "title": "Hitman",
        "filename": "Hitman.mp3",
        "bpm": 105,
        "length": "03:18",
        "genre": "Soundtrack",
        "feel": "Suspenseful, Dark, Cinematic",
        "description": "Tense espionage cinematic orchestral score.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "spazzmatica-polka",
        "title": "Spazzmatica Polka",
        "filename": "Spazzmatica Polka.mp3",
        "bpm": 140,
        "length": "01:35",
        "genre": "Humorous",
        "feel": "Frantic, Manic, Fast",
        "description": "Manic fast accordion polka comedy chase music.",
        "artist": DEFAULT_ARTIST,
    },
    {
        "id": "faster-does-it",
        "title": "Faster Does It",
        "filename": "Faster Does It.mp3",
        "bpm": 150,
        "length": "02:18",
        "genre": "Jazz",
        "feel": "Fast, Bouncy, Energetic",
        "description": "Upbeat vintage jazz and swing track.",
        "artist": DEFAULT_ARTIST,
    },
]

GENRE_ID_MAP: Dict[str, str] = {
    "2": "African",
    "3": "Blues",
    "4": "Classical",
    "5": "Contemporary",
    "6": "Disco",
    "7": "Electronica",
    "8": "Funk",
    "9": "Holiday",
    "10": "Horror",
    "11": "Jazz",
    "12": "Latin",
    "13": "Modern",
    "14": "Musical",
    "15": "Polka",
    "16": "Pop",
    "18": "Reggae",
    "19": "Rock",
    "20": "Silent Film Score",
    "21": "Ska",
    "22": "Soundtrack",
    "23": "Stings",
    "24": "Unclassifiable",
    "25": "World",
    "26": "Urban",
}


def _get_tls_verify() -> bool:
    tls_verify = config.app.get("tls_verify", True)
    if isinstance(tls_verify, str):
        tls_verify = tls_verify.strip().lower() not in ("0", "false", "no", "off")
    return bool(tls_verify)


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", str(text or "")).strip().lower()
    return re.sub(r"[-\s]+", "-", cleaned) or str(uuid4())[:8]


def get_cache_path() -> str:
    """Returns absolute path to storage/cache/incompetech_pieces.json."""
    cache_dir = utils.storage_dir("cache", create=True)
    return os.path.join(cache_dir, CACHE_FILENAME)


def normalize_track(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a track dictionary ensuring all expected keys exist."""
    title = str(raw.get("title", "")).strip()
    filename = str(raw.get("filename", "")).strip()
    if not filename and title:
        filename = f"{title}.mp3"

    raw_bpm = raw.get("bpm")
    bpm: Optional[Union[int, float]] = None
    if raw_bpm is not None:
        try:
            bpm_val = float(raw_bpm)
            bpm = int(bpm_val) if bpm_val.is_integer() else bpm_val
        except (ValueError, TypeError):
            bpm = None

    track_id = str(raw.get("id") or raw.get("uuid") or _slugify(title))
    artist = str(raw.get("artist", DEFAULT_ARTIST)).strip() or DEFAULT_ARTIST
    raw_genre = str(raw.get("genre", "")).strip()
    genre = GENRE_ID_MAP.get(raw_genre, raw_genre)
    feel = str(raw.get("feel") or raw.get("mood") or "").strip()
    length = str(raw.get("length", "")).strip()
    description = str(raw.get("description", "")).strip()
    download_url = f"{DOWNLOAD_BASE_URL}{filename}"

    return {
        "id": track_id,
        "title": title,
        "filename": filename,
        "bpm": bpm,
        "length": length,
        "genre": genre,
        "feel": feel,
        "description": description,
        "artist": artist,
        "download_url": download_url,
    }


def _save_cache(tracks: List[Dict[str, Any]], cache_file: str) -> None:
    """Safely saves manifest tracks to the cache file."""
    try:
        temp_file = f"{cache_file}.tmp.{uuid4().hex[:8]}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(tracks, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, cache_file)
    except Exception as e:
        logger.warning(f"Could not persist Incompetech manifest cache to {cache_file}: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass


def load_manifest(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Loads manifest tracks from memory, disk cache, or remote URL."""
    global _MANIFEST_MEMORY_CACHE

    if not force_refresh and _MANIFEST_MEMORY_CACHE is not None:
        return _MANIFEST_MEMORY_CACHE

    cache_file = get_cache_path()

    # 1. Attempt loading from disk cache
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            if isinstance(cached_data, list) and cached_data:
                normalized = [normalize_track(item) for item in cached_data if isinstance(item, dict)]
                if normalized:
                    _MANIFEST_MEMORY_CACHE = normalized
                    return _MANIFEST_MEMORY_CACHE
        except Exception as e:
            logger.warning(f"Failed to read Incompetech cache file ({cache_file}): {e}")

    # 2. Fetch from remote manifest URL
    try:
        logger.info(f"Fetching Incompetech manifest from {MANIFEST_URL}...")
        response = requests.get(
            MANIFEST_URL,
            headers={
                "User-Agent": "Dark_print/1.0",
                "Accept": "application/json",
            },
            timeout=(8, 20),
            proxies=config.proxy,
            verify=_get_tls_verify(),
        )
        if response.status_code == 200:
            payload = response.json()
            raw_pieces: List[Dict[str, Any]] = []
            if isinstance(payload, list):
                raw_pieces = payload
            elif isinstance(payload, dict):
                if "pieces" in payload and isinstance(payload["pieces"], list):
                    raw_pieces = payload["pieces"]
                else:
                    raw_pieces = [v for v in payload.values() if isinstance(v, dict)]

            normalized = [normalize_track(p) for p in raw_pieces if isinstance(p, dict)]
            if normalized:
                _save_cache(normalized, cache_file)
                _MANIFEST_MEMORY_CACHE = normalized
                logger.info(f"Successfully loaded and cached {len(normalized)} Incompetech pieces.")
                return _MANIFEST_MEMORY_CACHE
        else:
            logger.warning(f"Incompetech manifest responded with status {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to fetch Incompetech manifest from remote ({e}). Using fallback catalog.")

    # 3. Fallback to existing cache if available
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            if isinstance(cached_data, list) and cached_data:
                normalized = [normalize_track(item) for item in cached_data if isinstance(item, dict)]
                if normalized:
                    _MANIFEST_MEMORY_CACHE = normalized
                    return _MANIFEST_MEMORY_CACHE
        except Exception:
            pass

    # 4. Fallback to bundled curated tracks
    fallback_normalized = [normalize_track(track) for track in TOP_TRACKS_FALLBACK]
    _save_cache(fallback_normalized, cache_file)
    _MANIFEST_MEMORY_CACHE = fallback_normalized
    return _MANIFEST_MEMORY_CACHE


def search_incompetech_tracks(
    feel: Optional[str] = None,
    genre: Optional[str] = None,
    min_bpm: Optional[Union[float, int]] = None,
    max_bpm: Optional[Union[float, int]] = None,
    query: Optional[str] = None,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """Filters Incompetech catalog by feel/mood, genre, BPM range, or keyword search."""
    tracks = load_manifest()
    results: List[Dict[str, Any]] = []

    feel_term = (feel or "").strip().lower()
    genre_term = (genre or "").strip().lower()
    q_term = (query or "").strip().lower()

    for track in tracks:
        if feel_term:
            track_feel = str(track.get("feel", "")).lower()
            if feel_term not in track_feel:
                continue

        if genre_term:
            track_genre = str(track.get("genre", "")).lower()
            track_feel = str(track.get("feel", "")).lower()
            if genre_term not in track_genre and genre_term not in track_feel:
                continue

        bpm_val = track.get("bpm")
        if min_bpm is not None:
            if bpm_val is None or float(bpm_val) < float(min_bpm):
                continue
        if max_bpm is not None:
            if bpm_val is None or float(bpm_val) > float(max_bpm):
                continue

        if q_term:
            matched = False
            for field in ("title", "feel", "genre", "description", "filename"):
                if q_term in str(track.get(field, "")).lower():
                    matched = True
                    break
            if not matched:
                continue

        results.append(track)

    if limit is not None and limit > 0:
        return results[:limit]
    return results


def search_tracks(
    genre: Optional[str] = None,
    feel: Optional[str] = None,
    min_bpm: Optional[Union[float, int]] = None,
    max_bpm: Optional[Union[float, int]] = None,
    query: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Alias for search_incompetech_tracks matching flexible parameter conventions."""
    return search_incompetech_tracks(
        feel=feel,
        genre=genre,
        min_bpm=min_bpm,
        max_bpm=max_bpm,
        query=query,
        limit=limit,
    )


def download_incompetech_track(filename: str, dest_dir: str = "resource/bgm") -> str:
    """Downloads an MP3 track safely with streaming, retries, and local caching."""
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename is required")

    clean_name = os.path.basename(filename.strip())
    # Reject directory traversal and malicious characters
    if ".." in filename or "/" in filename or "\\" in filename or "\0" in filename:
        raise ValueError(f"Unsafe filename: {filename}")

    if not clean_name:
        raise ValueError("Filename cannot be empty")

    if not clean_name.lower().endswith(".mp3"):
        clean_name = f"{clean_name}.mp3"

    if os.path.isabs(dest_dir):
        target_dir = dest_dir
    else:
        target_dir = os.path.join(utils.root_dir(), dest_dir)
    os.makedirs(target_dir, exist_ok=True)

    dest_file = os.path.join(target_dir, clean_name)
    if os.path.exists(dest_file) and os.path.getsize(dest_file) > 0:
        logger.info(f"Incompetech track '{clean_name}' already exists locally at {dest_file}")
        return dest_file

    encoded_name = urllib.parse.quote(clean_name)
    url = f"{DOWNLOAD_BASE_URL}{encoded_name}"
    logger.info(f"Downloading Incompetech track '{clean_name}' from {url}")

    last_error: Optional[Exception] = None
    for attempt in range(1, 4):
        temp_file = os.path.join(target_dir, f".incompetech-{uuid4().hex[:8]}-{clean_name}")
        try:
            with requests.get(
                url,
                stream=True,
                timeout=(15, 60),
                headers={"User-Agent": "Dark_print/1.0"},
                proxies=config.proxy,
                verify=_get_tls_verify(),
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"HTTP status {response.status_code} while downloading {url}")
                with open(temp_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                raise RuntimeError("Downloaded file is empty")

            os.replace(temp_file, dest_file)
            logger.info(f"Successfully downloaded {clean_name} to {dest_file}")
            return dest_file
        except Exception as e:
            last_error = e
            logger.warning(f"Download attempt {attempt}/3 for '{clean_name}' failed: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            if attempt < 3:
                time.sleep(1.0 * attempt)

    raise RuntimeError(f"Failed to download Incompetech track '{clean_name}' after 3 attempts: {last_error}")


def download_track(filename: str, destination_dir: str = "resource/bgm") -> str:
    """Alias for download_incompetech_track."""
    return download_incompetech_track(filename=filename, dest_dir=destination_dir)


def get_cc_attribution(track_title: str, artist: str = DEFAULT_ARTIST) -> str:
    """Returns compliant CC-BY 4.0 credit string for YouTube descriptions."""
    title = (track_title or "").strip()
    if title.lower().endswith(".mp3"):
        title = title[:-4].strip()
    art = (artist or DEFAULT_ARTIST).strip()
    return (
        f'"{title}" {art} (incompetech.com)\n'
        f"Licensed under Creative Commons: By Attribution 4.0 License\n"
        f"http://creativecommons.org/licenses/by/4.0/"
    )


get_attribution = get_cc_attribution
