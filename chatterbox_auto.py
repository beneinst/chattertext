# Script generato da ChatterText v2.6
# V1..V5 configurabili | V6/V7 segnaposto -> fallback automatico V1
# Pause gaussiane 6L + giunzioni 12L + dynamic_pause
import os,re,sys,random,torch,torchaudio as ta,pathlib,time
if sys.platform=='win32':
    import io
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
    sys.stderr=io.TextIOWrapper(sys.stderr.buffer,encoding='utf-8',errors='replace')
if torch.cuda.is_available():
    DEVICE=torch.device('cuda')
    print(f'GPU {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory//(1024**3)}GB)')
else:
    DEVICE=torch.device('cpu')
    print('CPU (nessuna GPU)')
_olt=torch.load
def _sl(*a,**k):
    if DEVICE.type=='cpu': k.setdefault('map_location',torch.device('cpu'))
    return _olt(*a,**k)
torch.load=_sl
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
print('Caricamento modello...')
model=ChatterboxMultilingualTTS.from_pretrained(device=DEVICE.type)
print('Modello su {}!'.format(DEVICE.type.upper()))
chunks=[
  "Nel campo mèzzo grìgio e mèzzo nèro,[p2] rèsta un aràtro senza buòi,[p1] che pàre dimenticàto,[p1] tra il vapór leggèro. [p3] E cadenzàto dalla góra viène[p1] lo sciabordàre delle lavandàre,[p1] con tónfi spèssi[p1] e lùnghe cantilène.",
  "[p3] Il vènto sòffia e nèvica la fràsca,[p1] e tù non tórni ancóra al tuo paése! [p2] quàndo partìsti,[p1] còme son rimàsta! [p2] còme laràtro in mèzzo alla maggése."
]
AUDIO_V1="2.Voci/2Emanuela.wav"
AUDIO_V2="2.Voci/2Emanuela.wav"
AUDIO_V3="2.Voci/2Emanuela.wav"
AUDIO_V4="2.Voci/2Emanuela.wav"
AUDIO_V5="2.Voci/2Emanuela.wav"
AUDIO_V6="2.Voci/2Emanuela.wav"
AUDIO_V7="2.Voci/2Emanuela.wav"
HAS2=False
HAS3=False
HAS4=False
HAS5=False
HAS6=False
HAS7=False
for p,lbl,en in [(AUDIO_V1,'V1',True),(AUDIO_V2,'V2',HAS2),(AUDIO_V3,'V3',HAS3),(AUDIO_V4,'V4',HAS4),(AUDIO_V5,'V5',HAS5),(AUDIO_V6,'V6',HAS6),(AUDIO_V7,'V7',HAS7)]:
    if en and not os.path.exists(p): print(f'NON TROVATO [{lbl}]: {p}'); exit(1)
EPRESET={
    "calmo": {
        "exaggeration": 0.35,
        "cfg_weight": 0.85,
        "temperature": 0.4,
        "top_p": 0.75,
        "min_p": 0.15
    },
    "appassionato": {
        "exaggeration": 0.75,
        "cfg_weight": 0.6,
        "temperature": 0.65,
        "top_p": 0.8,
        "min_p": 0.1
    },
    "arrabbiato": {
        "exaggeration": 0.9,
        "cfg_weight": 0.5,
        "temperature": 0.75,
        "top_p": 0.85,
        "min_p": 0.08
    },
    "triste": {
        "exaggeration": 0.45,
        "cfg_weight": 0.8,
        "temperature": 0.45,
        "top_p": 0.7,
        "min_p": 0.18
    },
    "ironico": {
        "exaggeration": 0.65,
        "cfg_weight": 0.65,
        "temperature": 0.7,
        "top_p": 0.82,
        "min_p": 0.12
    },
    "sussurrato": {
        "exaggeration": 0.25,
        "cfg_weight": 0.9,
        "temperature": 0.35,
        "top_p": 0.65,
        "min_p": 0.2
    },
    "riflessivo": {
        "exaggeration": 0.4,
        "cfg_weight": 0.78,
        "temperature": 0.48,
        "top_p": 0.72,
        "min_p": 0.16
    },
    "deciso": {
        "exaggeration": 0.8,
        "cfg_weight": 0.55,
        "temperature": 0.6,
        "top_p": 0.78,
        "min_p": 0.1
    },
    "preoccupato": {
        "exaggeration": 0.55,
        "cfg_weight": 0.72,
        "temperature": 0.55,
        "top_p": 0.74,
        "min_p": 0.14
    },
    "gentile": {
        "exaggeration": 0.42,
        "cfg_weight": 0.82,
        "temperature": 0.42,
        "top_p": 0.7,
        "min_p": 0.16
    },
    "serio": {
        "exaggeration": 0.5,
        "cfg_weight": 0.75,
        "temperature": 0.5,
        "top_p": 0.73,
        "min_p": 0.15
    }
}
DEF_P={'exaggeration':0.82,'cfg_weight':0.7,'temperature':0.68,'top_p':0.75,'min_p':0.15}
PM={
    '[p1]':(0.18,0.03), '[p2]':(0.40,0.05), '[p3]':(0.65,0.07),
    '[b]': (1.00,0.10), '[bd]':(1.60,0.15), '[cap]':(2.00,0.20),
    '[pausa]':(0.50,0.05),'[pausa_lunga]':(1.20,0.10),'[silenzio]':(2.00,0.15),
}
def gp(tag):
    b,s=PM.get(tag.lower(),(0.40,0.05))
    raw=random.gauss(b,s)
    return max(b*0.60, min(raw, b*1.40))
# GIUNZIONI 12 livelli (cambio6/7 per voci segnaposto)
JM={'[join]':(0.00,'overlap'),'[cont]':(0.12,'smooth'),
    '[cambio]':(0.50,'cambio'),'[cambio3]':(0.50,'cambio'),
    '[cambio4]':(0.50,'cambio'),'[cambio5]':(0.50,'cambio'),
    '[cambio6]':(0.50,'cambio'),'[cambio7]':(0.50,'cambio'),
    '[para]':(0.90,'silence'),'[stacco]':(1.40,'fade_sil_fade'),
    '[lungo]':(1.80,'fade_sil_fade'),'[scena]':(2.40,'hard')}
EP={'e1':{'exaggeration_delta':0.10,'cfg_weight_delta':-0.05},'e2':{'exaggeration_delta':0.25,'cfg_weight_delta':-0.12}}
EN=r"calmo|appassionato|arrabbiato|triste|ironico|sussurrato|riflessivo|deciso|preoccupato|gentile|serio"
PR=re.compile(r'(\[p[123]\]|\[b(?:d)?\]|\[cap\]|\[pausa(?:_lunga)?\]|\[silenzio\])',re.IGNORECASE)
ER=re.compile(r'\[e[12]\]',re.IGNORECASE)
JR=re.compile(r'\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena)\]',re.IGNORECASE)
def pc(chunk):
    rp=PR.findall(chunk)
    ps=[(p,gp(p)) for p in rp]; tp=sum(d for _,d in ps)
    et=ER.findall(chunk); ek=et[-1].lower().strip('[]') if et else None
    jt=JR.findall(chunk); jk=jt[-1].lower() if jt else None
    def si(t):
        t=PR.sub('',t); t=ER.sub('',t); t=JR.sub('',t); return t.strip()
    # Gestisce v1..v7 (v6/v7 -> fallback v1 nel routing)
    m=re.search(r'\[(v1|v2|v3|v4|v5|v6|v7)_(' +EN+r')\]',chunk,re.IGNORECASE)
    if m:
        v,e=m.group(1).lower(),m.group(2).lower()
        cl=re.sub(r'\[(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\]','',chunk,flags=re.IGNORECASE)
        cl=re.sub(r'\[/(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\]','',cl,flags=re.IGNORECASE)
        return si(cl),v,e,ps,tp,ek,jk
    m=re.search(r'\[(v1|v2|v3|v4|v5|v6|v7)\]',chunk,re.IGNORECASE)
    if m:
        v=m.group(1).lower()
        cl=re.sub(r'\[/?(?:v1|v2|v3|v4|v5|v6|v7)\]','',chunk,flags=re.IGNORECASE)
        return si(cl),v,None,ps,tp,ek,jk
    m=re.search(r'\[('+EN+r')\]',chunk,re.IGNORECASE)
    if m:
        e=m.group(1).lower()
        cl=re.sub(r'\[(?:'+EN+r')\]','',chunk,flags=re.IGNORECASE)
        cl=re.sub(r'\[/(?:'+EN+r')\]','',cl,flags=re.IGNORECASE)
        return si(cl),'v1',e,ps,tp,ek,jk
    return si(chunk),'v1',None,ps,tp,ek,jk
def pp(emo,ek=None):
    p=EPRESET[emo].copy() if emo and emo in EPRESET else DEF_P.copy()
    p.setdefault('top_p',0.75); p.setdefault('min_p',0.15)
    if ek and ek in EP:
        p['exaggeration']=min(1.0,p['exaggeration']+EP[ek]['exaggeration_delta'])
        p['cfg_weight']=max(0.1,p['cfg_weight']+EP[ek]['cfg_weight_delta'])
    return p
tc=[pc(c) for c in chunks]
def rn(wav,sr,gtdb=-50,hpz=80):
    thr=10**(gtdb/20)
    if wav.dim()==1: wav=wav.unsqueeze(0)
    gm=(torch.abs(wav)>thr).float()
    k=int(sr*0.008)
    if k%2==0: k+=1
    kern=torch.ones(1,1,k)/k
    gm=torch.nn.functional.conv1d(gm.unsqueeze(0),kern,padding=k//2).squeeze(0).clamp(0,1)
    wav=wav*gm; wav=ta.functional.highpass_biquad(wav,sr,cutoff_freq=hpz); return wav
segs=[]; fail=[]
st=time.time()
print('\n'+'='*55)
print('AVVIO GENERAZIONE [{}]'.format(DEVICE.type.upper()))
print('='*55)
for i,(txt,vo,em,ps,tp,ek,jk) in enumerate(tc):
    if i>0:
        el=time.time()-st; av=el/i; rm=av*(len(tc)-i)
        eta='  ETA:{:.0f}s'.format(rm)
    else: eta=''
    pct=int(i/len(tc)*100)
    bar=chr(9608)*(pct//5)+chr(9617)*(20-pct//5)
    _em_s='['+em+']' if em else ''
    _ek_s='['+ek+']' if ek else ''
    _jk_s='['+jk.strip('[]')+']' if jk else ''
    _tail='...' if len(txt)>80 else ''
    _rep=repr(txt[:80])
    print('\n [{}] {}%{}'.format(bar,pct,eta))
    print(' Chunk {}/{} [{}]{}{}{}'.format(i+1,len(tc),vo.upper(),_em_s,_ek_s,_jk_s))
    print('   {}{}'.format(_rep,_tail))
    if tp>0: print('   pausa: {:.2f}s (gauss)'.format(tp))
    if len(txt.split())<5: print('   ATTENZIONE: chunk corto!')
    # Routing: v7->V7, v6->V6, v5->V5, v4->V4, v3->V3, v2->V2 (se configurati), default V1
    if   vo=='v7' and HAS7: vp=AUDIO_V7
    elif vo=='v6' and HAS6: vp=AUDIO_V6
    elif vo=='v5' and HAS5: vp=AUDIO_V5
    elif vo=='v4' and HAS4: vp=AUDIO_V4
    elif vo=='v3' and HAS3: vp=AUDIO_V3
    elif vo=='v2' and HAS2: vp=AUDIO_V2
    else:                   vp=AUDIO_V1
    p=pp(em,ek); ok=False
    try:
        wav=model.generate(txt,language_id='it',audio_prompt_path=vp,
            exaggeration=p['exaggeration'],cfg_weight=p['cfg_weight'],
            temperature=p['temperature'],min_p=p['min_p'],top_p=p['top_p'])
        if DEVICE.type=='cuda': wav=wav.cpu()
        wav=wav/(torch.max(torch.abs(wav))+1e-8)*0.95
        if tp>0:
            sil=torch.zeros((wav.shape[0],int(model.sr*tp)))
            wav=torch.cat([wav,sil],dim=-1)
        segs.append(wav); ok=True; print('   OK!')
    except Exception as e: print('   ERR:{} retry...'.format(e))
    if not ok:
        try:
            wav=model.generate(txt,language_id='it',audio_prompt_path=vp,
                exaggeration=0.0,cfg_weight=0.25,temperature=0.22,min_p=0.20,top_p=0.65)
            if DEVICE.type=='cuda': wav=wav.cpu()
            wav=wav/(torch.max(torch.abs(wav))+1e-8)*0.95
            segs.append(wav); print('   Recuperato!')
        except Exception as e2: print(f'   FALLITO:{e2}'); fail.append(i)
if not segs: print('Nessun audio.'); exit(1)
od=pathlib.Path('1.Output'); od.mkdir(exist_ok=True)
num=len(list(od.glob('audiolibro_*.wav')))+1
out=od/'audiolibro_{:02d}.wav'.format(num)
SCENE=[
        "poi" ,"quando" ,"all'improvviso" ,"improvvisamente" ,"in quel momento" ,"mentre" ,"subito dopo" ,"intanto" ,"nel frattempo" ,"a quel punto" ,"alla fine"
    ]
DIALOG=[
        "disse" ,"penso" ,"grido" ,"urlo" ,"sussurro" ,"domando" ,"rispose" ,"chiese" ,"mormoro" ,"esclamo" ,"borbotto" ,"annuncio" ,"replico" ,"aggiunse" ,"continuo" ,"riprese"
    ]
EMOW=[
        "paura" ,"orrore" ,"ansia" ,"terrore" ,"pianto" ,"felice" ,"gioia" ,"triste" ,"disperato" ,"sconvolto" ,"agitato" ,"sorpreso" ,"commosso" ,"morte" ,"vita" ,"anima" ,"silenzio" ,"infinito"
    ]
CONCS=[
        "tuttavia" ,"eppure" ,"nonostante" ,"al contrario" ,"invece" ,"d'altra parte" ,"in realta" ,"in verita" ,"dunque" ,"quindi" ,"pertanto" ,"di conseguenza"
    ]
REFL=[
        "forse" ,"chissa" ,"davvero" ,"possibile che" ,"si chiese" ,"si domando" ,"aveva senso" ,"non aveva senso" ,"significava" ,"voleva dire"
    ]
PHIL=[
        "verita" ,"giustizia" ,"anima" ,"essere" ,"nulla" ,"infinito" ,"eternita" ,"ragione" ,"sapienza" ,"virtu" ,"bene" ,"male" ,"conoscenza" ,"ignoranza" ,"logos"
    ]
def dyn_pause(txt, emo=None):
    t=txt.strip(); lo=t.lower(); ln=len(t); lc=t[-1:] if t else ''
    if t.endswith('...'): base,sig=1.50,0.15
    elif lc in '?!':     base,sig=1.00,0.12
    elif lc=='.':        base,sig=0.42,0.06
    elif lc==':':        base,sig=0.70,0.08
    elif lc==';':        base,sig=0.60,0.07
    elif lc==',':        base,sig=0.20,0.03
    else:                base,sig=0.18,0.03
    if ln>500:   base*=1.50
    elif ln>300: base*=1.30
    elif ln>150: base*=1.12
    elif ln<60:  base*=0.80
    if any(lo.startswith(s) for s in SCENE):  base*=1.28
    if any(w in lo for w in PHIL):            base*=1.45
    if any(w in lo for w in CONCS):           base*=1.38
    if any(w in lo for w in REFL):            base*=1.30
    if any(w in lo for w in EMOW):            base*=1.18
    if any(v in lo for v in DIALOG):          base*=0.75
    if emo in ('riflessivo','calmo','triste','preoccupato'):  base*=1.18
    elif emo in ('arrabbiato','deciso'):                      base*=0.72
    elif emo=='sussurrato':                                   base*=1.10
    raw=random.gauss(base, sig)
    return max(base*0.60, min(raw, base*1.40))
def te(wav,sr,tdb=-45,mms=30):
    mg=int(sr*mms/1000); thr=10**(tdb/20)
    mo=wav[0] if wav.dim()>1 else wav; en=torch.abs(mo)
    s=next((max(0,i-mg) for i,v in enumerate(en) if v>thr),0)
    e=next((min(len(en),i+mg) for i in range(len(en)-1,-1,-1) if en[i]>thr),len(en))
    return wav[...,s:e]
def cf(s1,s2,sr,fms=55):
    f=int(sr*fms/1000)
    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)
    fo=torch.linspace(1,0,f)**1.5; fi=torch.linspace(0,1,f)**1.5
    return torch.cat([s1[...,:-f],s1[...,-f:]*fo+s2[...,:f]*fi,s2[...,f:]],dim=-1)
def ov(s1,s2,sr,oms=80):
    f=int(sr*oms/1000)
    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)
    fo=torch.linspace(1,0,f)**2; fi=torch.linspace(0,1,f)**2
    return torch.cat([s1[...,:-f],s1[...,-f:]*fo+s2[...,:f]*fi,s2[...,f:]],dim=-1)
def af(wav,sr,fms=14):
    f=int(sr*fms/1000); wav=wav.clone()
    wav[...,:f]*=torch.linspace(0,1,f); wav[...,-f:]*=torch.linspace(1,0,f); return wav
def fsf(s1,s2,sr,ss,foms=80,fims=60):
    fl=int(sr*foms/1000); il=int(sr*fims/1000)
    sl=max(0,int(sr*ss)-fl-il)
    s1=s1.clone()
    if s1.shape[-1]>=fl: s1[...,-fl:]*=torch.linspace(1.0,0.0,fl)**1.8
    sil=torch.zeros((s2.shape[0],sl),dtype=s2.dtype)
    s2=s2.clone()
    if s2.shape[-1]>=il: s2[...,:il]*=torch.linspace(0.0,1.0,il)**1.8
    return torch.cat([s1,sil,s2],dim=-1)
def asmb(s1,s2,sr,jt):
    if jt is None: return None
    ss,mode=JM.get(jt,(0.5,'silence'))
    if mode=='overlap': return ov(s1,s2,sr)
    if mode=='fade_sil_fade': return fsf(s1,s2,sr,ss)
    sil=torch.zeros((s2.shape[0],int(sr*ss))) if ss>0 else None
    if mode=='smooth': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=30)
    if mode=='cambio': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=100)
    if mode=='silence': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=55)
    if mode=='hard': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)
    return cf(s1,s2,sr)
jl=[x[6] for x in tc]
fa=None
for i,seg in enumerate(segs):
    seg=rn(seg,model.sr); seg=te(seg,model.sr); seg=af(seg,model.sr)
    if fa is None: fa=seg; continue
    jt=jl[i-1]; res=asmb(fa,seg,model.sr,jt)
    if res is None:
        pau=dyn_pause(chunks[i-1], emo=tc[i-1][2])
        sil=torch.zeros((seg.shape[0],int(model.sr*pau)))
        fa=cf(fa,torch.cat([sil,seg],dim=-1),model.sr)
        js='auto({:.2f}s)'.format(pau)
    else: fa=res; js=jt if jt else 'auto'
    print(f'   -> join {i}: {js}')
fa=fa/(torch.max(torch.abs(fa))+1e-8)*0.95
ta.save(out,fa,model.sr)
dur=fa.shape[-1]/model.sr; tot=time.time()-st
print(f'\n FILE: {out}')
print(f'   Durata: {dur:.1f}s ({dur/60:.1f} min)')
print(f'   Tempo:  {tot:.1f}s ({tot/60:.1f} min)')
print(f'   Device: {DEVICE.type.upper()}')
voci_attive=[('V2',HAS2),('V3',HAS3),('V4',HAS4),('V5',HAS5),('V6',HAS6),('V7',HAS7)]
voci_str=' | '.join(n for n,a in voci_attive if a) or '-'
v67note=' (V6/V7 non config->V1)' if not HAS6 or not HAS7 else ''
print(f'   Voci: V1 + {voci_str}{v67note}')
print(f'   OK: {len(segs)}/{len(chunks)}')
if fail: print(f'   FAIL: {fail}')
print('\nProcesso completato!')
print('__CHATTERTEXT_DONE__')