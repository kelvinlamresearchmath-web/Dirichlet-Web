from pathlib import Path
import subprocess,json,xml.etree.ElementTree as ET,hashlib
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
source_root=Path(r'M:\Dirichlet')
binary=Path(r'M:\lualatex\2026\bin\windows\pdftocairo.exe')
dest=root/'assets'/'pdf-svg';dest.mkdir(parents=True,exist_ok=True)
report=json.loads((root/'reports/import-report.json').read_text(encoding='utf-8'))
manifest={};count=0
for source,asset in report['assets'].items():
    if not source.lower().endswith('.pdf'):continue
    pdf=source_root/source
    reader=PdfReader(pdf);pages=[]
    for n,page in enumerate(reader.pages,1):
        out=dest/(Path(asset['file']).stem+f'-{n}.svg')
        result=subprocess.run([str(binary),'-svg','-f',str(n),'-l',str(n),str(pdf),str(out)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        if result.returncode:raise RuntimeError(source+' '+result.stderr)
        tree=ET.parse(out);svg=tree.getroot()
        for parent in svg.iter():
            for child in list(parent):
                if child.tag.split('}')[-1] in ['script','foreignObject']:parent.remove(child)
            for attr,value in list(parent.attrib.items()):
                local=attr.split('}')[-1]
                if local.startswith('on'):del parent.attrib[attr]
                elif local in ['href','src'] and not (value.startswith('#') or value.startswith(('data:image/png;base64,','data:image/jpeg;base64,'))):del parent.attrib[attr]
        ET.register_namespace('','http://www.w3.org/2000/svg');ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
        tree.write(out,encoding='utf-8',xml_declaration=True)
        pages.append({'file':out.relative_to(root).as_posix(),'width':float(page.mediabox.width),'height':float(page.mediabox.height),'vectorPaths':sum(1 for el in svg.iter() if el.tag.split('}')[-1]=='path')})
        count+=1
    manifest[source]={'sourceHash':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pages':pages}
    print(Path(source).name.encode('ascii','backslashreplace').decode()+': '+str(len(pages))+' SVG',flush=True)
output={'converter':'pdftocairo 25.02.0','pdfCount':len(manifest),'svgPages':count,'documents':manifest}
(root/'content/pdf-svg.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(len(manifest))+' PDFs / '+str(count)+' SVG pages complete.')
