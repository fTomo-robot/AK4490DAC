from clusters import *
from copy import deepcopy
import uuid

def num(x): return str(round(x,5)).rstrip('0').rstrip('.') if '.' in str(round(x,5)) else str(int(x))
def shift(n,dx,dy):
 for c in n:
  if not isinstance(c,list):continue
  if c[0] in ('at','xy','start','end') and len(c)>=3:
   c[1]=num(float(c[1])+dx);c[2]=num(float(c[2])+dy)
  else:shift(c,dx,dy)
def dump(n,indent=0):
 if not isinstance(n,list): return n
 if not any(isinstance(c,list) for c in n):return '('+' '.join(n)+')'
 return '('+' '.join(c for c in n if not isinstance(c,list))+''.join('\n'+'\t'*(indent+1)+dump(c,indent+1) for c in n if isinstance(c,list))+'\n'+'\t'*indent+')'
def add(s):root.append(parse(s))
def uid():return str(uuid.uuid4())
def text(s,x,y,size=2):add(f'(text {json.dumps(s)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{uid()}"))')
def box(x1,y1,x2,y2,title,sub):
 add(f'(polyline (pts (xy {x1} {y1}) (xy {x2} {y1}) (xy {x2} {y2}) (xy {x1} {y2}) (xy {x1} {y1})) (stroke (width 0.3) (type default)) (fill (type none)) (uuid "{uid()}"))')
 text(title,x1+5,y1+9,2.5);text(sub,x1+5,y1+16,1.4)
# Target coordinates for first non-power symbol in each physically connected cluster.
targets={0:(625,90),1:(588,60),2:(558,205),3:(725,295),4:(737,205),5:(468,90),6:(46,75),7:(558,60),8:(558,265),9:(588,90),10:(690,60),11:(690,90),12:(466,243),13:(690,205),14:(690,235),15:(690,120),16:(558,235),17:(558,90),18:(625,235),19:(780,205),20:(588,235),21:(690,265),22:(558,120),23:(588,205),24:(425,243),25:(737,60),26:(780,60),27:(429,185),28:(320,383),29:(665,383),30:(75,383),31:(488,320),32:(405,383),33:(429,297),34:(490,383),35:(521,316),36:(100,410),37:(35,383),38:(492,214),39:(473,214),40:(589,302),41:(126,410),42:(425,214),43:(463,320),44:(235,383),45:(521,291),46:(496,291),47:(150,383),48:(185,432),49:(161,432),50:(209,432),51:(510,316),52:(315,106),53:(190,89),54:(304,213),55:(304,253),56:(235,433),57:(320,433),58:(355,422),59:(355,452),60:(309,302)}
targets[52]=(315,140)
targets[53]=(190,105)
targets.update({3:(725,433),31:(550,456),33:(493,429),35:(611,456),38:(446,210),39:(425,210),40:(65,215),42:(467,210),43:(575,456),45:(603,426),46:(627,426),51:(631,456),24:(432,243)})
# Expand dense custom-symbol rows to 2.54 mm, including all connected stubs.
custom_names=['XU316-1024-QF60B-C24','ISOUSB211DPR']
custom_defs={}
for ix in (52,53):
 g=list(groups.values())[ix];s=next(e for e in g if e[0]=='symbol');oy=float(child(s,'at')[2])
 def stretch(n):
  for c in n:
   if not isinstance(c,list):continue
   if c[0] in ('at','xy'):c[2]=num(oy+2*(float(c[2])-oy))
   else:stretch(c)
 for e in g:stretch(e)
 lib=libs[unq(val(s,'lib_id'))]
 for sub in children(lib,'symbol'):
  for pin in children(sub,'pin'):child(pin,'at')[2]=num(2*float(child(pin,'at')[2]))
 ys=[float(child(pin,'at')[2]) for sub in children(lib,'symbol') for pin in children(sub,'pin')]
 for sub in children(lib,'symbol'):
  for r in children(sub,'rectangle'):
   child(r,'start')[2]=num(max(ys)+2.54);child(r,'end')[2]=num(min(ys)-2.54)
 for p in children(lib,'property'):
  if unq(p[1]) in ('Reference','Value'):child(p,'at')[1:]=['0',num(max(ys)+(7.62 if unq(p[1])=='Reference' else 5.08)),'0']
 custom_defs[unq(val(s,'lib_id')).split(':',1)[1]]=deepcopy(lib)
anchors={6:'J2',12:'U4',24:'U3',29:'U7',37:'J1'}
for ix,g in enumerate(groups.values()):
 ss=[e for e in g if e[0]=='symbol'];s=next((s for s in ss if props(s)['Reference']==anchors.get(ix)),None) or next((s for s in ss if not props(s)['Reference'].startswith('#')),ss[0]);a=child(s,'at'); tx,ty=targets[ix];dx=round((tx-float(a[1]))/1.27)*1.27;dy=round((ty-float(a[2]))/1.27)*1.27
 for e in g:shift(e,dx,dy)
# Place reference/value above each symbol, preserving pin geometry and definitions.
for s in syms:
 if props(s)['Reference'].startswith('#'):continue
 lib=libs[unq(val(s,'lib_id'))]; ps=pins(s); x,y=map(float,child(s,'at')[1:3]); top=min(p[1] for p in ps)
 # large IC bodies: actual rectangle bounds
 for sub in children(lib,'symbol'):
  for r in children(sub,'rectangle'):
   if float(child(s,'at')[3])==0: top=min(top,y-float(child(r,'start')[2]),y-float(child(r,'end')[2]))
 for p in children(s,'property'):
  if unq(p[1]) in ('Reference','Value'):
   a=child(p,'at');a[1:]=[num(x),num(top-(5 if unq(p[1])=='Reference' else 2.5)),'0']
   ef=child(p,'effects');j=child(ef,'justify')
   if j:ef.remove(j)
   size=child(child(ef,'font'),'size');size[1:]=['1.0','1.0']
   if props(s)['Reference'].startswith(('R','C')):
    a[1:]=[num(x+2.54),num(y+(-1.27 if unq(p[1])=='Reference' else 1.27)),'0']
    ef.append(['justify','left'])
child(root,'paper')[1:]=['"User"','820','530']
tb=child(root,'title_block');tb[:]=parse('(title_block (title "AK4490 USB DAC - functional layout") (comment 1 "USB-C > ISOUSB211 > XMOS XU316 > AK4490 > stereo line output") (comment 2 "Layout cleanup only. Existing incomplete connections retained."))')
text('AK4490 USB DAC',20,17,4)
text('SIGNAL FLOW   USB INPUT  >  ISOLATION  >  XMOS / I2S  >  DAC  >  ANALOG FILTER / LINE OUTPUT',20,26,2)
box(15,35,128,330,'01  USB-C INPUT','PC / USB bus power / USB_GND')
box(135,35,250,330,'02  USB ISOLATION','ISOUSB211 | USB_GND <-> main GND')
box(257,35,393,330,'03  XMOS / USB AUDIO','XU316 | I2S / QSPI boot / clock / debug')
box(400,35,533,330,'04  DAC / REFERENCES','AK4490 | digital control / analog reference')
box(540,35,800,175,'05  LEFT ANALOG OUTPUT','Differential input > filter / MUSES8920 > LINE_OUT_L')
box(540,180,800,330,'06  RIGHT ANALOG OUTPUT','Differential input > filter / MUSES8920 > LINE_OUT_R')
box(15,343,800,480,'07  POWER SUPPLIES','DC input / digital rails / DAC rails / analog +/-15 V')
text('QSPI BOOT FLASH',271,190,1.8);text('24 MHz CLOCK',271,236,1.8);text('JTAG DEBUG',271,282,1.8)
text('REFERENCE BYPASS',466,176,1.6);text('RESET SUPERVISORS',412,222,1.8);text('EXISTING UNUSED POWER STUBS',493,398,1.4)
text('AUXILIARY LOGIC',25,190,1.8)
text('OP-AMP SUPPLY',695,410,1.8)
text('USB signals connect by matching net labels.',25,145,1.5)
text('Isolation domains are retained.',145,145,1.5)
text('I2S GPIO assignments are provisional.',267,170,1.5)
text('Existing unconnected pins are retained.',25,465,1.5)
text('U3 / U4 reference duplicates exist in the source design.',410,465,1.5)
Path('AK4490DAC.kicad_sch').write_text(dump(root)+'\n',encoding='utf-8')
library=parse(Path('AK4490DAC.kicad_sym').read_text(encoding='utf-8'))
for i,item in enumerate(library):
 if isinstance(item,list) and item[0]=='symbol' and unq(item[1]).split(':')[-1] in custom_defs:
  replacement=deepcopy(custom_defs[unq(item[1]).split(':')[-1]]);replacement[1]=item[1];library[i]=replacement
Path('AK4490DAC.kicad_sym').write_text(dump(library)+'\n',encoding='utf-8')
