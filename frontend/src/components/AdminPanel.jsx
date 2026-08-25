/**
 * AdminPanel - private feedback digest for the site owner.
 *
 * Shows questions the digital twin couldn't answer (or answered poorly)
 * so they can be turned into new training data. Gated by an admin key
 * (ADMIN_KEY on the backend) entered once and cached in sessionStorage.
 * Reachable at /admin - not linked anywhere in the public UI.
 */

import { useState, useEffect, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''
const SESSION_KEY = 'adt_admin_key'

function KeyEntry({ onSubmit }) {
  const [value, setValue] = useState('')

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (value.trim()) onSubmit(value.trim())
      }}
      style={styles.keyForm}
    >
      <h1 style={styles.title}>Feedback Digest</h1>
      <input
        type="password"
        autoFocus
        placeholder="Admin key"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={styles.input}
      />
      <button type="submit" style={styles.button}>Enter</button>
    </form>
  )
}

function FeedbackCard({ item, onMarkReviewed }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <span style={styles.badge}>{item.feedback_type}</span>
        {item.rating && (
          <span style={styles.badge}>{item.rating === 'positive' ? 'thumbs up' : 'thumbs down'}</span>
        )}
        <span style={styles.timestamp}>{new Date(item.created_at).toLocaleString()}</span>
      </div>
      <p style={styles.label}>User asked</p>
      <p style={styles.text}>{item.user_message}</p>
      {item.assistant_response && (
        <>
          <p style={styles.label}>Twin responded</p>
          <p style={styles.text}>{item.assistant_response}</p>
        </>
      )}
      {item.notes && (
        <>
          <p style={styles.label}>Notes</p>
          <p style={styles.text}>{item.notes}</p>
        </>
      )}
      {!item.reviewed && (
        <button style={styles.reviewButton} onClick={() => onMarkReviewed(item.id)}>
          Mark reviewed
        </button>
      )}
    </div>
  )
}

export function AdminPanel() {
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem(SESSION_KEY) || '')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showAll, setShowAll] = useState(false)

  const fetchFeedback = useCallback(async (key, unreviewedOnly) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `${API_URL}/api/admin/feedback?key=${encodeURIComponent(key)}&unreviewed_only=${!unreviewedOnly}`
      )
      if (res.status === 403) {
        sessionStorage.removeItem(SESSION_KEY)
        setAdminKey('')
        setError('Invalid admin key.')
        return
      }
      if (!res.ok) {
        setError(`Server error: ${res.status}`)
        return
      }
      setData(await res.json())
    } catch (err) {
      setError('Failed to reach the server.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (adminKey) fetchFeedback(adminKey, showAll)
  }, [adminKey, showAll, fetchFeedback])

  const handleKeySubmit = (key) => {
    sessionStorage.setItem(SESSION_KEY, key)
    setAdminKey(key)
  }

  const handleMarkReviewed = async (feedbackId) => {
    try {
      await fetch(
        `${API_URL}/api/admin/feedback/${feedbackId}/review?key=${encodeURIComponent(adminKey)}`,
        { method: 'POST' }
      )
      fetchFeedback(adminKey, showAll)
    } catch (err) {
      setError('Failed to mark as reviewed.')
    }
  }

  if (!adminKey) {
    return (
      <div style={styles.page}>
        <KeyEntry onSubmit={handleKeySubmit} />
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.headerRow}>
          <h1 style={styles.title}>Feedback Digest</h1>
          <label style={styles.toggle}>
            <input
              type="checkbox"
              checked={showAll}
              onChange={(e) => setShowAll(e.target.checked)}
            />
            Show reviewed too
          </label>
        </div>

        {loading && <p style={styles.muted}>Loading...</p>}
        {error && <p style={styles.errorText}>{error}</p>}

        {data && (
          <>
            <p style={styles.muted}>
              {data.unreviewed} unreviewed / {data.total} total
            </p>
            {data.items.length === 0 ? (
              <p style={styles.muted}>Nothing here. All caught up.</p>
            ) : (
              data.items.map((item) => (
                <FeedbackCard key={item.id} item={item} onMarkReviewed={handleMarkReviewed} />
              ))
            )}
          </>
        )}
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    backgroundColor: 'var(--color-bg)',
    color: 'var(--color-text)',
    padding: 'var(--spacing-xl)',
  },
  container: {
    maxWidth: '720px',
    margin: '0 auto',
  },
  keyForm: {
    maxWidth: '320px',
    margin: '4rem auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-md)',
  },
  title: {
    fontSize: 'var(--font-size-xl)',
    fontWeight: 600,
  },
  headerRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 'var(--spacing-lg)',
    flexWrap: 'wrap',
    gap: 'var(--spacing-md)',
  },
  toggle: {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-xs)',
    fontSize: 'var(--font-size-sm)',
    color: 'var(--color-text-secondary)',
  },
  input: {
    padding: 'var(--spacing-sm) var(--spacing-md)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--color-border)',
    background: 'var(--color-surface)',
    color: 'var(--color-text)',
    fontSize: 'var(--font-size-base)',
  },
  button: {
    padding: 'var(--spacing-sm) var(--spacing-md)',
    borderRadius: 'var(--radius-md)',
    border: 'none',
    background: 'var(--color-primary)',
    color: '#fff',
    cursor: 'pointer',
    fontSize: 'var(--font-size-base)',
  },
  reviewButton: {
    marginTop: 'var(--spacing-sm)',
    padding: 'var(--spacing-xs) var(--spacing-md)',
    borderRadius: 'var(--radius-full)',
    border: '1px solid var(--color-border)',
    background: 'transparent',
    color: 'var(--color-text-secondary)',
    cursor: 'pointer',
    fontSize: 'var(--font-size-sm)',
  },
  muted: {
    color: 'var(--color-text-muted)',
    fontSize: 'var(--font-size-sm)',
    marginBottom: 'var(--spacing-md)',
  },
  errorText: {
    color: '#f87171',
    fontSize: 'var(--font-size-sm)',
    marginBottom: 'var(--spacing-md)',
  },
  card: {
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--spacing-lg)',
    marginBottom: 'var(--spacing-md)',
  },
  cardHeader: {
    display: 'flex',
    gap: 'var(--spacing-sm)',
    alignItems: 'center',
    marginBottom: 'var(--spacing-sm)',
    flexWrap: 'wrap',
  },
  badge: {
    fontSize: '0.75rem',
    padding: '0.15rem 0.5rem',
    borderRadius: 'var(--radius-full)',
    background: 'var(--color-primary-light)',
    color: 'var(--color-primary)',
  },
  timestamp: {
    fontSize: '0.75rem',
    color: 'var(--color-text-muted)',
    marginLeft: 'auto',
  },
  label: {
    fontSize: '0.75rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: 'var(--color-text-muted)',
    marginTop: 'var(--spacing-sm)',
  },
  text: {
    fontSize: 'var(--font-size-sm)',
    color: 'var(--color-text)',
    whiteSpace: 'pre-wrap',
  },
}

export default AdminPanel
