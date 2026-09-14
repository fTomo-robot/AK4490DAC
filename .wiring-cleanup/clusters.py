import math
exec(open('.wiring-cleanup/layout.py',encoding='utf-8-sig').read().split("if __name__")[0])
syms=children(root,'symbol'); libs={unq(s[1]):s for s in children(child(root,'lib_symbols'),'symbol')}
def pins(s):
 lib=libs[unq(val(s,'lib_id'))]; unit=int(val(s,'unit')); at=child(s,'at'); ox,oy,ang=map(float,at[1:]); theta=math.radians(ang); mirror=val(s,'mirror'); out=[]
 for sub in children(lib,'symbol'):
  u,b=map(int,unq(sub[1]).rsplit('_',2)[1:])
  if u not in (0,unit): continue
  for pin in children(sub,'pin'):
   x,y,a=map(float,child(pin,'at')[1:]); y=-y
   if mirror=='x': y=-y
   if mirror=='y': x=-x
   out.append((round(ox+x*math.cos(theta)+y*math.sin(theta),5),round(oy-x*math.sin(theta)+y*math.cos(theta),5)))
 return out
def coords(e):
 if e[0]=='wire': return [tuple(map(float,p[1:])) for p in children(child(e,'pts'),'xy')]
 if e[0]=='symbol': return pins(e)
 a=child(e,'at'); return [tuple(map(float,a[1:3]))] if a else []
elems=[e for e in root if isinstance(e,list) and e[0] in ('symbol','wire','junction','label','no_connect')]
parent=list(range(len(elems)))
def find(i):
 while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
 return i
def union(i,j): parent[find(i)]=find(j)
points={}
for i,e in enumerate(elems):
 for p in coords(e):
  if p in points: union(i,points[p])
  points[p]=i
# connect points on wire segments
for i,e in enumerate(elems):
 if e[0]!='wire':continue
 (x1,y1),(x2,y2)=coords(e)
 for (x,y),j in points.items():
  if min(x1,x2)-1e-5<=x<=max(x1,x2)+1e-5 and min(y1,y2)-1e-5<=y<=max(y1,y2)+1e-5 and abs((x-x1)*(y2-y1)-(y-y1)*(x2-x1))<1e-5:union(i,j)
groups={}
for i,e in enumerate(elems): groups.setdefault(find(i),[]).append(e)
def props(s):return {unq(x[1]):unq(x[2]) for x in children(s,'property')}
for ix,g in enumerate(groups.values()):
 ss=[e for e in g if e[0]=='symbol']; pp=[p for e in g for p in coords(e)]
 print(ix, [(props(s).get('Reference'),props(s).get('Value')) for s in ss],(min(p[0] for p in pp),min(p[1] for p in pp),max(p[0] for p in pp),max(p[1] for p in pp)),len(g))
