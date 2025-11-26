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
async function loadTeamStats() {
  try {
    const res = await fetch('./data/team_advanced.json')
;
    const teams = await res.json();

    const tbody = document.querySelector('#team-table tbody');
    tbody.innerHTML = '';

    teams.forEach((team) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${team.team_name}</td>
        <td>${team.efg ? team.efg.toFixed(3) : '-'}</td>
        <td>${team.ts ? team.ts.toFixed(3) : '-'}</td>
        <td>${team.off_rtg ? team.off_rtg.toFixed(1) : '-'}</td>
        <td>${team.def_rtg ? team.def_rtg.toFixed(1) : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('讀取 team_advanced.json 失敗：', err);
  }
}

// --- 讀取球員進階數據 ---
async function loadPlayerStats() {
  try {
    const res = await fetch('./data/team_advanced.json');
    const players = await res.json();

    const tbody = document.querySelector('#player-table tbody');
    tbody.innerHTML = '';

    players.forEach((p) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${p.player_name}</td>
        <td>${p.team_name}</td>
        <td>${p.pts != null ? p.pts.toFixed(1) : '-'}</td>
        <td>${p.ts_official != null ? p.ts_official.toFixed(3) : '-'}</td>
        <td>${p.efg_official != null ? p.efg_official.toFixed(3) : '-'}</td>
        <td>${p.usage_share != null ? p.usage_share.toFixed(3) : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('讀取 player_advanced.json 失敗：', err);
  }
}

// --- 讀取賽程資訊 ---
// schedule.json 建議格式：
// [
//   {
//     "date": "2025-01-05",
//     "home_team": "台啤英熊",
//     "away_team": "新北國王",
//     "score": "95 - 88"   // 還沒打可以放 "-" 或空字串
//   },
//   ...
// ]
async function loadSchedule() {
  try {
    const res = await fetch('./data/team_advanced.json');
    const games = await res.json();

    const tbody = document.querySelector('#schedule-table tbody');
    tbody.innerHTML = '';

    games.forEach((g) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${g.date}</td>
        <td>${g.home_team}</td>
        <td>${g.away_team}</td>
        <td>${g.score || '-'}</td>
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
