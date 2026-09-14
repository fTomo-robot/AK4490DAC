from inspect_sch import *
import collections, fitz
def nets(path):
    d=parse(path.read_text(encoding='utf-8')); out={}
    for n in children(child(d,'nets'),'net'):
        pts=frozenset((child(p,'ref')[1],child(p,'pin')[1]) for p in children(n,'node'))
        out[child(n,'name')[1]]=pts
    return out
b=nets(BASE/'before.net');a=nets(BASE/'after.net')
print('Net names and pin membership identical:',a==b)
for name in sorted(a.keys()|b.keys()):
    if a.get(name)!=b.get(name): print('NET DIFF',name,'REMOVED',b.get(name,set())-a.get(name,set()),'ADDED',a.get(name,set())-b.get(name,set()))
def erc(path):
    d=json.loads(path.read_text(encoding='utf-8')); vs=[v for s in d['sheets'] for v in s['violations']]
    return collections.Counter((v['severity'],v['type']) for v in vs)
print('ERC before:',erc(BASE/'before-erc.json'))
print('ERC after:',erc(BASE/'after-erc.json'))
p=fitz.open(BASE/'after.pdf')[0]
for name,rect in [('after',None),('digital',(190,80,402,180)),('reset',(198,180,319,234)),('supply',(350,235,435,285)),('usb',(540,0,618,94)),('analog',(225,275,265,317)),('input',(0,80,50,165)),('filters',(390,10,442,130)),('bypass',(52,8,78,40))]:
    clip=fitz.Rect(*(v*72/25.4 for v in rect)) if rect else None
    p.get_pixmap(matrix=fitz.Matrix(2 if rect is None else 3,2 if rect is None else 3),clip=clip).save(BASE/f'{name}.png')
