from layout import *
def compact(n): return '('+' '.join(compact(x) if isinstance(x,list) else x for x in n)+')'
def preserve(old,new):
 tokens=list(TOKEN.finditer(old)); pos=0
 def read():
  nonlocal pos
  m=tokens[pos];pos+=1
  if m.group()!='(':return (m.group(),m.start(),m.end(),[])
  cs=[]
  while tokens[pos].group()!=')':cs.append(read())
  end=tokens[pos].end();pos+=1
  return ([c[0] for c in cs],m.start(),end,cs)
 tree=read(); edits=[]
 def walk(t,n):
  v,a,b,cs=t
  if v==n:return
  if isinstance(v,list) and isinstance(n,list) and len(v)==len(n):
   for c,x in zip(cs,n):walk(c,x)
  elif isinstance(v,list) and isinstance(n,list) and len(n)>len(v) and v[0]=='kicad_sch':
   for c,x in zip(cs,n):walk(c,x)
   edits.append((b-1,b-1,'\n'+''.join('\t'+compact(x)+'\n' for x in n[len(v):])))
  else:edits.append((a,b,compact(n) if isinstance(n,list) else n))
 walk(tree,new)
 for a,b,s in sorted(edits,reverse=True):old=old[:a]+s+old[b:]
 return old
for suffix in ('kicad_sch','kicad_sym'):
 target=Path('AK4490DAC.'+suffix); current=parse(target.read_text(encoding='utf-8')); old=Path('.wiring-cleanup/before.'+suffix).read_text(encoding='utf-8'); target.write_text(preserve(old,current),encoding='utf-8')
