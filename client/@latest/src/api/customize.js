import request from '../request/request.js'
export const submitCustomization=(data)=>request.post('/requirements',data)
