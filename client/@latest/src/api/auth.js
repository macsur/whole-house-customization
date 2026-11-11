import request from '../request/request.js'
export const login=(data)=>request.post('/login',data);export const register=(data)=>request.post('/register',data)
