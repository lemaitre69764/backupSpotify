#!/usr/bin/env python3
import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
from pathlib import Path
import json
from datetime import datetime

OUTPUT_DIR = Path("./spotify_backup")
OUTPUT_DIR.mkdir(exist_ok=True)

#  СЮДА  CLIENT ID 
CLIENT_ID = "secret"  
CLIENT_SECRET = "secret"  

SCOPE = "playlist-read-private playlist-read-collaborative user-library-read user-follow-read"

# =====================================

def get_spotify_client():
    cache_path = OUTPUT_DIR / ".spotify_cache"
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope=SCOPE,
        cache_path=cache_path,
        open_browser=True,
        requests_timeout=30,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def save_json(data, filename):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: {path}")

def save_txt(playlists_data):
    path = OUTPUT_DIR / f"spotify_backup_{datetime.now():%Y-%m-%d}.txt"
    with open(path, "w", encoding="utf-8") as f:
        for playlist in playlists_data:
            name = playlist["name"]
            f.write(f"{name}\n")
            f.write("-" * len(name) + "\n")
            for item in playlist["tracks"]:
                track = item["track"]
                if not track:
                    continue
                artists = ", ".join([a["name"] for a in track["artists"]])
                line = f"{track['name']}  —  {artists}  —  {track['album']['name']}\n"
                f.write(line)
            f.write("\n\n")
    print(f"Сохранено: {path}")

def main():
    print("Запуск Spotify Backup 2025")
    sp = get_spotify_client()

    print("Получаем информацию о профиле...")
    user = sp.current_user()
    print(f"Привет, {user['display_name'] or user['id']}!\n")

    all_playlists = []
    liked_tracks_playlist = None

    print("Загрузка Понравившихся треков...")
    liked_tracks = []
    results = sp.current_user_saved_tracks(limit=50)
    with tqdm(total=results["total"], desc="Понравившиеся", unit="трэк") as pbar:
        while results:
            liked_tracks.extend(results["items"])
            pbar.update(len(results["items"]))
            results = sp.next(results) if results["next"] else None

    if liked_tracks:
        liked_tracks_playlist = {
            "name": "Понравившиеся треки ❤",
            "tracks": liked_tracks,
            "total": len(liked_tracks)
        }
        all_playlists.append(liked_tracks_playlist)

    print("\nЗагрузка плейлистов...")
    results = sp.current_user_playlists(limit=50)
    user_playlists = []
    while results:
        user_playlists.extend(results["items"])
        results = sp.next(results) if results["next"] else None

    for playlist in tqdm(user_playlists, desc="Плейлисты", unit="плейлист"):
        if playlist["tracks"]["total"] == 0:
            continue

        pl_items = []
        pl_results = sp.playlist_items(
            playlist["id"],
            fields="items(track(id,name,artists(name),album(name,release_date),duration_ms)),next,total"
        )
        with tqdm(total=pl_results["total"], desc=f"  {playlist['name'][:30]:<30}", leave=False) as pbar:
            while pl_results:
                pl_items.extend(pl_results["items"])
                pbar.update(len(pl_results["items"]))
                pl_results = sp.next(pl_results) if pl_results["next"] else None

        all_playlists.append({
            "name": playlist["name"],
            "tracks": pl_items,
            "total": len(pl_items),
            "spotify_url": playlist["external_urls"]["spotify"]
        })

    print(f"\nГотово! Найдено {len(all_playlists)} плейлистов, всего треков: {sum(p.get('total',0) for p in all_playlists)}")

    save_json(all_playlists, f"spotify_full_backup_{datetime.now():%Y-%m-%d_%H-%M}.json")

    save_txt(all_playlists)

    print("\nВсё сохранено в папку:", OUTPUT_DIR.resolve())
    print("Теперь ты независим от Spotify")

if __name__ == "__main__":
    main()
