import test from 'node:test'
import assert from 'node:assert/strict'
import request, { getToken, setToken } from '../src/request/request.js'

function mockFetch(handler) {
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options })
    return handler(url, options)
  }
  return calls
}

function jsonRes(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }
}

test('GET 请求拼查询参数并返回统一信封', async () => {
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: [] }))
  const response = await request.get('/entities', { params: { entity: 'orders', status: '' } })
  assert.equal(response.code, 200)
  assert.match(calls[0].url, /^\/api\/entities\?entity=orders$/)
})

test('后端错误信封抛出可展示 message', async () => {
  mockFetch(async () => jsonRes(401, { code: 401, message: '账号或密码不正确', data: null }))
  await assert.rejects(() => request.post('/admin/login', {}), /账号或密码不正确/)
})

test('携带管理端 token 时附加 Authorization 头', async () => {
  setToken('admin-token-abc')
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: {} }))
  await request.get('/entities', { params: { entity: 'requirements' } })
  assert.equal(calls[0].options.headers.Authorization, 'Token admin-token-abc')
  setToken('')
})
