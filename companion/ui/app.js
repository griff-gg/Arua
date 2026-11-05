// Arua Companion page: all data goes through window.pywebview.api (Python).
'use strict';
const COLORS = ['yellow', 'blue', 'purple', 'red', 'green', 'rainbow'];
const LABEL = { yellow: 'Yellow', blue: 'Blue', purple: 'Purple', red: 'Red', green: 'Green', rainbow: 'Rainbow' };
let state = null;
let api = null;
const $ = (id) => document.getElementById(id);

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;   // item names are always text, never HTML
  return e;
}

const split = (s) => (s || '').split(',').map((x) => x.trim()).filter(Boolean);
const join = (a) => a.join(', ');

function setStatus(text, kind) {
  const s = $('status');
  s.textContent = text || '';
  s.className = 'status' + (kind ? ' ' + kind : '');
}

// lists: editing them also updates the selected profile, like Save in the game's Loot Filter tab
function syncProfile() {
  const p = state.profiles.items.find((x) => x.name === state.profiles.active);
  if (p) COLORS.forEach((c) => { p.lists[c] = state.lists[c]; });
}

function addName(name, color) {
  name = name.trim();
  if (!name) return;
  if (/[,"\\]/.test(name)) {   // lists are comma separated and the glow rules drop quotes: it could never match
    setStatus('Names with a comma, quote or backslash cannot be used in loot lists.', 'bad');
    return;
  }
  COLORS.forEach((c) => { state.lists[c] = join(split(state.lists[c]).filter((n) => n !== name)); });
  state.lists[color] = join(split(state.lists[color]).concat([name]));
  syncProfile();
  renderLists();
  setStatus(`Added ${name} to ${LABEL[color]}. Press Save to keep it.`);
}

function removeName(name, color) {
  state.lists[color] = join(split(state.lists[color]).filter((n) => n !== name));
  syncProfile();
  renderLists();
  setStatus('Removed. Press Save to keep it.');
}

function renderLists() {
  const box = $('lists');
  box.replaceChildren();
  $('lists-of').textContent = state.profiles.active
    ? `(profile ${state.profiles.active}; rarer colour wins, × removes)` : '(rarer colour wins, × removes)';
  COLORS.forEach((c) => {
    const row = el('div', 'list');
    row.append(el('span', 'lname ' + c, LABEL[c]));
    const pills = el('div', 'pills');
    split(state.lists[c]).forEach((n) => {
      const p = el('span', 'npill', n);
      const x = el('button', '', '×');
      x.title = 'Remove';
      x.onclick = () => removeName(n, c);
      p.append(x);
      pills.append(p);
    });
    if (!pills.children.length) pills.append(el('span', 'hint', 'empty'));
    row.append(pills);
    box.append(row);
  });
}

function resultRow(name, cat) {
  const r = el('div', 'result');
  r.append(el('span', 'name', name), el('span', 'cat', cat));
  COLORS.forEach((c) => {
    const d = el('button', 'dot ' + c);
    d.title = 'Add to ' + LABEL[c];
    d.onclick = () => addName(name, c);
    r.append(d);
  });
  return r;
}

let searchTimer = null;
function onSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    const q = $('search').value;
    const box = $('results');
    box.replaceChildren();
    box.hidden = true;
    if (q.trim().length < 2) return;
    const found = await api.search(q);
    found.forEach((i) => box.append(resultRow(i.name, i.cat)));
    if (!found.some((i) => i.name.toLowerCase() === q.trim().toLowerCase())) {
      box.append(resultRow(q.trim(), 'as typed'));   // names not in the list can still be added
    }
    box.hidden = false;
  }, 120);
}

function renderProfiles() {
  const box = $('profiles');
  box.replaceChildren();
  state.profiles.items.forEach((p) => {
    const b = el('button', 'ppill' + (p.name === state.profiles.active ? ' on' : ''), p.name);
    b.onclick = () => {
      state.profiles.active = p.name;
      COLORS.forEach((c) => { state.lists[c] = p.lists[c] || ''; });
      renderProfiles();
      renderLists();
      setStatus(`Profile ${p.name} selected. Press Save to keep it.`);
    };
    box.append(b);
  });
  if (!state.profiles.items.length) box.append(el('span', 'hint', 'No profiles yet.'));
}

function seg(id, value, onPick) {
  const box = $(id);
  box.querySelectorAll('button').forEach((b) => {
    b.classList.toggle('sel', String(b.dataset.v) === String(value));
    b.onclick = () => { onPick(b.dataset.v); seg(id, b.dataset.v, onPick); };
  });
}

function renderLook() {
  const s = state.settings;
  $('markers').querySelectorAll('.card').forEach((b) => {
    b.classList.toggle('sel', b.dataset.v === s.marker);
    b.onclick = () => { s.marker = b.dataset.v; renderLook(); };
  });
  $('drop-box').checked = s.drop_box;
  $('drop-outline').checked = s.drop_outline;
  seg('opacity', s.drop_opacity, (v) => { s.drop_opacity = Number(v); renderPreview(); });
  renderPreview();
}

function renderPreview() {
  const s = state.settings;
  const p = $('drop-preview');
  p.classList.toggle('box', s.drop_box);
  p.classList.toggle('outline', s.drop_outline);
  p.style.opacity = s.drop_opacity / 100;
}

function renderGroup() {
  const s = state.settings;
  seg('rows', s.group_rows, (v) => { s.group_rows = Number(v); });
  seg('columns', s.group_columns, (v) => { s.group_columns = Number(v); });
  $('class-icons').checked = s.class_icons;
  $('minimap').value = s.minimap_size;
  $('minimap-v').textContent = s.minimap_size;
  seg('bars', s.party_bars, (v) => { s.party_bars = v; });
}

function renderAll() {
  renderLists();
  renderProfiles();
  $('only').checked = state.lists.only_filtered;
  $('dim').checked = state.lists.dim_others;
  seg('size', state.lists.name_size, (v) => { state.lists.name_size = Number(v); });
  renderLook();
  renderGroup();
  $('items-info').textContent = state.items_patch ? `Item list from the game patch of ${state.items_patch}.` : 'No item list found.';
  if (!state.themes.length) setStatus('No Arua theme found in data\\ui\\themes. Install Arua first.', 'bad');
}

function wire() {
  document.querySelectorAll('.tab').forEach((t) => {
    t.onclick = () => {
      document.querySelectorAll('.tab').forEach((x) => x.classList.toggle('sel', x === t));
      document.querySelectorAll('.page').forEach((p) => { p.hidden = p.id !== 'tab-' + t.dataset.tab; });
    };
  });
  $('search').addEventListener('input', onSearch);
  $('search').addEventListener('focus', () => { if ($('results').children.length) $('results').hidden = false; });
  $('search').addEventListener('keydown', (e) => { if (e.key === 'Escape') $('results').hidden = true; });
  document.addEventListener('mousedown', (e) => {
    if (!e.target.closest('.box.search')) $('results').hidden = true;
  });
  $('close').onclick = () => api.close();
  $('only').onchange = (e) => { state.lists.only_filtered = e.target.checked; };
  $('dim').onchange = (e) => { state.lists.dim_others = e.target.checked; };
  $('drop-box').onchange = (e) => { state.settings.drop_box = e.target.checked; renderPreview(); };
  $('drop-outline').onchange = (e) => { state.settings.drop_outline = e.target.checked; renderPreview(); };
  $('class-icons').onchange = (e) => { state.settings.class_icons = e.target.checked; };
  $('minimap').oninput = (e) => { state.settings.minimap_size = Number(e.target.value); $('minimap-v').textContent = e.target.value; };
  $('profile-new').onclick = () => {
    const name = $('profile-name').value.replace(/[\[\]=<>&"\r\n]/g, '').trim().slice(0, 20);
    if (!name) { setStatus('Type a profile name first.', 'bad'); return; }
    const lists = {};
    COLORS.forEach((c) => { lists[c] = state.lists[c]; });
    const old = state.profiles.items.find((p) => p.name === name);
    if (old) old.lists = lists; else state.profiles.items.push({ name, lists });
    state.profiles.active = name;
    $('profile-name').value = '';
    renderProfiles();
    renderLists();
    setStatus(`Profile ${name} saved in the list. Press Save to keep it.`);
  };
  $('profile-del').onclick = () => {
    const name = state.profiles.active;
    if (!name) { setStatus('Click a profile first.', 'bad'); return; }
    state.profiles.items = state.profiles.items.filter((p) => p.name !== name);
    state.profiles.active = null;
    renderProfiles();
    renderLists();
    setStatus(`Profile ${name} deleted. Press Save to keep it.`);
  };
  $('update-items').onclick = async () => {
    setStatus('Downloading the item list…');
    const r = await api.update_item_list();
    setStatus(r.message, r.ok ? 'ok' : 'bad');
    if (r.ok) { state.items_patch = r.items_patch; $('items-info').textContent = `Item list from the game patch of ${r.items_patch}.`; }
  };
  $('save').onclick = async () => {
    setStatus('Saving…');
    const r = await api.save(state);
    let text = r.message;
    if (r.skipped && r.skipped.length) text += ' Skipped: ' + r.skipped.join('; ');
    setStatus(text, r.ok ? 'ok' : 'bad');
  };
}

window.addEventListener('pywebviewready', async () => {
  api = window.pywebview.api;
  state = await api.get_state();
  wire();
  renderAll();
});
