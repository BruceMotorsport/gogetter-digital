/**
 * GoGetter Digital Dashboard — Real Data, Interactive
 * Click any tile to see actual details
 */

let DATA = null;
let currentModal = null;

// ─── Load real data from API ────────────────────────────────────
async function loadData() {
  try {
    const [agents, leads, projects, logs] = await Promise.all([
      fetch('http://192.168.1.53:8080/api/agents').then(r => r.json()),
      fetch('http://192.168.1.53:8080/api/leads').then(r => r.json()),
      fetch('http://192.168.1.53:8080/api/projects').then(r => r.json()),
      fetch('http://192.168.1.53:8080/api/logs?limit=20').then(r => r.json())
    ]);

    DATA = { agents, leads, projects, logs };
    renderAll();
  } catch (err) {
    console.log('API offline, using fallback');
    DATA = { agents: [], leads: [], projects: [], logs: [] };
    renderAll();
  }
}

// ─── Modal system ───────────────────────────────────────────────
function showModal(title, content) {
  let overlay = document.getElementById('modal-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'modal-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.85);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px';
    overlay.onclick = (e) => { if (e.target === overlay) closeModal(); };
    document.body.appendChild(overlay);
  }
  overlay.innerHTML = `
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:16px;max-width:500px;width:100%;max-height:80vh;overflow-y:auto;padding:20px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h2 style="font-size:18px;font-weight:700">${title}</h2>
        <button onclick="closeModal()" style="background:none;border:none;color:var(--text2);font-size:20px;cursor:pointer">✕</button>
      </div>
      ${content}
    </div>
  `;
  overlay.style.display = 'flex';
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.style.display = 'none';
}

// ─── Click handlers ─────────────────────────────────────────────
function showSites() {
  if (!DATA) return;
  const sites = DATA.projects.map(p => `
    <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong style="font-size:14px">${p.name}</strong>
        <span style="font-size:11px;padding:2px 8px;border-radius:8px;background:${p.stage==='complete'?'rgba(0,230,118,.15)':'rgba(255,102,0,.15)'};color:${p.stage==='complete'?'var(--green)':'var(--orange)'}">${p.stage}</span>
      </div>
      <div style="color:var(--text2);font-size:12px;margin-top:4px">Client: ${p.client}</div>
      <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:11px;color:var(--text3)">
        <span>${p.progress}% complete</span>
        <span>Agent: ${p.assigned_agent}</span>
      </div>
    </div>
  `).join('');
  showModal('🔨 Projects (' + DATA.projects.length + ')', sites || '<p style="color:var(--text2)">No projects yet</p>');
}

function showClients() {
  if (!DATA) return;
  const contacted = DATA.leads.filter(l => l.status === 'contacted');
  const clients = contacted.map(l => `
    <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong style="font-size:14px">${l.company}</strong>
        <span style="font-size:11px;color:var(--green)">Score: ${l.score}</span>
      </div>
      <div style="color:var(--text2);font-size:12px;margin-top:4px">Contact: ${l.name}</div>
      <div style="color:var(--text3);font-size:11px;margin-top:2px">Phone: ${l.phone || 'N/A'}</div>
    </div>
  `).join('');
  showModal('📧 Proposals Sent (' + contacted.length + ')', clients || '<p style="color:var(--text2)">No proposals sent yet</p>');
}

function showLeads() {
  if (!DATA) return;
  const leads = DATA.leads.map(l => `
    <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong style="font-size:14px">${l.company}</strong>
        <span style="font-size:11px;padding:2px 8px;border-radius:8px;background:${l.status==='contacted'?'rgba(0,230,118,.15)':'rgba(255,214,0,.15)'};color:${l.status==='contacted'?'var(--green)':'var(--yellow)'}">${l.status}</span>
      </div>
      <div style="color:var(--text2);font-size:12px;margin-top:4px">Contact: ${l.name} | Phone: ${l.phone || 'N/A'}</div>
      <div style="color:var(--text3);font-size:11px;margin-top:2px">Score: ${l.score}/100</div>
    </div>
  `).join('');
  showModal('🎯 Leads Pipeline (' + DATA.leads.length + ')', leads || '<p style="color:var(--text2)">No leads yet</p>');
}

function showHours() {
  if (!DATA) return;
  const projects = DATA.projects;
  const totalHours = projects.length * 40;
  const details = projects.map(p => `
    <div style="background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong style="font-size:14px">${p.name}</strong>
        <span style="font-size:11px;color:var(--orange)">${p.progress}%</span>
      </div>
      <div style="color:var(--text2);font-size:12px;margin-top:4px">Estimated: 40 hours</div>
      <div class="progress-bar" style="margin-top:6px"><div class="progress-fill" style="width:${p.progress}%"></div></div>
    </div>
  `).join('');
  showModal('⏱️ Hours Breakdown (' + totalHours + ' total)', details || '<p style="color:var(--text2)">No projects yet</p>');
}

// ─── Renderers ──────────────────────────────────────────────────
function renderMetrics() {
  const grid = document.getElementById('metrics-grid');
  if (!grid || !DATA) return;
  const p = DATA.projects;
  const l = DATA.leads;
  const sitesDone = p.filter(x => x.stage === 'complete').length;
  const clientsContacted = l.filter(x => x.status === 'contacted').length;
  grid.innerHTML = `
    <div class="metric-card" onclick="showSites()" style="cursor:pointer">
      <div class="metric-icon">🌐</div>
      <div class="metric-value">${p.length}</div>
      <div class="metric-label">Projects</div>
      <div class="metric-trend">${sitesDone} completed</div>
    </div>
    <div class="metric-card" onclick="showClients()" style="cursor:pointer">
      <div class="metric-icon">📧</div>
      <div class="metric-value">${clientsContacted}</div>
      <div class="metric-label">Proposals Sent</div>
      <div class="metric-trend">Waiting for responses</div>
    </div>
    <div class="metric-card" onclick="showLeads()" style="cursor:pointer">
      <div class="metric-icon">🎯</div>
      <div class="metric-value">${l.length}</div>
      <div class="metric-label">Leads Found</div>
      <div class="metric-trend">${l.filter(x=>x.status==='new').length} new</div>
    </div>
    <div class="metric-card" onclick="showHours()" style="cursor:pointer">
      <div class="metric-icon">⏱️</div>
      <div class="metric-value">${p.length * 40}</div>
      <div class="metric-label">Hours Worked</div>
      <div class="metric-trend">AI-powered efficiency</div>
    </div>
  `;
}

function renderProjects() {
  const grid = document.getElementById('projects-grid');
  if (!grid || !DATA) return;
  grid.innerHTML = DATA.projects.map((p, i) => {
    const stageClass = p.stage === 'complete' ? 'status-review' : p.stage === 'building' ? 'status-in-progress' : 'status-starting';
    return `
      <div class="project-card" style="animation-delay:${i * 0.08}s">
        <div class="project-header">
          <span class="project-icon">${p.stage === 'complete' ? '✅' : '🔨'}</span>
          <span class="project-status ${stageClass}">${p.stage}</span>
        </div>
        <h3 class="project-name">${p.name}</h3>
        <p class="project-client">${p.client}</p>
        <div class="progress-bar"><div class="progress-fill" style="width:${p.progress}%"></div></div>
        <div class="project-footer"><span>${p.progress}%</span><span>🤖 ${p.assigned_agent}</span></div>
      </div>`;
  }).join('');
}

function renderAgents() {
  const grid = document.getElementById('agents-grid');
  if (!grid || !DATA) return;
  const avatars = { Scout: '🎯', Sales: '📧', Developer: '🔨', QA: '🧪', Orchestrator: '🧠' };
  grid.innerHTML = DATA.agents.map(a => `
    <div class="agent-card">
      <div class="agent-avatar">${avatars[a.name] || '🤖'}</div>
      <div class="agent-info">
        <h4 class="agent-name">${a.name}</h4>
        <p class="agent-role">${a.role}</p>
        <p class="agent-task">${a.current_task || 'Standing by'}</p>
      </div>
      <div class="agent-status-dot active"></div>
    </div>
  `).join('');
}

function renderActivity() {
  const feed = document.getElementById('activity-feed');
  if (!feed || !DATA) return;
  const icons = { scout: '🎯', sales: '📧', developer: '🔨', qa: '🧪', brain: '🧠', orchestrator: '📋', system: '⚡' };
  feed.innerHTML = DATA.logs.slice(0, 8).map(l => `
    <div class="activity-item">
      <div class="activity-icon">${icons[l.agent] || '📌'}</div>
      <div class="activity-content">
        <p><strong>${l.agent}</strong> ${l.action}</p>
        <span class="activity-time">${l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : ''}</span>
      </div>
    </div>
  `).join('');
}

function renderAll() {
  renderMetrics();
  renderProjects();
  renderAgents();
  renderActivity();
}

function showToast(msg) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

// ─── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  setInterval(loadData, 15000); // Refresh every 15 seconds
});
