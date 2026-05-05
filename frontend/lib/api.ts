export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

interface FetchError extends Error {
  info?: unknown;
  status?: number;
}

export const fetcher = async (url: string) => {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`
  const res = await fetch(fullUrl)
  
  if (!res.ok) {
    const error: FetchError = new Error("An error occurred while fetching the data.")
    // Attach extra info to the error object.
    const info = await res.json().catch(() => ({}))
    error.info = info
    error.status = res.status
    throw error
  }
  
  return res.json()
}
export const poster = async (url: string, body?: Record<string, unknown> | unknown) => {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`
  const res = await fetch(fullUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  
  if (!res.ok) {
    const error: FetchError = new Error("An error occurred while posting data.")
    const info = await res.json().catch(() => ({}))
    error.info = info
    error.status = res.status
    throw error
  }
  
  return res.json()
}
