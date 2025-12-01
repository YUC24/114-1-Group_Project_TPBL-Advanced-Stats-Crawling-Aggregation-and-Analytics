import requests
import json
from pathlib import Path

API_URL = "https://api.tpbl.basketball/api/games/stats/players?division_id=9"
OUTPUT = Path("data/player_stats_raw.json")

def fetch_player_stats():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print("向 TPBL API 抓取球員場均 Stats 中...")
    r = requests.get(API_URL, headers=headers, timeout=10)
    r.raise_for_status()

    data = r.json()
    print(f"共抓取 {len(data)} 位球員的場均資料")

    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已寫入 {OUTPUT}")

if __name__ == "__main__":
    fetch_player_stats()
