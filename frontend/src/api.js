const API_URL = import.meta.env.VITE_API_URL || '';
const BASE = `${API_URL}/servers`;

function parseError(detail, fallback) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((e) => e.msg).join('; ');
  return fallback;
}

export async function fetchServers() {
  const res = await fetch(BASE);
  if (!res.ok) throw new Error('Failed to fetch servers');
  return res.json();
}

export async function createServer(data) {
  const res = await fetch(BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(parseError(err.detail, 'Failed to create server'));
  }
  return res.json();
}

export async function updateServer(id, data) {
  const res = await fetch(`${BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(parseError(err.detail, 'Failed to update server'));
  }
  return res.json();
}

export async function deleteServer(id) {
  const res = await fetch(`${BASE}/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete server');
}
