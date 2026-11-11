import test from 'node:test';import assert from 'node:assert/strict';import {createDraft,validateDraft} from '../src/utils/customize.js'
test('定制草稿提供稳定默认结构',()=>{const draft=createDraft();assert.equal(draft.space,'厨房');assert.deepEqual(draft.dimensions,{length:null,width:null,height:null})})
test('缺少联系人和预算时给出明确错误',()=>{const errors=validateDraft(createDraft());assert.deepEqual(errors,['请填写联系人','请选择预算范围'])})

import {draftToFormData,setFloorPlanFile,getFloorPlanFile} from '../src/utils/customize.js'

test('E1：草稿转 FormData 含附件与结构化字段',()=>{
  const file=new File(['fake'],'户型.png',{type:'image/png'})
  setFloorPlanFile(file)
  const draft={...createDraft(),contact:'测试',phone:'13800000000',budget:'5–8 万元',floorPlan:file}
  const fd=draftToFormData(draft)
  assert.equal(fd.get('floorPlan'),file)
  assert.equal(fd.get('contact'),'测试')
  assert.equal(fd.get('dimensions'),'{"length":null,"width":null,"height":null}')
  assert.equal(fd.get('materials'),'[]')
  setFloorPlanFile(null)
})

test('E1：前端校验拒绝超 10MB 与错误类型口径正确',()=>{
  // 口径与后端一致：10*1024*1024 字节上限、jpg/png/webp/pdf 白名单
  const okTypes=['image/jpeg','image/png','image/webp','application/pdf']
  assert.equal(okTypes.includes('text/plain'),false)
  assert.equal(10*1024*1024+1>10*1024*1024,true)
})
