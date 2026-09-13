"""Read main1.tex as data; never run TeX, shell escapes, or source scripts."""
from pathlib import Path
import re, json, html, hashlib, shutil, collections
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'M:\Dirichlet\main1.tex')
SOURCE_ROOT = SOURCE.parent
raw = SOURCE.read_text(encoding='utf-8')
text = re.sub(r'(?<!\\)%[^\n]*', '', raw)
body_start = text.index(r'\mainmatter')
body = text[body_start:]
entries, occurrences, formulas, assets, warnings = {}, [], [], {}, collections.Counter()
chapter_id = ''
color_report=json.loads((ROOT/'reports/colors.json').read_text(encoding='utf-8')) if (ROOT/'reports/colors.json').exists() else {'colors':{'white':'#ffffff','black':'#000000'},'chapters':{}}
score_report=json.loads((ROOT/'content/scores.json').read_text(encoding='utf-8')) if (ROOT/'content/scores.json').exists() else {'scores':{}}
pdf_report=json.loads((ROOT/'content/pdf-svg.json').read_text(encoding='utf-8')) if (ROOT/'content/pdf-svg.json').exists() else {'documents':{}}

def key(prefix, value):
    return prefix + hashlib.sha256(value.encode()).hexdigest()[:12]

def group(s, p, opening='{', closing='}'):
    while p < len(s) and s[p].isspace(): p += 1
    if p >= len(s) or s[p] != opening: return '', p
    depth, start = 1, p + 1
    p += 1
    while p < len(s):
        if s[p] == '\\' and p + 1 < len(s) and s[p+1] in '{}%': p += 2; continue
        if s[p] == opening: depth += 1
        elif s[p] == closing:
            depth -= 1
            if depth == 0: return s[start:p], p+1
        p += 1
    raise ValueError('Unbalanced source group: ' + s[start:start+100])

def plain(s):
    s = re.sub(r'\\(?:twkkai|textit|textbf|textrm)\{([^{}]*)\}', r'\1', s)
    return re.sub(r'\\[,;! ]', ' ', s).replace('{','').replace('}','').strip()

def split_index(s, delimiter):
    parts, depth, start, quote = [], 0, 0, False
    for i,c in enumerate(s):
        if quote: quote=False; continue
        if c == '"': quote=True; continue
        if c == '{': depth += 1
        if c == '}': depth -= 1
        if c == delimiter and depth == 0: parts.append(s[start:i]); start=i+1
    return parts+[s[start:]]

def index_info(raw_entry):
    main = split_index(raw_entry, '|')[0]
    levels = split_index(main, '!')
    displays = [split_index(level, '@')[-1] for level in levels]
    canonical = '!'.join(re.sub(r'\s+', ' ', x).strip() for x in displays)
    return key('idx-',canonical), displays

def index_link(value, out):
    eid, levels = index_info(value)
    entries.setdefault(eid, {'id':eid,'label':' › '.join(levels), 'levels':levels,'raw':value,'occurrences':[]})
    seq = sum(o['entryId']==eid and o['chapterId']==chapter_id for o in occurrences)
    oid = key('ref-',chapter_id+'|'+eid+'|'+str(seq))
    rec = {'id':oid,'entryId':eid,'chapterId':chapter_id,'raw':value}
    occurrences.append(rec); entries[eid]['occurrences'].append(oid)
    label = entries[eid]['label']
    attrs = f'id="{oid}" href="#index/{eid}" data-index="{eid}" aria-label="查看索引：{html.escape(label,quote=True)}"'
    candidate = re.split('[（(]', plain(levels[0]))[0].strip()
    if candidate and '$' not in candidate and '\\' not in candidate and out:
        last=out[-1]; needle=html.escape(candidate); pos=last.rfind(needle)
        if pos>=0 and len(last)-pos<450 and '<a ' not in last:
            out[-1]=last[:pos]+f'<a class="entity-link" {attrs}>'+needle+'</a>'+last[pos+len(needle):]
            rec['linkedText']=candidate
            return
    out.append(f'<a class="index-ref" {attrs}><sup>索引</sup></a>')
    rec['linkedText']=None

def math(s, display=False):
    anchors=''.join(f'<span id="{key("label-",v)}"></span>' for v in re.findall(r'\\label\{([^}]+)\}',s))
    s=re.sub(r'\\label\{[^}]+\}', '', s)
    while r'\tag{' in s:
        at=s.index(r'\tag{'); v,end=group(s,at+4)
        s=s[:at]+r'\qquad\text{（}'+v.replace('$','').replace(r'\(','').replace(r'\)','')+r'\text{）}'+s[end:]
    # Print-only font/size macros do not change the underlying expression.
    s=s.replace(r'\twkkai',r'\text').replace(r'\mathlarger',r'\mathord')
    s=re.sub(r'\\color\{[^}]*\}', '', s)
    s=s.replace(r'\(', '$').replace(r'\)', '$')
    mid=key('formula-',s+str(display))
    formulas.append({'id':mid,'tex':s,'display':display})
    return anchors+f'<span class="math-source {"display-math" if display else "inline-math"}" data-math="{mid}">{html.escape(s)}</span>'

def asset(path):
    source=(SOURCE_ROOT/path).resolve()
    source.relative_to(SOURCE_ROOT.resolve())
    if not source.is_file(): warnings['missing-asset:'+path]+=1; return None
    aid=key('asset-',path)
    name=aid+source.suffix.lower()
    dest=ROOT/'assets'/name
    if not dest.exists(): shutil.copyfile(source,dest)
    assets[path]={'file':'assets/'+name,'source':path}
    return assets[path]['file']

def image_asset(path):
    url=asset(path)
    if not url: return f'<span class="source-note">原稿插图：{html.escape(path)}（资源待核对）</span>'
    caption=html.escape(Path(path).stem)
    if path.lower().endswith('.pdf'):
        converted=pdf_report['documents'].get(path)
        if converted and converted['sourceHash']==hashlib.sha256((SOURCE_ROOT/path).read_bytes()).hexdigest():
            images=''.join(f'<img src="{item["file"]}" width="{round(item["width"])}" height="{round(item["height"])}" alt="{caption}，第 {n+1} 页" loading="lazy">' for n,item in enumerate(converted['pages']))
            return f'<span class="illustration svg-illustration" data-source-pdf="{html.escape(path,quote=True)}">{images}<a href="{url}" target="_blank" rel="noopener">原 PDF · {caption} ↗</a></span>'
        pages=PdfReader(SOURCE_ROOT/path).pages
        ratio=sum(float(page.mediabox.height)/float(page.mediabox.width) for page in pages)
        return f'<span class="illustration" data-pdf="{url}"><span class="pdf-pages" style="display:block;aspect-ratio:1 / {ratio:.6f};width:100%"></span><a href="{url}" target="_blank" rel="noopener">查看原版图谱 · {caption} ↗</a></span>'
    return f'<span class="illustration"><img src="{url}" alt="{caption}" loading="lazy"></span>'

def render(s):
    out=[]; p=0; bg_open=False; ink_open=False; ink='inherit'
    while p<len(s):
        if s.startswith('\\(',p) or s.startswith('\\[',p):
            display=s[p+1]=='['; end='\\]' if display else '\\)'; q=s.find(end,p+2)
            if q<0: raise ValueError('Unclosed math')
            out.append(math(s[p+2:q],display));p=q+2;continue
        if s[p]=='$':
            delim='$$' if s.startswith('$$',p) else '$'; q=p+len(delim)
            while q<len(s) and (not s.startswith(delim,q) or s[q-1]=='\\'): q+=1
            out.append(math(s[p+len(delim):q],len(delim)==2));p=q+len(delim);continue
        if s[p]=='{':
            v,p=group(s,p);out.append(render(v));continue
        if s[p]=='}': p+=1;continue
        if s[p]!='\\':
            q=p+1
            while q<len(s) and s[q] not in '\\${}': q+=1
            v=html.escape(s[p:q]);v=re.sub(r'\n\s*\n+', '<span class="paragraph-break"></span><span class="paragraph-indent" aria-hidden="true"></span>',v);v=v.replace('\n',' ')
            out.append(v.replace('~','&nbsp;'));p=q;continue
        command_start=p
        m=re.match(r'\\([A-Za-z]+|.)',s[p:],re.S)
        if not m: p+=1;continue
        cmd=m.group(1);p+=len(m.group())
        if p<len(s) and s[p]=='*': p+=1
        opt=''
        if p<len(s) and s[p]=='[': opt,p=group(s,p,'[',']')
        if cmd=='index': v,p=group(s,p);index_link(v,out);continue
        if cmd=='pagecolor':
            value,p=group(s,p);bg=color_report['colors'].get(value,'transparent')
            if ink_open:out.append('</span>');ink_open=False
            if bg_open:out.append('</span>')
            base=color_report['chapters'].get(chapter_id,{}).get('background')
            cls='source-page' + (' inset-page' if bg!=base else '')
            out.append(f'<span class="{cls}" style="background-color:{bg};color:{ink}">');bg_open=True;continue
        if cmd=='color':
            value,p=group(s,p);ink=color_report['colors'].get(value,'inherit')
            if ink_open:out.append('</span>')
            out.append(f'<span class="source-ink" style="color:{ink}">');ink_open=True;continue
        if cmd=='renewcommand':
            name,p=group(s,p);value,p=group(s,p)
            if name==r'\bibname':out.append('<span class="bibliography-heading">'+render(value)+'</span>')
            continue
        if cmd=='end': _,p=group(s,p);continue
        if cmd.startswith('Publisher'):
            counts=(SOURCE_ROOT/'wordcount.tex').read_text(encoding='utf-8')
            match=re.search(r'\\newcommand\{\\'+re.escape(cmd)+r'\}\{([^}]+)\}',counts)
            if match:out.append(html.escape(match.group(1)))
            continue
        if cmd=='begin':
            env,p=group(s,p);end='\\end{'+env+'}';q=-1;depth=1
            for boundary in re.finditer(r'\\(begin|end)\{'+re.escape(env)+r'\}',s[p:]):
                depth+=1 if boundary.group(1)=='begin' else -1
                if depth==0:q=p+boundary.start();break
            if q<0: warnings['unclosed-env:'+env]+=1;continue
            inner=s[p:q];p=q+len(end)
            if env in ['align*','gather*','equation*','align','gather','equation']:
                wrapper={'align*':'aligned','align':'aligned','gather*':'gathered','gather':'gathered'}.get(env)
                out.append(math(('\\begin{'+wrapper+'}'+inner+'\\end{'+wrapper+'}') if wrapper else inner,True));continue
            if env=='tikzpicture':
                graphics=re.findall(r'\\includegraphics(?:\[[^]]*\])?\s*\{([^}]+)\}',inner)
                if graphics:out.append('<span class="ornament-group">'+''.join(image_asset(g) for g in graphics)+'</span>')
                else:warnings['tikz-source-preserved']+=1;out.append('<span class="source-note">原稿图形（排版版中保留）</span>')
                continue
            if env=='tabular':
                _,a=group(inner,0);inner=inner[a:]
                cells=[]
                for row in re.split(r'\\\\',inner):
                    cells.append('<span class="table-row">'+''.join('<span class="table-cell">'+render(c)+'</span>' for c in row.split('&'))+'</span>')
                out.append('<span class="table-block">'+''.join(cells)+'</span>');continue
            if env=='thebibliography': _,a=group(inner,0);inner=inner[a:]
            names={'lmm':'引理','thrm':'定理','proof':'证明','rmk':'注','quote':'','center':'','flushright':''}
            tag='theorem' if env in ['lmm','thrm','proof','rmk'] else 'env-'+env
            heading=names.get(env,'')
            if inner.startswith('['): heading, a=group(inner,0,'[',']');inner=inner[a:]
            out.append(f'<span class="{tag}">'+(f'<strong>{render(heading)}</strong>' if heading else '')+render(inner)+'</span>');continue
        if cmd in ['twkkai','textit','emph','textbf','textrm','textnormal','underline','mbox','mathlarger']:
            v,p=group(s,p); cls='dialogue' if cmd=='twkkai' else ('strong' if cmd=='textbf' else 'emphasis')
            out.append(f'<span class="{cls}">'+render(v)+'</span>');continue
        if cmd=='lettrine':
            a,p=group(s,p);b,p=group(s,p);out.append('<span class="dropcap">'+render(a)+'</span>'+render(b));continue
        if cmd in ['includegraphics','includepdf']:
            v,p=group(s,p);out.append(image_asset(v));continue
        if cmd=='qraudio':
            name,p=group(s,p);_,p=group(s,p);_,p=group(s,p);url=asset(name+'.mp3')
            if url: out.append(f'<span class="music"><span>♫ {html.escape(name)}</span><audio controls preload="none" src="{url}" aria-label="播放 {html.escape(name)}"></audio></span>')
            continue
        if cmd=='lily':
            v,p=group(s,p);lid=key('lily-',v);(ROOT/'content'/f'{lid}.ly').write_text(v,encoding='utf-8')
            score=score_report['scores'].get(lid)
            if score and score['sourceHash']==hashlib.sha256(v.encode()).hexdigest():
                before=s[:command_start].rsplit('\n\n',1)[-1]
                before=re.sub(r'\\(?:kern|hspace)\s*[-+\d.]+(?:pt|em|cm|mm)?','',before).strip()
                mode='inline' if before else 'display'
                images=''
                for item in score['files']:
                    _,_,width,height=map(float,item['viewBox'].split())
                    images+=f'<img src="{item["file"]}" width="{round(width*10)}" height="{round(height*10)}" alt="本处乐谱" loading="lazy">'
                out.append(f'<span id="{lid}" class="score-{mode}" data-score="{lid}" role="img" aria-label="正文中的 LilyPond 乐谱">{images}</span>')
            else:
                warnings['uncompiled-score']+=1
                out.append(f'<span class="source-note">本处乐谱待生成</span>')
            continue
        if cmd in ['marginnote','footnote']:
            v,p=group(s,p);out.append('<span class="note" role="note">'+render(v)+'</span>')
            if p<len(s) and s[p]=='[': _,p=group(s,p,'[',']')
            continue
        if cmd=='adjustbox': _,p=group(s,p);v,p=group(s,p);out.append(render(v));continue
        if cmd=='href':
            url,p=group(s,p);v,p=group(s,p)
            if url.startswith(('https://','http://')): out.append(f'<a href="{html.escape(url,quote=True)}" target="_blank" rel="noopener">'+render(v)+'</a>')
            else: out.append(render(v))
            continue
        if cmd=='url': v,p=group(s,p);out.append(html.escape(v));continue
        if cmd=='label': v,p=group(s,p);out.append(f'<span id="{key("label-",v)}"></span>');continue
        if cmd in ['ref','eqref','autoref']:
            v,p=group(s,p);out.append(f'<a data-label="{key("label-",v)}" href="#{key("label-",v)}">相关{ "公式" if cmd=="eqref" else "段落"}</a>');continue
        if cmd=='bibitem': v,p=group(s,p);out.append(f'<span class="paragraph-break"></span><span class="paragraph-indent" aria-hidden="true"></span><span id="{key("bib-",v)}"></span>');continue
        if cmd=='cite': v,p=group(s,p);out.append(f'<span class="citation">[{html.escape(v)}]</span>');continue
        arity={'pagecolor':1,'color':1,'setlength':2,'renewcommand':2,'addcontentsline':3,'markboth':2,'thispagestyle':1,'vspace':1,'hspace':1,'rule':2,'input':1,'fontsize':2,'textcolor':1,'raisebox':1,'rotatebox':1,'scalebox':1}
        if cmd in arity:
            for _ in range(arity[cmd]): _,p=group(s,p)
            continue
        if cmd in ['kern','vskip','hskip']:
            m=re.match(r'\s*[-+\d.]+(?:pt|cm|mm|em|ex)?',s[p:]);p+=len(m.group()) if m else 0;continue
        if cmd in ['quad','qquad',',',';',' ','!']: out.append(' ');continue
        if cmd=='\\':out.append('<br>');continue
        if cmd in ['%','&','_','#','{','}','$']:out.append(html.escape(cmd));continue
        if cmd=='item':out.append('<br><span class="bullet">• </span>');continue
        if cmd in ['LaTeX','TeX']:out.append(cmd);continue
        if cmd in ['ldots','dots']:out.append('…');continue
        ignored=['mainmatter','backmatter','appendix','cleardoublepage','clearpage','newpage','noindent','centering','null','small','large','Large','huge','Huge','normalsize','bfseries','itshape','selectfont','printindex','AddSymbolsA','AddSymbolsB','AddSymbolsC','AddSymbolsD','AddSymbolsE','AddSymbolsF','end','hfill','vfill']
        if cmd not in ignored:
            warnings['command:'+cmd]+=1
    if ink_open:out.append('</span>')
    if bg_open:out.append('</span>')
    return ''.join(out)

# Chapter boundaries use balanced groups, not a regex for nested titles.
boundaries=[]
for m in re.finditer(r'\\chapter\*?',body):
    title,end=group(body,m.end());boundaries.append((m.start(),end,plain(title)))
# The afterword is printed manually in the source; preserve it as its own HTML section.
afterword=re.search(r'\\begin\{center\}\s*\{\\Huge 后记\}\s*\\end\{center\}',body)
if afterword: boundaries.append((afterword.start(),afterword.end(),'后记'))
appendix=body.find('\\part{附录}')
if appendix>=0: boundaries.append((appendix,appendix+len('\\part{附录}'),'附录与参考文献'))
boundaries.sort()
chapters=[]
for n,(start,end,title) in enumerate(boundaries):
    chapter_id=key('ch-',title)
    endpos=boundaries[n+1][0] if n+1<len(boundaries) else len(body)
    section=body[end:endpos]
    color=re.search(r'\\pagecolor\{([^}]+)\}',section)
    theme='night' if '对话录' in title else 'sage'
    if color and color.group(1)=='white':theme='paper'
    # The afterword's print-only blank-page setup is not part of the final chapter.
    reading_section=section
    if title=='奖章：终章':
        reading_section=re.sub(r'\\cleardoublepage\s*\\thispagestyle\{empty\}\s*\\pagecolor\{white\}\s*\\color\{black\}\s*\\vspace\*\{0[.]3\\textheight\}\s*\Z','',section)
    result=render(reading_section)
    # Retain exact extracted material per chapter for future importer refinements.
    (ROOT/'content'/f'{chapter_id}.tex').write_text(section,encoding='utf-8')
    (ROOT/'content'/f'{chapter_id}.html').write_text('<div class="prose">'+result+'</div>',encoding='utf-8')
    chapters.append({'id':chapter_id,'title':title,'theme':theme,'file':f'content/{chapter_id}.html','number':n+1,**color_report['chapters'].get(chapter_id,{})})

data={'title':'寻找狄利克雷','source':'main1.tex','chapters':chapters,'entries':list(entries.values()),'occurrences':occurrences}
(ROOT/'content'/'book.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'content'/'formulas.json').write_text(json.dumps({x['id']:x for x in formulas},ensure_ascii=False),encoding='utf-8')
source_indexes=len(re.findall(r'\\index\s*\{',text))
assert len(occurrences)==source_indexes, (len(occurrences),source_indexes)
report={'source':str(SOURCE),'sourceSha256':hashlib.sha256(raw.encode()).hexdigest(),'chapters':len(chapters),'sourceIndexCount':source_indexes,'linkedIndexCount':len(occurrences),'uniqueEntries':len(entries),'directTermLinks':sum(bool(x['linkedText']) for x in occurrences),'formulaOccurrences':len(formulas),'warnings':dict(warnings),'assets':assets}
(ROOT/'reports'/'import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['assets']},ensure_ascii=True))
