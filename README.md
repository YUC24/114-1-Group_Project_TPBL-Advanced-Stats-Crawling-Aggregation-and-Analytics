# TPBL 進階數據分析 (TPBL Advanced Stats Crawling, Aggregation & Dashboard)

一個用於抓取 TPBL 賽事資料、計算球隊／球員進階指標，並以互動式 Dashboard 呈現的專案。

主要功能
- 自動爬取 TPBL 官方 API（比賽、賽程、球員、球隊等原始資料）。
- 計算球隊進階指標：OffRtg / DefRtg / Pace / eFG% / TS% / TOV% / FT Rate 等。
- 計算球員進階指標：TS%、eFG%、Usage、每場數據等。
- 以 Streamlit 提供互動式 Dashboard（包含四象限圖、Usage vs TS 散佈、球員雷達圖、賽程瀏覽等）。

專案結構（摘錄）
- app.py — Streamlit Dashboard 主程式。
- src/
  - analyze_team_advanced.py — 將 data/team_stats_raw.json 聚合並計算 team_advanced.json（含 `pace`）。
  - player_advanced.py — 計算球員進階數據並寫入 data/player_advanced.json。
  - tpbl_crawler.py / stats_crawler.py / player_stats_crawler.py / schedule_crawler.py — 各類爬蟲與資料擷取程式。
- data/
  - player_advanced.json — 球員進階數據（Dashboard 讀取）。
  - player_stats_raw.json, players_master_raw.json, schedule_raw.json, team_stats_raw.json, team_advanced.json, tpbl_crawler_raw.json — 原始與中間資料檔。

Pace（回合數）在哪裡？
- 最終的 Pace 值會寫入 `data/team_advanced.json`，每支球隊物件包含欄位 `"pace"`（代表每場平均回合數，程式已將 possessions 校正到聯盟目標 Pace）。
- 計算邏輯位置：`src/analyze_team_advanced.py`。程式使用常見的 possessions 估算公式：
  possessions ≈ FGA + 0.44 * FTA − OREB + TOV
  然後聚合每隊的 possessions_for，計算聯盟 raw_pace 平均值，將其縮放（scale）到目標 Pace（預設 TARGET_PACE = 90），最後將校正後的 possessions 除以場數得到 `pace`。

快速上手
1. 建議建立虛擬環境並安裝相依套件：

   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   若沒有 requirements.txt，請至少安裝：
   pip install pandas streamlit plotly altair requests beautifulsoup4

2. 取得資料（範例）：
   - 先執行爬蟲抓資料（會把原始 JSON 寫到 data/）：
     python src/tpbl_crawler.py
     python src/stats_crawler.py
     python src/player_stats_crawler.py
     python src/schedule_crawler.py

   - 或執行單一爬蟲：
     python tpbl_crawler.py

3. 計算進階數據：
   - 球隊：
     python src/analyze_team_advanced.py
     會讀取 `data/team_stats_raw.json` 並輸出 `data/team_advanced.json`

   - 球員：
     python src/player_advanced.py
     會讀取 player 原始資料並輸出 `data/player_advanced.json`

4. 啟動 Dashboard：
   streamlit run app.py

貢獻與擴充建議
- 可加入更多資料欄位（例如球員位置、上場/替補指標），或把 dashboard 部署到 Streamlit Cloud / Heroku。
- 若想把原始 possessions_for / possessions_against 也儲存在輸出 JSON 中，可修改 `src/analyze_team_advanced.py`，將未校正與校正後數值一併寫入 `data/team_advanced.json`。

License
- 自行選擇合適授權並在此處聲明。

聯絡
- 若需協助撰寫 README 或修改程式，使輸出包含更多欄位（例如把 possessions 原始值也存出），請告訴我具體要新增的欄位或介面呈現方式，我可以直接幫你修改程式碼。
