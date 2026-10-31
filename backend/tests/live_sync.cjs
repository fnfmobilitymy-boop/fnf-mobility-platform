// Deterministic sync tests without network, credentials or a running browser.
const {readFileSync}=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let now=100000;
const root={addEventListener(){},querySelectorAll(){return []},querySelector(){return null}};
const document={hidden:false,querySelector(s){return s==='#app'?root:s==='#language'?{}:null},addEventListener(){}};
const ctx=vm.createContext({document,localStorage:{getItem(){return null}},sessionStorage:{},setTimeout(){},setInterval(){},window:{addEventListener(){}},Date:{now:()=>now},console,FormData:class{},scrollX:0,scrollY:100,scrollTo(){},fetch(){throw Error('unexpected fetch')}});
let src=readFileSync('backend/static/app.js','utf8').replace(/^\$\('#language'\)\.onchange=.*$/m,'');vm.runInContext(src,ctx);
const run=s=>vm.runInContext(s,ctx);
(async()=>{
 run("syncStatus=()=>{};renderOrderList=()=>{lists++};let lists=0,renders=0;customerOrder=async o=>{state.order=o;renders++};adminOrder=async(id,o)=>{state.order=o;renders++};state.view='customer';state.oid='one';state.order={version:1};api=async()=>({version:2})");
 await run('syncUpdates()');assert.equal(run('renders'),1);await run('syncUpdates()');assert.equal(run('renders'),1);
 now+=5000;await run('syncUpdates()');assert.equal(run('renders'),1,'unchanged data must not replace DOM');
 run("state.view='admin';state.activeOrder='one';state.orders=[];api=async p=>p==='/admin/orders'?{orders:[{id:'two',status:'quoted',pending_receipts:1}]}:{version:3}");now+=5000;await run('syncUpdates()');assert.equal(run('lists'),1);assert.equal(run('renders'),2);
 run("document.hidden=true");now+=5000;await run('syncUpdates()');assert.equal(run('renders'),2);run('document.hidden=false');
 run("state.mutations=1;api=async()=>{throw Error('must skip during mutation')}");now+=5000;await run('syncUpdates()');assert.equal(run('syncFailures'),0);run('state.mutations=0');
 run("let resolve;api=()=>new Promise(r=>resolve=r);state.view='customer';state.order={version:1}");const pending=run('syncUpdates()');run('state.syncEpoch++;resolve({version:9})');await pending;assert.equal(run('state.order.version'),1,'in-flight stale response discarded');
 now+=5000;run("api=async()=>{throw Error('offline')}");await run('syncUpdates()');assert.equal(run('syncFailures'),1);now+=10000;run('api=async()=>({version:4})');await run('syncUpdates()');assert.equal(run('syncFailures'),0);assert.equal(run('state.order.version'),4);
 // Preserve typed values, checked boxes, selected files and focus when repainting.
 ctx.oldFile={type:'file',value:'receipt.png',checked:false,selectionStart:null,matches(){return true}};
 ctx.oldText={type:'text',value:'BANK-123',checked:false,selectionStart:2,selectionEnd:5,matches(){return true}};
 run("document.activeElement=oldText;let oldForm={id:'',dataset:{upload:'deposit'},elements:[oldText,oldFile]};let saved=saveDrafts({querySelectorAll:()=>[oldForm]})");
 ctx.freshText={value:'',matches(s){return s==='input,textarea,select'},focus(){this.focused=true},setSelectionRange(a,b){this.range=[a,b]}};ctx.freshFile={matches(){return true},replaceWith(file){ctx.retainedFile=file}};
 run("let freshForm={id:'',dataset:{upload:'deposit'},elements:[freshText,freshFile]};restoreDrafts({querySelectorAll:()=>[freshForm]},saved)");assert.equal(ctx.freshText.value,'BANK-123');assert.equal(ctx.freshText.focused,true);assert.deepEqual(ctx.freshText.range,[2,5]);assert.equal(ctx.retainedFile,ctx.oldFile);

 // Render every administrative tool with hostile client labels; no browser fetch is involved.
 vm.runInContext(readFileSync('backend/static/admin-tools.js','utf8'),ctx);
 ctx.toolHost={innerHTML:'',querySelectorAll(){return []}};
 ctx.search={value:'',oninput:null};ctx.results={innerHTML:''};
 document.querySelector=s=>s==='#admin-detail'?ctx.toolHost:s==='#client-search'?ctx.search:s==='#client-results'?ctx.results:s==='#app'?root:s==='#language'?{}:null;
 run("let sample={finance:{contract_value:100000,settled_project_value:50000,outstanding_project_value:50000,verified_stripe_fees:0},counts:{pending_receipts:1,open_tasks:1,overdue_tasks:1},today:'2026-10-31',projects:[{id:'one',name:'<script>alert(1)</script>',public_no:'QA-1',delivery:'building',priority:'urgent',due_date:'2026-11-30'}],receipts:[{id:'r1',order_id:'one',name:'<img src=x onerror=alert(1)>',customer:'QA',public_no:'QA-1',phase:'deposit',total:50000,method:'bank',reference:'REF'}],tasks:[{id:1,order_id:'one',title:'<script>bad</script>',customer:'QA',public_no:'QA-1',due_date:'2020-01-01',done:0,version:1}],clients:[{name:'<script>bad</script>',email:'qa@example.invalid',phone:'+60123456789',business:'QA',orders:1,contract_value:100000}]}");
 for(const tool of ['overview','receipts','tasks','clients','exports']){run(`state.tool='${tool}';renderTool(sample)`);assert(!ctx.toolHost.innerHTML.includes('<script>'));assert(!ctx.results.innerHTML.includes('<script>'));assert(ctx.toolHost.innerHTML.includes('KENNY STUDIO / TOOLS'))}
 run("let backgroundAlerts=0;notifyNewOrders=()=>backgroundAlerts++;state.view='admin';state.activeOrder='';state.orders=[];document.hidden=true;api=async()=>({orders:[{id:'background-new',status:'requested'}],queuedMail:0})");const listBefore=run('lists');now+=5000;await run('syncUpdates()');assert.equal(run('backgroundAlerts'),1,'background admin still checks new orders');assert.equal(run('lists'),listBefore,'background polling does not repaint forms');assert.equal(run('state.orders.length'),0,'keep UI baseline for visible resync');run('document.hidden=false');now+=5000;await run('syncUpdates()');assert.equal(run('lists'),listBefore+1);
 console.log('PASS background admin order polling and visible resync');
 console.log('PASS tools rendering: overview, receipts, tasks, clients, exports and escaped customer content');
 console.log('PASS live sync: automatic updates, pending badges, unchanged DOM, hidden tabs, mutation guard, stale response, reconnect, draft/file/focus preservation');
})().catch(e=>{console.error(e);process.exitCode=1});
