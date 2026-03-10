import { useState } from 'react';

const STATES = ['active', 'offline', 'retired'];

const EMPTY = { hostname: '', ip_address: '', datacenter: '', state: 'active' };

export default function ServerForm({ server, onSave, onCancel }) {
  const [form, setForm] = useState(
    server
      ? { hostname: server.hostname, ip_address: server.ip_address, datacenter: server.datacenter, state: server.state }
      : { ...EMPTY }
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave(form);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.backdrop} onClick={onCancel}>
      <form style={styles.form} onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div style={styles.formHeader}>
          <h2 style={styles.formTitle}>{server ? 'Edit Server' : 'New Server'}</h2>
          <button type="button" style={styles.closeBtn} onClick={onCancel}>&times;</button>
        </div>

        {error && <div style={styles.formError}>{error}</div>}

        <label style={styles.label}>
          <span style={styles.labelText}>hostname</span>
          <input
            style={styles.input}
            value={form.hostname}
            onChange={set('hostname')}
            placeholder="web-server-01.prod"
            required
            autoFocus
          />
        </label>

        <label style={styles.label}>
          <span style={styles.labelText}>ip_address</span>
          <input
            style={styles.input}
            value={form.ip_address}
            onChange={set('ip_address')}
            placeholder="192.168.1.100"
            required
          />
        </label>

        <label style={styles.label}>
          <span style={styles.labelText}>datacenter</span>
          <input
            style={styles.input}
            value={form.datacenter}
            onChange={set('datacenter')}
            placeholder="us-east-1"
            required
          />
        </label>

        <label style={styles.label}>
          <span style={styles.labelText}>state</span>
          <select style={styles.input} value={form.state} onChange={set('state')}>
            {STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <div style={styles.actions}>
          <button type="button" style={styles.btnCancel} onClick={onCancel}>Cancel</button>
          <button type="submit" style={styles.btnSubmit} disabled={saving}>
            {saving ? 'Saving...' : server ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  );
}

const styles = {
  backdrop: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.6)',
    backdropFilter: 'blur(4px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  form: {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    padding: 24,
    width: '100%',
    maxWidth: 420,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  formHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  formTitle: {
    fontFamily: 'var(--font-mono)',
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--text)',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-muted)',
    fontSize: 22,
    cursor: 'pointer',
    padding: '0 4px',
  },
  formError: {
    padding: '8px 12px',
    background: 'var(--red-dim)',
    border: '1px solid var(--red)',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    color: 'var(--red)',
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  labelText: {
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    color: 'var(--text-muted)',
    letterSpacing: '0.02em',
  },
  input: {
    fontFamily: 'var(--font-mono)',
    fontSize: 14,
    padding: '8px 12px',
    background: 'var(--bg)',
    color: 'var(--text)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    outline: 'none',
    transition: 'border-color 0.15s',
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 8,
  },
  btnCancel: {
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    padding: '8px 16px',
    background: 'transparent',
    color: 'var(--text-muted)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    cursor: 'pointer',
  },
  btnSubmit: {
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    fontWeight: 500,
    padding: '8px 16px',
    background: 'var(--accent)',
    color: 'var(--bg)',
    border: 'none',
    borderRadius: 'var(--radius)',
    cursor: 'pointer',
  },
};
