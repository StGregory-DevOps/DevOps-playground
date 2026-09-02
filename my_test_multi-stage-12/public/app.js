'use strict';

const POLL_INTERVAL_MS = 3000;

const els = {
  liveIndicator: document.getElementById('live-indicator'),
  redisChip: document.getElementById('redis-chip'),
  redisChipText: document.getElementById('redis-chip-text'),
  updatedAt: document.getElementById('updated-at'),
  kpiRequests: document.getElementById('kpi-requests'),
  kpiCpu: document.getElementById('kpi-cpu'),
  kpiRam: document.getElementById('kpi-ram'),
  kpiIncidents: document.getElementById('kpi-incidents'),
  serversGrid: document.getElementById('servers-grid'),
  serversCount: document.getElementById('servers-count'),
  logsTbody: document.getElementById('logs-tbody'),
  logsCount: document.getElementById('logs-count'),
  footerUptime: document.getElementById('footer-uptime'),
};

const STATUS_LABELS = {
  online: 'online',
  warning: 'warning',
  critical: 'critical',
};

function formatTime(date) {
  return date.toLocaleTimeString('ru-RU', { hour12: false });
}

function formatUptime(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  return `uptime ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function statusPillClass(status) {
  if (status >= 500) return 's-500';
  if (status >= 400) return 's-404';
  return 's-200';
}

function renderKpis(data) {
  els.kpiRequests.textContent = data.requestCount.toLocaleString('ru-RU');
  els.kpiCpu.textContent = `${data.system.cpuPercent}%`;
  els.kpiRam.textContent = `${data.system.memoryPercent}%`;

  const atRiskCount = (data.servers || []).filter(
    (s) => s.status === 'warning' || s.status === 'critical'
  ).length;
  els.kpiIncidents.textContent = atRiskCount;
}

function renderServers(servers) {
  els.serversCount.textContent = `${servers.length} узлов`;
  els.serversGrid.innerHTML = '';

  servers.forEach((server) => {
    const card = document.createElement('div');
    card.className = `server-card status-${server.status}`;

    card.innerHTML = `
      <div class="server-card-head">
        <span class="server-name">${server.name}</span>
        <span class="server-status-label status-${server.status}">${STATUS_LABELS[server.status] || server.status}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">CPU</span>
        <div class="progress-track">
          <div class="progress-fill status-${server.status}" style="width:${server.cpu}%"></div>
        </div>
        <span class="metric-value">${server.cpu}%</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">RAM</span>
        <div class="progress-track">
          <div class="progress-fill status-${server.status}" style="width:${server.ram}%"></div>
        </div>
        <span class="metric-value">${server.ram}%</span>
      </div>
    `;

    els.serversGrid.appendChild(card);
  });
}

function renderLogs(logs) {
  els.logsCount.textContent = `${logs.length} записей`;

  if (!logs.length) {
    els.logsTbody.innerHTML = '<tr class="logs-empty-row"><td colspan="4">Ожидание событий…</td></tr>';
    return;
  }

  els.logsTbody.innerHTML = logs
    .map((entry) => {
      const time = new Date(entry.timestamp).toLocaleTimeString('ru-RU', { hour12: false });
      return `
        <tr>
          <td class="log-time">${time}</td>
          <td>${entry.method}</td>
          <td class="log-path">${entry.path}</td>
          <td><span class="status-pill ${statusPillClass(entry.status)}">${entry.status} ${entry.message}</span></td>
        </tr>
      `;
    })
    .join('');
}

function renderRedisStatus(connected) {
  els.redisChip.classList.toggle('is-connected', connected);
  els.redisChip.classList.toggle('is-disconnected', !connected);
  els.redisChipText.textContent = `Redis: ${connected ? 'подключен' : 'отключен'}`;
}

function renderLiveState(isLive) {
  els.liveIndicator.style.opacity = isLive ? '1' : '0.5';
  els.liveIndicator.querySelector('span:last-child').textContent = isLive ? 'Live' : 'Нет связи';
}

async function fetchMetrics() {
  try {
    const res = await fetch('/api/metrics', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    renderKpis(data);
    renderServers(data.servers || []);
    renderLogs(data.recentLogs || []);
    renderRedisStatus(data.redis === 'connected');
    renderLiveState(true);

    els.updatedAt.textContent = formatTime(new Date());
    els.footerUptime.textContent = formatUptime(data.system.uptimeSeconds);
  } catch (err) {
    renderLiveState(false);
    renderRedisStatus(false);
    console.error('Не удалось получить метрики:', err.message);
  }
}

fetchMetrics();
setInterval(fetchMetrics, POLL_INTERVAL_MS);
