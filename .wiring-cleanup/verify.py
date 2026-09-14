exec(open('.wiring-cleanup/layout.py',encoding='utf-8-sig').read().split('if __name__')[0])
l=parse(Path('AK4490DAC.kicad_sym').read_text(encoding='utf-8'));print([unq(x[1]) for x in children(l,'symbol')])
nets=[]
for file in ['before','after']:
 n=parse(Path('.wiring-cleanup/'+file+'.net').read_text(encoding='utf-8'))
 nets.append({tuple(sorted((unq(val(x,'ref')),unq(val(x,'pin'))) for x in children(net,'node'))) for net in children(child(n,'nets'),'net')})
print('nets',len(nets[0]),len(nets[1]),'identical',nets[0]==nets[1]);print('diff',nets[0]-nets[1],nets[1]-nets[0])
