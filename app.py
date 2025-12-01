import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ===== 路徑設定 =====
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEAM_FILE = DATA_DIR / "team_advanced.json"
PLAYER_FILE = DATA_DIR / "player_advanced.json"


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


# ========================
#       球隊頁面
# ========================
def show_team_page():
    st.header("🏀 球隊進階數據 Team Advanced Stats")

    df = load_json_to_df(TEAM_FILE)
    if df.empty:
        st.warning("找不到 data/team_advanced.json，請先跑一次分析程式再回來喔～")
        return

    st.subheader("排序方式")

    # 只讓「可排序欄位」進來（排除 dict / list）
    def is_sortable_column(series: pd.Series) -> bool:
        sample = series.dropna().head(20)
        if sample.empty:
            return True
        if all(isinstance(v, (dict, list)) for v in sample):
            return False
        return True

    valid_cols = [col for col in df.columns if is_sortable_column(df[col])]

    # 預設優先用這些欄位排序（如果存在）
    priority = [c for c in ["off_rtg", "def_rtg", "net_rtg", "games"] if c in valid_cols]
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

    st.markdown("### 全部球隊列表 (All teams)")
    st.dataframe(sorted_df, use_container_width=True)


# ========================
#       球員頁面（讀扁平版 player_advanced.json）
# ========================
def show_player_page():
    st.header("👤 球員進階數據 Player Advanced Stats")

    df = load_json_to_df(PLAYER_FILE)
    if df.empty:
        st.warning("找不到 data/player_advanced.json，請先跑 player_advanced.py 再回來喔～")
        return

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

    st.subheader("排序方式")

    # 只讓數值欄位可以選來排序
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        num_cols = df.columns.tolist()

    priority_cols = [c for c in ["ts_official", "efg_official", "usage_share", "pts"] if c in num_cols]
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

    # --- 4️⃣ 顯示主表 ---
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

    # --- 5️⃣ 單一球員 Summary ---
    st.markdown("### 單一球員 Summary")

    name_col = "player_name" if "player_name" in sorted_df.columns else sorted_df.columns[0]
    player_options = sorted_df[name_col].astype(str).tolist()
    selected_player = st.selectbox("選擇球員 (Select a player)", player_options)

    row = sorted_df[sorted_df[name_col].astype(str) == selected_player].iloc[0]

    name_display = row.get("player_name", selected_player)
    team_display = row.get("team_name", "")
    if team_display:
        st.write(f"**{name_display}** （{team_display}）")
    else:
        st.write(f"**{name_display}**")

    cols = st.columns(4)
    with cols[0]:
        if "pts" in row:
            st.metric("PTS", f"{row['pts']:.1f}")
    with cols[1]:
        if "reb" in row:
            st.metric("REB", f"{row['reb']:.1f}")
    with cols[2]:
        if "ast" in row:
            st.metric("AST", f"{row['ast']:.1f}")
    with cols[3]:
        if "games" in row:
            st.metric("Games", f"{int(row['games'])}")


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
        ["球隊進階數據", "球員進階數據"],
    )

    if page == "球隊進階數據":
        show_team_page()
    else:
        show_player_page()


if __name__ == "__main__":
    main()
