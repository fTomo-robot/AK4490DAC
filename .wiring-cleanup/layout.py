import re,json,collections
from pathlib import Path
TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]')
def parse(s):
 stack=[]; root=None
 for t in TOKEN.findall(s):
  if t=='(':
   a=[]
   if stack: stack[-1].append(a)
   stack.append(a)
  elif t==')':
   root=stack.pop()
  else: stack[-1].append(t)
 return root
def children(n,k): return [x for x in n if isinstance(x,list) and x and x[0]==k]
def child(n,k): return next(iter(children(n,k)),None)
def val(n,k):
 c=child(n,k); return c[1] if c else None
def unq(x): return json.loads(x) if x and x.startswith('"') else x
p=Path('.wiring-cleanup/before.kicad_sch'); root=parse(p.read_text(encoding='utf-8'))
if __name__=='__main__':
 print(collections.Counter(x[0] for x in root if isinstance(x,list)))
 for s in children(root,'symbol'):
  props={unq(x[1]):unq(x[2]) for x in children(s,'property')}
  print(props.get('Reference'),props.get('Value'),child(s,'at'),val(s,'unit'))
 for t in children(root,'text'): print('TEXT',t[:3])
