import request from '../request/request.js'
export const getOrders=(params={})=>request.get('/orders',{params});export const getOrder=(id)=>request.get('/order',{params:{id}})
