const $=id=>document.getElementById(id);
let book,activeChapter,lastRead='',request=0,returnFocus=null,pdfjs;
const chapterMap=new Map(),entryMap=new Map(),occMap=new Map();
function readingHash(id,anchor=''){return `#read/${id}${anchor?'/'+anchor:''}`;}
function setSide(mode){for(const name of ['chapters','indices']){$(name+'-pane').hidden=name!==mode;$(name+'-tab').setAttribute('aria-pressed',String(name===mode));}}
$('chapters-tab').onclick=()=>setSide('chapters');
$('indices-tab').onclick=()=>{setSide('indices');$('index-search').focus();};
$('menu').onclick=()=>{const open=$('sidebar').classList.toggle('open');$('menu').setAttribute('aria-expanded',String(open));};
$('side-close').onclick=()=>{$('sidebar').classList.remove('open');$('menu').setAttribute('aria-expanded','false');$('menu').focus();};
let fontSize=20;
for(const [id,delta] of [['smaller',-1],['larger',1]])$(id).onclick=()=>{fontSize=Math.max(16,Math.min(28,fontSize+delta));document.documentElement.style.setProperty('--font-size',fontSize+'px');};
function closePanel(){if(location.hash.startsWith('#index/'))location.hash=lastRead||readingHash(book.chapters[0].id);else $('index-dialog').close();}
$('panel-close').onclick=closePanel;
$('index-dialog').addEventListener('cancel',e=>{e.preventDefault();closePanel();});
$('index-dialog').addEventListener('close',()=>{if(returnFocus?.isConnected)returnFocus.focus();});
document.addEventListener('click',e=>{const link=e.target.closest('a[data-index]');if(link){returnFocus=link;lastRead=readingHash(activeChapter,link.id);}});
$('index-search').oninput=()=>{const q=$('index-search').value.normalize('NFKC').toLowerCase().replace(/\s/g,'');let count=0;for(const a of $('index-list').children){a.hidden=!a.textContent.normalize('NFKC').toLowerCase().replace(/\s/g,'').includes(q);if(!a.hidden)count++;}$('index-count').textContent=`${count} 个索引条目`;};
window.addEventListener('scroll',()=>{const total=document.documentElement.scrollHeight-innerHeight;document.documentElement.style.setProperty('--progress',String(total>0?scrollY/total:0));},{passive:true});
async function renderIllustrations(container,token){
  const figures=[...container.querySelectorAll('[data-pdf]')];if(!figures.length)return;
  const observer=new IntersectionObserver(async items=>{for(const item of items){if(!item.isIntersecting)continue;observer.unobserve(item.target);const figure=item.target;
    try{pdfjs??=import('./vendor/pdfjs/build/pdf.mjs');const lib=await pdfjs;lib.GlobalWorkerOptions.workerSrc='./vendor/pdfjs/build/pdf.worker.mjs';const doc=await lib.getDocument({url:figure.dataset.pdf,isEvalSupported:false,cMapUrl:'./vendor/pdfjs/cmaps/',cMapPacked:true,standardFontDataUrl:'./vendor/pdfjs/standard_fonts/',wasmUrl:'./vendor/pdfjs/wasm/'}).promise;
      for(let n=1;n<=doc.numPages;n++){if(token!==request)break;const page=await doc.getPage(n),base=page.getViewport({scale:1}),scale=Math.min(900,Math.max(260,figure.clientWidth-26))/base.width,viewport=page.getViewport({scale});const canvas=document.createElement('canvas');canvas.width=Math.ceil(viewport.width*2);canvas.height=Math.ceil(viewport.height*2);canvas.style.width=viewport.width+'px';canvas.setAttribute('aria-label','原稿图谱第 '+n+' 页');figure.querySelector('.pdf-pages').append(canvas);await page.render({canvasContext:canvas.getContext('2d'),viewport,transform:[2,0,0,2,0,0],background:'#18231f'}).promise;}await doc.destroy();
    }catch{figure.querySelector('.pdf-pages').textContent='图谱未能载入，请打开下方原版链接。';}}
  },{rootMargin:'300px'});figures.forEach(f=>observer.observe(f));
}
async function showChapter(id,anchor){
 const ch=chapterMap.get(id)||book.chapters[0];
 if(activeChapter!==ch.id){const token=++request;$('article-body').innerHTML='<p class="loading">正在打开章节…</p>';const res=await fetch(ch.file);if(!res.ok)throw Error('章节载入失败');const html=await res.text();if(token!==request)return;
 activeChapter=ch.id;$('article').dataset.chapter=ch.id;$('article-body').innerHTML=html;$('chapter-title').textContent=ch.title;$('current-title').textContent=ch.title;$('kicker').textContent=`CHAPTER ${String(ch.number).padStart(2,'0')}`;$('article').dataset.theme=ch.theme;document.documentElement.style.setProperty('--chapter-bg',ch.background||'#56873e');document.documentElement.style.setProperty('--chapter-ink',ch.foreground||'#ffffff');document.title=ch.title+' · 寻找狄利克雷';
 for(const a of $('chapter-list').children)a.setAttribute('aria-current',String(a.dataset.chapter===ch.id));
 const pos=book.chapters.indexOf(ch);$('chapter-navigation').replaceChildren();for(const [offset,label] of [[-1,'上一章'],[1,'下一章']]){const other=book.chapters[pos+offset];if(other){const a=document.createElement('a');a.href=readingHash(other.id);const small=document.createElement('small');small.textContent=label;a.append(small,other.title);$('chapter-navigation').append(a);}}
 renderIllustrations($('article-body'),token);
 // Resolve labels against a generated map rather than guessing a target chapter.
 for(const a of $('article-body').querySelectorAll('[data-label]')){const target=book.labels?.[a.dataset.label];if(target)a.href=readingHash(target,a.dataset.label);}
 }
 $('sidebar').classList.remove('open');$('menu').setAttribute('aria-expanded','false');
 if(anchor){const el=document.getElementById(anchor);if(el){el.scrollIntoView({block:'center'});el.classList.remove('flash');void el.offsetWidth;el.classList.add('flash');}}else window.scrollTo(0,0);
 lastRead=readingHash(ch.id,anchor);
}
function showIndex(id){const entry=entryMap.get(id);if(!entry)return;$('entry-title').innerHTML=entry.html;$('entry-meta').textContent='来自原稿索引 · '+entry.occurrences.length+' 处标记';$('occurrence-list').replaceChildren();
 for(const ref of entry.occurrences){const occ=occMap.get(ref),ch=chapterMap.get(occ.chapterId);const a=document.createElement('a');a.href=readingHash(ch.id,ref);a.textContent=ch.title+' → 返回正文';$('occurrence-list').append(a);}
 const related=book.entries.filter(e=>e.root===entry.root&&e.id!==id);$('related-links').replaceChildren();$('related-heading').hidden=!related.length;for(const other of related){const a=document.createElement('a');a.href='#index/'+other.id;a.innerHTML=other.html;$('related-links').append(a);}
 if(!$('index-dialog').open)$('index-dialog').showModal();$('panel-close').focus();
}
async function route(){if(!book)return;const parts=location.hash.slice(1).split('/');try{if(parts[0]==='index'){if(!activeChapter)await showChapter(book.chapters[0].id);showIndex(parts[1]);}else{if($('index-dialog').open)$('index-dialog').close();await showChapter(parts[0]==='read'?parts[1]:book.chapters[0].id,parts[2]);}}catch(error){$('article-body').textContent='章节未能载入，请刷新重试。';console.error(error);}}
window.addEventListener('hashchange',route);
try{const res=await fetch('content/book.json');if(!res.ok)throw Error('目录载入失败');book=await res.json();for(const ch of book.chapters){chapterMap.set(ch.id,ch);const a=document.createElement('a');a.href=readingHash(ch.id);a.dataset.chapter=ch.id;const number=document.createElement('span');number.className='chapter-number';number.textContent=String(ch.number).padStart(2,'0');a.append(number,ch.title);$('chapter-list').append(a);}for(const e of book.entries){entryMap.set(e.id,e);const a=document.createElement('a');a.href='#index/'+e.id;a.innerHTML=e.html;$('index-list').append(a);}book.occurrences.forEach(o=>occMap.set(o.id,o));$('index-count').textContent=book.entries.length+' 个索引条目';await route();}catch(error){$('article-body').textContent='请通过本地预览地址打开本站，或刷新重试。';console.error(error);}
