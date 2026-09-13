"""Derive web RGB from source xcolor expressions, never sample a PDF/image."""
from pathlib import Path
import re,json,math,hashlib
from PIL import Image,ImageCms
root=Path(__file__).resolve().parents[1]
source=Path(r'M:\Dirichlet\main1.tex')
definitions=Path(r'M:\lualatex\2026\texmf-dist\tex\latex\graphics\dvipsnam.def')
xcolor=Path(r'M:\lualatex\2026\texmf-dist\tex\latex\xcolor\xcolor.sty')
# Natural models from xcolor.sty and the active dvipsnames option in main1.tex.
colors={'white':('gray',[1]),'black':('gray',[0]),'gray':('gray',[.5]),'purple':('rgb',[.75,0,.25]),'cyan':('cmyk',[1,0,0,0]),'red':('rgb',[1,0,0]),'blue':('rgb',[0,0,1]),'green':('rgb',[0,1,0])}
for name,values in re.findall(r'\\DefineNamedColor\{named\}\{([^}]+)\}\s*\{cmyk\}\{([^}]+)\}',definitions.read_text()):colors[name]=('cmyk',list(map(float,values.split(','))))

def convert(model,v,target):
    if model==target:return v
    if model=='gray':return [v[0]]*3 if target=='rgb' else [0,0,0,1-v[0]]
    if model=='cmyk':rgb=[1-min(1,a+v[3]) for a in v[:3]]
    elif model=='rgb':rgb=v
    else:raise ValueError(model)
    if target=='rgb':return rgb
    if target=='cmyk':
        cmy=[1-a for a in rgb];k=min(cmy);return [a-k for a in cmy]+[k]
    raise ValueError(target)

# Screen approximation of print CMYK, derived from source components only.
profile=Path(r'M:\lualatex\2026\tlpkg\tlgs\iccprofiles\default_cmyk.icc')
screen_transform=ImageCms.buildTransform(str(profile),ImageCms.createProfile('sRGB'),'CMYK','RGB')

def evaluate(expression):
    # A trailing separator carries no percentage/color pair; it does not add white.
    tokens=expression.strip().rstrip('!').split('!')
    model,value=colors[tokens[0]];value=list(value);steps=[]
    for i in range(1,len(tokens),2):
        fraction=float(tokens[i])/100
        if not 0<=fraction<=1:raise ValueError(expression)
        other=tokens[i+1] if i+1<len(tokens) else 'white'
        othermodel,otherval=colors[other]
        if fraction==0:model,value=othermodel,list(otherval)
        elif fraction!=1:
            # xcolor promotes a gray first operand to the second operand's model.
            if model=='gray' and othermodel!='gray':value=convert(model,value,othermodel);model=othermodel
            value=[fraction*a+(1-fraction)*b for a,b in zip(value,convert(othermodel,otherval,model))]
        steps.append({'percentage':fraction*100,'other':other,'model':model,'components':value})
    rgb=[max(0,min(255,math.floor(v*255+.5))) for v in convert(model,value,'rgb')]
    display_method='xcolor RGB'
    # Correct the shared opening/closing olive paper without retuning other chapters.
    if tokens[0]=='OliveGreen' and model=='cmyk':
        ink=tuple(max(0,min(255,math.floor(v*255+.5))) for v in value)
        rgb=list(ImageCms.applyTransform(Image.new('CMYK',(1,1),ink),screen_transform).getpixel((0,0)))
        display_method='source CMYK via default_cmyk ICC to sRGB'
    return {'rgb':rgb,'hex':'#'+''.join(f'{v:02x}' for v in rgb),'model':model,'components':value,'steps':steps,'displayMethod':display_method}

data=json.loads((root/'content/book.json').read_text(encoding='utf-8'))
full=re.sub(r'(?<!\\)%[^\n]*','',source.read_text(encoding='utf-8'))
expressions=set(re.findall(r'\\(?:pagecolor|color)\{([^}]+)\}',full[full.index(r'\mainmatter'):]))|{'white','black'}
computed={e:evaluate(e) for e in sorted(expressions)}
chapters={};background='white';foreground='black'
for ch in data['chapters']:
    text=(root/'content'/f'{ch["id"]}.tex').read_text(encoding='utf-8')
    commands=list(re.finditer(r'\\(pagecolor|color)\{([^}]+)\}',text))
    header=commands[:]
    # Chapter color declarations precede the prose, within the opening layout commands.
    for command in header:
        if command.start()>350:break
        if command.group(1)=='pagecolor':background=command.group(2)
        else:foreground=command.group(2)
    chapters[ch['id']]={'title':ch['title'],'expression':background,'textExpression':foreground,'background':computed[background]['hex'],'foreground':computed[foreground]['hex'],'rgb':computed[background]['rgb'],'transitions':[{'command':m.group(1),'expression':m.group(2),'rgb':computed[m.group(2)]['rgb']} for m in commands]}
    for m in commands:
        if m.group(1)=='pagecolor':background=m.group(2)
        else:foreground=m.group(2)
report={'source':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'xcolor natural-model sequential mixing; additive CMYK→RGB, with ICC screen approximation for OliveGreen; no PDF or image sampling','definitions':[str(definitions),str(xcolor)],'screenProfile':{'file':str(profile),'sha256':hashlib.sha256(profile.read_bytes()).hexdigest()},'colors':{e:v['hex'] for e,v in computed.items()},'calculations':computed,'chapters':chapters}
(root/'reports/colors.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['colors']))
