import re, json, pathlib, math
BASE=pathlib.Path(__file__).resolve().parent
SCH=BASE.parents[1]/'AK4490DAC.kicad_sch'
class Node(list):
    pass
class Quoted(str):
    pass
def parse(text):
    stack=[]; root=None
    for m in re.finditer(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text):
        t=m.group()
        if t=='(':
            n=Node(); n.start=m.start()
            if stack: stack[-1].append(n)
            else: root=n
            stack.append(n)
        elif t==')': stack.pop().end=m.end()
        else: stack[-1].append(Quoted(json.loads(t)) if t.startswith('"') else t)
    return root
def children(n,key): return [v for v in n if isinstance(v,list) and v and v[0]==key]
def child(n,key): return next(iter(children(n,key)),None)
def prop(n,key): return next(v[2] for v in children(n,'property') if v[1]==key)
def xy(n,key='at'): return tuple(map(float,child(n,key)[1:3]))
def pins(n,libs):
    lib=libs[child(n,'lib_id')[1]]; x,y=xy(n); a=float(child(n,'at')[3])*math.pi/180; u=int(child(n,'unit')[1]); out=[]
    mirror=child(n,'mirror')
    for s in children(lib,'symbol'):
        if int(s[1].split('_')[-2]) not in (0,u): continue
        for p in children(s,'pin'):
            px,py=xy(p)
            if mirror:
                if mirror[1]=='x': py=-py
                else: px=-px
            gx=x+px*math.cos(a)-py*math.sin(a); gy=y-px*math.sin(a)-py*math.cos(a)
            out.append({'num':child(p,'number')[1],'name':child(p,'name')[1], 'type':p[1], 'xy':[round(gx,4),round(gy,4)]})
    return out
if __name__=='__main__':
    doc=parse(SCH.read_text(encoding='utf-8')); libs={s[1]:s for s in children(child(doc,'lib_symbols'),'symbol')}
    for s in children(doc,'symbol'):
        print(json.dumps({'ref':prop(s,'Reference'),'value':prop(s,'Value'),'at':child(s,'at')[1:],'unit':child(s,'unit')[1],'pins':pins(s,libs)},ensure_ascii=False))
    for k in ('text','label','global_label'):
        for n in children(doc,k): print(k,n[1],xy(n))
