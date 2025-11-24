# stats_crawler.py
# 功能：
# 1. 讀取 data/games.json（你之前抓好的賽程）
# 2. 對每一場比賽呼叫 https://api.tpbl.basketball/api/games/{id}/stats
# 3. 把每場比賽的「home/away 隊伍總數據」整理成一張表，存成 data/team_stats.json
# 4. 另外抓 https://api.tpbl.basketball/api/divisions/9/players
#    存成 data/players_master.json（球員基本資料，之後如果找到球員 stats API 可以 join）

import json
from pathlib import Path
import time

import requests


GAMES_PATH = Path("data/games.json")
GAME_STATS_URL = "https://api.tpbl.basketball/api/games/{game_id}/stats"
DIVISION_PLAYERS_URL = "https://api.tpbl.basketball/api/divisions/9/players"


# -------- 共用：簡單的 HTTP 請求 --------

def http_get_json(url):
    """發送 GET 並回傳 JSON，失敗時丟錯。"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


# -------- 讀取既有的 games.json --------

def load_games():
    """載入 data/games.json，回傳 list[dict]。"""
    if not GAMES_PATH.exists():
        print("找不到 data/games.json，請先執行 tpbl_crawler.py。")
        return []

    with GAMES_PATH.open("r", encoding="utf-8") as f:
        games = json.load(f)

    # 依日期、時間排序（保險）
    games.sort(key=lambda x: (x.get("date"), x.get("time")))
    return games


# -------- 解析 /games/{id}/stats 裡的隊伍最終統計 --------

def extract_team_totals(game_id, stats_json):
    """
    從單場比賽的 stats_json 中，抽出 home / away 兩隊「全場總數據」。

    /games/{id}/stats 典型結構：
    {
      "home_team": {
        "id": 8,
        "name": "...",
        "teams": {
          "rounds": {
            "1": {...},
            "2": {...},
            "3": {...},
            "4": {...}
          }
        }
      },
      "away_team": { ... }
    }

    每一個 round 裡有：
      - won_score, lost_score
      - total_won_score, total_lost_score
      - field_goals_made, field_goals_attempted, ...
    我們用「最後一節」的資料（最大 round 編號），把 total_xxx 當作全場數據。
    """
    if not isinstance(stats_json, dict):
        # 有些比賽可能回傳 [] 或其他格式，先跳過
        return []

    results = []

    for side in ("home_team", "away_team"):
        team_root = stats_json.get(side)
        if not team_root:
            continue

        team_id = team_root.get("id")
        team_name = team_root.get("name")

        teams_part = team_root.get("teams") or {}
        rounds_dict = teams_part.get("rounds") or {}

        if not rounds_dict:
            # 沒有分節資料，跳過這隊
            continue

        # rounds_dict 的 key 可能是 "1", "2", ... 取最大那個當成「全場」累積
        try:
            last_round_key = max(rounds_dict.keys(), key=lambda k: int(k))
            total_stats = rounds_dict[last_round_key]
        except Exception:
            # key 不是數字就整包放棄
            continue

        # 從 total_stats 抓出我們關心的欄位（沒有就給 None）
        def g(key):
            return total_stats.get(key)

        row = {
            "game_id": game_id,
            "team_side": "home" if side == "home_team" else "away",
            "team_id": team_id,
            "team_name": team_name,

            # 比數：total_won_score / total_lost_score
            "points_for": g("total_won_score"),
            "points_against": g("total_lost_score"),

            # 投籃相關
            "fgm": g("field_goals_made"),
            "fga": g("field_goals_attempted"),
            "fg_pct": g("field_goals_percentage"),

            "two_pm": g("two_pointers_made"),
            "two_pa": g("two_pointers_attempted"),
            "two_pct": g("two_pointers_percentage"),

            "three_pm": g("three_pointers_made"),
            "three_pa": g("three_pointers_attempted"),
            "three_pct": g("three_pointers_percentage"),

            "ftm": g("free_throws_made"),
            "fta": g("free_throws_attempted"),
            "ft_pct": g("free_throws_percentage"),

            # 籃板、助攻、失誤等
            "reb": g("rebounds"),
            "oreb": g("offensive_rebounds"),
            "dreb": g("defensive_rebounds"),
            "ast": g("assists"),
            "stl": g("steals"),
            "blk": g("blocks"),
            "tov": g("turnovers"),

            # 其他進階用數據
            "pf": g("personal_fouls"),
            "points_in_paint": g("points_in_paint"),
            "second_chance_points": g("second_chance_points"),
            "fast_break_points": g("fast_break_points"),
        }

        results.append(row)

    return results


def crawl_all_team_stats():
    """對所有比賽抓 stats，產生 team_stats.json"""
    games = load_games()
    if not games:
        return

    all_rows = []
    total_games = len(games)

    for idx, g in enumerate(games, start=1):
        game_id = g["id"]
        print(f"[{idx}/{total_games}] 抓取比賽 {game_id} 的隊伍 stats...")

        url = GAME_STATS_URL.format(game_id=game_id)
        try:
            stats_json = http_get_json(url)
        except Exception as e:
            print(f"  ⚠ 抓取比賽 {game_id} 失敗：{e}")
            continue

        rows = extract_team_totals(game_id, stats_json)
        print(f"  取得 {len(rows)} 筆隊伍數據")
        all_rows.extend(rows)

        # 禮貌一點，避免對 API 太兇
        time.sleep(0.2)

    out_path = Path("data/team_stats.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"\n共彙整 {len(all_rows)} 筆隊伍數據，已寫入 {out_path}")


# -------- 抓聯盟球員清單 players_master --------

def crawl_division_players():
    """
    呼叫 /api/divisions/9/players，存成 data/players_master.json。
    """
    print("抓取 division 9 的球員清單...")
    data = http_get_json(DIVISION_PLAYERS_URL)

    out_path = Path("data/players_master.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已將球員清單寫入 {out_path}")


def main():
    # 1. 抓所有比賽的隊伍總數據
    crawl_all_team_stats()

    # 2. 抓聯盟球員清單（先有 roster，日後如果找到球員 stats API 可 join）
    crawl_division_players()


if __name__ == "__main__":
    main()
