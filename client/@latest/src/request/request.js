// 木序客户端 HTTP 请求层：统一信封 {code, message, data}，错误抛出 message 供 ElMessage 展示。
// 后端地址：构建时由 VITE_API_BASE 指定（容器内为同源反代 /api，本地 dev 默认 localhost:8000）。
const BASE_URL = (import.meta.env?.VITE_API_BASE ?? '/api').replace(/\/$/, '')

const TOKEN_KEY = 'whc_client_token'

const tokenStore = typeof localStorage !== 'undefined' ? localStorage : {
  _mem: {},
  getItem(k) { return this._mem[k] ?? null },
  setItem(k, v) { this._mem[k] = v },
  removeItem(k) { delete this._mem[k] },
}

export function getToken() {
  return tokenStore.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) tokenStore.setItem(TOKEN_KEY, token)
  else tokenStore.removeItem(TOKEN_KEY)
}

async function send(method, url, payload, config = {}) {
  const headers = { ...(config.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Token ${token}`

  let body
  if (payload instanceof FormData) {
    body = payload
  } else if (payload !== undefined && method !== 'GET' && method !== 'DELETE') {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(payload ?? {})
  }

  const query = method === 'GET' || method === 'DELETE' ? config.params || {} : {}
  const qs = new URLSearchParams(
    Object.entries(query).filter(([, v]) => v !== '' && v !== undefined && v !== null),
  ).toString()

  const response = await fetch(`${BASE_URL}${url}${qs ? `?${qs}` : ''}`, {
    method,
    headers,
    body,
  })
  const json = await response.json().catch(() => ({}))
  if (!response.ok || (json.code && json.code >= 400)) {
    throw new Error(json.message || `请求失败（${response.status}）`)
  }
  return json
}

const request = {
  get: (url, config = {}) => send('GET', url, undefined, config),
  post: (url, body = {}, config = {}) => send('POST', url, body, config),
  put: (url, body = {}, config = {}) => send('PUT', url, body, config),
  delete: (url, config = {}) => send('DELETE', url, undefined, config),
}

export default request
