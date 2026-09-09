const form = document.querySelector('#ask-form');
const question = document.querySelector('#question');
const snapshot = document.querySelector('#snapshot');
const statusNode = document.querySelector('#status');
const result = document.querySelector('#result');
const submitButton = form.querySelector('button[type="submit"]');

function fillList(id, values) {
  const node = document.querySelector(id); node.innerHTML = '';
  for (const value of values) { const item = document.createElement('li'); item.textContent = value; node.appendChild(item); }
  node.parentElement.hidden = values.length === 0;
}

async function loadSnapshots() {
  const healthResponse = await fetch('/api/health');
  if (!healthResponse.ok) throw new Error('health');
  const health = await healthResponse.json();
  const items = await fetch('/api/snapshots').then(r => r.json());
  snapshot.innerHTML = '';
  for (const item of items) { const option = document.createElement('option'); option.value = item.snapshot_id; option.textContent = item.snapshot_id; snapshot.appendChild(option); }
  statusNode.textContent = health.indexed ? `${items[0].source_count} fuentes · ${items[0].chunk_count} fragmentos` : 'Sin índice: ejecute ragscate index';
  const chip = document.querySelector('#llm-chip');
  const llm = health.llm;
  chip.textContent = llm.enabled ? `${llm.model || 'Modelo sin configurar'} · ${llm.model_available ? 'Ollama listo' : 'Ollama no disponible'}` : 'LLM deshabilitado';
  chip.dataset.ready = String(Boolean(llm.available && llm.model_available));
  chip.title = llm.detail;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusNode.textContent = 'Recuperando y verificando evidencia…';
  submitButton.disabled = true;
  try {
    const response = await fetch('/api/ask', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question: question.value, snapshot_id: snapshot.value || null})});
    const data = await response.json();
    if (!response.ok) { statusNode.textContent = data.detail || 'Error'; return; }
    result.classList.remove('hidden');
    const badge = document.querySelector('#classification'); badge.textContent = data.classification; badge.dataset.kind = data.classification;
    document.querySelector('#answer').textContent = data.answer;
    const metric = data.generation.total_duration_ms == null ? '' : ` · ${(data.generation.total_duration_ms / 1000).toFixed(2)} s`;
    const speed = data.generation.tokens_per_second == null ? '' : ` · ${data.generation.tokens_per_second.toFixed(1)} tok/s`;
    document.querySelector('#generation').textContent = `${data.generation.model || 'Sin LLM'} · ${data.generation.detail}${metric}${speed}`;
    document.querySelector('#generation').dataset.status = data.generation.status;
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
  } catch (_error) {
    statusNode.textContent = 'No se pudo completar la consulta local';
  } finally {
    submitButton.disabled = false;
  }
});

loadSnapshots().catch(() => { statusNode.textContent = 'No se pudo leer el índice'; });
