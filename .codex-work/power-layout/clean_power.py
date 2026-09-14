from inspect_sch import *
import uuid, shutil

backup=BASE/'before.kicad_sch'
if not backup.exists(): shutil.copy2(SCH,backup)
source=backup.read_text(encoding='utf-8')
doc=parse(source)
syms=children(doc,'symbol')
refs={prop(s,'Reference'):s for s in syms}
wires=children(doc,'wire')
removed=set(); changed=set(); added=[]
def fmt(v): return f'{float(v):.4f}'.rstrip('0').rstrip('.') if float(v) else '0'
def new(s): return parse(s)
def mark(n): changed.add(id(n))
def remove(n): removed.add(id(n))
def at(n,x,y,a=None):
    v=child(n,'at'); v[1:3]=[fmt(x),fmt(y)]
    if a is not None: v[3]=str(a)
def endpts(w): return [tuple(map(float,v[1:3])) for v in child(w,'pts')[1:]]
def wire(a,b):
    if a==b:return
    assert a[0]==b[0] or a[1]==b[1], (a,b)
    added.append(new(f'(wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})) (stroke (width 0) (type default)) (uuid "{uuid.uuid4()}"))'))
def path(*pts):
    for a,b in zip(pts,pts[1:]): wire(a,b)
def move(n,x,y):
    ox,oy=xy(n); dx=x-ox; dy=y-oy
    at(n,x,y)
    for p in children(n,'property'):
        px,py=xy(p); at(p,px+dx,py+dy)
    mark(n)
def capfields(s):
    x,y=xy(s)
    for p in children(s,'property'):
        if p[1] in ('Reference','Value'):
            at(p,x+2.54,y+(-1.27 if p[1]=='Reference' else 1.27),0)
            e=child(p,'effects'); j=child(e,'justify')
            if j: j[:]=['justify','left']
            else:e.append(new('(justify left)'))
    mark(s)
def pwrplace(s,x,y):
    move(s,x,y); at(s,x,y,0)
    ground='GND' in prop(s,'Value')
    for p in children(s,'property'):
        at(p,x,y+(3.81 if ground else -5.08) if p[1]=='Value' else y,0)
    mark(s)
def detach(ref):
    s=refs[ref]; pos=xy(s)
    ws=[w for w in wires if pos in endpts(w)]
    assert len(ws)==1,(ref,len(ws))
    w=ws[0]; ends=endpts(w); pin=next(p for p in ends if p!=pos)
    remove(w); return pin
def group(nums,axis,terminal):
    names=[f'#PWR{n:03}' for n in nums]
    ss=[refs[r] for r in names]
    assert len({prop(s,'Value') for s in ss})==1
    pts=[detach(r) for r in names]
    for s in ss[1:]: remove(s)
    pwrplace(ss[0],*terminal)
    # Vertical shared rail, split at every branch to make all joins explicit.
    ys=sorted(set([p[1] for p in pts]+[terminal[1]]))
    for p in pts: wire(p,(axis,p[1]))
    for y1,y2 in zip(ys,ys[1:]): wire((axis,y1),(axis,y2))
    wire((axis,terminal[1]),terminal)
def single(num,points):
    r=f'#PWR{num:03}'; pin=detach(r); path(pin,*points); pwrplace(refs[r],*points[-1])

# AK4118: configuration supply and ground branches, one symbol per rail.
group([12,15,17],203.2,(203.2,93.98))
group([11,13,14,16,18,19,20,21],208.28,(208.28,167.64))
group([22,23,24,25,26,27],251.46,(251.46,167.64))
# Move the two right-side signal label endpoints off the ground rail.
for l in children(doc,'label'):
    if (l[1] in ('BICK','SDATA') and xy(l)[0]==251.46) or (l[1] in ('RX0','RST_118') and xy(l)[0]==248.92):
        old=xy(l); move(l,255.27,old[1])
        for w in wires:
            if old in endpts(w):
                for p in child(w,'pts')[1:]:
                    if tuple(map(float,p[1:]))==old:p[1]=fmt(255.27)
                mark(w)

# AK4490: separate digital supply and ground rails with explicit junctions.
group([31,33,34,36,38,40],273.05,(273.05,92.71))
group([28,29,30,32,35,37,39,41,42,43,44],278.13,(278.13,170.18))
group([45,46,47,48],353.06,(353.06,170.18))

# Reset supervisors: put bypass capacitors next to the IC and share the rails.
for c,x in [('C28',208.28),('C29',304.8)]:
    move(refs[c],x,203.2); capfields(refs[c])
for nums,points,term in [
    ([1,3],[(228.6,193.04),(208.28,199.39)],(228.6,187.96)),
    ([6,8],[(266.7,193.04),(304.8,199.39)],(266.7,187.96)),
    ([2,4,5],[(228.6,213.36),(208.28,207.01),(218.44,222.25)],(228.6,227.33)),
    ([7,9,10],[(266.7,213.36),(304.8,207.01),(281.94,222.25)],(266.7,227.33))]:
    for num in nums:detach(f'#PWR{num:03}')
    for num in nums[1:]:remove(refs[f'#PWR{num:03}'])
    s=refs[f'#PWR{nums[0]:03}'];pwrplace(s,*term)
    yy=190.5 if nums[0] in (1,6) else 224.79
    xs=sorted(set(p[0] for p in points))
    for p in points:wire(p,(p[0],yy))
    for x1,x2 in zip(xs,xs[1:]):wire((x1,yy),(x2,yy))
    wire((term[0],yy),term)
for r in ('R25','R26'):capfields(refs[r])
for r in ('U3','U4'):
    s=refs[r];x,y=xy(s)
    for p in children(s,'property'):
        if p[1] in ('Reference','Value'):
            at(p,x+7.62,y+(-7.62 if p[1]=='Reference' else -5.08),0)
            child(p,'effects').append(new('(justify left)'))
    mark(s)

# VREF bias capacitors: side by side in free space beside the DAC.
for ref,xx,num,labelname in [('C30',365.76,49,'VREFHR_NET'),('C31',386.08,50,'VREFHL_NET')]:
    s=refs[ref]; old=xy(s)
    for w in wires:
        if (old[0],round(old[1]+3.81,4)) in endpts(w):remove(w)
    detach(f'#PWR{num:03}')
    move(s,xx,149.86);capfields(s)
    label=next(l for l in children(doc,'label') if l[1]==labelname and xy(l)[0]==old[0])
    move(label,xx,158.75);wire((xx,153.67),(xx,158.75))
    wire((xx,146.05),(xx,139.7))
wire((365.76,139.7),(386.08,139.7))
pwrplace(refs['#PWR049'],365.76,137.16);wire((365.76,137.16),(365.76,139.7));remove(refs['#PWR050'])

# DC/DC module, power input connector, and line-output returns.
group([51,53],369.57,(369.57,276.86))
single(52,[(361.95,257.81),(361.95,246.38)])
single(54,[(411.48,255.27),(411.48,246.38)])
single(56,[(424.18,260.35),(424.18,246.38)])
single(55,[(407.67,257.81),(407.67,276.86)])
single(59,[(8.89,101.6),(8.89,93.98)])
single(60,[(8.89,104.14),(8.89,111.76)])
for r in ('J1','#PWR059','#PWR060'):
    s=refs[r];x,y=xy(s);move(s,x+15.24,y-7.62)
for w in added:
    if all(p[0]<15 and 90<p[1]<115 for p in endpts(w)):
        for p in child(w,'pts')[1:]:p[1:3]=[fmt(float(p[1])+15.24),fmt(float(p[2])-7.62)]
single(63,[(431.8,22.86),(431.8,30.48)])
single(66,[(431.8,78.74),(431.8,86.36)])
group([61,62],424.18,(424.18,63.5))
group([64,65],424.18,(424.18,121.92))
# Keep both positive and negative supply symbols above the op-amp power unit.
single(58,[(251.46,309.88),(231.14,309.88),(231.14,287.02)])

# Optical receiver: allow room at the left for its upward supply route.
single(73,[(2.54,142.24),(2.54,129.54)])
single(72,[(5.08,139.7),(5.08,152.4)])
# Shift this small block into the page margin after routing.
optical=[refs['J3'],refs['#PWR072'],refs['#PWR073']]
for l in children(doc,'label'):
    if l[1]=='SPDIF_OPT' and xy(l)[0]<10:optical.append(l)
for n in optical:
    x,y=xy(n);move(n,x+20.32,y)
for w in wires+added:
    if id(w) in removed:continue
    pts=endpts(w)
    if all(p[0]<10 and 125<p[1]<155 for p in pts):
        for p in child(w,'pts')[1:]:p[1]=fmt(float(p[1])+20.32)
        mark(w)

# USB connector, shield, and CC pulldowns share their own isolated ground.
nums=[67,68,70,71]
points=[detach(f'#PWR{n:03}') for n in nums]
for n in nums[1:]:remove(refs[f'#PWR{n:03}'])
xs=sorted(p[0] for p in points)
for p in points:wire(p,(p[0],58.42))
for x1,x2 in zip(xs,xs[1:]):wire((x1,58.42),(x2,58.42))
pwrplace(refs['#PWR067'],561.34,60.96);wire((561.34,58.42),(561.34,60.96))
single(69,[(581.66,5.08),(581.66,0)])
for n in syms+children(doc,'label'):
    if id(n) not in removed and xy(n)[0]>=550 and xy(n)[1]<100:
        x,y=xy(n);move(n,x,y+22.86)
for w in wires+added:
    if id(w) not in removed and all(p[0]>=550 and p[1]<100 for p in endpts(w)):
        for p in child(w,'pts')[1:]:p[2]=fmt(float(p[2])+22.86)
        mark(w)
for r in ['R27','R28','C4']:capfields(refs[r])
# Give the optical receiver bypass capacitor room above its supply and below GND.
for r in ('C4','#PWR074','#PWR075'):
    s=refs[r];x,y=xy(s);move(s,x+19.05,y+3.81)
for w in wires:
    if all(p[0]==44.45 and 13<=p[1]<=25 for p in endpts(w)):
        for p in child(w,'pts')[1:]:p[1:3]=[fmt(float(p[1])+19.05),fmt(float(p[2])+3.81)]
        mark(w)
for p in children(refs['J2'],'property'):
    if p[1] in ('Reference','Value'):at(p,561.34,20.32 if p[1]=='Reference' else 22.86,0)
for p in children(refs['J3'],'property'):
    if p[1] in ('Reference','Value'):at(p,39.37,129.54 if p[1]=='Reference' else 132.08,0)
mark(refs['J3'])

# Normalize every remaining power symbol and place its net text clear of wires.
for s in syms:
    if prop(s,'Reference').startswith('#PWR') and id(s) not in removed:pwrplace(s,*xy(s))

# Explicit junctions at every branch of the newly shared buses.
activew=[w for w in wires+added if id(w) not in removed]
counts={}
for w in activew:
    for p in endpts(w):counts[p]=counts.get(p,0)+1
for p,count in counts.items():
    if count>=3:added.append(new(f'(junction (at {fmt(p[0])} {fmt(p[1])}) (diameter 0) (color 0 0 0 0) (uuid "{uuid.uuid4()}"))'))

# The existing sheet contains components beyond A3; include them in the print area.
paper=child(doc,'paper');paper[:]=['paper',Quoted('User'),'635','340'];mark(paper)
def render(n,level=1):
    def atom(v):return json.dumps(str(v),ensure_ascii=False) if isinstance(v,Quoted) else str(v)
    if not isinstance(n,list):return atom(n)
    if not any(isinstance(v,list) for v in n):return '('+' '.join(atom(v) for v in n)+')'
    head=[];body=[]
    for v in n:
        if isinstance(v,list):body.append('\t'*(level+1)+render(v,level+1))
        else:head.append(atom(v))
    return '('+' '.join(head)+'\n'+'\n'.join(body)+'\n'+'\t'*level+')'
edits=[]
for n in doc:
    if not isinstance(n,list):continue
    if id(n) in removed:edits.append((n.start,n.end,''))
    elif id(n) in changed:edits.append((n.start,n.end,render(n)))
edits.append((doc.end-1,doc.end-1,'\n'+'\n'.join('\t'+render(n) for n in added)+'\n'))
result=source
for a,b,text in sorted(edits,reverse=True):result=result[:a]+text+result[b:]
SCH.write_text(result,encoding='utf-8',newline='\n')
print(f'Power symbols: {sum(prop(s,"Reference").startswith("#PWR") for s in syms)} -> {sum(prop(s,"Reference").startswith("#PWR") and id(s) not in removed for s in syms)}')
print(f'Updated {len(changed)} objects, removed {len(removed)}, added {len(added)}')
