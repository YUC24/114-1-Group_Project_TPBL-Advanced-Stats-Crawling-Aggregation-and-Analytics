# schedule_viewer.py
# 功能：讀取 data/games.json，提供簡單的賽程查詢（依日期、依隊伍）

import json
from pathlib import Path


DATA_PATH = Path("data/games.json")


def load_games():
    """從 data/games.json 載入全部比賽資料（list of dict）"""
    if not DATA_PATH.exists():
        print("找不到 data/games.json，請先執行 tpbl_crawler.py 抓資料。")
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        games = json.load(f)

    # 保險起見再依日期、時間排序一次
    games.sort(key=lambda x: (x.get("date"), x.get("time")))
    return games


def show_all_games(games):
    """列出所有比賽（依日期排序）"""
    print("\n=== 全部賽程 ===")
    for g in games:
        date = g.get("date") or "????-??-??"
        time = g.get("time") or "??:??:??"
        home = g.get("home_team_name")
        away = g.get("away_team_name")
        venue = g.get("venue") or ""
        status = g.get("status")

        home_score = g.get("home_score")
        away_score = g.get("away_score")

        if home_score is not None and away_score is not None:
            score_text = f"{away_score} @ {home_score}"
        else:
            score_text = "尚未開打"

        print(
            f"{date} {time} | "
            f"{away} {score_text} {home} | {venue} | 狀態：{status} | ID={g['id']}"
        )
    print()


def show_games_by_team(games):
    """依隊伍關鍵字查詢賽程"""
    keyword = input("請輸入隊名關鍵字（例如：國王、夢想家）：").strip()
    if not keyword:
        print("關鍵字是空的，返回主選單。\n")
        return

    keyword = keyword.lower()

    filtered = []
    for g in games:
        home = g.get("home_team_name") or ""
        away = g.get("away_team_name") or ""
        if keyword in home.lower() or keyword in away.lower():
            filtered.append(g)

    if not filtered:
        print(f"找不到包含「{keyword}」的隊伍賽程。\n")
        return

    print(f"\n=== 含有「{keyword}」的賽程，共 {len(filtered)} 場 ===")
    for g in filtered:
        date = g.get("date") or "????-??-??"
        time = g.get("time") or "??:??:??"
        home = g.get("home_team_name")
        away = g.get("away_team_name")
        venue = g.get("venue") or ""
        status = g.get("status")

        home_score = g.get("home_score")
        away_score = g.get("away_score")

        if home_score is not None and away_score is not None:
            score_text = f"{away_score} @ {home_score}"
        else:
            score_text = "尚未開打"

        print(
            f"{date} {time} | "
            f"{away} {score_text} {home} | {venue} | 狀態：{status} | ID={g['id']}"
        )
    print()


def main():
    games = load_games()
    if not games:
        return

    while True:
        print("========== TPBL 賽程查詢 ==========")
        print("1. 查看全部賽程")
        print("2. 依隊伍關鍵字查詢賽程")
        print("0. 離開")
        choice = input("請輸入選項：").strip()

        if choice == "1":
            show_all_games(games)
        elif choice == "2":
            show_games_by_team(games)
        elif choice == "0":
            print("再見～")
            break
        else:
            print("無效選項，請重新輸入。\n")


if __name__ == "__main__":
    main()
