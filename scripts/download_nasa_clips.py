import requests
import os

out_dir = r"storage\local_videos"
os.makedirs(out_dir, exist_ok=True)

queries = [
    ("earth orbit", "nasa_earth_orbit.mp4"),
    ("aurora borealis space", "nasa_aurora_space.mp4"),
    ("mars landscape", "nasa_mars_landscape.mp4"),
    ("deep space nebula", "nasa_space_nebula.mp4"),
]

headers = {"User-Agent": "PrintMoneyStudio/1.0"}

for query, filename in queries:
    target_path = os.path.join(out_dir, filename)
    if os.path.exists(target_path) and os.path.getsize(target_path) > 100000:
        print(f"Already exists: {target_path} ({os.path.getsize(target_path)} bytes)")
        continue

    try:
        print(f"Searching NASA for '{query}'...")
        search_url = f"https://images-api.nasa.gov/search?q={requests.utils.quote(query)}&media_type=video"
        r = requests.get(search_url, headers=headers, timeout=15)
        items = r.json().get("collection", {}).get("items", [])
        if not items:
            print(f"No results for '{query}'")
            continue

        downloaded = False
        for item in items[:5]:
            href = item.get("href", "").replace("http://", "https://")
            if not href:
                continue

            ar = requests.get(href, headers=headers, timeout=15)
            assets = ar.json()
            mp4_candidates = [
                a.replace("http://", "https://")
                for a in assets
                if isinstance(a, str) and (a.endswith("~medium.mp4") or a.endswith("~mobile.mp4") or a.endswith(".mp4"))
            ]
            # Prioritize mobile or medium for fast download and great quality
            mp4_candidates.sort(key=lambda u: 0 if "~mobile" in u else (1 if "~medium" in u else 2))

            for mp4_url in mp4_candidates:
                try:
                    print(f"Downloading {mp4_url} -> {target_path}...")
                    with requests.get(mp4_url, headers=headers, stream=True, timeout=60) as resp:
                        if resp.status_code == 200:
                            with open(target_path, "wb") as f:
                                for chunk in resp.iter_content(chunk_size=65536):
                                    if chunk:
                                        f.write(chunk)
                            size = os.path.getsize(target_path)
                            print(f"Success! Saved {filename} ({size} bytes)")
                            downloaded = True
                            break
                except Exception as dl_err:
                    print(f"Download attempt error: {dl_err}")
            if downloaded:
                break
    except Exception as e:
        print(f"Error querying NASA for '{query}': {e}")
