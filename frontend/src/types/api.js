export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
}

export async function apiRequest(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: 'include',
    ...options,
    headers: {
      ...(options.body ? DEFAULT_HEADERS : {}),
      ...(options.headers || {}),
    },
  })

  if (response.status === 401) {
    window.location.href = '/login'
    throw new Error('未登录')
  }

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    const message = typeof payload === 'string' ? payload : payload?.error || '请求失败'
    throw new Error(message)
  }

  return payload
}
