// 木序管理端 HTTP 请求层：统一信封 {code, message, data}，Token 鉴权。
// 后端地址：构建时由 VITE_API_BASE 指定（容器内同源 /api，本地 dev 默认 localhost:8000）。
const BASE_URL=(import.meta.env?.VITE_API_BASE ?? '/api').replace(/\/$/, '')
const TOKEN_KEY='whc_admin_token'
const tokenStore=typeof localStorage!=='undefined'?localStorage:{_mem:{},getItem(k){return this._mem[k]??null},setItem(k,v){this._mem[k]=v},removeItem(k){delete this._mem[k]}}
export const getToken=()=>tokenStore.getItem(TOKEN_KEY)||''
export const setToken=t=>{t?tokenStore.setItem(TOKEN_KEY,t):tokenStore.removeItem(TOKEN_KEY)}
async function send(m,u,p,c={}){const headers={...(c.headers||{})};const t=getToken();if(t)headers.Authorization=`Token ${t}`;let body;if(p!==undefined&&m!=='GET'&&m!=='DELETE'){headers['Content-Type']='application/json';body=JSON.stringify(p??{})}
const q=m==='GET'||m==='DELETE'?c.params||{}:{};const qs=new URLSearchParams(Object.entries(q).filter(([,v])=>v!==''&&v!==undefined&&v!==null)).toString()
const res=await fetch(`${BASE_URL}${u}${qs?`?${qs}`:''}`,{method:m,headers,body});const json=await res.json().catch(()=>({}))
if(res.status===401&&typeof location!=='undefined'&&location.pathname!=='/login'){setToken('');location.href='/login'}
if(!res.ok||(json.code&&json.code>=400))throw new Error(json.message||`请求失败（${res.status}）`)
return json}
export default{get:(u,c={})=>send('GET',u,undefined,c),post:(u,b={})=>send('POST',u,b),put:(u,b={})=>send('PUT',u,b),delete:(u,c={})=>send('DELETE',u,undefined,c)}