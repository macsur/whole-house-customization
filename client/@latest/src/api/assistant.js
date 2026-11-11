import request from '../request/request.js'
export const sendMessage=(message)=>request.post('/assistant',{message})
