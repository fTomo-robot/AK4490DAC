"""Reproducible, pin-checked XU316 / AK4490 schematic. Coordinates are 2.54 mm units."""
from pathlib import Path
import sys, uuid, copy, json, math, collections
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.codex-work/power-layout'))
from inspect_sch import parse, children, child, prop, Quoted
KLIB=Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
Q=lambda s:json.dumps(str(s),ensure_ascii=False)
mm=lambda n:f'{n*2.54:.4f}'.rstrip('0').rstrip('.')
uid=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'AK4490DAC/XU316/v1/'+s))
ROOT_ID=uid('root')
LIB={};CUSTOM={};META={};EXPECTED={};COMP={};PAGES=[]
def dump(n):
    if isinstance(n,list):return '('+' '.join(dump(x) for x in n)+')'
    return Q(n) if isinstance(n,Quoted) else str(n)
def std(key):
    if key in LIB:return LIB[key]
    ns,name=key.split(':'); d=parse((KLIB/(ns+'.kicad_sym')).read_text(encoding='utf-8'))
    allsyms={s[1]:s for s in children(d,'symbol')}
    def resolve(name):
        s=copy.deepcopy(allsyms[name]); ext=child(s,'extends')
        if ext:
            base=resolve(ext[1]); own={p[1]:p for p in children(s,'property')}
            for p in children(base,'property'):
                if p[1] in own:base[base.index(p)]=own[p[1]]
            for sub in children(base,'symbol'):sub[1]=Quoted(name+'_'+sub[1].split('_')[-2]+'_'+sub[1].split('_')[-1])
            base[1]=Quoted(name);s=base
        return s
    s=resolve(name);s[1]=Quoted(key);LIB[key]=s;return s
def custom(name,units,footprint,desc,url=''):
    """units = (width, height, [(number,name,x,y,angle,type), ...])."""
    key='XU316DAC:'+name
    body=f'(symbol {Q(key)} (pin_names (offset 0.762)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 0 0) (effects (font (size 1.27 1.27)))) (property "Value" {Q(name)} (at 0 0 0) (effects (font (size 1.27 1.27)))) (property "Footprint" {Q(footprint)} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Datasheet" {Q(url)} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Description" {Q(desc)} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    for i,(w,h,ps) in enumerate(units,1):
        body+=f'(symbol {Q(name+"_"+str(i)+"_1")} (rectangle (start {mm(-w/2)} {mm(h/2)}) (end {mm(w/2)} {mm(-h/2)}) (stroke (width 0.254) (type default)) (fill (type background)))'
        for num,pn,x,y,a,typ in ps:
            body+=f'(pin {typ} line (at {mm(x)} {mm(y)} {a}) (length 5.08) (name {Q(pn)} (effects (font (size 1.016 1.016)))) (number {Q(num)} (effects (font (size 1.016 1.016)))))'
        body+=')'
    s=parse(body+')');LIB[key]=s;CUSTOM[name]=s;META[key]=units;return key
def box(w,h,left=(),right=(),top=(),bottom=()):
    ps=[]
    for entries,side in [(left,'L'),(right,'R'),(top,'T'),(bottom,'B')]:
        for num,name,pos,typ in entries:
            x,y,a={'L':(-w/2-2,pos,0),'R':(w/2+2,pos,180),'T':(pos,h/2+2,270),'B':(pos,-h/2-2,90)}[side]
            ps.append((str(num),name,x,y,a,typ))
    return w,h,ps
def pspec(s,unit):
    out={}
    for sub in children(s,'symbol'):
        if int(sub[1].split('_')[-2]) not in (0,unit):continue
        for p in children(sub,'pin'):
            at=child(p,'at');out[child(p,'number')[1]]=(float(at[1])/2.54,float(at[2])/2.54,float(at[3]),p[1])
    return out
class Sheet:
    def __init__(self,name,title,page):
        self.name=name;self.title=title;self.page=page;self.id=uid(name);self.sheetid=uid('sheet/'+name);self.items=[];self.used=set();self.inst={};self.segments=[];self.seq=0;PAGES.append(self)
    def add(self,s):self.items.append(s)
    def uuid(self,kind):self.seq+=1;return uid(self.name+'/'+kind+'/'+str(self.seq))
    def text(self,text,x,y,size=1.27):self.add(f'(text {Q(text)} (at {mm(x)} {mm(y)} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{self.uuid("text")}"))')
    def heading(self,text,x,y):self.text(text,x,y,1.778)
    def sym(self,key,ref,value,x,y,angle=0,unit=1,fp=None,mpn=None,note=''):
        lib=LIB[key] if key in LIB else std(key);self.used.add(key)
        footprints=[p[2] for p in children(lib,'property') if p[1]=='Footprint'];fp=fp if fp is not None else (footprints[0] if footprints else '')
        suid=uid('component/'+ref)
        actualid=uid('component/'+ref+'/'+str(unit))
        fields=[];passive=key in ('Device:R','Device:C','Device:C_Polarized','Device:L','Device:FerriteBead','Device:D','Device:D_Schottky','Device:Fuse','Device:Crystal','Device:Crystal_GND24')
        if key in META:
            w,h,_=META[key][unit-1];fx=x;fy=y-h/2-5
        else:fx=x;fy=y-6
        if passive and angle==0:fx=x+2;fy=y-1
        for pn,pv,px,py,hide in [('Reference',ref,fx,fy,False),('Value',value,fx,fy+1.5,False),('Footprint',fp,x,y,True),('Datasheet',next((p[2] for p in children(lib,'property') if p[1]=='Datasheet'),''),x,y,True),('MPN',mpn or value,x,y,True),('Design_note',note,x,y,True)]:
            just=' (justify left)' if passive and angle==0 and not hide else ''
            fields.append(f'(property {Q(pn)} {Q(pv)} (at {mm(px)} {mm(py)} 0) (effects (font (size 1.016 1.016)){just}{" (hide yes)" if hide else ""}))')
        rootpath='/'+ROOT_ID+'/'+self.sheetid
        pdef=pspec(lib,unit);pinuuids=''.join(f'(pin {Q(n)} (uuid "{uid(ref+"/pin/"+n)}"))' for n in pdef)
        self.add(f'(symbol (lib_id {Q(key)}) (at {mm(x)} {mm(y)} {angle}) (unit {unit}) (in_bom yes) (on_board yes) (dnp no) (uuid "{actualid}") {" ".join(fields)} {pinuuids} (instances (project "AK4490DAC" (path "{rootpath}" (reference {Q(ref)}) (unit {unit})))))')
        coords={};a=angle*math.pi/180
        for n,(px,py,pa,t) in pdef.items():
            coords[n]=(round(x+px*math.cos(a)-py*math.sin(a),5),round(y-px*math.sin(a)-py*math.cos(a),5),(pa+angle)%360,t)
        inst=(ref,unit);self.inst[inst]=coords
        if not ref.startswith('#'):COMP[ref]={'Reference':ref,'Value':value,'MPN':mpn or value,'Footprint':fp,'Sheet':self.name,'Note':note}
        return inst
    def pin(self,inst,num):return self.inst[inst][str(num)][:2]
    def net(self,inst,num,net):
        k=(inst[0],str(num));old=EXPECTED.get(k)
        assert old is None or old==net,(k,old,net)
        EXPECTED[k]=net
    def wire(self,*pts):
        for a,b in zip(pts,pts[1:]):
            a=tuple(round(v,5) for v in a);b=tuple(round(v,5) for v in b)
            if a==b:continue
            assert a[0]==b[0] or a[1]==b[1],(self.name,a,b)
            self.segments.append((a,b))
    def label(self,net,p,angle=0):
        self.add(f'(global_label {Q(net)} (shape bidirectional) (at {mm(p[0])} {mm(p[1])} {angle}) (effects (font (size 1.016 1.016)) (justify {"right" if angle==0 else "left"})) (uuid "{self.uuid("label")}"))')
    def power(self,net,p):
        if net=='GND':key='power:GND'
        else:
            key='XU316DAC:PWR_'+net
            if key not in LIB:
                body=f'(symbol {Q(key)} (power) (pin_names (offset 0)) (in_bom yes) (on_board yes) (property "Reference" "#PWR" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Value" {Q(net)} (at 0 5.08 0) (effects (font (size 1.27 1.27)))) (symbol {Q("PWR_"+net+"_0_1")} (polyline (pts (xy -0.762 3.048) (xy 0 4.572) (xy 0.762 3.048)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy 0 0) (xy 0 4.572)) (stroke (width 0) (type default)) (fill (type none)))) (symbol {Q("PWR_"+net+"_1_1")} (pin power_in line (at 0 0 90) (length 0) (hide yes) (name {Q(net)} (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))))'
                LIB[key]=parse(body);CUSTOM['PWR_'+net]=LIB[key]
        self.used.add(key);lib=LIB[key] if key in LIB else std(key);ref='#PWR'+str(self.page*1000+self.seq);self.seq+=1
        pp=f'(property "Reference" {Q(ref)} (at {mm(p[0])} {mm(p[1])} 0) (effects (font (size 1.016 1.016)) (hide yes))) (property "Value" {Q(net)} (at {mm(p[0])} {mm(p[1]+1.5 if net=="GND" else p[1]-2.8)} 0) (effects (font (size 1.016 1.016))))'
        self.add(f'(symbol (lib_id {Q(key)}) (at {mm(p[0])} {mm(p[1])} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{self.uuid("power")}") {pp} (instances (project "AK4490DAC" (path "/{ROOT_ID}/{self.sheetid}" (reference {Q(ref)}) (unit 1)))))')
    def connect(self,inst,num,net,length=4):
        x,y,a,t=self.inst[inst][str(num)];p=(x,y);d={0:(-length,0),180:(length,0),90:(0,length),270:(0,-length)}[a];q=(round(x+d[0],5),round(y+d[1],5));self.wire(p,q);self.net(inst,num,net)
        if net=='GND' and a==90 or net.startswith('+') and a==270:self.power(net,q)
        else:self.label(net,q,0 if a==0 else 180)
    def nc(self,inst,num):
        p=self.pin(inst,num);self.net(inst,num,'NC');self.add(f'(no_connect (at {mm(p[0])} {mm(p[1])}) (uuid "{self.uuid("nc")}"))')
    def group(self,inst,nums,net,y):
        pts=[self.pin(inst,n) for n in nums];xs=sorted(set(p[0] for p in pts))
        for n,p in zip(nums,pts):self.net(inst,n,net);self.wire(p,(p[0],y))
        self.wire((xs[0],y),(xs[-1],y));t=(xs[0],y+2 if net=='GND' else y-2);self.wire((xs[0],y),t);self.power(net,t)
    def capbank(self,x,y,values,net,prefix,start,ground='GND'):
        xs=[]
        for i,val in enumerate(values):
            xx=x+i*8;ref=prefix+str(start+i);key='Device:C_Polarized' if val in ('220u/10V','47u/25V','100u/25V') else 'Device:C'
            fp='Capacitor_SMD:C_0603_1608Metric'
            if key.endswith('Polarized'):fp='Capacitor_SMD:CP_Elec_6.3x7.7'
            elif val.startswith(('10u','22u','47u')):fp='Capacitor_SMD:C_0805_2012Metric'
            inst=self.sym(key,ref,val,xx,y,fp=fp,note='X7R; capacitance specified after DC bias' if key=='Device:C' and 'u' in val else 'C0G for pF/nF filters; 16V minimum unless marked')
            self.net(inst,1,net);self.net(inst,2,ground);self.wire(self.pin(inst,1),(xx,y-5));self.wire(self.pin(inst,2),(xx,y+5));xs.append(xx)
        self.wire((xs[0],y-5),(xs[-1],y-5));self.wire((xs[0],y+5),(xs[-1],y+5));self.power(net,(xs[0],y-5));self.power(ground,(xs[0],y+5))
    def resistor(self,ref,val,x,y,n1,n2,angle=90,fp='Resistor_SMD:R_0603_1608Metric',note='1% unless specified'):
        i=self.sym('Device:R',ref,val,x,y,angle,fp=fp,note=note);self.connect(i,1,n1,2);self.connect(i,2,n2,2);return i
    def finish(self):
        # Split all wires at collinear endpoints; only T junctions and intentional endpoints join.
        endpoints=set(p for seg in self.segments for p in seg);segments=set()
        for a,b in self.segments:
            on=[p for p in endpoints if (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0]))]
            on=sorted(on)
            segments.update((c,d) for c,d in zip(on,on[1:]) if c!=d)
        cnt=collections.Counter(p for seg in segments for p in seg)
        for a,b in sorted(segments):self.add(f'(wire (pts (xy {mm(a[0])} {mm(a[1])}) (xy {mm(b[0])} {mm(b[1])})) (stroke (width 0) (type default)) (uuid "{self.uuid("wire")}"))')
        for p,c in cnt.items():
            if c>2:self.add(f'(junction (at {mm(p[0])} {mm(p[1])}) (diameter 0) (color 0 0 0 0) (uuid "{self.uuid("junction")}"))')
        text=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{self.id}") (paper "A3") (title_block (title {Q(self.title)}) (date "2026-09-13") (rev "XU316-A1") (company "AK4490DAC") (comment 1 "USB-only / External regulated 12V DC / PCM + DSD")) (lib_symbols '+ '\n'.join(dump(LIB[k]) for k in sorted(self.used))+')\n'+'\n'.join(self.items)+'\n(embedded_fonts no))\n'
        (ROOT/'hardware'/f'{self.name}.kicad_sch').write_text(text,encoding='utf-8')

# Custom symbols follow manufacturer pin functions, with mode-specific AK4490 pin names.
XURL='https://www.xmos.com/documentation/XM-015129-PC/pdf/XU316-1024.pdf'
AURL='https://www.akm.com/content/dam/documents/products/audio/audio-dac/ak4490eq/ak4490eq-en-datasheet.pdf'
left=[(28,'USB_DM',16,'bidirectional'),(29,'USB_DP',13,'bidirectional'),(16,'XIN',8,'input'),(15,'XOUT',5,'output'),(21,'RST_N / 1V8',0,'input'),(18,'TDI / 1V8',-5,'input'),(20,'TDO / 1V8',-8,'output'),(23,'TMS / 1V8',-11,'input'),(24,'TCK / 1V8',-14,'input')]
right=[(41,'X0D35 / 1L',16,'bidirectional'),(43,'X0D36 / 1M',13,'bidirectional'),(44,'X0D37 / 1N',10,'bidirectional'),(45,'X0D38 / 1O',7,'bidirectional'),(6,'X0D00 / 1A',2,'bidirectional'),(7,'X0D11 / 1D',-1,'bidirectional'),(40,'X0D29 / 4F.1',-6,'bidirectional'),(54,'X0D30 / 4F.2',-9,'bidirectional'),(55,'X0D31 / 4F.3',-12,'bidirectional'),(10,'X1D01 / 1B',-17,'bidirectional'),(9,'X1D00 / 1A',-20,'bidirectional')]
core=[4,12,19,27,34,42,49,57,61,62,63,64]
unused=[11,13,14,25,32,33,35,36,37,39,47,46,48,50,51,53,56,58]
units=[box(26,46,left,right),box(36,12,top=[(n,'VDD',-15+i*2,'power_in') for i,n in enumerate(core)]+[(22,'PLL_AVDD',15,'power_in')],bottom=[(65,'VSS / EP',0,'power_in')]),box(30,20,top=[(8,'VDDIOL',-12,'power_in'),(38,'VDDIOR',-9,'power_in'),(52,'VDDIOT',-6,'power_in'),(30,'USB_VDD33',0,'power_in'),(17,'VDDIOB18',6,'power_in'),(26,'VDDIOB18',9,'power_in'),(31,'USB_VDD18',12,'power_in')]),box(24,22,[(n,'NC' if n==25 else 'UNUSED GPIO',9-i*2,'no_connect' if n==25 else 'bidirectional') for i,n in enumerate(unused[:9])],[(n,'UNUSED GPIO',9-i*2,'bidirectional') for i,n in enumerate(unused[9:])]),box(22,20,[(3,'X0D01 / CS_N',7,'bidirectional'),(5,'X0D10 / CLK',4,'bidirectional')],[(59,'X0D04 / IO0',7,'bidirectional'),(1,'X0D05 / IO1',3,'bidirectional'),(60,'X0D06 / IO2',-1,'bidirectional'),(2,'X0D07 / IO3',-5,'bidirectional')])]
XU=custom('XU316-1024-QF60B-C24',units,'AK4490DAC:XMOS_QF60B_7x7_5EP','QF60B only; four exposed VDD pads 61-64; ground pad 65; USB tile 1, audio tile 0',XURL)
dg=[(2,'PDN',10,'input'),(46,'MCLK',7,'input'),(3,'BICK / DCLK',4,'input'),(4,'SDATA / DSDL',1,'input'),(5,'LRCK / DSDR',-2,'input'),(8,'SCL',-7,'input'),(9,'SDA',-10,'bidirectional')]
dr=[(10,'DZFL',10,'output'),(11,'DZFR',7,'output'),(6,'WCK (unused)',4,'input'),(7,'CSN (I2C mode)',1,'input'),(12,'CAD0',-2,'input'),(13,'PSN = 0',-5,'input'),(14,'I2C = 1',-8,'input'),(15,'DEM0 = 1',-11,'input'),(16,'DEM1 = 0',-14,'input'),(17,'CAD1',-17,'input')]
ap=[(44,'AVDD',-15,'power_in'),(48,'DVDD',-10,'power_in'),(33,'VDDL',-5,'power_in'),(34,'VDDL',-2,'power_in'),(27,'VDDR',5,'power_in'),(28,'VDDR',8,'power_in')]
ag=[45,47,29,30,31,32,21,22,39,40,1,18,24,37,43]
AK=custom('AK4490EQ_I2C',[box(26,42,dg,dr),box(38,34,[(19,'VREFHR',12,'passive'),(20,'VREFHR',9,'passive'),(23,'VCMR',5,'passive'),(41,'VREFHL',-3,'passive'),(42,'VREFHL',-6,'passive'),(38,'VCML',-10,'passive')],[(36,'AOUTLP',9,'output'),(35,'AOUTLN',6,'output'),(25,'AOUTRP',-4,'output'),(26,'AOUTRN',-7,'output')],ap,[(n,('GND' if n not in [1,18,24,37,43] else 'NC->GND'),-14+i*2,'power_in' if n not in [1,18,24,37,43] else 'passive') for i,n in enumerate(ag)])],'Package_QFP:LQFP-48_7x7mm_P0.5mm','AK4490EQ in I2C serial PCM/DSD mode. Verified against AKM MS1648-E-03.',AURL)
OSC=custom('CCHD-957',[box(16,10,[(1,'E/D',0,'input')],[(3,'OUT',0,'output')],[(4,'VCC',0,'power_in')],[(2,'GND',0,'power_in')])],'AK4490DAC:CCHD957_14.2x9.14','Crystek audio oscillator, 3.3V','https://www.mouser.com/pdfdocs/CrystekNoiseOsc957.pdf')
MUX=custom('74LVC1G157GW',[box(12,14,[(3,'I0',4,'input'),(1,'I1',0,'input'),(6,'S',-4,'input')],[(4,'Y',0,'output')],[(5,'VCC',0,'power_in')],[(2,'GND',0,'power_in')])],'Package_TO_SOT_SMD:SOT-363_SC-70-6','Clock mux; change selection only while DAC muted and PDN low','https://assets.nexperia.com/documents/data-sheet/74LVC1G157.pdf')
DIV=custom('SN74LVC1G74DCTR',[box(14,14,[(1,'CLK',3,'input'),(2,'D',-3,'input')],[(5,'Q',3,'output'),(3,'~Q',-3,'output')],[(8,'VCC',-4,'power_in'),(7,'PRE_N',0,'input'),(6,'CLR_N',4,'input')],[(4,'GND',0,'power_in')])],'Package_SO:TSSOP-8_3x3mm_P0.65mm','Divide by 2: ~Q feeds D. DAC MCLK = 22.5792 / 24.576 MHz','https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf')
SUP=custom('TPS3808G18DBVR',[box(14,12,[(5,'SENSE',2,'input'),(3,'MR_N',-2,'input')],[(1,'RESET_N / OD',2,'open_collector'),(4,'CT',-2,'passive')],[(6,'VDD',0,'power_in')],[(2,'GND',0,'power_in')])],'Package_TO_SOT_SMD:SOT-23-6','1.67V supervisor, CT open = 20ms delay','https://www.ti.com/lit/ds/symlink/tps3808.pdf')
DC=custom('MCWI03-12D15',[box(18,16,[(2,'+VIN',4,'power_in'),(3,'CTRL (on=GND)',0,'input')],[(6,'+15V',4,'power_out'),(7,'COMMON',0,'passive'),(8,'-15V',-4,'power_out')],bottom=[(1,'-VIN',0,'power_in'),(5,'NC',5,'no_connect')])],'AK4490DAC:MCWI03_SIP7','MINMAX MCWI03, 25mA minimum load per rail; preload resistors fitted','https://akizukidenshi.com/download/ds/minmax/MCWI03.pdf')
