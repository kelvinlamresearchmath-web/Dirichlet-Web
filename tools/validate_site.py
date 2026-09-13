from pathlib import Path
from html.parser import HTMLParser
import json,collections,hashlib
root=Path(__file__).resolve().parents[1]
book=json.loads((root/'content/book.json').read_text(encoding='utf-8'))
class Inspect(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.refs=[];self.assets=[];self.math=0;self.links=0;self.scores=0;self.modes=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if 'data-index' in a:self.refs.append((a['id'],a['data-index']))
        if 'data-formula' in a:self.math+=1
        if 'data-score' in a:self.scores+=1;self.modes.append(a['class'])
        if tag=='a':
            assert self.links==0,'Nested hyperlink'
            self.links+=1
        for key in ['src','data-pdf']:
            if key in a and a[key].startswith('assets/'):self.assets.append(a[key])
    def handle_endtag(self,tag):
        if tag=='a':self.links-=1
entries={e['id']:e for e in book['entries']};occ={o['id']:o for o in book['occurrences']};found=[];formulas=0;scores=0;modes=[]
for chapter in book['chapters']:
    raw=(root/chapter['file']).read_bytes()
    payload=json.loads((root/chapter['payloadFile']).read_text(encoding='utf-8'))
    assert payload['id']==chapter['id'] and payload['html'].encode('utf-8')==raw
    assert len(raw)==chapter['htmlBytes'] and hashlib.sha256(raw).hexdigest()==chapter['htmlSha256']
    parser=Inspect();parser.feed((root/chapter['file']).read_text(encoding='utf-8'))
    assert len(parser.ids)==len(set(parser.ids)),chapter['title']+' duplicate anchors'
    assert chapter['background'].startswith('#') and len(chapter['background'])==7
    for oid,eid in parser.refs:
        assert eid in entries and oid in occ
        assert occ[oid]['chapterId']==chapter['id'] and occ[oid]['entryId']==eid
        assert oid in entries[eid]['occurrences']
        found.append(oid)
    for asset in parser.assets:assert (root/asset).is_file(),asset
    formulas+=parser.math
    scores+=parser.scores
    modes.extend(parser.modes)
assert set(found)==set(occ) and len(found)==len(occ)==110
assert formulas==596,formulas
assert scores==12,scores
pdf_manifest=json.loads((root/'content/pdf-svg.json').read_text(encoding='utf-8'))
referenced_pdfs={k for k in json.loads((root/'reports/import-report.json').read_text(encoding='utf-8'))['assets'] if k.lower().endswith('.pdf')}
assert referenced_pdfs==set(pdf_manifest['documents'])
for ch in book['chapters']:assert 'data-pdf=' not in (root/ch['file']).read_text(encoding='utf-8')
for doc in pdf_manifest['documents'].values():
    for page in doc['pages']:assert (root/page['file']).is_file()
report={'chapters':len(book['chapters']),'indexLinks':len(found),'formulaOccurrences':formulas,'inlineAndDisplayScores':scores,'scoreModes':dict(collections.Counter(modes)),'brokenIndexLinks':0,'missingReferencedAssets':0,'colorSource':'main1.tex xcolor commands'}
report.update(pdfDocuments=pdf_manifest['pdfCount'],pdfSvgPages=pdf_manifest['svgPages'])
(root/'reports/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report))
