const form = document.querySelector('#ask-form');
const question = document.querySelector('#question');
const snapshot = document.querySelector('#snapshot');
const statusNode = document.querySelector('#status');
const result = document.querySelector('#result');

function fillList(id, values) {
  const node = document.querySelector(id); node.innerHTML = '';
  for (const value of values) { const item = document.createElement('li'); item.textContent = value; node.appendChild(item); }
  node.parentElement.hidden = values.length === 0;
}

async function loadSnapshots() {
  const health = await fetch('/api/health').then(r => r.json());
  const items = await fetch('/api/snapshots').then(r => r.json());
  snapshot.innerHTML = '';
  for (const item of items) { const option = document.createElement('option'); option.value = item.snapshot_id; option.textContent = item.snapshot_id; snapshot.appendChild(option); }
  statusNode.textContent = health.indexed ? `${items[0].source_count} fuentes · ${items[0].chunk_count} fragmentos` : 'Sin índice: ejecute ragscate index';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault(); statusNode.textContent = 'Verificando evidencia…';
  const response = await fetch('/api/ask', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question: question.value, snapshot_id: snapshot.value || null})});
  const data = await response.json();
  if (!response.ok) { statusNode.textContent = data.detail || 'Error'; return; }
  result.classList.remove('hidden');
  const badge = document.querySelector('#classification'); badge.textContent = data.classification; badge.dataset.kind = data.classification;
  document.querySelector('#answer').textContent = data.answer;
  fillList('#flow', data.flow); fillList('#changes', data.possible_change_locations); fillList('#risks', data.risks); fillList('#tests', data.recommended_tests);
  const citations = document.querySelector('#citations'); citations.innerHTML = '';
  for (const c of data.citations) {
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = `${c.pbl} → ${c.file} → ${c.object} → ${c.member} → líneas ${c.start_line}-${c.end_line} → ${c.snapshot_id}`;
    const pre = document.createElement('pre'); pre.textContent = c.snippet;
    details.append(summary, pre); citations.appendChild(details);
  }
  statusNode.textContent = `${data.citations.length} cita(s) validadas`;
});

loadSnapshots().catch(() => { statusNode.textContent = 'No se pudo leer el índice'; });
