export const createDraft=()=>({contact:'',phone:'',space:'厨房',houseType:'',dimensions:{length:null,width:null,height:null},style:'现代欧式',materials:[],budget:'',deliveryDate:'',description:'',floorPlan:''})
export function validateDraft(draft){const errors=[];if(!draft.contact?.trim())errors.push('请填写联系人');if(!draft.budget)errors.push('请选择预算范围');return errors}
// E1：File 对象无法过 sessionStorage（JSON 序列化），用内存暂存区在 选文件→确认→提交 间携带
const floorPlanHolder={file:null}
export function setFloorPlanFile(file){floorPlanHolder.file=file||null}
export function getFloorPlanFile(){return floorPlanHolder.file}
// E1：把草稿序列化为 FormData（multipart 提交，floorPlan 为 File 对象）
export function draftToFormData(draft){const fd=new FormData();Object.entries(draft).forEach(([k,v])=>{if(k==='dimensions'&&v&&typeof v==='object'){fd.append('dimensions',JSON.stringify(v))}else if(k==='materials'){fd.append('materials',JSON.stringify(v||[]))}else if(k==='floorPlan'){const f=getFloorPlanFile();if(f instanceof File)fd.append('floorPlan',f)}else if(v!==undefined&&v!==null&&v!==''){fd.append(k,v)}});return fd}
