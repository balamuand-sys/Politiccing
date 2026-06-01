import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail
    if (detail) {
      err.message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    }
    return Promise.reject(err)
  },
)

// SSE streaming helper
export function streamSSE(
  url: string,
  onChunk: (chunk: string) => void,
  onDone: (meta?: Record<string, unknown>) => void,
  onError: (err: string) => void,
  method: 'GET' | 'POST' = 'GET',
  body?: unknown,
): () => void {
  let cancelled = false
  let controller: AbortController | null = null

  async function run() {
    controller = new AbortController()
    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      if (!res.ok) {
        const text = await res.text()
        let msg = `Serverfeil (${res.status})`
        try {
          const json = JSON.parse(text)
          msg = json.detail || msg
        } catch {}
        onError(msg)
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done || cancelled) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.chunk) onChunk(data.chunk)
              if (data.done) onDone(data)
            } catch {}
          }
        }
      }
    } catch (err: unknown) {
      if (!cancelled) {
        onError((err as Error).message || 'Ukjent feil')
      }
    }
  }

  run()
  return () => {
    cancelled = true
    controller?.abort()
  }
}
