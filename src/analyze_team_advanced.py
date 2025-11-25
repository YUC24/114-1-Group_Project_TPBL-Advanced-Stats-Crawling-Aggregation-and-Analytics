# analyze_team_advanced.py
# 功能：
# 讀取 data/team_stats.json，將每支球隊在所有已完成比賽中的數據加總，
# 並計算一些進階指標（eFG%、TS%、OffRtg、DefRtg），
# 存成 data/team_advanced.json，並在終端機印出一個排行榜。
#好耶

import json
from pathlib import Path
from math import isnan

TEAM_STATS_PATH = Path("data/team_stats.jsons")
OUTPUT_PATH = Path("data/team_advanced.json")


def load_team_stats():
    if not TEAM_STATS_PATH.exists():
        print("找不到 data/team_stats.json，請先跑 stats_crawler.py")
        return []

    with TEAM_STATS_PATH.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    return rows


def safe_div(num, den):
    if den is None or den == 0:
        return None
    return num / den


def compute_advanced():
    rows = load_team_stats()
    if not rows:
        return

    # 聚合每隊的累計數據（目前 rows 一筆 = 一場比賽的某隊數據）
    teams = {}  # team_id -> dict

    for r in rows:
        team_id = r["team_id"]
        team = teams.setdefault(
            team_id,
            {
                "team_id": team_id,
                "team_name": r["team_name"],
                "games": 0,
                "points_for": 0,
                "points_against": 0,
                "fgm": 0,
                "fga": 0,
                "three_pm": 0,
                "three_pa": 0,
                "ftm": 0,
                "fta": 0,
                "oreb": 0,
                "tov": 0,
                "possessions_for": 0.0,
                "possessions_against": 0.0,
            },
        )

        # 有些未完成比賽可能是 None，小心處理
        pf = r.get("points_for") or 0
        pa = r.get("points_against") or 0
        fgm = r.get("fgm") or 0
        fga = r.get("fga") or 0
        three_pm = r.get("three_pm") or 0
        three_pa = r.get("three_pa") or 0
        ftm = r.get("ftm") or 0
        fta = r.get("fta") or 0
        oreb = r.get("oreb") or 0
        tov = r.get("tov") or 0

        # 估計進攻回合數 (常見籃球公式)
        # possessions_raw ≈ FGA + 0.44 * FTA − OREB + TOV
        poss_for_raw = fga + 0.44 * fta - oreb + tov

        team["games"] += 1
        team["points_for"] += pf
        team["points_against"] += pa
        team["fgm"] += fgm
        team["fga"] += fga
        team["three_pm"] += three_pm
        team["three_pa"] += three_pa
        team["ftm"] += ftm
        team["fta"] += fta
        team["oreb"] += oreb
        team["tov"] += tov
        team["possessions_for"] += poss_for_raw

    # 先假設：長期下我方回合 ≈ 對手回合
    for t in teams.values():
        t["possessions_against"] = t["possessions_for"]

    # === 🔧 校正回合數：讓聯盟平均 Pace ≈ 90 回合/場 ===
    raw_paces = []
    for t in teams.values():
        if t["games"] > 0 and t["possessions_for"] > 0:
            raw_paces.append(t["possessions_for"] / t["games"])

    if raw_paces:
        league_raw_pace = sum(raw_paces) / len(raw_paces)
    else:
        league_raw_pace = 1.0  # 避免除以 0

    # 目標：聯盟平均 Pace ≈ 90（NBA / FIBA 常見區間）
    TARGET_PACE = 90.0
    pace_scale = TARGET_PACE / league_raw_pace if league_raw_pace > 0 else 1.0

    # 計算進階指標
    result = []
    for t in teams.values():
        games = t["games"] or 1

        fgm = t["fgm"]
        fga = t["fga"]
        three_pm = t["three_pm"]
        ftm = t["ftm"]
        fta = t["fta"]
        pf = t["points_for"]
        pa = t["points_against"]

        poss_for_raw = t["possessions_for"]
        poss_against_raw = t["possessions_against"]

        # 套用 Pace 校正係數（把 poss 拉回合理尺度）
        poss_for = poss_for_raw * pace_scale
        poss_against = poss_against_raw * pace_scale

        # eFG% = (FGM + 0.5 * 3PM) / FGA
        efg = safe_div(fgm + 0.5 * three_pm, fga)

        # TS% = PTS / (2 * (FGA + 0.44 * FTA))
        ts = safe_div(pf, 2 * (fga + 0.44 * fta))

        # OffRtg = 每 100 回合得分（已校正 possessions）
        off_rtg = safe_div(pf * 100, poss_for)

        # DefRtg = 每 100 回合失分
        def_rtg = safe_div(pa * 100, poss_against)

        # Pace = 每場平均回合數（已校正）
        pace = safe_div(poss_for, games)

        # TOV% = TOV / possessions
        tov_pct = safe_div(t["tov"], poss_for)

        # FT Rate = FTA / FGA
        ft_rate = safe_div(fta, fga)

        summary = {
            "team_id": t["team_id"],
            "team_name": t["team_name"],
            "games": games,
            "points_for_total": pf,
            "points_against_total": pa,
            "points_for_avg": pf / games,
            "points_against_avg": pa / games,
            "efg": efg,
            "ts": ts,
            "off_rtg": off_rtg,
            "def_rtg": def_rtg,
            "pace": pace,
            "tov_pct": tov_pct,
            "ft_rate": ft_rate,
        }
        result.append(summary)

    # 依照 OffRtg 排序，看哪隊進攻效率最強
    result.sort(key=lambda x: (x["off_rtg"] or 0), reverse=True)

    # 存成 JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 在終端機印出簡單排行榜（含 OffRtg、DefRtg、Pace、TOV%、FT Rate）
    print(f"已將進階數據寫入 {OUTPUT_PATH}\n")
    print("=== TPBL 隊伍進階數據排行榜（依 OffRtg 排序） ===")
    print("{:<10} {:<12} {:>5} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8}".format(
        "TeamID", "Team", "G",
        "OffRtg", "DefRtg", "Pace", "eFG%", "TOV%", "FTR"
    ))

    for t in result:
        print("{:<10} {:<12} {:>5} {:>8.1f} {:>8.1f} {:>8.1f} {:>8.3f} {:>8.3f} {:>8.3f}".format(
            t["team_id"],
            t["team_name"][:10],
            t["games"],
            t["off_rtg"] or 0,
            t["def_rtg"] or 0,
            t["pace"] or 0,
            t["efg"] or 0,
            t["tov_pct"] or 0,
            t["ft_rate"] or 0,
        ))



if __name__ == "__main__":
    compute_advanced()
