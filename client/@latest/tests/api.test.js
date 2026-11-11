import test from 'node:test'
import assert from 'node:assert/strict'
import { getProducts, getProduct, getCases } from '../src/api/catalog.js'
import { getOrders } from '../src/api/orders.js'
import { login } from '../src/api/auth.js'

function mockFetch(handler) {
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options })
    return handler(url, options)
  }
  return calls
}

function jsonRes(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

test('产品列表请求携带分类查询参数', async () => {
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: [] }))
  await getProducts({ category: '厨房' })
  assert.match(calls[0].url, /\/api\/products\?category=%E5%8E%A8%E6%88%BF/)
})

test('产品详情请求携带 id 查询参数', async () => {
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: { id: 1 } }))
  await getProduct(1)
  assert.match(calls[0].url, /\/api\/product\?id=1/)
})

test('订单列表请求携带状态查询参数', async () => {
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: { items: [], total: 0 } }))
  await getOrders({ status: '进行中' })
  assert.match(calls[0].url, /\/api\/orders\?status=%E8%BF%9B%E8%A1%8C%E4%B8%AD/)
})

test('登录 POST 提交手机号与密码', async () => {
  const calls = mockFetch(async () => jsonRes(200, { code: 200, message: 'success', data: { token: 't' } }))
  await login({ phone: '13800000000', password: 'x12345678' })
  const sent = JSON.parse(calls[0].options.body)
  assert.equal(sent.phone, '13800000000')
})

test('后端拒绝登录时抛出 message', async () => {
  mockFetch(async () => jsonRes(401, { code: 401, message: '手机号或密码不正确', data: null }))
  await assert.rejects(() => login({ phone: '13800000000', password: '' }), /手机号或密码不正确/)
})
