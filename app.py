import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import streamlit as st
import plotly.express as px

# ===== 路徑設定 =====
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEAM_FILE = DATA_DIR / "team_advanced.json"
PLAYER_FILE = DATA_DIR / "player_advanced.json"
SCHEDULE_FILE = DATA_DIR / "schedule_raw.json"  # 賽程（沒有比分）
SCORE_FILE = DATA_DIR / "tpbl_crawler_raw.json"  # 比分（有 home_score / away_score）
GAMES_FILE = DATA_DIR / "tpbl_crawler_raw.json"


@st.cache_data
def load_team_advanced():
    """讀取球隊進階數據 team_advanced.json"""
    if not TEAM_ADV_PATH.exists():
        return pd.DataFrame()
    with TEAM_ADV_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


@st.cache_data
def load_games():
    """讀取賽程／比分資料 games.json，用來計算互打戰績"""
    if not GAMES_PATH.exists():
        return pd.DataFrame()
    with GAMES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


@st.cache_data
def load_json_to_df(path: Path) -> pd.DataFrame:
    """讀取 JSON 檔並轉成 DataFrame，若找不到檔案就回傳空表。"""
    if not path.exists():
        return pd.DataFrame()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return pd.DataFrame(data)


def load_json_to_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


# ========================
#        首頁
# ========================
def show_home_page():
    # ---- 全域深色 + 卡片樣式 CSS ----
    st.markdown(
        """
        <style>
        /* 整體背景再暗一點，偏 ESPN / NBA Stats 風格 */
        .main {
            background-color: #050814;
        }
        /* 卡片外框 */
        .tpbl-card {
            background: #111827;
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.35);
            border: 1px solid rgba(148,163,184,0.25);
        }
        .tpbl-card h3 {
            font-size: 1.0rem;
            color: #e5e7eb;
            margin-bottom: 6px;
        }
        .tpbl-metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #f97316;  /* 橘色重點 */
        }
        .tpbl-metric-sub {
            font-size: 0.8rem;
            color: #9ca3af;
        }
        .tpbl-section-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #f9fafb;
            margin-top: 4px;
            margin-bottom: 6px;
        }
        .tpbl-section-caption {
            font-size: 0.85rem;
            color: #9ca3af;
            margin-bottom: 12px;
        }
        .tpbl-nav-card {
            background: #020617;
            border-radius: 14px;
            padding: 12px 14px;
            border: 1px solid rgba(148,163,184,0.4);
        }
        .tpbl-nav-title {
            font-size: 1.0rem;
            color: #e5e7eb;
            margin-bottom: 4px;
        }
        .tpbl-nav-desc {
            font-size: 0.85rem;
            color: #9ca3af;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---- Hero 區塊 ----
    st.markdown(
        "<div class='tpbl-section-caption'>League Overview · Team Ratings · Player Usage & Efficiency</div>",
        unsafe_allow_html=True,
    )

    # 可以未來支援多季
    col_title, col_season = st.columns([3, 1])
    with col_season:
        st.selectbox("Season", ["2025-26"], index=0)

    # ---- 讀取球隊進階數據 ----
    team_df = load_json_to_df(TEAM_FILE)
    player_df_raw = load_json_to_df(PLAYER_FILE)  # 提前讀取球員數據

    if team_df.empty:
        st.warning("找不到 data/team_advanced.json，請先執行球隊進階分析程式。")
        return

    for col in ["off_rtg", "def_rtg", "pace", "ts", "efg"]:
        if col in team_df.columns:
            team_df[col] = pd.to_numeric(team_df[col], errors="coerce")

    # ---- 聯盟 Summary 卡片列 ----
    league_avg_off = team_df["off_rtg"].mean()
    league_avg_def = team_df["def_rtg"].mean()
    league_avg_pace = team_df["pace"].mean()

    best_off = team_df.loc[team_df["off_rtg"].idxmax()]
    best_def = team_df.loc[team_df["def_rtg"].idxmin()]
    fastest = team_df.loc[team_df["pace"].idxmax()]

    c1, c2, c3 = st.columns(3)
    with c1:
        # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
        st.markdown("<h3>League OffRtg</h3>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='tpbl-metric-value'>{league_avg_off:.1f}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='tpbl-metric-sub'>最佳進攻：{best_off['team_name']} ({best_off['off_rtg']:.1f})</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
        st.markdown("<h3>League DefRtg</h3>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='tpbl-metric-value'>{league_avg_def:.1f}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='tpbl-metric-sub'>最佳防守：{best_def['team_name']} ({best_def['def_rtg']:.1f})</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
        st.markdown("<h3>League Pace</h3>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='tpbl-metric-value'>{league_avg_pace:.1f}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='tpbl-metric-sub'>最快節奏：{fastest['team_name']} ({fastest['pace']:.1f})</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ---- 核心圖表區：左 OffRtg/DefRtg 四象限；右 Usage vs TS% ----
    st.markdown(
        "<div class='tpbl-section-title'>Key Visuals</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='tpbl-section-caption'>進攻 vs 防守、球員 Usage vs TS% 一眼看出聯盟風格。</div>",
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns(2)

    # ==========================================================
    # 🔴 左：OffRtg vs DefRtg 四象限 (Altair)
    # ==========================================================
    with left_col:
        # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
        st.markdown("#### OffRtg vs DefRtg 四象限", unsafe_allow_html=True)

        quad_df = team_df.dropna(subset=["off_rtg", "def_rtg", "team_name"]).copy()

        if not quad_df.empty:
            mean_off = quad_df["off_rtg"].mean()
            mean_def = quad_df["def_rtg"].mean()

            # 標記象限
            def determine_quadrant(row):
                is_good_off = row["off_rtg"] >= mean_off
                is_good_def = row["def_rtg"] < mean_def
                if is_good_off and is_good_def:
                    return "II. 攻守兼備 (強隊)"
                elif is_good_off and not is_good_def:
                    return "I. 攻強守弱"
                elif not is_good_off and is_good_def:
                    return "IV. 守強攻弱"
                else:
                    return "III. 攻守皆弱"

            quad_df["Quadrant"] = quad_df.apply(determine_quadrant, axis=1)

            # 繪圖邏輯：使用 Altair
            import altair as alt

            base = alt.Chart(quad_df).encode(
                # X 軸：DefRtg (越左越好，需反轉)
                x=alt.X(
                    "def_rtg:Q",
                    title="DefRtg (防守效率值, 越左越好)",
                    scale=alt.Scale(reverse=True),
                ),
                # Y 軸：OffRtg (越高越好)
                y=alt.Y("off_rtg:Q", title="OffRtg (進攻效率值, 越高越好)"),
                tooltip=[
                    "team_name",
                    alt.Tooltip("off_rtg", format=".2f"),
                    alt.Tooltip("def_rtg", format=".2f"),
                    "Quadrant",
                ],
            )

            # 散點圖層
            points = base.mark_circle(size=150, opacity=1).encode(
                color=alt.Color("Quadrant:N", legend=alt.Legend(title="攻守象限")),
            )

            # 文本標籤層
            text = base.mark_text(align="left", dx=8, dy=-5).encode(
                text=alt.Text("team_name:N"), color=alt.value("lightgray")
            )

            # 參考線層 (平均 OffRtg - 水平線)
            off_line = (
                alt.Chart(pd.DataFrame({"mean_off": [mean_off]}))
                .mark_rule(color="green", strokeDash=[3, 3])
                .encode(
                    y=alt.Y("mean_off", axis=None),
                    tooltip=[
                        alt.Tooltip("mean_off", format=".2f", title="平均 OffRtg")
                    ],
                )
            )

            # 參考線層 (平均 DefRtg - 垂直線)
            def_line = (
                alt.Chart(pd.DataFrame({"mean_def": [mean_def]}))
                .mark_rule(color="red", strokeDash=[3, 3])
                .encode(
                    x=alt.X("mean_def", axis=None),
                    tooltip=[
                        alt.Tooltip("mean_def", format=".2f", title="平均 DefRtg")
                    ],
                )
            )

            chart = (points + text + off_line + def_line).interactive()

            st.altair_chart(chart, use_container_width=True)

        else:
            st.info("OffRtg / DefRtg 資料不足。")

        st.markdown(
            "<div class='tpbl-metric-sub'>左上角：攻守兼備的強隊；右上：火力旺但防守較弱；左下：防守為主；右下：攻防都待加強。</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================================
    # 🔵 右：Usage vs TS%（球員）(Altair)
    # ==========================================================
    with right_col:
        # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
        st.markdown("#### Usage vs TS%（高用球權球員）", unsafe_allow_html=True)

        player_df = player_df_raw.copy()

        if not player_df.empty and {"usage_share", "ts_official"}.issubset(
            player_df.columns
        ):
            for col in ["usage_share", "ts_official", "minutes"]:
                if col in player_df.columns:
                    player_df[col] = pd.to_numeric(player_df[col], errors="coerce")

            # 篩掉出場時間太少的
            if "minutes" in player_df.columns:
                filtered = player_df[player_df["minutes"] >= 80].copy()
            else:
                filtered = player_df.copy()

            filtered = filtered.dropna(subset=["usage_share", "ts_official"])

            if not filtered.empty:
                filtered["usage_pct"] = filtered["usage_share"] * 100
                filtered["ts_pct"] = filtered["ts_official"] * 100

                # 繪圖邏輯：使用 Altair
                import altair as alt

                base = (
                    alt.Chart(filtered)
                    .encode(
                        x=alt.X("usage_pct:Q", axis=alt.Axis(title="Usage Share (%)")),
                        y=alt.Y("ts_pct:Q", axis=alt.Axis(title="TS% (%)")),
                        tooltip=[
                            alt.Tooltip("player_name:N", title="Player"),
                            alt.Tooltip("team_name:N", title="Team"),
                            alt.Tooltip("usage_pct:Q", title="Usage (%)", format=".1f"),
                            alt.Tooltip("ts_pct:Q", title="TS% (%)", format=".1f"),
                        ],
                    )
                    .properties(
                        # Altair 不直接支持 Plotly 的 margin 設置，但會自動適應
                    )
                )

                # 散點圖層
                points = base.mark_circle(size=70, opacity=0.8).encode(
                    color=alt.Color("team_name:N", title="Team")
                )

                # 文本標籤層 (只顯示 Usage 最高的前幾名)
                top_players = filtered.sort_values("usage_pct", ascending=False).head(5)
                text = (
                    alt.Chart(top_players)
                    .mark_text(align="left", dx=5, dy=0)
                    .encode(
                        x="usage_pct:Q",
                        y="ts_pct:Q",
                        text=alt.Text("player_name:N"),
                        color=alt.value("white"),
                    )
                )

                st.altair_chart((points + text).interactive(), use_container_width=True)

            else:
                st.info("目前沒有符合條件的球員可以畫 Usage vs TS%。")
        else:
            st.info(
                "找不到 player_advanced.json 或缺少 usage_share / ts_official 欄位。"
            )

        st.markdown(
            "<div class='tpbl-metric-sub'>右上角：高 Usage 且高 TS% 的超級火力點；左下角：用球權低、效率也較低的角色球員。</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ... (後續導航和賽程邏輯保持不變)

    # ---- 最近賽果 & 即將開打 ----
    # st.markdown(
    #     "<div class='tpbl-section-title'>最近賽事 & 即將開打</div>",
    #     unsafe_allow_html=True,
    # )

    games_df = load_json_to_df(SCHEDULE_FILE)
    if not games_df.empty:
        if "datetime" in games_df.columns:
            games_df["datetime"] = pd.to_datetime(games_df["datetime"], errors="coerce")
            games_df = games_df.sort_values("datetime")

        completed = games_df[games_df.get("status", "") == "COMPLETED"].copy()
        upcoming = games_df[games_df.get("status", "") != "COMPLETED"].copy()

        c1, c2 = st.columns(2)
        with c1:
            # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
            st.markdown("#### 最近已完成", unsafe_allow_html=True)
            if not completed.empty:
                last_games = completed.sort_values(
                    "datetime" if "datetime" in completed.columns else "date",
                    ascending=False,
                ).head(5)
                cols = [
                    c
                    for c in [
                        "date",
                        "home_team_name",
                        "home_score",
                        "away_team_name",
                        "away_score",
                        "venue",
                    ]
                    if c in last_games.columns
                ]
                st.dataframe(
                    last_games[cols], use_container_width=True, hide_index=True
                )
            else:
                st.caption("還沒有已完成的比賽。")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            # st.markdown("<div class='tpbl-card'>", unsafe_allow_html=True)
            st.markdown("#### 即將開打", unsafe_allow_html=True)
            if not upcoming.empty:
                next_games = upcoming.head(5)
                cols = [
                    c
                    for c in [
                        "date",
                        "time",
                        "home_team_name",
                        "away_team_name",
                        "venue",
                    ]
                    if c in next_games.columns
                ]
                st.dataframe(
                    next_games[cols], use_container_width=True, hide_index=True
                )
            else:
                st.caption("目前沒有即將開打的賽事（或還沒更新）。")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("目前沒有賽程資料（data/games.json）。")

    st.markdown("---")

    # ---- 快速導覽卡片 ----
    st.markdown(
        "<div class='tpbl-section-title'>Quick Navigation</div>",
        unsafe_allow_html=True,
    )

    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        # st.markdown("<div class='tpbl-nav-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='tpbl-nav-title'>球隊進階數據</div>", unsafe_allow_html=True
        )
        st.markdown(
            "<div class='tpbl-nav-desc'>查看各隊 Off/Def Rating、四要素、互打勝負 Heatmap。</div>",
            unsafe_allow_html=True,
        )
        st.markdown("從左側選單選「球隊進階數據」。")
        st.markdown("</div>", unsafe_allow_html=True)

    with nav2:
        # st.markdown("<div class='tpbl-nav-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='tpbl-nav-title'>球員進階數據</div>", unsafe_allow_html=True
        )
        st.markdown(
            "<div class='tpbl-nav-desc'>TS%、Usage、進階效率指標、雷達圖。</div>",
            unsafe_allow_html=True,
        )
        st.markdown("從左側選單選「球員進階數據」。")
        st.markdown("</div>", unsafe_allow_html=True)

    with nav3:
        # st.markdown("<div class='tpbl-nav-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='tpbl-nav-title'>賽程資訊</div>", unsafe_allow_html=True
        )
        st.markdown(
            "<div class='tpbl-nav-desc'>查詢賽程、比數、主客場與場館資訊。</div>",
            unsafe_allow_html=True,
        )
        st.markdown("從左側選單選「賽程資訊」。")
        st.markdown("</div>", unsafe_allow_html=True)


# ========================
#       球隊頁面
# ========================

def show_team_page():
    st.markdown(
        """
        <style>
        /* 整體背景再暗一點，偏 ESPN / NBA Stats 風格 */
        .main {
            background-color: #050814;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.header("球隊進階數據 Team Advanced Stats")

    # 讀球隊進階數據
    df = load_json_to_df(TEAM_FILE)
    if df.empty:
        st.warning("找不到 data/team_advanced.json，請先跑一次分析程式再回來喔～")
        return

    # ====================
    #  排序與球隊 Summary
    # ====================
    st.subheader("排序方式")

    def is_sortable_column(series: pd.Series) -> bool:
        sample = series.dropna().head(20)
        if sample.empty:
            return True
        if all(isinstance(v, (dict, list)) for v in sample):
            return False
        return True

    valid_cols = [col for col in df.columns if is_sortable_column(df[col])]

    priority = [
        c for c in ["off_rtg", "def_rtg", "net_rtg", "games"] if c in valid_cols
    ]
    candidate_sort_cols = priority or valid_cols

    sort_column = st.selectbox("排序欄位 (Sort by)", candidate_sort_cols)
    ascending = st.checkbox(
        "由小到大排序 (Ascending)",
        value=False,
        key="team_sort_asc",
    )

    try:
        sorted_df = df.sort_values(by=sort_column, ascending=ascending)
    except TypeError:
        st.warning("這個欄位的資料型態無法排序，已改用原始順序顯示。")
        sorted_df = df

    team_col_name = "team_name" if "team_name" in df.columns else df.columns[0]
    team_names = sorted_df[team_col_name].unique().tolist()
    selected_team = st.selectbox("選擇球隊 (Select a team)", team_names)

    team_row = sorted_df[sorted_df[team_col_name] == selected_team].iloc[0]

    st.markdown("### 球隊 Summary")
    cols = st.columns(4)

    games = team_row.get("games", None)
    off_rtg = team_row.get("off_rtg", None)
    def_rtg = team_row.get("def_rtg", None)
    net_rtg = None
    if isinstance(off_rtg, (int, float)) and isinstance(def_rtg, (int, float)):
        net_rtg = off_rtg - def_rtg

    with cols[0]:
        if games is not None:
            st.metric("比賽數 (Games)", int(games))
    with cols[1]:
        if off_rtg is not None:
            st.metric("OffRtg", f"{off_rtg:.1f}")
    with cols[2]:
        if def_rtg is not None:
            st.metric("DefRtg", f"{def_rtg:.1f}")
    with cols[3]:
        if net_rtg is not None:
            st.metric("NetRtg", f"{net_rtg:.1f}")

    # ==========================================================
    # 📈 OffRtg vs DefRtg 四象限圖 - 改用 Altair
    # ==========================================================
    st.markdown("### OffRtg vs DefRtg 四象限圖 (攻守平衡)")

    need_cols = {"team_name", "off_rtg", "def_rtg"}
    if not need_cols.issubset(df.columns):
        st.info("目前資料缺少 team_name / off_rtg / def_rtg 欄位，暫時無法畫四象限圖。")
        return

    quad_df = df.copy()

    for col in ["off_rtg", "def_rtg"]:
        if col in quad_df.columns:
            quad_df[col] = pd.to_numeric(quad_df[col], errors="coerce")

    quad_df = quad_df.dropna(subset=["off_rtg", "def_rtg"])

    if quad_df.empty:
        st.info("目前沒有同時具有 OffRtg 和 DefRtg 的球隊資料。")
    else:
        # 計算聯盟平均值作為分隔線
        mean_off = quad_df["off_rtg"].mean()
        mean_def = quad_df["def_rtg"].mean()

        # 標記象限 (DefRtg 越低越好, OffRtg 越高越好)
        def determine_quadrant(row):
            is_good_off = row["off_rtg"] >= mean_off
            is_good_def = row["def_rtg"] < mean_def

            if is_good_off and is_good_def:
                return "II. 攻守兼備 (強隊)"
            elif is_good_off and not is_good_def:
                return "I. 攻強守弱"
            elif not is_good_off and is_good_def:
                return "IV. 守強攻弱"
            else:
                return "III. 攻守皆弱"

        quad_df["Quadrant"] = quad_df.apply(determine_quadrant, axis=1)

        # 繪圖邏輯：使用 Altair
        import altair as alt

        base = (
            alt.Chart(quad_df)
            .encode(
                # X 軸：DefRtg (防守效率，越左越好，需反轉)
                x=alt.X(
                    "def_rtg:Q",
                    title="DefRtg (防守效率值, 越左越好)",
                    scale=alt.Scale(reverse=True),
                ),
                # Y 軸：OffRtg (進攻效率，越高越好)
                y=alt.Y("off_rtg:Q", title="OffRtg (進攻效率值, 越高越好)"),
                tooltip=[
                    "team_name",
                    alt.Tooltip("off_rtg", format=".2f"),
                    alt.Tooltip("def_rtg", format=".2f"),
                    "Quadrant",
                ],
            )
            .properties(title="OffRtg vs DefRtg 四象限分析：左上角 = 攻守兼備強隊")
        )

        # 散點圖層
        points = base.mark_circle(size=100, opacity=0.8).encode(
            color=alt.Color("Quadrant:N", legend=alt.Legend(title="攻守象限")),
        )

        # 文本標籤層
        text = base.mark_text(align="left", dx=5).encode(
            text="team_name:N", color=alt.value("lightgray")
        )

        # 🟢 參考線層 (平均 OffRtg - 水平線)
        off_line = (
            alt.Chart(pd.DataFrame({"mean_off": [mean_off]}))
            .mark_rule(color="green", strokeDash=[3, 3])
            .encode(
                y="mean_off",
                tooltip=[alt.Tooltip("mean_off", format=".2f", title="平均 OffRtg")],
            )
        )

        # 🔴 參考線層 (平均 DefRtg - 垂直線)
        def_line = (
            alt.Chart(pd.DataFrame({"mean_def": [mean_def]}))
            .mark_rule(color="red", strokeDash=[3, 3])
            .encode(
                x="mean_def",
                tooltip=[alt.Tooltip("mean_def", format=".2f", title="平均 DefRtg")],
            )
        )

        # 組合圖層並顯示
        chart = (points + text + off_line + def_line).interactive()

        st.altair_chart(chart, use_container_width=True)

        st.caption(
            "圖中每一點代表一支球隊。X 軸為 DefRtg (越左越好)，Y 軸為 OffRtg (越高越好)。"
            "**左上象限** = 攻守兼備強隊；**右上** = 攻強守弱；**左下** = 守強攻弱；**右下** = 攻守皆弱。"
        )

    st.markdown("---")

    # ==========================================================
    # 🏀 球隊進階數據 Bar Chart (單圖選擇模式)
    # ==========================================================
    st.markdown("### 球隊進階數據長條圖")

    # 🚨 這裡重新讀一次 team_advanced.json
    try:
        chart_src = load_json_to_df(TEAM_FILE)
    except NameError:
        # 由於檔案載入函數 load_json_to_df 在您的程式碼中是有效的，這裡保持原樣
        chart_src = pd.DataFrame()

    if chart_src.empty:
        st.warning("找不到 data/team_advanced.json，無法繪製球隊進階數據的長條圖。")
        return  # 添加 return 以防止執行到不存在的代碼

    team_col_name = (
        "team_name" if "team_name" in chart_src.columns else chart_src.columns[0]
    )

    # 假設 team_order 已經從 sorted_df 正確獲取
    try:
        team_order = sorted_df[team_col_name].tolist()
    except NameError:
        team_order = chart_src[team_col_name].tolist()

    chart_df = (
        chart_src[chart_src[team_col_name].isin(team_order)]
        .set_index(team_col_name)
        .loc[team_order]
        .reset_index()
        .rename(columns={team_col_name: "球隊"})
    )

    metric_label_to_col = {
        "TS%": "ts",
        "eFG%": "efg",
        "OffRtg": "off_rtg",
    }

    plot_wide_df = chart_df[["球隊"]].copy()

    # 關鍵：統一數值標準化 (將所有百分比轉換為 1~100 的範圍，OffRtg 保留 100+)
    for label, col in metric_label_to_col.items():
        if col not in chart_df.columns:
            continue

        value = pd.to_numeric(chart_df[col], errors="coerce")

        if label in ["TS%", "eFG%"]:
            # 強制將小數乘以 100
            plot_wide_df[label] = value * 100
        else:  # OffRtg
            plot_wide_df[label] = value

    valid_metrics = [
        label for label in metric_label_to_col.keys() if label in plot_wide_df.columns
    ]

    if not valid_metrics:
        st.info("目前沒有 TS%、eFG%、OffRtg 等欄位可以畫圖。")
        return

    # ⬇️ 核心變動：使用 selectbox 進行單指標選擇
    selected_metric = st.selectbox(
        "選擇要顯示的指標",
        options=valid_metrics,
        # 預設選擇 OffRtg，如果沒有則選擇第一個
        index=valid_metrics.index("OffRtg") if "OffRtg" in valid_metrics else 0,
        format_func=lambda x: f"{x} (已乘以 100)" if x in ["TS%", "eFG%"] else x,
        key="team_bar_metric_single",
    )

    if selected_metric:
        # 1. 過濾並轉換為 Long Format (只包含選定的單一指標)
        long_df = (
            plot_wide_df[["球隊", selected_metric]]
            .melt(
                id_vars="球隊",
                value_vars=[selected_metric],
                var_name="指標",
                value_name="數值",
            )
            .reset_index(drop=True)
        )

        # 確保欄位類型正確
        long_df["球隊"] = long_df["球隊"].astype(str)
        long_df["數值"] = long_df["數值"].astype(float)

        plot_df_single = long_df
        metric = selected_metric  # 將選定的 metric 賦值給 metric 變數

        # # debug 用：確認數值到底長怎樣
        # with st.expander(f"DEBUG – Bar Chart 資料 ({metric} 的 long_df)"):
        #     st.dataframe(plot_df_single.head(20), use_container_width=True)

        # 2. 使用 plotly.graph_objects (go) 繪製單圖
        import plotly.graph_objects as go

        # 顏色映射 (可自定義)
        color_map = {
            "TS%": "rgba(255, 99, 132, 0.8)",  # 紅色調
            "eFG%": "rgba(54, 162, 235, 0.8)",  # 藍色調
            "OffRtg": "rgba(255, 206, 86, 0.8)",  # 黃色調
        }

        # 動態決定 Y 軸標題
        y_label = f"{metric} (%)" if metric in ["TS%", "eFG%"] else f"{metric} (Rating)"

        # 建立 go.Figure
        fig_go = go.Figure()

        # 使用 go.Bar 手動添加長條圖 trace
        fig_go.add_trace(
            go.Bar(
                x=plot_df_single["球隊"],
                y=plot_df_single["數值"],
                name=metric,
                marker_color=color_map.get(metric, "gray"),  # 手動設定顏色
                text=plot_df_single["數值"].apply(lambda x: f"{x:.1f}"),  # 設定標籤
                textposition="outside",  # 標籤位置
            )
        )

        # 3. 強制 Y 軸範圍
        min_val = plot_df_single["數值"].min()
        max_val = plot_df_single["數值"].max()

        y_min = max(0, min_val * 0.95)
        y_max = max_val * 1.05

        # 設定佈局
        fig_go.update_layout(
            title_text=f"{metric}球隊表現排名",
            xaxis_title="球隊",
            yaxis_title=y_label,
            yaxis=dict(range=[y_min, y_max]),
            showlegend=False,
            # 啟用 Plotly 的 X 軸類別處理
            xaxis=dict(
                categoryorder="array", categoryarray=plot_df_single["球隊"].tolist()
            ),
        )

        # 渲染圖表
        st.plotly_chart(fig_go, use_container_width=True)

    else:
        st.info("請至少選擇一個指標來顯示長條圖。")

        # ... (長條圖繪製區塊結束) ...

    # ==========================================================
    # 📚 進階數據指標解釋
    # ==========================================================
    st.markdown("---")
    st.markdown("### 進階數據指標解釋")

    # 使用 Markdown 和表格呈現指標定義
    st.markdown(
        """
    | 英文縮寫 | 中文名稱 | 定義 | 數值範圍 (處理後) |
    | :---: | :---: | :--- | :--- |
    | **TS%** | **真實投籃命中率** (True Shooting Percentage) | 衡量球隊每次出手（包括三分球和罰球）獲得的分數效率。 | 約 45 ~ 65 (已乘以 100) |
    | **eFG%** | **有效投籃命中率** (Effective Field Goal Percentage) | 衡量球隊的投籃效率。對三分球賦予 1.5 倍權重。 | 約 45 ~ 60 (已乘以 100) |
    | **OffRtg** | **進攻效率值** (Offensive Rating) | 衡量球隊的得分能力。計算每 100 次球權所獲得的分數。 | 約 100 ~ 120 |
    """
    )

    st.markdown(
        """
    > **核心差異：** **eFG%** 專注於衡量**投籃選擇**的效率；**OffRtg** 專注於衡量**整體進攻**的效率 (納入失誤、籃板等因素)。
    """
    )

    st.markdown("---")

    # ===========================
    #  全部球隊列表
    # ===========================
    st.markdown("### 全部球隊列表 (All teams)")
    st.dataframe(sorted_df, use_container_width=True)

    st.markdown("---")

    # ========================
    #       球員頁面
    # ========================

# ========================
#       球員頁面
# ========================

def show_player_page():
    import math
    import json
    from pathlib import Path

    import pandas as pd
    import plotly.graph_objects as go
    import altair as alt

    st.header("👤 球員進階數據 Player Advanced Stats")
    st.markdown(
        """
        <style>
        /* 整體背景再暗一點，偏 ESPN / NBA Stats 風格 */
        .main {
            background-color: #050814;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 讀進階數據
    df = load_json_to_df(PLAYER_FILE)
    if df.empty:
        st.warning(
            "找不到 data/player_advanced.json，請先跑 player_advanced.py 再回來喔～"
        )
        return

    # ------------------------------------------------
    # 讀取球員基本資料 + 照片：players_master_raw.json
    # 建一個 name -> info 的 map
    # ------------------------------------------------
    master_info_map = {}
    try:
        master_path = Path("data/players_master_raw.json")
        if master_path.exists():
            with master_path.open("r", encoding="utf-8") as f:
                master_players = json.load(f)

            for p in master_players:
                name = p.get("name")
                if not name:
                    continue

                meta = p.get("meta") or {}
                images = p.get("images") or []

                img_url = None
                # 優先用 key == "md"，沒有就第一張
                for img in images:
                    if img.get("key") == "md":
                        img_url = img.get("url")
                        break
                if not img_url and images:
                    img_url = images[0].get("url")

                info = {
                    "img_url": img_url,
                    "number": p.get("number"),
                    "position": meta.get("position"),
                    "alt_name": meta.get("alt_name"),
                    "height": meta.get("height"),
                    "weight": meta.get("weight"),
                }
                master_info_map[name] = info
    except Exception as e:
        st.caption(f"⚠️ 讀取球員基本資料時發生錯誤：{e}")

    # ------------------------------------------------
    # 篩選條件（適用於整個頁面）
    # ------------------------------------------------
    st.subheader("篩選條件")

    # 依球隊篩選
    team_col = "team_name" if "team_name" in df.columns else None
    if team_col:
        all_teams = ["(All)"] + sorted(df[team_col].dropna().unique().tolist())
        selected_team = st.selectbox("選擇球隊 (Filter by team)", all_teams)
        if selected_team != "(All)":
            df = df[df[team_col] == selected_team]

    # 依得分門檻篩選
    if "pts" in df.columns:
        pts_series = df["pts"].dropna()
        if not pts_series.empty:
            min_val = float(pts_series.min())
            max_val = float(pts_series.max())
            min_pts = st.slider(
                "最低場均得分門檻 (Min PTS per game)",
                min_value=min_val,
                max_value=max_val,
                value=min_val,
                step=0.5,
            )
            df = df[df["pts"] >= min_pts]

    if df.empty:
        st.info("目前篩選條件下沒有球員資料喔。")
        return

    # 小工具：檢查數字是否有效
    def valid_num(x):
        return isinstance(x, (int, float)) and not (
            isinstance(x, float) and math.isnan(x)
        )

    # =========================================================
    # ① 最上面：球員 Profile & 能力雷達圖
    # =========================================================
    st.markdown("### 球員 Profile & 能力雷達圖")

    name_col = "player_name" if "player_name" in df.columns else df.columns[0]
    player_options = df[name_col].astype(str).tolist()
    selected_player = st.selectbox(
        "選擇球員 (Select a player)", player_options, key="player_profile_select"
    )

    row = df[df[name_col].astype(str) == selected_player].iloc[0]

    name_display = row.get("player_name", selected_player)
    team_display = row.get("team_name", "")

    # 從 master_info_map 拿基本資料
    info = master_info_map.get(name_display, {}) or {}
    img_url = info.get("img_url")
    number = info.get("number")
    position = info.get("position")
    alt_name = info.get("alt_name")
    height = info.get("height")
    weight = info.get("weight")

    # Subtitle：#8 | SF | 球隊
    subtitle_parts = []
    if number:
        subtitle_parts.append(f"#{number}")
    if position:
        subtitle_parts.append(position)
    if team_display:
        subtitle_parts.append(team_display)
    subtitle_text = " | ".join(subtitle_parts) if subtitle_parts else ""

    # 左右欄：左 profile 卡片，右雷達圖
    col_profile, col_radar = st.columns([1.4, 2])

    # ------------ 左邊：NBA.com 風格 Player Card ------------
    with col_profile:
        st.markdown(
            """
            <style>
            .player-card {
                background: linear-gradient(135deg, #0b1f3b, #133667);
                border-radius: 20px;
                padding: 18px 18px 16px 18px;
                color: white;
                box-shadow: 0 10px 22px rgba(0,0,0,0.40);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin-bottom: 14px;
            }
            .player-main-row {
                display: flex;
                gap: 16px;
                align-items: center;
            }
            .player-photo-wrapper {
                position: relative;
                width: 130px;
                height: 130px;
                border-radius: 14px;
                overflow: hidden;
                background: #0b1f3b;
            }
            .player-photo-wrapper img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            .player-number-badge {
                position: absolute;
                bottom: -4px;
                left: 8px;
                background: rgba(0,0,0,0.8);
                padding: 3px 9px;
                border-radius: 12px;
                font-weight: 700;
                font-size: 13px;
                letter-spacing: 1px;
            }
            .player-text-block {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .player-name {
                font-size: 24px;
                font-weight: 750;
            }
            .player-subtitle {
                font-size: 14px;
                opacity: 0.9;
            }
            .player-altname {
                font-size: 13px;
                opacity: 0.8;
            }
            .player-meta-row {
                margin-top: 12px;
                display: flex;
                gap: 18px;
                font-size: 13px;
                opacity: 0.95;
            }
            .player-meta-item span {
                display: block;
                font-size: 11px;
                opacity: 0.7;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Height / Weight 字串
        hw_text = ""
        if valid_num(height) and valid_num(weight):
            hw_text = f"{height} cm / {weight} kg"
        elif valid_num(height):
            hw_text = f"{height} cm"
        elif valid_num(weight):
            hw_text = f"{weight} kg"

        # 卡片 HTML
        html = '<div class="player-card">'
        html += '<div class="player-main-row">'

        html += '<div class="player-photo-wrapper">'
        if img_url:
            html += f'<img src="{img_url}" alt="{name_display} headshot" />'
        else:
            html += '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:12px;opacity:0.7;">No Photo</div>'
        if number:
            html += f'<div class="player-number-badge">#{number}</div>'
        html += "</div>"  # photo wrapper

        html += '<div class="player-text-block">'
        html += f'<div class="player-name">{name_display}</div>'
        if subtitle_text:
            html += f'<div class="player-subtitle">{subtitle_text}</div>'
        if alt_name:
            html += f'<div class="player-altname">{alt_name}</div>'
        html += "</div>"  # text block

        html += "</div>"  # main row

        # Meta row
        meta_html_parts = []
        if hw_text:
            meta_html_parts.append(
                f'<div class="player-meta-item"><span>Height / Weight</span>{hw_text}</div>'
            )
        if "games" in row and valid_num(row["games"]):
            meta_html_parts.append(
                f'<div class="player-meta-item"><span>Games</span>{int(row["games"])}</div>'
            )
        if "min_pg" in row and valid_num(row["min_pg"]):
            meta_html_parts.append(
                f'<div class="player-meta-item"><span>Min / Game</span>{row["min_pg"]:.1f}</div>'
            )

        if meta_html_parts:
            html += (
                '<div class="player-meta-row">' + "".join(meta_html_parts) + "</div>"
            )

        html += "</div>"  # card
        st.markdown(html, unsafe_allow_html=True)

        # 下方 metrics（多顯示一點指標）
        metric_cols = st.columns(5)
        with metric_cols[0]:
            if "pts" in row and valid_num(row["pts"]):
                st.metric("PTS / G", f"{row['pts']:.1f}")
        with metric_cols[1]:
            if "reb" in row and valid_num(row["reb"]):
                st.metric("REB / G", f"{row['reb']:.1f}")
        with metric_cols[2]:
            if "ast" in row and valid_num(row["ast"]):
                st.metric("AST / G", f"{row['ast']:.1f}")
        with metric_cols[3]:
            if "ts_official" in row and valid_num(row["ts_official"]):
                st.metric("TS%", f"{row['ts_official']*100:.1f}%")
        with metric_cols[4]:
            if "usage_share" in row and valid_num(row["usage_share"]):
                st.metric("USG%", f"{row['usage_share']*100:.1f}%")

    # ------------ 右邊：雷達圖 ------------
    radar_labels = []
    radar_values = []

    def safe_add(col_name, label, scale=1.0):
        if col_name in row.index:
            v = row[col_name]
            if valid_num(v):
                radar_labels.append(label)
                radar_values.append(float(v) * scale)

    safe_add("pts", "PTS")
    safe_add("reb", "REB")
    safe_add("ast", "AST")
    safe_add("ts_official", "TS%")
    safe_add("efg_official", "eFG%")
    safe_add("usage_share", "Usage")

    with col_radar:
        if len(radar_labels) >= 3:
            radar_values.append(radar_values[0])
            radar_labels.append(radar_labels[0])

            fig_radar = go.Figure()
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=radar_values,
                    theta=radar_labels,
                    fill="toself",
                    name=name_display,
                )
            )
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                showlegend=False,
                margin=dict(l=0, r=0, t=20, b=10),
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("目前這位球員可用來畫雷達圖的數據不足（至少需要 3 個指標）。")

    # =========================================================
    # ② 中間：Usage vs Efficiency 散佈圖
    # =========================================================
    st.markdown("---")
    st.markdown("### Usage vs Efficiency：TS% x Usage Share")

    if all(col in df.columns for col in ["usage_share", "ts_official"]):
        scatter_df = df.copy()
        scatter_df["usage_share"] = pd.to_numeric(
            scatter_df["usage_share"], errors="coerce"
        )
        scatter_df["ts_official"] = pd.to_numeric(
            scatter_df["ts_official"], errors="coerce"
        )

        valid_df = scatter_df.dropna(subset=["usage_share", "ts_official"])

        st.caption(
            f"目前符合篩選條件的球員共有 {len(scatter_df)} 位，"
            f"其中有有效 TS% + Usage 的共有 {len(valid_df)} 位。"
        )

        with st.expander("查看部分原始數據"):
            st.dataframe(
                valid_df[
                    ["player_name", "team_name", "usage_share", "ts_official"]
                ].head(10),
                use_container_width=True,
            )

        if not valid_df.empty:
            valid_df = valid_df.copy()
            valid_df["usage_pct"] = valid_df["usage_share"] * 100.0
            valid_df["ts_pct"] = valid_df["ts_official"] * 100.0

            color_field = "team_name" if "team_name" in valid_df.columns else None

            base = (
                alt.Chart(valid_df)
                .mark_circle(size=70, opacity=0.8)
                .encode(
                    x=alt.X("usage_pct:Q", axis=alt.Axis(title="Usage Share (%)")),
                    y=alt.Y("ts_pct:Q", axis=alt.Axis(title="TS% (official, %)")),
                    tooltip=[
                        alt.Tooltip("player_name:N", title="Player"),
                        alt.Tooltip("team_name:N", title="Team"),
                        alt.Tooltip("usage_pct:Q", title="Usage (%)", format=".1f"),
                        alt.Tooltip("ts_pct:Q", title="TS% (%)", format=".1f"),
                    ],
                )
            )

            if color_field:
                base = base.encode(color=alt.Color("team_name:N", title="Team"))

            st.altair_chart(base.interactive(), use_container_width=True)
        else:
            st.info("目前沒有同時具有 TS% 和 Usage Share 的球員資料可以畫散佈圖。")
    else:
        st.info("目前資料中缺少 `usage_share` 或 `ts_official` 欄位，無法顯示散佈圖。")

    # =========================================================
    # ③ 最下面：排序方式 + 球員列表
    # =========================================================
    st.markdown("---")
    st.subheader("排序方式")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        num_cols = df.columns.tolist()

    priority_cols = [
        c
        for c in ["ts_official", "efg_official", "usage_share", "pts"]
        if c in num_cols
    ]
    candidate_sort_cols = priority_cols or num_cols

    sort_col = st.selectbox("排序欄位 (Sort by)", candidate_sort_cols)
    ascending = st.checkbox(
        "由小到大排序 (Ascending)",
        value=False,
        key="player_sort_asc",
    )

    try:
        sorted_df = df.sort_values(by=sort_col, ascending=ascending)
    except TypeError:
        st.warning("這個欄位的資料型態無法排序，已改用原始順序顯示。")
        sorted_df = df

    st.markdown("### 球員列表 (Players)")
    display_cols = [
        c
        for c in [
            "player_name",
            "team_name",
            "games",
            "min_pg",
            "pts",
            "reb",
            "ast",
            "ts_official",
            "efg_official",
            "usage_share",
        ]
        if c in sorted_df.columns
    ]
    if not display_cols:
        display_cols = sorted_df.columns.tolist()

    st.dataframe(sorted_df[display_cols], use_container_width=True)

# ========================
#       賽程頁面
# ========================

def show_schedule_page():
    st.header("賽程資訊 Game Schedule")

    st.markdown(
        """
        <style>
        /* 整體背景再暗一點，偏 ESPN / NBA Stats 風格 */
        .main {
            background-color: #050814;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 🔁 一鍵重新爬取最新資料
    if st.button("重新抓取最新賽程 (Refresh Data)", use_container_width=True):
        with st.spinner("正在爬取最新 TPBL 賽程資料..."):
            try:
                result = subprocess.run(
                    [sys.executable, str(BASE_DIR / "tpbl_crawler.py")],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    st.success(
                        "Data refreshed!（已成功更新 data/schedule_raw.json / tpbl_crawler_raw.json）"
                    )
                else:
                    st.warning("Crawler completed with warnings，請查看終端機或 log。")
                    if result.stderr:
                        st.text_area("錯誤訊息 (stderr)", result.stderr, height=150)
            except FileNotFoundError:
                st.warning("找不到 tpbl_crawler.py，請確認檔案是否存在於專案目錄。")
            except subprocess.TimeoutExpired:
                st.error("爬蟲執行逾時（Timeout），請稍後再試。")
            finally:
                st.cache_data.clear()
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 讀 schedule（基本賽程）+ scores（比分）
    schedule_df = load_json_to_df(SCHEDULE_FILE)
    scores_df = load_json_to_df(SCORE_FILE)

    if schedule_df.empty:
        st.info(
            "目前沒有賽程資料，請先確認 data/schedule_raw.json 是否存在，或按上方按鈕重新抓取。"
        )
        return

    # 合併比分：schedule_df.game_id ↔ scores_df.id
    games_df = schedule_df.copy()
    if not scores_df.empty:
        if "id" in scores_df.columns and "game_id" in games_df.columns:
            score_cols = ["id", "home_score", "away_score"]
            score_cols = [c for c in score_cols if c in scores_df.columns]
            games_df = games_df.merge(
                scores_df[score_cols],
                left_on="game_id",
                right_on="id",
                how="left",
            )

    # ===== 日期處理 + 排序選項 =====
    if "date" in games_df.columns:
        games_df["date"] = pd.to_datetime(games_df["date"], errors="coerce")

        sort_choice = st.radio(
            "日期排序",
            ["最近的比賽在前", "最遠的比賽在前"],
            index=0,
            horizontal=True,
        )
        # 最近在前 → 由新到舊（descending = True）
        ascending = sort_choice == "最遠的比賽在前"
        games_df = games_df.sort_values("date", ascending=ascending)

    today = pd.Timestamp.now().normalize()

    # 逐場比賽列出
    for _, game in games_df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            st.write(f"**{game.get('home_team_name', 'TBD')}**")

        with col2:
            st.write(f"**vs {game.get('away_team_name', 'TBD')}**")

        # 狀態 + 比分
        with col3:
            status_raw = game.get("status", "")
            status = str(status_raw).upper() if status_raw is not None else ""

            # 日期
            game_date = game.get("date")
            if pd.notna(game_date):
                game_date = pd.to_datetime(game_date, errors="coerce")

            # 從合併後的欄位取比分
            home_score = None
            away_score = None

            hs_raw = game.get("home_score", None)
            as_raw = game.get("away_score", None)

            if hs_raw is not None and pd.notna(hs_raw):
                try:
                    home_score = int(hs_raw)
                except Exception:
                    home_score = None

            if as_raw is not None and pd.notna(as_raw):
                try:
                    away_score = int(as_raw)
                except Exception:
                    away_score = None

            has_score = (home_score is not None) and (away_score is not None)

            # 1️⃣ 完成比賽
            if status == "COMPLETED":
                st.markdown(
                    '<span style="color: green; font-weight: bold;">✓ FINAL</span>',
                    unsafe_allow_html=True,
                )
                if has_score:
                    st.write(f"{home_score} - {away_score}")

            # 2️⃣ 直播中
            elif status in {"LIVE", "IN_PROGRESS"} or game.get("is_live", False):
                st.markdown(
                    '<span style="color: red; font-weight: bold;">● LIVE</span>',
                    unsafe_allow_html=True,
                )

            # 3️⃣ 其他狀態：用日期分 Upcoming / Pending
            else:
                if pd.isna(game_date):
                    st.markdown(
                        '<span style="color: gray;">UPCOMING</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    if game_date >= today:
                        st.markdown(
                            '<span style="color: gray;">UPCOMING</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<span style="color: orange; font-weight: bold;">Pending</span>',
                            unsafe_allow_html=True,
                        )

        with col4:
            game_date = game.get("date")
            if pd.notna(game_date):
                game_date = pd.to_datetime(game_date, errors="coerce")
                st.write(game_date.strftime("%Y-%m-%d"))
            else:
                st.write("TBD")

        st.markdown("---")


# ========================
#         主程式
# ========================
def main():
    st.set_page_config(
        page_title="TPBL 進階數據分析 Dashboard",
        page_icon="🏀",
        layout="wide",
    )

    st.title("TPBL 進階數據分析 Dashboard")
    st.caption("資料來源：TPBL 官網 API + 自行計算進階數據")

    page = st.sidebar.radio(
        "選擇頁面 (Select page)",
        ["首頁", "球隊進階數據", "球員進階數據", "賽程資訊"],
    )

    if page == "首頁":
        show_home_page()
    elif page == "球隊進階數據":
        show_team_page()
    elif page == "球員進階數據":
        show_player_page()
    else:
        show_schedule_page()

if __name__ == "__main__":
    main()