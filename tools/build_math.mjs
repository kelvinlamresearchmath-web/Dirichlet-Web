import fs from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import katex from '../vendor/katex/dist/katex.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=JSON.parse(fs.readFileSync(path.join(root,'content/book.json'),'utf8'));
const formulas=JSON.parse(fs.readFileSync(path.join(root,'content/formulas.json'),'utf8'));
const errors=[];
const cache={};
const options={throwOnError:true,trust:false,strict:'ignore',output:'htmlAndMathml',maxExpand:1000,macros:{'\\twkkai':'\\text{#1}','\\mathlarger':'{#1}'}};
for(const [id,f] of Object.entries(formulas)) {
  try { cache[id]=katex.renderToString(f.tex,{...options,displayMode:f.display}); }
  catch(e) {errors.push({id,tex:f.tex,error:e.message});}
}
data.labels={};
for(const chapter of data.chapters) {
  const file=path.join(root,chapter.file);
  let html=fs.readFileSync(file,'utf8');
  html=html.replace(/<span class="math-source ([^"]+)" data-math="([^"]+)">[\s\S]*?<\/span>/g,(all,cls,id)=>cache[id]?`<span class="${cls}" data-formula="${id}">${cache[id]}</span>`:all);
  fs.writeFileSync(file,html);
  chapter.htmlBytes=Buffer.byteLength(html);
  chapter.htmlSha256=createHash("sha256").update(html).digest("hex");
  chapter.payloadFile=chapter.file.replace(/\.html$/,'.json');
  fs.writeFileSync(path.join(root,chapter.payloadFile),JSON.stringify({id:chapter.id,html}));
  for(const match of html.matchAll(/id="(label-[^"]+)"/g))data.labels[match[1]]=chapter.id;
}
function renderLabel(value) {
  return value.split(/(\$[^$]+\$)/g).map(part=>{
    if(part.startsWith('$')&&part.endsWith('$'))return katex.renderToString(part.slice(1,-1),{...options,displayMode:false});
    return part.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
  }).join('');
}
for(const e of data.entries) { e.html=renderLabel(e.label);e.root= e.levels[0]; }
fs.writeFileSync(path.join(root,'content/book.json'),JSON.stringify(data));
fs.writeFileSync(path.join(root,'reports/math-report.json'),JSON.stringify({total:Object.keys(formulas).length,rendered:Object.keys(cache).length,errors},null,2));
console.log(JSON.stringify({total:Object.keys(formulas).length,rendered:Object.keys(cache).length,errors}));
