import { useState, useEffect } from 'react';
import { fetchServers, createServer, updateServer, deleteServer } from './api';
import ServerTable from './ServerTable';
import ServerForm from './ServerForm';

export default function App() {
  const [servers, setServers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      setLoading(true);
      setServers(await fetchServers());
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async (data) => {
    if (editing) {
      await updateServer(editing.id, data);
    } else {
      await createServer(data);
    }
    setShowForm(false);
    setEditing(null);
    await load();
  };

  const handleEdit = (server) => {
    setEditing(server);
    setShowForm(true);
  };

  const handleDelete = async (server) => {
    if (!confirm(`Delete ${server.hostname}?`)) return;
    try {
      await deleteServer(server.id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditing(null);
  };

  const handleNew = () => {
    setEditing(null);
    setShowForm(true);
  };

  return (
    <div style={styles.shell}>
      <header style={styles.header}>
        <div style={styles.titleRow}>
          <h1 style={styles.title}>
            <span style={styles.prompt}>$</span> server-inventory
          </h1>
          <span style={styles.count}>
            {servers.length} node{servers.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div style={styles.toolbar}>
          <button style={styles.btnPrimary} onClick={handleNew}>
            + Add Server
          </button>
        </div>
      </header>

      {error && (
        <div style={styles.error}>
          <span style={styles.errorIcon}>!</span> {error}
          <button style={styles.errorDismiss} onClick={() => setError(null)}>&times;</button>
        </div>
      )}

      {showForm && (
        <ServerForm
          server={editing}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}

      {loading ? (
        <div style={styles.loading}>Loading...</div>
      ) : (
        <ServerTable
          servers={servers}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

const styles = {
  shell: {
    maxWidth: 1100,
    margin: '0 auto',
    padding: '32px 24px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: 24,
    paddingBottom: 16,
    borderBottom: '1px solid var(--border)',
  },
  titleRow: {
    display: 'flex',
    alignItems: 'baseline',
    gap: 16,
  },
  title: {
    fontFamily: 'var(--font-mono)',
    fontSize: 20,
    fontWeight: 600,
    color: 'var(--text)',
    letterSpacing: '-0.02em',
  },
  prompt: {
    color: 'var(--green)',
    marginRight: 2,
  },
  count: {
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    color: 'var(--text-muted)',
  },
  toolbar: {
    display: 'flex',
    gap: 8,
  },
  btnPrimary: {
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
  error: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 14px',
    marginBottom: 16,
    background: 'var(--red-dim)',
    border: '1px solid var(--red)',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    color: 'var(--red)',
  },
  errorIcon: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 18,
    height: 18,
    borderRadius: '50%',
    background: 'var(--red)',
    color: 'var(--bg)',
    fontSize: 11,
    fontWeight: 700,
    flexShrink: 0,
  },
  errorDismiss: {
    marginLeft: 'auto',
    background: 'none',
    border: 'none',
    color: 'var(--red)',
    fontSize: 18,
    cursor: 'pointer',
    padding: '0 4px',
  },
  loading: {
    fontFamily: 'var(--font-mono)',
    fontSize: 14,
    color: 'var(--text-muted)',
    textAlign: 'center',
    padding: 48,
  },
};
