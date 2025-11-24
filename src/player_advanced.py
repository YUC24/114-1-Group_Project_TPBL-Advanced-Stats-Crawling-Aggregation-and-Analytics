import json
from pathlib import Path
from collections import defaultdict

# ✅ 正確路徑統一寫這裡
RAW_PATH = Path("data/player_stats_raw.json")   # ← 注意這裡是 player_stats_raw
OUTPUT_PATH = Path("data/player_advanced.json")


def safe_div(n, d):
    """安全除法，避免除以 0，回傳 None。"""
    return n / d if d else None


def load_raw_players():
    with RAW_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"讀入 {len(data)} 筆球員 raw stats")
    return data

def compute_team_usage_totals(raw_players):
    """
    對每隊計算簡化版 usage 總量：
    usage_base = FGA + 0.44*FTA + TOV
    這裡用的是「場均數據」（average_stats），
    之後球員的 usage_share = 個人 usage_base / 全隊 usage_base
    """
    team_usage = defaultdict(float)

    for row in raw_players:
        team = row.get("team", {})
        team_id = team.get("id")

        stats_avg = row.get("average_stats", {}) or {}

        # 這些 key 全部來自你貼的 JSON 裡的 average_stats
        fga = float(stats_avg.get("field_goals_attempted", 0.0))
        fta = float(stats_avg.get("free_throws_attempted", 0.0))
        tov = float(stats_avg.get("turnovers", 0.0))

        usage_base = fga + 0.44 * fta + tov
        if team_id is not None:
            team_usage[team_id] += usage_base

    return team_usage


def pct_to_float(p):
    """
    把 "49.6" 這種百分比字串轉成 0.496
    如果是 None 或怪東西就回傳 None
    """
    if p is None:
        return None
    try:
        return float(p) / 100.0
    except:
        return None


def build_player_advanced(raw_players):
    team_usage_totals = compute_team_usage_totals(raw_players)
    result = []

    for row in raw_players:
        player = row.get("player", {}) or {}
        team = row.get("team", {}) or {}
        stats_avg = row.get("average_stats", {}) or {}
        stats_acc = row.get("accumulated_stats", {}) or {}
        pct = row.get("percentage_stats", {}) or {}

        player_id = player.get("id")
        player_name = player.get("name", "N/A")
        team_id = team.get("id")
        team_name = team.get("name", "N/A")

        games = row.get("game_count", 0)

        # ===== 場均數據（全部從 average_stats 抓） =====
        pts = float(stats_avg.get("score", 0.0))
        reb = float(stats_avg.get("rebounds", 0.0))
        ast = float(stats_avg.get("assists", 0.0))
        stl = float(stats_avg.get("steals", 0.0))
        blk = float(stats_avg.get("blocks", 0.0))
        tov = float(stats_avg.get("turnovers", 0.0))

        fgm = float(stats_avg.get("field_goals_made", 0.0))
        fga = float(stats_avg.get("field_goals_attempted", 0.0))

        three_pm = float(stats_avg.get("three_pointers_made", 0.0))
        three_pa = float(stats_avg.get("three_pointers_attempted", 0.0))

        ftm = float(stats_avg.get("free_throws_made", 0.0))
        fta = float(stats_avg.get("free_throws_attempted", 0.0))

        # time_on_court 是毫秒? 這裡假設是「秒」，所以 /60 變成每場分鐘數
        time_on_court = float(stats_avg.get("time_on_court", 0.0))
        min_per_game = time_on_court / 60.0

        # 官方給的效率值（場均）
        eff_raw = float(stats_avg.get("efficiency", 0.0))

        # ===== 百分比（官方已算好，我們直接轉成 0.x） =====
        efg = pct_to_float(pct.get("effective_field_goals_percentage"))
        ts = pct_to_float(pct.get("true_shooting_percentage"))
        tov_pct_official = pct_to_float(pct.get("turnovers_percentage"))

        # ===== 我們自算的其他進階數據 =====

        # FTr（罰球率） = FTA / FGA
        ft_rate = safe_div(fta, fga)

        # 3PAr（三分出手比例） = 3PA / FGA
        three_par = safe_div(three_pa, fga)

        # 簡化版 Usage：個人使用回合 / 全隊使用回合
        usage_base = fga + 0.44 * fta + tov
        team_total_usage = team_usage_totals.get(team_id, 0.0)
        usage_share = safe_div(usage_base, team_total_usage)

        # PPP（Points Per Possession，個人佔用回合的得分）
        ppp = safe_div(pts, usage_base)

        # 簡化版 PER / EFF：參考常見 EFF 算法
        per_simple = (
            pts + reb + ast + stl + blk
            - (fga - fgm)
            - (fta - ftm)
            - tov
        )

        result.append({
            "player_id": player_id,
            "player_name": player_name,
            "team_id": team_id,
            "team_name": team_name,
            "games": games,
            "min_pg": min_per_game,

            # 場均 boxscore
            "pts": pts,
            "reb": reb,
            "ast": ast,
            "stl": stl,
            "blk": blk,
            "tov": tov,
            "fgm": fgm,
            "fga": fga,
            "three_pm": three_pm,
            "three_pa": three_pa,
            "ftm": ftm,
            "fta": fta,
            "eff_raw": eff_raw,

            # 官方給的進階命中率
            "efg_official": efg,
            "ts_official": ts,
            "tov_pct_official": tov_pct_official,

            # 我們自己算的進階數據
            "ft_rate": ft_rate,
            "three_par": three_par,
            "usage_share": usage_share,
            "ppp": ppp,
            "per_simple": per_simple,
        })

    return result

def fmt(v, digits=3):
    """安全格式化：None → '--'，其他數字照正常格式輸出"""
    if v is None:
        return "--"
    try:
        return f"{v:.{digits}f}"
    except:
        return str(v)

def fmt(v, d=3):
    if v is None:
        return "--"
    try:
        return f"{v:.{d}f}"
    except:
        return str(v)


def main():
    # 先確認 raw 檔案在不在
    if not RAW_PATH.exists():
        print(f"❌ 找不到 {RAW_PATH}，請先跑 player_stats_crawler.py 抓球員資料！")
        return

    # 讀入 raw stats
    with RAW_PATH.open("r", encoding="utf-8") as f:
        raw_players = json.load(f)
    print(f"讀入 {len(raw_players)} 筆球員 raw stats")
        
    # 算進階數據
    advanced = build_player_advanced(raw_players)

    # 用官方 TS 排序（高→低）
    advanced.sort(
        key=lambda p: (p.get("ts_official") is None, -(p.get("ts_official") or 0))
    )

    # 存成 JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(advanced, f, ensure_ascii=False, indent=2)

    print(f"已將球員進階數據寫入 {OUTPUT_PATH}\n")
    print("全部球員（依 TS% 排序）：")
    for p in advanced:
        print(
            f'{p["player_name"]} ({p["team_name"]}) - '
            f'PTS {fmt(p["pts"],1)}, '
            f'TS {fmt(p.get("ts_official"))}, '
            f'eFG {fmt(p.get("efg_official"))}, '
            f'USG_share {fmt(p.get("usage_share"))}'
        )



if __name__ == "__main__":
    main()
