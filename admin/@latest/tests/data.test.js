import test from'node:test';import assert from'node:assert/strict';import{queryEntity,updateRequirement,adminLogin}from'../src/api/admin.js'

function mockFetch(handler){const calls=[];globalThis.fetch=async(u,o)=>{calls.push({url:u,options:o});return handler(u,o)};return calls}
function jsonRes(status,body){return{ok:status>=200&&status<300,status,json:async()=>body}}

test('实体列表请求携带 entity 与 keyword 查询参数',async()=>{const calls=mockFetch(async()=>jsonRes(200,{code:200,message:'success',data:{items:[],total:0}}));await queryEntity('customers',{keyword:'张'});assert.match(calls[0].url,/\/api\/entities\?entity=customers&keyword=%E5%BC%A0/)})

test('需求更新以 PUT 提交 id 与状态',async()=>{const calls=mockFetch(async()=>jsonRes(200,{code:200,message:'success',data:{id:1,status:'已受理'}}));await updateRequirement(1,{status:'已受理'});assert.equal(calls[0].options.method,'PUT');const sent=JSON.parse(calls[0].options.body);assert.equal(sent.id,1);assert.equal(sent.status,'已受理')})

test('管理端登录 POST 指向 admin/login',async()=>{const calls=mockFetch(async()=>jsonRes(200,{code:200,message:'success',data:{token:'t'}}));await adminLogin({account:'admin',password:'x12345678'});assert.match(calls[0].url,/\/api\/admin\/login$/)})

test('后端拒绝登录时抛出 message',async()=>{mockFetch(async()=>jsonRes(401,{code:401,message:'账号或密码不正确',data:null}));await assert.rejects(()=>adminLogin({account:'admin',password:'x'}),/账号或密码不正确/)})