import { useState } from 'react'

const API_BASE = 'http://localhost:8000'

interface IndexResponse {
  success: boolean
  repo?: string | null
  chunks_indexed?: number | null
  files_indexed?: number | null
  reason?: string | null
}

interface SearchResult {
  file_path: string
  name: string
  kind: string
  start_line: number
  end_line: number
  source: string
  parent_class?: string | null
  docstring?: string | null
  distance: number
}

interface SearchResponse {
  results: SearchResult[]
  count: number
}

const styles = {
  page: {
    minHeight: '100vh',
    background: '#0f1419',
    color: '#e6edf3',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    padding: '2rem',
    maxWidth: '900px',
    margin: '0 auto',
  } as const,
  heading: {
    margin: '0 0 0.5rem',
    fontSize: '2rem',
    fontWeight: 700,
  } as const,
  tagline: {
    margin: '0 0 2rem',
    color: '#8b949e',
  } as const,
  section: {
    marginBottom: '2rem',
    padding: '1.25rem',
    background: '#161b22',
    borderRadius: '8px',
    border: '1px solid #30363d',
  } as const,
  sectionTitle: {
    margin: '0 0 1rem',
    fontSize: '1.1rem',
    fontWeight: 600,
  } as const,
  row: {
    display: 'flex',
    gap: '0.75rem',
    marginBottom: '0.75rem',
  } as const,
  input: {
    flex: 1,
    padding: '0.6rem 0.75rem',
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '6px',
    color: '#e6edf3',
    fontSize: '0.95rem',
  } as const,
  button: {
    padding: '0.6rem 1rem',
    background: '#238636',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    fontWeight: 600,
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
  } as const,
  buttonDisabled: {
    background: '#21262d',
    color: '#8b949e',
    cursor: 'not-allowed',
  } as const,
  message: {
    margin: '0.5rem 0 0',
    fontSize: '0.9rem',
  } as const,
  success: {
    color: '#3fb950',
  } as const,
  error: {
    color: '#f85149',
  } as const,
  loading: {
    color: '#8b949e',
    fontStyle: 'italic' as const,
  } as const,
  card: {
    marginBottom: '1rem',
    padding: '1rem',
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '6px',
  } as const,
  cardTitle: {
    margin: '0 0 0.35rem',
    fontSize: '1rem',
  } as const,
  meta: {
    margin: '0 0 0.5rem',
    color: '#8b949e',
    fontSize: '0.85rem',
  } as const,
  pre: {
    margin: 0,
    padding: '0.75rem',
    background: '#161b22',
    borderRadius: '4px',
    overflow: 'auto',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
    fontSize: '0.8rem',
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
  } as const,
}

function App() {
  const [url, setUrl] = useState('')
  const [repo, setRepo] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [indexing, setIndexing] = useState(false)
  const [searching, setSearching] = useState(false)
  const [indexMessage, setIndexMessage] = useState<string | null>(null)
  const [indexError, setIndexError] = useState<string | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)

  const handleIndex = async () => {
    setIndexing(true)
    setIndexMessage(null)
    setIndexError(null)
    setRepo(null)
    setResults([])
    setSearchError(null)

    try {
      const response = await fetch(`${API_BASE}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const data: IndexResponse = await response.json()

      if (!data.success) {
        setIndexError(data.reason ?? 'Indexing failed')
        return
      }

      setRepo(data.repo ?? null)
      setIndexMessage(
        `Indexed ${data.repo} — ${data.chunks_indexed ?? 0} chunks`,
      )
    } catch (err) {
      setIndexError(
        err instanceof Error ? err.message : 'Failed to reach the API',
      )
    } finally {
      setIndexing(false)
    }
  }

  const handleSearch = async () => {
    if (!repo) return

    setSearching(true)
    setSearchError(null)
    setResults([])

    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo, query, limit: 10 }),
      })

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const data: SearchResponse = await response.json()
      setResults(data.results)
    } catch (err) {
      setSearchError(
        err instanceof Error ? err.message : 'Failed to reach the API',
      )
    } finally {
      setSearching(false)
    }
  }

  const searchDisabled = !repo || searching

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>RepoLens</h1>
      <p style={styles.tagline}>
        Index a GitHub repository and search its code with natural language.
      </p>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Index Repository</h2>
        <div style={styles.row}>
          <input
            type="text"
            placeholder="https://github.com/owner/repo"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={styles.input}
          />
          <button
            type="button"
            onClick={handleIndex}
            disabled={indexing || !url.trim()}
            style={{
              ...styles.button,
              ...(indexing || !url.trim() ? styles.buttonDisabled : {}),
            }}
          >
            Index Repository
          </button>
        </div>
        {indexing && (
          <p style={{ ...styles.message, ...styles.loading }}>
            Indexing… this may take a minute
          </p>
        )}
        {indexMessage && (
          <p style={{ ...styles.message, ...styles.success }}>{indexMessage}</p>
        )}
        {indexError && (
          <p style={{ ...styles.message, ...styles.error }}>{indexError}</p>
        )}
      </section>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Search</h2>
        <div style={styles.row}>
          <input
            type="text"
            placeholder="e.g. command line argument parsing"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={!repo}
            style={{
              ...styles.input,
              ...(!repo ? { opacity: 0.6 } : {}),
            }}
          />
          <button
            type="button"
            onClick={handleSearch}
            disabled={searchDisabled || !query.trim()}
            style={{
              ...styles.button,
              ...(searchDisabled || !query.trim() ? styles.buttonDisabled : {}),
            }}
          >
            Search
          </button>
        </div>
        {searching && (
          <p style={{ ...styles.message, ...styles.loading }}>Searching…</p>
        )}
        {searchError && (
          <p style={{ ...styles.message, ...styles.error }}>{searchError}</p>
        )}
        {!repo && (
          <p style={{ ...styles.message, ...styles.loading }}>
            Index a repository first to enable search.
          </p>
        )}
      </section>

      {results.length > 0 && (
        <section>
          <h2 style={styles.sectionTitle}>
            Results ({results.length})
          </h2>
          {results.map((result, index) => (
            <article key={`${result.file_path}-${result.name}-${index}`} style={styles.card}>
              <p style={styles.cardTitle}>
                <strong>{result.name}</strong>
              </p>
              <p style={styles.meta}>
                {result.kind}
                {result.parent_class ? ` · in ${result.parent_class}` : ''}
                {' · '}
                {result.file_path}:{result.start_line}-{result.end_line}
                {' · '}
                distance {result.distance.toFixed(3)}
              </p>
              <pre style={styles.pre}>{result.source}</pre>
            </article>
          ))}
        </section>
      )}
    </div>
  )
}

export default App
