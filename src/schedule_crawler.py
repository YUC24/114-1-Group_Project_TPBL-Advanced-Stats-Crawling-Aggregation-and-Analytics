# tpbl_crawler_schedule.py
# 功能：呼叫 TPBL 官方 API，把某幾季的全部賽程抓下來，
#       轉成自己統一的格式，存成 data/games.json

import json
import time
from pathlib import Path

import requests

OUTPUT_PATH = Path("data/schedule_raw.json")

BASE_URL = "https://api.tpbl.basketball/api/seasons/{season_id}/games"

HEADERS = {
    "User-Agent": "ntu-im-tpbl-project/1.0 (course project)"
}


def fetch_games_for_season(season_id: int):
    """
    送 request 拿某一季的所有比賽。

    會回傳 list[dict]，每個 dict 就是你剛剛貼的那種 game 物件。
    """
    url = BASE_URL.format(season_id=season_id)
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    # 有些 API 會包成 {"data": [...]}，保險處理一下
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def normalize_game(raw_game: dict, season_id: int) -> dict:
    """
    把官方 game JSON 轉成我們專案統一使用的欄位。
    注意：目前這個 JSON 片段沒有看到單場比分欄位，
    只有 team.won_score / team.lost_score，這看起來比較像球隊累積戰績，
    所以暫時不填 home_score / away_score。
    """

    home = raw_game.get("home_team") or {}
    away = raw_game.get("away_team") or {}
    home_meta = home.get("meta") or {}
    away_meta = away.get("meta") or {}
    meta = raw_game.get("meta") or {}

    game_time = raw_game.get("game_time")  # e.g. "17:00:00"
    # 轉成 "HH:MM"
    time_str = game_time[:5] if isinstance(game_time, str) and len(game_time) >= 5 else None

    return {
        "game_id": raw_game.get("id"),
        "season_id": season_id,
        "division_id": raw_game.get("division_id"),
        "code": raw_game.get("code"),                    # 例如 "1"
        "date": raw_game.get("game_date"),               # "2025-10-11"
        "time": time_str,                                # "17:00"
        "datetime": raw_game.get("gamed_at"),            # "2025-10-11 17:00:00"
        "day_of_week": raw_game.get("game_day_of_week"), # "(六)"

        "venue": raw_game.get("venue"),
        "status": raw_game.get("status"),                # "COMPLETED", "SCHEDULED"...
        "is_live": raw_game.get("is_live"),
        "round": raw_game.get("round"),

        # 主隊資訊
        "home_team_id": home.get("id"),
        "home_team_name": home.get("name"),
        "home_team_logo": home_meta.get("logo"),
        "home_team_alt_name": home_meta.get("alt_name"),

        # 客隊資訊
        "away_team_id": away.get("id"),
        "away_team_name": away.get("name"),
        "away_team_logo": away_meta.get("logo"),
        "away_team_alt_name": away_meta.get("alt_name"),

        # 進階連結
        "recap_url": meta.get("recap"),
        "live_stream_url": meta.get("live_stream_url"),
        "judgement_report_url": meta.get("judgement_report"),
    }


def crawl_all_games():
    """
    抓多個 season_id 的賽程，合併寫入一個 games.json
    season_id 你可以之後自己再加。
    目前先只抓你找到的 season 2。
    """
    season_ids = [2]  # 之後如果有 1, 3, 4... 就自己加進來

    all_games = []

    for sid in season_ids:
        print(f"抓取 season {sid} 的賽程中...")
        raw_games = fetch_games_for_season(sid)
        print(f"season {sid} 共 {len(raw_games)} 場")

        for g in raw_games:
            norm = normalize_game(g, sid)
            all_games.append(norm)

        # 禮貌休息一下，避免一直打 API
        time.sleep(1)

    # 依日期 & 時間排序，沒時間的排後面
    def sort_key(g):
        return (g.get("date") or "", g.get("time") or "99:99")

    all_games.sort(key=sort_key)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(all_games, f, ensure_ascii=False, indent=2)

    print(f"已寫入 {OUTPUT_PATH}，總共 {len(all_games)} 場比賽")


if __name__ == "__main__":
    crawl_all_games()
