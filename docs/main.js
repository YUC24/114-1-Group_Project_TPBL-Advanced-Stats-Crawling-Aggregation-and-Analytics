// 共用：數字格式化，小數位數可調
function fmt(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-';
  return Number(value).toFixed(digits);
}

// --- 索引切換（tab 切換） ---
function setupTabs() {
  const buttons = document.querySelectorAll('.tab-button');
  const sections = document.querySelectorAll('.tab-section');

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      // 標籤按鈕 active 樣式切換
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      // 對應的 section 顯示
      const targetId = btn.dataset.target;
      sections.forEach((sec) => {
        if (sec.id === targetId) {
          sec.classList.add('active');
        } else {
          sec.classList.remove('active');
        }
      });
    });
  });
}

// --- 讀取球隊進階數據 ---
// 期待檔案：data/team_advanced.json
// 每筆資料格式大概像：
// {
//   "team_name": "新北國王",
//   "efg": 0.515,
//   "ts": 2.306,
//   "off_rtg": 113.2,
//   "def_rtg": 114.0
// }
async function loadTeamStats() {
  try {
    const res = await fetch('data/team_advanced.json');
    const teams = await res.json();

    const tbody = document.querySelector('#team-table tbody');
    tbody.innerHTML = '';

    teams.forEach((team) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${team.team_name ?? '-'}</td>
        <td>${fmt(team.efg)}</td>
        <td>${fmt(team.ts)}</td>
        <td>${fmt(team.off_rtg, 1)}</td>
        <td>${fmt(team.def_rtg, 1)}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('讀取 team_advanced.json 失敗：', err);
  }
}

// --- 讀取球員進階數據 ---
// 期待檔案：data/player_advanced.json
// 每筆資料格式大概像：
// {
//   "player_name": "王OO",
//   "team_name": "新北國王",
//   "pts": 18.5,
//   "ts_official": 0.585,
//   "efg_official": 0.560,
//   "usage_share": 0.245
// }
async function loadPlayerStats() {
  try {
    const res = await fetch('data/player_advanced.json');
    const players = await res.json();

    const tbody = document.querySelector('#player-table tbody');
    tbody.innerHTML = '';

    players.forEach((p) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${p.player_name ?? '-'}</td>
        <td>${p.team_name ?? '-'}</td>
        <td>${p.pts != null ? fmt(p.pts, 1) : '-'}</td>
        <td>${p.ts_official != null ? fmt(p.ts_official) : '-'}</td>
        <td>${p.efg_official != null ? fmt(p.efg_official) : '-'}</td>
        <td>${p.usage_share != null ? fmt(p.usage_share) : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('讀取 player_advanced.json 失敗：', err);
  }
}

// --- 讀取賽程資訊 ---
// 期待檔案：data/schedule.json
// 每筆資料格式建議：
// {
//   "date": "2025-01-05",        // YYYY-MM-DD
//   "home_team": "台啤英熊",
//   "away_team": "新北國王",
//   "home_score": 95,            // 還沒打可以是 null
//   "away_score": 88
// }
async function loadSchedule() {
  try {
    const res = await fetch('data/schedule.json');
    const games = await res.json();

    const tbody = document.querySelector('#schedule-table tbody');
    tbody.innerHTML = '';

    games.forEach((g) => {
      const haveScore =
        g.home_score !== null && g.home_score !== undefined &&
        g.away_score !== null && g.away_score !== undefined;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${g.date ?? '-'}</td>
        <td>${g.home_team ?? '-'}</td>
        <td>${g.away_team ?? '-'}</td>
        <td>${haveScore ? `${g.home_score} : ${g.away_score}` : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('讀取 schedule.json 失敗：', err);
  }
}

// --- 頁面載入時執行 ---
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  loadTeamStats();
  loadPlayerStats();
  loadSchedule();
});
