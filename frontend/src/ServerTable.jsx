const STATE_STYLES = {
  active: { color: 'var(--green)', bg: 'var(--green-dim)' },
  offline: { color: 'var(--yellow)', bg: 'var(--yellow-dim)' },
  retired: { color: 'var(--red)', bg: 'var(--red-dim)' },
};

function StateBadge({ state }) {
  const s = STATE_STYLES[state] || STATE_STYLES.offline;
  return (
    <span style={{
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      padding: '3px 8px',
      borderRadius: 'var(--radius)',
      background: s.bg,
      color: s.color,
      border: `1px solid ${s.color}33`,
    }}>
      {state}
    </span>
  );
}

export default function ServerTable({ servers, onEdit, onDelete }) {
  if (servers.length === 0) {
    return (
      <div style={styles.empty}>
        <div style={styles.emptyIcon}>~</div>
        <div>No servers registered</div>
      </div>
    );
  }

  return (
    <div style={styles.tableWrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>ID</th>
            <th style={styles.th}>Hostname</th>
            <th style={styles.th}>IP Address</th>
            <th style={styles.th}>Datacenter</th>
            <th style={styles.th}>State</th>
            <th style={{ ...styles.th, textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {servers.map((s) => (
            <tr key={s.id} style={styles.tr}>
              <td style={styles.tdMono}>{s.id}</td>
              <td style={styles.tdMono}>{s.hostname}</td>
              <td style={styles.tdMono}>{s.ip_address}</td>
              <td style={styles.td}>{s.datacenter}</td>
              <td style={styles.td}><StateBadge state={s.state} /></td>
              <td style={{ ...styles.td, textAlign: 'right' }}>
                <button style={styles.btnEdit} onClick={() => onEdit(s)}>Edit</button>
                <button style={styles.btnDelete} onClick={() => onDelete(s)}>Del</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  tableWrap: {
    overflowX: 'auto',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    background: 'var(--bg-surface)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    color: 'var(--text-muted)',
    textAlign: 'left',
    padding: '10px 16px',
    borderBottom: '1px solid var(--border)',
    whiteSpace: 'nowrap',
  },
  tr: {
    borderBottom: '1px solid var(--border)',
  },
  td: {
    padding: '10px 16px',
    fontSize: 14,
    verticalAlign: 'middle',
  },
  tdMono: {
    padding: '10px 16px',
    fontSize: 13,
    fontFamily: 'var(--font-mono)',
    verticalAlign: 'middle',
    color: 'var(--text)',
  },
  btnEdit: {
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    padding: '4px 10px',
    marginRight: 6,
    background: 'transparent',
    color: 'var(--accent)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    cursor: 'pointer',
  },
  btnDelete: {
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    padding: '4px 10px',
    background: 'transparent',
    color: 'var(--red)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    cursor: 'pointer',
  },
  empty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 8,
    padding: 64,
    fontFamily: 'var(--font-mono)',
    fontSize: 14,
    color: 'var(--text-muted)',
    border: '1px dashed var(--border)',
    borderRadius: 'var(--radius)',
  },
  emptyIcon: {
    fontSize: 28,
    color: 'var(--text-faint)',
  },
};
