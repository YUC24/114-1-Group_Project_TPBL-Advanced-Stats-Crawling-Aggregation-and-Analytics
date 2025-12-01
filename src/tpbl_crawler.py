# tpbl_crawler.py
# 功能：從 TPBL 官方 API 抓「整季所有比賽」，整理後存成 data/games.json

import requests
import json
from pathlib import Path


# 這是你剛剛找到的 API
API_URL = "https://api.tpbl.basketball/api/seasons/2/games"


def fetch_games_json():
    """
    向 TPBL 的 games API 發送請求，取得原始 JSON 資料。
    回傳值是一個 list，每個元素就是一場比賽的 dict。
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    resp = requests.get(API_URL, headers=headers, timeout=10)
    resp.raise_for_status()  # 如果 4xx/5xx 會直接丟錯
    return resp.json()       # 直接變成 Python 的 list/dict


def normalize_games(raw_games):
    games = []

    for g in raw_games:
        home = g["home_team"]
        away = g["away_team"]

        # 可能不存在（未開打），用 get() 取值，若沒有則回傳 None
        home_won = home.get("won_score")
        home_lost = home.get("lost_score")
        away_won = away.get("won_score")
        away_lost = away.get("lost_score")

        # 分數處理 — 若沒有資料（未開打）就設為 None
        def pick_score(won, lost):
            if won is None and lost is None:
                return None
            # 有些 API 在比分未出來時可能傳 0 或 null
            if won is None:
                return lost
            if lost is None:
                return won
            return max(won, lost)

        home_score = pick_score(home_won, home_lost)
        away_score = pick_score(away_won, away_lost)

        game_item = {
            "id": g["id"],
            "code": g.get("code"),
            "date": g.get("game_date"),
            "time": g.get("game_time"),
            "datetime": g.get("gamed_at"),
            "venue": g.get("venue"),
            "status": g.get("status"),  # COMPLETED / UPCOMING
            "is_live": g.get("is_live"),
            "division_id": g.get("division_id"),

            "home_team_id": home["id"],
            "home_team_name": home["name"],
            "home_score": home_score,

            "away_team_id": away["id"],
            "away_team_name": away["name"],
            "away_score": away_score,
        }

        games.append(game_item)

    # 依照日期、時間排序（未來 + 已完成都能排序）
    games.sort(key=lambda x: (x["date"], x["time"]))

    return games


def save_games_to_json(games, path="data/tpbl_crawler_raw.json"):
    """
    把整理好的 games list 存成 JSON 檔案。
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with path_obj.open("w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)


def main():
    print("向 TPBL API 抓取賽程資料中...")
    raw_games = fetch_games_json()
    print(f"原始資料共 {len(raw_games)} 場比賽")

    games = normalize_games(raw_games)

    # 先在終端機印出前 5 場看一下，確認格式
    print("\n前 5 場比賽：")
    for g in games[:5]:
        print(
            f"{g['date']} {g['time']} | "
            f"{g['away_team_name']} {g['away_score']} @ "
            f"{g['home_team_name']} {g['home_score']} | "
            f"{g['venue']} (ID={g['id']})"
        )

    save_games_to_json(games)
    print("\n已儲存整理後的賽程到 data/tpbl_crawler_raw.json")


if __name__ == "__main__":
    main()
