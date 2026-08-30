import { useEffect, useState } from 'react'

// В контейнере Nginx этот путь должен проксироваться на сервис api (см. nginx.conf).
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: 640 }}>
      <h1>Polyglot Microservices — Frontend</h1>
      <p>Статика собрана через Vite и отдаётся через Nginx.</p>
      <h2>Статус API</h2>
      {error && <p style={{ color: 'crimson' }}>Ошибка соединения: {error}</p>}
      {!error && !health && <p>Проверка соединения с API...</p>}
      {health && <pre>{JSON.stringify(health, null, 2)}</pre>}
    </div>
  )
}

export default App
