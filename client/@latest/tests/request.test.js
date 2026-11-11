import test from 'node:test'
import assert from 'node:assert/strict'
import request, { setToken } from '../src/request/request.js'

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
  const response = await request.get('/products', { params: { category: '厨房', style: '' } })
  assert.equal(response.code, 200)
  assert.equal(calls[0].url, '/api/products?category=%E5%8E%A8%E6%88%BF')
})

test('后端错误信封抛出可展示 message', async () => {
  mockFetch(async () => jsonRes(400, { code: 400, message: '手机号格式不正确', data: null }))
  await assert.rejects(() => request.post('/register', {}), /手机号格式不正确/)
})

test('携带客户端 token 时附加 Authorization 头', async () => {
  setToken('test-token-123')
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: {} }))
  await request.get('/profile')
  assert.equal(calls[0].options.headers.Authorization, 'Token test-token-123')
  setToken('')
})

test('无 token 时不附加 Authorization 头', async () => {
  setToken('')
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: {} }))
  await request.get('/profile')
  assert.equal(calls[0].options.headers.Authorization, undefined)
})
