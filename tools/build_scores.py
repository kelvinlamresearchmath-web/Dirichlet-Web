"""Compile the reviewed music-only snippets into static, sanitized SVG assets."""
from pathlib import Path
import subprocess,json,hashlib,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
binary=Path(r'M:\lilypond-2.24.4-mingw-x86_64\lilypond-2.24.4\bin\lilypond.exe')
work=root/'work'/'scores';work.mkdir(parents=True,exist_ok=True)
dest=root/'assets'/'scores';dest.mkdir(parents=True,exist_ok=True)
version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
manifest={}
for source in sorted((root/'content').glob('lily-*.ly')):
    music=source.read_text(encoding='utf-8')
    # These snippets use notation plus white-color overrides; no Scheme evaluation or includes.
    assert '#(' not in music and '\\include' not in music and '\\include' not in music.replace(' ','')
    prepared='\\version "2.24.4"\n\\pointAndClickOff\n\\header { tagline = ##f }\n\\paper { indent = 0\\mm line-width = 160\\mm ragged-right = ##t }\n\\score { {\n'+music+'\n} \\layout { } }\n'
    f=work/source.name;f.write_text(prepared,encoding='utf-8')
    prefix=work/source.stem
    result=subprocess.run([str(binary),'-dbackend=svg','-dno-point-and-click','-dcrop','-dno-print-pages','-o',str(prefix),str(f)],cwd=work,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    (work/(source.stem+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(source.name+' compilation failed: '+result.stderr[-1500:])
    candidates=sorted(work.glob(source.stem+'*.svg'))
    cropped=[p for p in candidates if '.cropped.' in p.name]
    selected=cropped or candidates
    if not selected:raise RuntimeError('No SVG for '+source.name)
    files=[]
    for n,path in enumerate(selected):
        tree=ET.parse(path);svg=tree.getroot()
        for parent in svg.iter():
            for child in list(parent):
                if child.tag.split('}')[-1] in ['script','foreignObject']:parent.remove(child)
            for attr in list(parent.attrib):
                local=attr.split('}')[-1]
                if local.startswith('on') or local in ['href','src']:del parent.attrib[attr]
        ET.register_namespace('','http://www.w3.org/2000/svg')
        output=dest/(source.stem+f'-{n+1}.svg');tree.write(output,encoding='utf-8',xml_declaration=True)
        files.append({'file':output.relative_to(root).as_posix(),'viewBox':svg.attrib.get('viewBox')})
    manifest[source.stem]={'files':files,'source':source.relative_to(root).as_posix(),'sourceHash':hashlib.sha256(music.encode()).hexdigest()}
    print(source.stem+' OK',flush=True)
report={'compiler':version,'count':len(manifest),'scores':manifest}
(root/'content'/'scores.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('All '+str(len(manifest))+' scores compiled.',flush=True)
