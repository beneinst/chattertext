#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatterText - App Desktop Python v2.4
Posizionare nella root di Chatterbox ed eseguire con: python chattertext_app.py

NOVITA v2.4 (terza voce):
  - Aggiunta Voce 3 [v3] / [V3_emozione] opzionale come V1 e V2
  - Tag: [v3]testo[/v3] e [V3_emozione]...[/V3_emozione]
  - Giunzione [cambio3] per transizione V1/V2 <-> V3 (0.50s crossfade)
  - Badge turchese per V3 nell'interfaccia chunk
  - Script generato supporta AUDIO_V3 e routing automatico
  - Verifica voci estesa a V3

NOVITA v2.3 (ottimizzazione produzione):
  - Clamp gaussiana a ±40% del valore base (mai sotto 60%, mai sopra 140%)
  - [scena] portato a 2.40s per differenziarlo percettivamente da [cap] 2.00s
  - Regola anti-accumulo: max 2 pause consecutive
  - Emozione influenza scelta pause in dynamic_pause()
  - Regola [e2]: max 1 ogni 2-3 blocchi
  - Prompt Guida aggiornato con tutte le nuove regole
"""
import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import os, subprocess, threading, sys, re, json, pathlib, time

# =========================================================
# PALETTE
# =========================================================
C = {
    "bg":       "#0d0d0d", "surface":  "#131313", "surface2": "#1a1a1a",
    "border":   "#2a2a2a", "accent":   "#81ecec", "accent2":  "#4a90e2",
    "text":     "#e0e0e0", "text_dim": "#7f8c8d", "success":  "#00b894",
    "warning":  "#fdcb6e", "danger":   "#e84357", "v1":       "#3498db",
    "v2":       "#e74c3c", "v3":       "#00b894",  # <-- turchese per V3
    "chunk_bg": "#111111", "hdr_bg":   "#181818",
    "gpu":      "#76b900", "cpu":      "#4a90e2",
}
EMO_C = {
    "calmo":"#27ae60","appassionato":"#e67e22","arrabbiato":"#c0392b",
    "triste":"#8e44ad","ironico":"#16a085","sussurrato":"#546e7a",
    "riflessivo":"#2980b9","deciso":"#d35400","preoccupato":"#7f8c8d",
    "gentile":"#2ecc71","serio":"#34495e",
}
FM = ("Courier New",11); FB = ("Segoe UI",10); FL = ("Segoe UI",9,"bold")
FH1 = ("Georgia",18,"bold"); FH2 = ("Segoe UI",12,"bold")
FST = ("Courier New",22,"bold"); FS = ("Segoe UI",8)

# =========================================================
# PRESET EMOTIVI
# =========================================================
EMOTION_PRESETS = {
    "calmo":       {"exaggeration":0.35,"cfg_weight":0.85,"temperature":0.40,"top_p":0.75,"min_p":0.15},
    "appassionato":{"exaggeration":0.75,"cfg_weight":0.60,"temperature":0.65,"top_p":0.80,"min_p":0.10},
    "arrabbiato":  {"exaggeration":0.90,"cfg_weight":0.50,"temperature":0.75,"top_p":0.85,"min_p":0.08},
    "triste":      {"exaggeration":0.45,"cfg_weight":0.80,"temperature":0.45,"top_p":0.70,"min_p":0.18},
    "ironico":     {"exaggeration":0.65,"cfg_weight":0.65,"temperature":0.70,"top_p":0.82,"min_p":0.12},
    "sussurrato":  {"exaggeration":0.25,"cfg_weight":0.90,"temperature":0.35,"top_p":0.65,"min_p":0.20},
    "riflessivo":  {"exaggeration":0.40,"cfg_weight":0.78,"temperature":0.48,"top_p":0.72,"min_p":0.16},
    "deciso":      {"exaggeration":0.80,"cfg_weight":0.55,"temperature":0.60,"top_p":0.78,"min_p":0.10},
    "preoccupato": {"exaggeration":0.55,"cfg_weight":0.72,"temperature":0.55,"top_p":0.74,"min_p":0.14},
    "gentile":     {"exaggeration":0.42,"cfg_weight":0.82,"temperature":0.42,"top_p":0.70,"min_p":0.16},
    "serio":       {"exaggeration":0.50,"cfg_weight":0.75,"temperature":0.50,"top_p":0.73,"min_p":0.15},
}
ALL_EMO = list(EMOTION_PRESETS.keys())

# =========================================================
# PAUSE  (base_s, sigma)
# =========================================================
PAUSE_MAP = {
    "[p1]": (0.18,0.03), "[p2]": (0.40,0.05), "[p3]": (0.65,0.07),
    "[b]":  (1.00,0.10), "[bd]": (1.60,0.15), "[cap]":(2.00,0.20),
    "[pausa]":(0.50,0.05), "[pausa_lunga]":(1.20,0.10), "[silenzio]":(2.00,0.15),
}
PAUSE_FLAT = {k:v[0] for k,v in PAUSE_MAP.items()}
ALL_PAUSE_NAMES = ["p1","p2","p3","b","bd","cap","pausa","pausa_lunga","silenzio"]

EMPH_PRESETS = {
    "e1":{"exaggeration_delta":+0.10,"cfg_weight_delta":-0.05},
    "e2":{"exaggeration_delta":+0.25,"cfg_weight_delta":-0.12},
}
ALL_EMPH_NAMES = ["e1","e2"]

# =========================================================
# GIUNZIONI  8 livelli (aggiunta [cambio3])
# =========================================================
JOIN_MAP = {
    "[join]":    (0.00,"overlap"),
    "[cont]":    (0.12,"smooth"),
    "[cambio]":  (0.50,"cambio"),
    "[cambio3]": (0.50,"cambio"),   # <-- nuovo: transizione con/da V3
    "[para]":    (0.90,"silence"),
    "[stacco]":  (1.40,"fade_sil_fade"),
    "[lungo]":   (1.80,"fade_sil_fade"),
    "[scena]":   (2.40,"hard"),
}
ALL_JOIN_NAMES = ["join","cont","cambio","cambio3","para","stacco","lungo","scena"]

BREATH_MAX_W = 14; BREATH_MAX_C = 80
CHUNK_MIN_W  = 5;  CHUNK_MIN_C  = 20

PAUSE_BADGE_C = {"p1":"#4a9080","p2":"#2980b9","p3":"#8e44ad",
                 "b":"#27ae60","bd":"#e84357","cap":"#e67e22"}
JOIN_BADGE_C  = {"join":"#00cec9","cont":"#74b9ff","cambio":"#a29bfe","cambio3":"#00b894",
                 "para":"#fdcb6e","stacco":"#fd79a8","lungo":"#e17055","scena":"#636e72"}

# =========================================================
# HELPERS TESTO
# =========================================================
def _protected():
    emo = "|".join(ALL_EMO)
    return re.compile(
        r"\[/?(?:v1|v2|v3|inizio|fine|pausa|pausa_lunga|silenzio"
        r"|p1|p2|p3|b|bd|cap|e1|e2"
        r"|join|cont|cambio|cambio3|para|stacco|lungo|scena"
        r"|(?:(?:v1|v2|v3)_)?(?:"+emo+r"))\]", re.IGNORECASE)

def normalize_text(text):
    tm={};idx=[0];pat=_protected()
    def sv(m):
        ph="__T{}__".format(idx[0]);tm[ph]=m.group(0);idx[0]+=1;return ph
    text=pat.sub(sv,text)
    text=re.sub(r"l'Om\b","l'om",text)
    text=re.sub(r"nell'(\w)",lambda m:"nell'"+m.group(1).lower(),text)
    text=re.sub(r"dell'(\w)",lambda m:"dell'"+m.group(1).lower(),text)
    text=re.sub(r"[`\u00b4]","'",text)
    text=re.sub(r"[^\w\s.,;:!?\u00C0-\u00F9'\"\\-]","",text)
    text=re.sub(r"\s+"," ",text)
    text=re.sub(r"\n\s*\n+","\n\n",text)
    text=re.sub(r"(?<!\n)\n(?!\n)"," ",text)
    text=re.sub(r"([.!?])\1+",r"\1",text)
    for ph,t in tm.items(): text=text.replace(ph,t)
    return text.strip()

def analyze_text(text):
    errs=[]
    if len(text)>10000: errs.append(("warning","Testo troppo lungo ({} car.)".format(len(text))))
    caps=re.findall(r"[''`\u00b4]\w*[A-Z]\w*",text)
    if caps: errs.append(("warning","Maiuscole dopo apostrofo: "+", ".join(caps[:3])))
    tnt=_protected().sub("",text)
    wc={}
    for w in re.findall(r"\b\w+\b",tnt.lower()): wc[w]=wc.get(w,0)+1
    rep=sorted([(w,c) for w,c in wc.items() if c>3 and len(w)>3],key=lambda x:-x[1])[:5]
    if rep: errs.append(("info","Parole ripetute: "+", ".join('"{}"({}x)'.format(w,c) for w,c in rep)))
    sp=re.findall(r"[^\w\s.,;:!?\u00C0-\u00F9'\"\\-]",tnt)
    if sp: errs.append(("warning","Caratteri speciali: "+" ".join(list(dict.fromkeys(sp))[:10])))
    return errs

def chunk_text(text,min_w,max_w,max_c):
    tms=list(re.finditer(r"\[inizio\]([\s\S]*?)\[fine\]",text,re.IGNORECASE))
    if tms:
        chunks=[];emo="|".join(ALL_EMO)
        # Esteso a v1|v2|v3
        vpat=re.compile(r"\[(v1|v2|v3)(?:_(?:"+emo+r"))?\]([\s\S]*?)\[/(?:v1|v2|v3)(?:_(?:"+emo+r"))?\]",re.IGNORECASE)
        for m in tms:
            cont=m.group(1).strip()
            if not cont: continue
            vml=list(vpat.finditer(cont))
            if vml:
                for vm in vml:
                    ft=vm.group(0).strip()
                    if vm.group(2).strip(): chunks.append(ft)
            else:
                if cont: chunks.append(cont)
        return chunks
    paragraphs=[p.strip() for p in re.split(r"\n\s*\n",text) if p.strip()]
    chunks=[]
    for p in paragraphs:
        if len(p)<=max_c and len(p.split())<=max_w: chunks.append(p); continue
        sentences=re.findall(r"[^.!?]+[.!?]+",p) or [p]; buf=""
        for fr in sentences:
            test=(buf+" "+fr).strip() if buf else fr
            if len(test)>max_c or len(test.split())>max_w:
                if buf.strip(): chunks.append(buf.strip())
                buf=fr
            else: buf=test
        if buf.strip(): chunks.append(buf.strip())
    return chunks

def chunk_status(words,chars):
    if words>60 or chars>350: return "danger","Troppo lungo"
    if words>BREATH_MAX_W or chars>BREATH_MAX_C: return "warning","Supera blocco-respiro ({}/14)".format(words)
    if words<CHUNK_MIN_W or chars<CHUNK_MIN_C: return "danger","TROPPO CORTO ({} par.)".format(words)
    return "success","Ottimale"

def detect_emph(chunk):
    return [t for t in ALL_EMPH_NAMES if re.search(r"\["+t+r"\]",chunk,re.IGNORECASE)]

def detect_pauses(chunk):
    res=[]
    for n in ALL_PAUSE_NAMES:
        tag="[{}]".format(n)
        for _ in re.findall(re.escape(tag),chunk,re.IGNORECASE):
            res.append((tag,PAUSE_FLAT.get(tag,0.4)))
    return res

def detect_voice_emo(chunk):
    emo="|".join(ALL_EMO)
    # Ora gestisce v1, v2, v3
    m=re.search(r"\[(v1|v2|v3)_("+emo+r")\]",chunk,re.IGNORECASE)
    if m: return m.group(1).lower(),m.group(2).lower()
    m=re.search(r"\[(v1|v2|v3)\]",chunk,re.IGNORECASE)
    if m: return m.group(1).lower(),None
    m=re.search(r"\[("+emo+r")\]",chunk,re.IGNORECASE)
    if m: return None,m.group(1).lower()
    return None,None

def detect_join(chunk):
    for n in ALL_JOIN_NAMES:
        if re.search(r"\["+n+r"\]",chunk,re.IGNORECASE): return "[{}]".format(n)
    return None

# =========================================================
# SUONO
# =========================================================
def play_sound():
    try:
        if sys.platform=="win32":
            import winsound
            for f,d in [(523,120),(659,120),(784,200),(1047,350)]:
                winsound.Beep(f,d); time.sleep(0.04)
        elif sys.platform=="darwin":
            subprocess.run(["afplay","/System/Library/Sounds/Glass.aiff"],capture_output=True)
        else:
            if subprocess.run(["which","paplay"],capture_output=True).returncode==0:
                subprocess.run(["paplay","/usr/share/sounds/freedesktop/stereo/complete.oga"],capture_output=True)
            else: print("\a\a\a",end="",flush=True)
    except Exception: pass

# =========================================================
# GPU
# =========================================================
def detect_device():
    try:
        import torch
        if torch.cuda.is_available():
            name=torch.cuda.get_device_name(0)
            vram=torch.cuda.get_device_properties(0).total_memory//(1024**3)
            return "cuda","GPU: {} ({}GB VRAM)".format(name,vram)
    except ImportError: pass
    return "cpu","CPU: nessuna GPU CUDA rilevata"

# =========================================================
# PROMPT GUIDA (aggiornato v2.4 con V3)
# =========================================================
GUIDE_PROMPT = '''# PROMPT PER RISCRITTURA CAPITOLO — ChatterText TTS v2.4

Sei un editor specializzato nella preparazione di testi per la sintesi vocale con Chatterbox TTS.
Riscrivi il capitolo che ti fornirò applicando il sistema di tag di ChatterText v2.4.

## REGOLA FONDAMENTALE: BLOCCO-RESPIRO
Ogni blocco [inizio]...[fine] deve contenere UNA SOLA unita di respiro:
  * Minimo 5 parole (OBBLIGATORIO — chunk piu corti causano ripetizioni nel TTS)
  * Massimo 14 parole / 80 caratteri (consigliato)
  * Una frase breve o una parte logica di frase

## STRUTTURA BASE
[inizio]
[V1_emozione]
Testo da leggere.[p3][para]
[/V1_emozione]
[fine]

## TAG VOCE (ora con V3!)
  [v1]testo[/v1]                  -> Voce 1 (narratore / personaggio A)
  [v2]testo[/v2]                  -> Voce 2 (personaggio B)
  [v3]testo[/v3]                  -> Voce 3 (personaggio C — opzionale)
  [V1_emozione]...[/V1_emozione]  -> Voce 1 con emozione
  [V2_emozione]...[/V2_emozione]  -> Voce 2 con emozione
  [V3_emozione]...[/V3_emozione]  -> Voce 3 con emozione

  RUOLI SUGGERITI:
    V1 = narratore / voce principale
    V2 = personaggio secondario / interlocutore
    V3 = terzo personaggio / voce narrante interiore / flashback

## GIUNZIONI — 8 livelli (aggiunta [cambio3])
  [join]    0.00s  overlap        stessa frase spezzata su due righe
  [cont]    0.12s  smooth         stessa battuta, stessa idea
  [cambio]  0.50s  crossfade      cambio voce V1<->V2
  [cambio3] 0.50s  crossfade      cambio voce con/da V3
  [para]    0.90s  silenzio netto fine paragrafo
  [stacco]  1.40s  fade+sil+fade  cambio pensiero/concetto
  [lungo]   1.80s  fade+sil+fade  pausa riflessiva
  [scena]   2.40s  stacco secco   cambio scena/capitolo

  REGOLA GIUNZIONI CON V3:
    V1 -> V2 o V2 -> V1  : usa [cambio]
    V1/V2 -> V3          : usa [cambio3]
    V3 -> V1/V2          : usa [cambio3]

## STATI EMOTIVI
  calmo | appassionato | arrabbiato | triste | ironico
  sussurrato | riflessivo | deciso | preoccupato | gentile | serio

## TAG PAUSE INLINE
  [p1]  ~0.18s  virgola, incisi
  [p2]  ~0.40s  punto normale
  [p3]  ~0.65s  riflessione, ;
  [b]   ~1.00s  cambio idea, :
  [bd]  ~1.60s  climax, rivelazioni
  [cap] ~2.00s  reset mentale, capoverso

## ENFASI
  [e1]  enfasi leggera  (+0.10 exaggeration)
  [e2]  enfasi forte    (+0.25 — max 1 ogni 2-3 blocchi)

## ESEMPIO CON TRE VOCI
  [inizio][V1_calmo]
  La porta si apri lentamente.[p3][stacco]
  [/V1_calmo][fine]

  [inizio][V2_arrabbiato]
  Chi sei? Cosa vuoi da noi![e2][bd][cambio3]
  [/V2_arrabbiato][fine]

  [inizio][V3_sussurrato]
  Sono tornato,[p1] come avevo promesso.[p3][para]
  [/V3_sussurrato][fine]

  [inizio][V1_riflessivo]
  Nessuno sapeva cosa sarebbe successo dopo.[b][lungo]
  [/V1_riflessivo][fine]

## REGOLE OBBLIGATORIE
  1. MAI chunk con meno di 5 parole pulite (esclusi tag)
  2. V1 = narratore principale | V2 = personaggio B | V3 = personaggio C (opz.)
  3. SEMPRE un tag di giunzione prima di [fine]
  4. [cambio] SOLO V1<->V2 | [cambio3] quando V3 entra o esce
  5. Max 2 pause consecutive
  6. [e2] max una volta ogni 2-3 blocchi
  7. Emozione guida il ritmo: riflessivo=lento, arrabbiato=veloce
  8. V3 e opzionale: se non serve, non usarla

---
Ora riscrivi il seguente capitolo applicando tutti questi tag:

[INCOLLA QUI IL TESTO DEL CAPITOLO]
'''

# =========================================================
# BUILD SCRIPT PYTHON (esteso per V3)
# =========================================================
def build_python_script(chunks, exag, cfg, temp, v1, v2, v3, epreset, devmode="auto"):
    has2   = bool(v2.strip())
    has3   = bool(v3.strip())
    v2eff  = v2.strip() if has2 else v1
    v3eff  = v3.strip() if has3 else v1
    ep_r   = json.dumps(epreset, ensure_ascii=False, indent=4)
    emop   = "|".join(ALL_EMO)

    scene   = ["poi","quando","all'improvviso","improvvisamente","in quel momento",
               "mentre","subito dopo","intanto","nel frattempo","a quel punto","alla fine"]
    dialog  = ["disse","penso","grido","urlo","sussurro","domando","rispose","chiese",
               "mormoro","esclamo","borbotto","annuncio","replico","aggiunse","continuo","riprese"]
    emow    = ["paura","orrore","ansia","terrore","pianto","felice","gioia","triste",
               "disperato","sconvolto","agitato","sorpreso","commosso","morte","vita",
               "anima","silenzio","infinito"]
    concsh  = ["tuttavia","eppure","nonostante","al contrario","invece","d'altra parte",
               "in realta","in verita","dunque","quindi","pertanto","di conseguenza"]
    reflc   = ["forse","chissa","davvero","possibile che","si chiese","si domando",
               "aveva senso","non aveva senso","significava","voleva dire"]
    philos  = ["verita","giustizia","anima","essere","nulla","infinito","eternita",
               "ragione","sapienza","virtu","bene","male","conoscenza","ignoranza","logos"]

    def pl(lst): return "[\n        "+" ,".join('"{}"'.format(s) for s in lst)+"\n    ]"

    if devmode=="cpu":
        devl = ["DEVICE=torch.device('cpu')", "print('Dispositivo: CPU')"]
    elif devmode=="cuda":
        devl = ["if not torch.cuda.is_available(): print('ERRORE: CUDA non disponibile'); exit(1)",
                "DEVICE=torch.device('cuda')",
                "print(f'Dispositivo: GPU {torch.cuda.get_device_name(0)}')"]
    else:
        devl = ["if torch.cuda.is_available():",
                "    DEVICE=torch.device('cuda')",
                "    print(f'GPU {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory//(1024**3)}GB)')",
                "else:",
                "    DEVICE=torch.device('cpu')",
                "    print('CPU (nessuna GPU)')"]

    L = [
"# Script generato da ChatterText v2.4",
"# Tre voci (V1/V2/V3) + pause gaussiane 6L + giunzioni 8L + dynamic_pause",
"import os,re,sys,random,torch,torchaudio as ta,pathlib,time",
"if sys.platform=='win32':",
"    import io",
"    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')",
"    sys.stderr=io.TextIOWrapper(sys.stderr.buffer,encoding='utf-8',errors='replace')",
    ] + devl + [
"_olt=torch.load",
"def _sl(*a,**k):",
"    if DEVICE.type=='cpu': k.setdefault('map_location',torch.device('cpu'))",
"    return _olt(*a,**k)",
"torch.load=_sl",
"from chatterbox.mtl_tts import ChatterboxMultilingualTTS",
"print('Caricamento modello...')",
"model=ChatterboxMultilingualTTS.from_pretrained(device=DEVICE.type)",
"print('Modello su {}!'.format(DEVICE.type.upper()))",
"chunks={}".format(json.dumps(chunks,ensure_ascii=False,indent=2)),
'AUDIO_V1="2.Voci/{}"'.format(v1),
'AUDIO_V2="2.Voci/{}"'.format(v2eff),
'AUDIO_V3="2.Voci/{}"'.format(v3eff),   # <-- V3
"HAS2={}".format(str(has2)),
"HAS3={}".format(str(has3)),             # <-- flag V3
"for p,lbl,en in [(AUDIO_V1,'V1',True),(AUDIO_V2,'V2',HAS2),(AUDIO_V3,'V3',HAS3)]:",
"    if en and not os.path.exists(p): print(f'NON TROVATO [{lbl}]: {p}'); exit(1)",
"EPRESET={}".format(ep_r),
"DEF_P={{'exaggeration':{},'cfg_weight':{},'temperature':{},'top_p':0.75,'min_p':0.15}}".format(exag,cfg,temp),
"PM={",
"    '[p1]':(0.18,0.03), '[p2]':(0.40,0.05), '[p3]':(0.65,0.07),",
"    '[b]': (1.00,0.10), '[bd]':(1.60,0.15), '[cap]':(2.00,0.20),",
"    '[pausa]':(0.50,0.05),'[pausa_lunga]':(1.20,0.10),'[silenzio]':(2.00,0.15),",
"}",
"def gp(tag):",
"    b,s=PM.get(tag.lower(),(0.40,0.05))",
"    raw=random.gauss(b,s)",
"    return max(b*0.60, min(raw, b*1.40))",
"# GIUNZIONI 8 livelli (cambio3 = come cambio, per V3)",
"JM={'[join]':(0.00,'overlap'),'[cont]':(0.12,'smooth'),",
"    '[cambio]':(0.50,'cambio'),'[cambio3]':(0.50,'cambio'),",
"    '[para]':(0.90,'silence'),'[stacco]':(1.40,'fade_sil_fade'),",
"    '[lungo]':(1.80,'fade_sil_fade'),'[scena]':(2.40,'hard')}",
"EP={'e1':{'exaggeration_delta':0.10,'cfg_weight_delta':-0.05},'e2':{'exaggeration_delta':0.25,'cfg_weight_delta':-0.12}}",
'EN=r"{}"'.format(emop),
"PR=re.compile(r'(\\[p[123]\\]|\\[b(?:d)?\\]|\\[cap\\]|\\[pausa(?:_lunga)?\\]|\\[silenzio\\])',re.IGNORECASE)",
"ER=re.compile(r'\\[e[12]\\]',re.IGNORECASE)",
"JR=re.compile(r'\\[(?:join|cont|cambio|cambio3|para|stacco|lungo|scena)\\]',re.IGNORECASE)",
"def pc(chunk):",
"    rp=PR.findall(chunk)",
"    ps=[(p,gp(p)) for p in rp]; tp=sum(d for _,d in ps)",
"    et=ER.findall(chunk); ek=et[-1].lower().strip('[]') if et else None",
"    jt=JR.findall(chunk); jk=jt[-1].lower() if jt else None",
"    def si(t):",
"        t=PR.sub('',t); t=ER.sub('',t); t=JR.sub('',t); return t.strip()",
"    # Gestisce v1, v2, v3",
"    m=re.search(r'\\[(v1|v2|v3)_(' +EN+r')\\]',chunk,re.IGNORECASE)",
"    if m:",
"        v,e=m.group(1).lower(),m.group(2).lower()",
"        cl=re.sub(r'\\[(?:v1|v2|v3)_(?:'+EN+r')\\]','',chunk,flags=re.IGNORECASE)",
"        cl=re.sub(r'\\[/(?:v1|v2|v3)_(?:'+EN+r')\\]','',cl,flags=re.IGNORECASE)",
"        return si(cl),v,e,ps,tp,ek,jk",
"    m=re.search(r'\\[(v1|v2|v3)\\]',chunk,re.IGNORECASE)",
"    if m:",
"        v=m.group(1).lower()",
"        cl=re.sub(r'\\[/?(?:v1|v2|v3)\\]','',chunk,flags=re.IGNORECASE)",
"        return si(cl),v,None,ps,tp,ek,jk",
"    m=re.search(r'\\[('+EN+r')\\]',chunk,re.IGNORECASE)",
"    if m:",
"        e=m.group(1).lower()",
"        cl=re.sub(r'\\[(?:'+EN+r')\\]','',chunk,flags=re.IGNORECASE)",
"        cl=re.sub(r'\\[/(?:'+EN+r')\\]','',cl,flags=re.IGNORECASE)",
"        return si(cl),'v1',e,ps,tp,ek,jk",
"    return si(chunk),'v1',None,ps,tp,ek,jk",
"def pp(emo,ek=None):",
"    p=EPRESET[emo].copy() if emo and emo in EPRESET else DEF_P.copy()",
"    p.setdefault('top_p',0.75); p.setdefault('min_p',0.15)",
"    if ek and ek in EP:",
"        p['exaggeration']=min(1.0,p['exaggeration']+EP[ek]['exaggeration_delta'])",
"        p['cfg_weight']=max(0.1,p['cfg_weight']+EP[ek]['cfg_weight_delta'])",
"    return p",
"tc=[pc(c) for c in chunks]",
"def rn(wav,sr,gtdb=-50,hpz=80):",
"    thr=10**(gtdb/20)",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    gm=(torch.abs(wav)>thr).float()",
"    k=int(sr*0.008)",
"    if k%2==0: k+=1",
"    kern=torch.ones(1,1,k)/k",
"    gm=torch.nn.functional.conv1d(gm.unsqueeze(0),kern,padding=k//2).squeeze(0).clamp(0,1)",
"    wav=wav*gm; wav=ta.functional.highpass_biquad(wav,sr,cutoff_freq=hpz); return wav",
"segs=[]; fail=[]",
"st=time.time()",
"print('\\n'+'='*55)",
"print('AVVIO GENERAZIONE [{}]'.format(DEVICE.type.upper()))",
"print('='*55)",
"for i,(txt,vo,em,ps,tp,ek,jk) in enumerate(tc):",
"    if i>0:",
"        el=time.time()-st; av=el/i; rm=av*(len(tc)-i)",
"        eta='  ETA:{:.0f}s'.format(rm)",
"    else: eta=''",
"    pct=int(i/len(tc)*100)",
"    bar=chr(9608)*(pct//5)+chr(9617)*(20-pct//5)",
"    _em_s='['+em+']' if em else ''",
"    _ek_s='['+ek+']' if ek else ''",
"    _jk_s='['+jk.strip('[]')+']' if jk else ''",
"    _tail='...' if len(txt)>80 else ''",
"    _rep=repr(txt[:80])",
"    print('\\n [{}] {}%{}'.format(bar,pct,eta))",
"    print(' Chunk {}/{} [{}]{}{}{}'.format(i+1,len(tc),vo.upper(),_em_s,_ek_s,_jk_s))",
"    print('   {}{}'.format(_rep,_tail))",
"    if tp>0: print('   pausa: {:.2f}s (gauss)'.format(tp))",
"    if len(txt.split())<5: print('   ATTENZIONE: chunk corto!')",
"    # Routing voce: v3 -> AUDIO_V3 (se disponibile), v2 -> AUDIO_V2, default V1",
"    if vo=='v3' and HAS3:   vp=AUDIO_V3",
"    elif vo=='v2' and HAS2: vp=AUDIO_V2",
"    else:                   vp=AUDIO_V1",
"    p=pp(em,ek); ok=False",
"    try:",
"        wav=model.generate(txt,language_id='it',audio_prompt_path=vp,",
"            exaggeration=p['exaggeration'],cfg_weight=p['cfg_weight'],",
"            temperature=p['temperature'],min_p=p['min_p'],top_p=p['top_p'])",
"        if DEVICE.type=='cuda': wav=wav.cpu()",
"        wav=wav/(torch.max(torch.abs(wav))+1e-8)*0.95",
"        if tp>0:",
"            sil=torch.zeros((wav.shape[0],int(model.sr*tp)))",
"            wav=torch.cat([wav,sil],dim=-1)",
"        segs.append(wav); ok=True; print('   OK!')",
"    except Exception as e: print('   ERR:{} retry...'.format(e))",
"    if not ok:",
"        try:",
"            wav=model.generate(txt,language_id='it',audio_prompt_path=vp,",
"                exaggeration=0.0,cfg_weight=0.25,temperature=0.22,min_p=0.20,top_p=0.65)",
"            if DEVICE.type=='cuda': wav=wav.cpu()",
"            wav=wav/(torch.max(torch.abs(wav))+1e-8)*0.95",
"            segs.append(wav); print('   Recuperato!')",
"        except Exception as e2: print(f'   FALLITO:{e2}'); fail.append(i)",
"if not segs: print('Nessun audio.'); exit(1)",
"od=pathlib.Path('1.Output'); od.mkdir(exist_ok=True)",
"num=len(list(od.glob('audiolibro_*.wav')))+1",
"out=od/'audiolibro_{:02d}.wav'.format(num)",
"SCENE={}".format(pl(scene)),
"DIALOG={}".format(pl(dialog)),
"EMOW={}".format(pl(emow)),
"CONCS={}".format(pl(concsh)),
"REFL={}".format(pl(reflc)),
"PHIL={}".format(pl(philos)),
"def dyn_pause(txt, emo=None):",
"    t=txt.strip(); lo=t.lower(); ln=len(t); lc=t[-1:] if t else ''",
"    if t.endswith('...'): base,sig=1.50,0.15",
"    elif lc in '?!':     base,sig=1.00,0.12",
"    elif lc=='.':        base,sig=0.42,0.06",
"    elif lc==':':        base,sig=0.70,0.08",
"    elif lc==';':        base,sig=0.60,0.07",
"    elif lc==',':        base,sig=0.20,0.03",
"    else:                base,sig=0.18,0.03",
"    if ln>500:   base*=1.50",
"    elif ln>300: base*=1.30",
"    elif ln>150: base*=1.12",
"    elif ln<60:  base*=0.80",
"    if any(lo.startswith(s) for s in SCENE):  base*=1.28",
"    if any(w in lo for w in PHIL):            base*=1.45",
"    if any(w in lo for w in CONCS):           base*=1.38",
"    if any(w in lo for w in REFL):            base*=1.30",
"    if any(w in lo for w in EMOW):            base*=1.18",
"    if any(v in lo for v in DIALOG):          base*=0.75",
"    if emo in ('riflessivo','calmo','triste','preoccupato'):  base*=1.18",
"    elif emo in ('arrabbiato','deciso'):                      base*=0.72",
"    elif emo=='sussurrato':                                   base*=1.10",
"    raw=random.gauss(base, sig)",
"    return max(base*0.60, min(raw, base*1.40))",
"def te(wav,sr,tdb=-45,mms=30):",
"    mg=int(sr*mms/1000); thr=10**(tdb/20)",
"    mo=wav[0] if wav.dim()>1 else wav; en=torch.abs(mo)",
"    s=next((max(0,i-mg) for i,v in enumerate(en) if v>thr),0)",
"    e=next((min(len(en),i+mg) for i in range(len(en)-1,-1,-1) if en[i]>thr),len(en))",
"    return wav[...,s:e]",
"def cf(s1,s2,sr,fms=55):",
"    f=int(sr*fms/1000)",
"    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)",
"    fo=torch.linspace(1,0,f)**1.5; fi=torch.linspace(0,1,f)**1.5",
"    return torch.cat([s1[...,:-f],s1[...,-f:]*fo+s2[...,:f]*fi,s2[...,f:]],dim=-1)",
"def ov(s1,s2,sr,oms=80):",
"    f=int(sr*oms/1000)",
"    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)",
"    fo=torch.linspace(1,0,f)**2; fi=torch.linspace(0,1,f)**2",
"    return torch.cat([s1[...,:-f],s1[...,-f:]*fo+s2[...,:f]*fi,s2[...,f:]],dim=-1)",
"def af(wav,sr,fms=14):",
"    f=int(sr*fms/1000); wav=wav.clone()",
"    wav[...,:f]*=torch.linspace(0,1,f); wav[...,-f:]*=torch.linspace(1,0,f); return wav",
"def fsf(s1,s2,sr,ss,foms=80,fims=60):",
"    fl=int(sr*foms/1000); il=int(sr*fims/1000)",
"    sl=max(0,int(sr*ss)-fl-il)",
"    s1=s1.clone()",
"    if s1.shape[-1]>=fl: s1[...,-fl:]*=torch.linspace(1.0,0.0,fl)**1.8",
"    sil=torch.zeros((s2.shape[0],sl),dtype=s2.dtype)",
"    s2=s2.clone()",
"    if s2.shape[-1]>=il: s2[...,:il]*=torch.linspace(0.0,1.0,il)**1.8",
"    return torch.cat([s1,sil,s2],dim=-1)",
"def asmb(s1,s2,sr,jt):",
"    if jt is None: return None",
"    ss,mode=JM.get(jt,(0.5,'silence'))",
"    if mode=='overlap': return ov(s1,s2,sr)",
"    if mode=='fade_sil_fade': return fsf(s1,s2,sr,ss)",
"    sil=torch.zeros((s2.shape[0],int(sr*ss))) if ss>0 else None",
"    if mode=='smooth': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=30)",
"    if mode=='cambio': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=100)",
"    if mode=='silence': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=55)",
"    if mode=='hard': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)",
"    return cf(s1,s2,sr)",
"jl=[x[6] for x in tc]",
"fa=None",
"for i,seg in enumerate(segs):",
"    seg=rn(seg,model.sr); seg=te(seg,model.sr); seg=af(seg,model.sr)",
"    if fa is None: fa=seg; continue",
"    jt=jl[i-1]; res=asmb(fa,seg,model.sr,jt)",
"    if res is None:",
"        pau=dyn_pause(chunks[i-1], emo=tc[i-1][2])",
"        sil=torch.zeros((seg.shape[0],int(model.sr*pau)))",
"        fa=cf(fa,torch.cat([sil,seg],dim=-1),model.sr)",
"        js='auto({:.2f}s)'.format(pau)",
"    else: fa=res; js=jt if jt else 'auto'",
"    print(f'   -> join {i}: {js}')",
"fa=fa/(torch.max(torch.abs(fa))+1e-8)*0.95",
"ta.save(out,fa,model.sr)",
"dur=fa.shape[-1]/model.sr; tot=time.time()-st",
"print(f'\\n FILE: {out}')",
"print(f'   Durata: {dur:.1f}s ({dur/60:.1f} min)')",
"print(f'   Tempo:  {tot:.1f}s ({tot/60:.1f} min)')",
"print(f'   Device: {DEVICE.type.upper()}')",
"v3info=' | V3: attiva' if HAS3 else ''",
"print(f'   Voci: V1+{\"V2\" if HAS2 else \"-\"}{v3info}')",
"print(f'   OK: {len(segs)}/{len(chunks)}')",
"if fail: print(f'   FAIL: {fail}')",
"print('\\nProcesso completato!')",
"print('__CHATTERTEXT_DONE__')",
    ]
    return "\n".join(L)

# =========================================================
# WIDGET HELPERS
# =========================================================
def sf(parent, **kw):
    kw.setdefault("bg", C["surface"]); kw.setdefault("bd", 0)
    return tk.Frame(parent, **kw)

def se(parent, width=18, **kw):
    return tk.Entry(parent, width=width, bg=C["surface2"], fg=C["text"],
                    insertbackground=C["accent"], relief="flat", bd=0,
                    highlightthickness=1, highlightcolor=C["accent"],
                    highlightbackground=C["border"], font=FB, **kw)

def sb_btn(parent, text, cmd, color=None, **kw):
    co = color or C["accent2"]
    b = tk.Button(parent, text=text, command=cmd,
                  bg=C["surface2"], fg=C["text"],
                  activebackground=co, activeforeground="#fff",
                  relief="flat", bd=0, cursor="hand2",
                  font=FL, padx=14, pady=8, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=co))
    b.bind("<Leave>", lambda e: b.config(bg=C["surface2"]))
    return b

def stat_card(parent, var, label):
    f = sf(parent, bg=C["surface2"], padx=20, pady=16)
    f.config(highlightthickness=1, highlightbackground=C["border"])
    tk.Label(f, textvariable=var, font=FST, fg=C["accent"], bg=C["surface2"]).pack()
    tk.Label(f, text=label, font=FS, fg=C["text_dim"], bg=C["surface2"]).pack()
    return f

# =========================================================
# PRESET WINDOW
# =========================================================
class PresetWindow(tk.Toplevel):
    PARAMS = ["exaggeration","cfg_weight","temperature","top_p","min_p"]
    def __init__(self, parent, presets, on_save):
        super().__init__(parent)
        self.title("Preset Emotivi"); self.configure(bg=C["bg"])
        self.resizable(True,True); self.on_save=on_save
        self.vs={}
        for emo,vals in presets.items():
            self.vs[emo]={}
            for p in self.PARAMS: self.vs[emo][p]=tk.StringVar(value=str(vals.get(p,"")))
        self._build(); self.grab_set()

    def _build(self):
        tk.Label(self,text="Parametri Prosodici per Emozione",font=FH2,
                 fg=C["accent"],bg=C["bg"],pady=14).pack(fill="x")
        hdr=tk.Frame(self,bg=C["hdr_bg"]); hdr.pack(fill="x",padx=16)
        for ci,(h,w) in enumerate(zip(["Emozione"]+self.PARAMS,[14]+[13]*5)):
            tk.Label(hdr,text=h,font=FL,fg=C["accent"],bg=C["hdr_bg"],
                     width=w,anchor="center",pady=6).grid(row=0,column=ci,padx=2)
        for ri,emo in enumerate(ALL_EMO):
            bg=C["surface"] if ri%2==0 else C["surface2"]
            rf=tk.Frame(self,bg=bg); rf.pack(fill="x",padx=16,pady=1)
            tk.Label(rf,text="  "+emo,font=FL,fg=EMO_C.get(emo,C["text_dim"]),
                     bg=bg,width=14,anchor="w",pady=5).grid(row=0,column=0,padx=2)
            for ci,param in enumerate(self.PARAMS):
                tk.Entry(rf,textvariable=self.vs[emo][param],width=10,
                         bg=C["surface2"],fg=C["text"],insertbackground=C["accent"],
                         relief="flat",bd=0,highlightthickness=1,
                         highlightbackground=C["border"],font=FB,
                         justify="center").grid(row=0,column=ci+1,padx=4,pady=3)
        br=tk.Frame(self,bg=C["bg"],pady=14); br.pack()
        sb_btn(br,"Salva e Chiudi",self._save,color=C["success"]).pack(side="left",padx=8)
        sb_btn(br,"Ripristina",self._reset,color=C["warning"]).pack(side="left",padx=8)
        sb_btn(br,"Annulla",self.destroy,color=C["danger"]).pack(side="left",padx=8)

    def _save(self):
        r={}
        for emo in ALL_EMO:
            r[emo]={}
            for p in self.PARAMS:
                try: r[emo][p]=round(float(self.vs[emo][p].get()),3)
                except: r[emo][p]=EMOTION_PRESETS[emo][p]
        self.on_save(r); self.destroy()

    def _reset(self):
        for emo in ALL_EMO:
            for p in self.PARAMS: self.vs[emo][p].set(str(EMOTION_PRESETS[emo][p]))

# =========================================================
# APP PRINCIPALE
# =========================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatterText v2.4")
        self.geometry("1100x900"); self.minsize(900,700)
        self.configure(bg=C["bg"])
        self.chunks=[]; self.chunk_vars=[]; self.script_path=None
        self.epreset={k:v.copy() for k,v in EMOTION_PRESETS.items()}
        self._proc=None; self._t0=None
        self.vwords=tk.StringVar(value="0"); self.vchars=tk.StringVar(value="0")
        self.vchunks=tk.StringVar(value="0"); self.verrs=tk.StringVar(value="0")
        self.vdev=tk.StringVar(value="auto"); self.vsound=tk.BooleanVar(value=True)
        self._build_ui(); self._detect_device()

    # ---- LAYOUT ----
    def _build_ui(self):
        canvas=tk.Canvas(self,bg=C["bg"],highlightthickness=0)
        scr=tk.Scrollbar(self,orient="vertical",command=canvas.yview)
        self.sf=tk.Frame(canvas,bg=C["bg"])
        self.sf.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        self._cw=canvas.create_window((0,0),window=self.sf,anchor="nw")
        def _rsz(e):
            cw=min(e.width,1080); x=(e.width-cw)//2
            canvas.itemconfig(self._cw,width=cw); canvas.coords(self._cw,x,0)
        canvas.bind("<Configure>",_rsz)
        canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side="left",fill="both",expand=True); scr.pack(side="right",fill="y")
        self.bind_all("<MouseWheel>",lambda e:canvas.yview_scroll(-1*(e.delta//120),"units"))
        r=self.sf
        self._hdr(r); self._dev_sec(r); self._inp_sec(r); self._ctrl_sec(r)
        self._stats_sec(r); self._log_sec(r); self._chunks_sec(r)
        self._guide_sec(r); self._footer(r)

    def _sec(self,parent,title):
        o=tk.Frame(parent,bg=C["bg"],padx=18,pady=10); o.pack(fill="x")
        tk.Label(o,text=title,font=FH2,fg=C["accent"],bg=C["bg"]).pack(anchor="w",pady=(0,8))
        i=tk.Frame(o,bg=C["surface"],bd=0,highlightthickness=1,
                   highlightbackground=C["border"],padx=20,pady=16)
        i.pack(fill="x"); return i

    def _le(self,parent,label,default,wide=False):
        g=sf(parent); g.pack(side="left",padx=(0,16))
        tk.Label(g,text=label,font=FL,fg=C["accent"],bg=C["surface"]).pack(anchor="w")
        v=tk.StringVar(value=default)
        se(g,width=30 if wide else 10,textvariable=v).pack(anchor="w",pady=(2,0))
        return v

    def _hdr(self,r):
        h=tk.Frame(r,bg="#0a1628",pady=24); h.pack(fill="x")
        tk.Label(h,text="ChatterText",font=FH1,fg="#fff",bg="#0a1628").pack()
        tk.Label(h,text="Analizza e prepara il testo per Chatterbox TTS",
                 font=FB,fg=C["text_dim"],bg="#0a1628").pack(pady=(4,0))
        tk.Label(h,text="v2.4  |  Tre voci V1/V2/V3  |  Pause gaussiane 6L  |  Giunzioni 8L  |  dynpause emo",
                 font=FS,fg=C["gpu"],bg="#0a1628").pack(pady=(2,0))

    def _dev_sec(self,r):
        sec=self._sec(r,"Dispositivo di Calcolo")
        top=sf(sec); top.pack(fill="x",pady=(0,10))
        self.badge_var=tk.StringVar(value="Rilevamento...")
        self.badge=tk.Label(top,textvariable=self.badge_var,font=FL,
                            fg="#fff",bg=C["cpu"],padx=12,pady=6)
        self.badge.pack(side="left",padx=(0,20))
        sf2=sf(top); sf2.pack(side="left")
        tk.Label(sf2,text="Modalità:",font=FL,fg=C["accent"],bg=C["surface"]).pack(side="left",padx=(0,8))
        for val,lbl in [("auto","Auto"),("cuda","Forza GPU"),("cpu","Forza CPU")]:
            tk.Radiobutton(sf2,text=lbl,variable=self.vdev,value=val,font=FB,
                           fg=C["text"],bg=C["surface"],selectcolor=C["surface2"],
                           activeforeground=C["accent"],activebackground=C["surface"],
                           cursor="hand2").pack(side="left",padx=6)
        nf=sf(top); nf.pack(side="right")
        tk.Checkbutton(nf,text="Suono fine generazione",variable=self.vsound,
                       font=FB,fg=C["text"],bg=C["surface"],selectcolor=C["surface2"],
                       activeforeground=C["accent"],activebackground=C["surface"],
                       cursor="hand2").pack(side="left")
        sb_btn(nf,"Test",lambda:threading.Thread(target=play_sound,daemon=True).start(),
               color=C["text_dim"]).pack(side="left",padx=(8,0))

    def _inp_sec(self,r):
        sec=self._sec(r,"Testo")
        self.txt=scrolledtext.ScrolledText(sec,height=10,bg=C["surface2"],fg=C["text"],
                    insertbackground=C["accent"],relief="flat",bd=0,font=FM,wrap="word",
                    highlightthickness=1,highlightbackground=C["border"])
        self.txt.pack(fill="x",pady=(0,10))
        self.txt.insert("1.0","Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.txt.bind("<FocusIn>",lambda e: self.txt.delete("1.0","end")
                      if "Incolla qui" in self.txt.get("1.0","end-1c") else None)
        self.vcc=tk.StringVar(value="0 / 10000")
        tk.Label(sec,textvariable=self.vcc,font=FS,fg=C["text_dim"],
                 bg=C["surface"],anchor="e").pack(fill="x")
        self.txt.bind("<KeyRelease>",lambda e:self.vcc.set(
            "{} / 10000".format(len(self.txt.get("1.0","end-1c")))))

    def _ctrl_sec(self,r):
        sec=self._sec(r,"Parametri")
        r1=sf(sec); r1.pack(fill="x",pady=(0,10))
        self.vminw=self._le(r1,"Min parole/chunk","20")
        self.vmaxw=self._le(r1,"Max parole/chunk","40")
        self.vmaxc=self._le(r1,"Max caratteri","240")

        # --- Riga voci: V1, V2, V3 (nuovo) ---
        r2=sf(sec); r2.pack(fill="x",pady=(0,10))
        self.vv1=self._le(r2,"Voce 1 (2.Voci/)","3l14n.wav",wide=True)
        self.vv2=self._le(r2,"Voce 2 (opz.)","",wide=True)
        self.vv3=self._le(r2,"Voce 3 (opz.)","",wide=True)   # <-- NUOVO campo V3
        gv=sf(r2); gv.pack(side="left",padx=(8,0),anchor="s")
        sb_btn(gv,"Verifica voci",self._verify_voices,color=C["text_dim"]).pack(pady=(18,0))

        r3=sf(sec); r3.pack(fill="x",pady=(0,10))
        self.vexag=self._le(r3,"Exaggeration","0.62")
        self.vcfg=self._le(r3,"CFG Weight","0.70")
        self.vtemp=self._le(r3,"Temperature","0.58")
        gp=sf(r3); gp.pack(side="left",padx=(16,0))
        tk.Label(gp,text="Preset emotivi",font=FL,fg=C["accent"],bg=C["surface"]).pack(anchor="w")
        sb_btn(gp,"Modifica",self._presets,color="#8e44ad").pack(anchor="w",pady=(4,0))
        r4=sf(sec); r4.pack(fill="x",pady=(0,14))
        tk.Label(r4,text="Cartella Chatterbox:",font=FL,fg=C["accent"],bg=C["surface"]).pack(side="left",padx=(0,8))
        self.vdir=tk.StringVar(value=str(pathlib.Path(__file__).parent))
        se(r4,width=55,textvariable=self.vdir).pack(side="left",padx=(0,8))
        sb_btn(r4,"Sfoglia",self._browse,color=C["text_dim"]).pack(side="left")
        br=sf(sec); br.pack(fill="x",pady=(6,0))
        sb_btn(br,"Analizza e Processa",self.process,color=C["accent2"]).pack(side="left",padx=(0,10))
        sb_btn(br,"Cancella",self.clear_all,color=C["danger"]).pack(side="left")

    def _verify_voices(self):
        base=pathlib.Path(self.vdir.get())/"2.Voci"
        res=[]
        # Aggiunto V3 alla verifica
        for v,lbl in [(self.vv1,"V1"),(self.vv2,"V2"),(self.vv3,"V3")]:
            fn=v.get().strip()
            if not fn: res.append("  {} — non specificata".format(lbl)); continue
            p=base/fn
            if p.exists(): res.append("  OK {} — {} ({} KB)".format(lbl,fn,p.stat().st_size//1024))
            else: res.append("  MANCANTE {} — {}".format(lbl,p))
        messagebox.showinfo("Verifica Voci","\n".join(res))

    def _stats_sec(self,r):
        self.stats=self._sec(r,"Statistiche"); self.stats.pack_forget()
        cards=sf(self.stats); cards.pack(fill="x")
        for ci in range(4): cards.columnconfigure(ci,weight=1)
        for ci,(v,l) in enumerate([(self.vwords,"Parole"),(self.vchars,"Caratteri"),
                                    (self.vchunks,"Chunk"),(self.verrs,"Problemi")]):
            stat_card(cards,v,l).grid(row=0,column=ci,sticky="ew",padx=6,pady=4)
        self.tag_lbl=tk.Label(self.stats,text="",font=FB,fg=C["warning"],bg=C["surface"],pady=6)
        self.tag_lbl.pack()
        self.err_box=tk.Text(self.stats,height=4,bg=C["surface2"],fg=C["warning"],
                             font=FS,relief="flat",bd=0,highlightthickness=1,
                             highlightbackground=C["border"],state="disabled",wrap="word")
        self.err_box.pack(fill="x",pady=(8,0))

    def _log_sec(self,r):
        self.logsec=self._sec(r,"Output"); self.logsec.pack_forget()
        pf=sf(self.logsec); pf.pack(fill="x",pady=(0,8))
        self.progv=tk.DoubleVar(value=0)
        sty=ttk.Style(); sty.theme_use("default")
        sty.configure("G.Horizontal.TProgressbar",troughcolor=C["surface2"],
                       background=C["success"],darkcolor=C["success"],
                       lightcolor=C["success"],bordercolor=C["border"])
        ttk.Progressbar(pf,variable=self.progv,maximum=100,
                        style="G.Horizontal.TProgressbar",length=400
                        ).pack(side="left",fill="x",expand=True,padx=(0,10))
        self.vprog=tk.StringVar(value="In attesa...")
        tk.Label(pf,textvariable=self.vprog,font=FS,fg=C["text_dim"],bg=C["surface"]).pack(side="left")
        er=sf(self.logsec); er.pack(fill="x",pady=(0,6))
        self.veta=tk.StringVar(value="")
        tk.Label(er,textvariable=self.veta,font=FS,fg=C["warning"],bg=C["surface"]).pack(side="left")
        self.vdevl=tk.StringVar(value="")
        tk.Label(er,textvariable=self.vdevl,font=FS,fg=C["gpu"],bg=C["surface"]).pack(side="right")
        self.log=scrolledtext.ScrolledText(self.logsec,height=14,bg="#050505",fg=C["success"],
                     font=("Courier New",9),relief="flat",bd=0,state="disabled",
                     highlightthickness=1,highlightbackground=C["border"])
        self.log.pack(fill="x")
        sr=sf(self.logsec); sr.pack(fill="x",pady=(8,0))
        self.stopbtn=sb_btn(sr,"Stop",self._stop,color=C["danger"])
        self.stopbtn.pack(side="left"); self.stopbtn.config(state="disabled")

    def _chunks_sec(self,r):
        self.chunksec=self._sec(r,"Chunk Generati"); self.chunksec.pack_forget()
        br=sf(self.chunksec); br.pack(fill="x",pady=(0,14))
        sb_btn(br,"Salva Script .py",self.save_script,color=C["accent2"]).pack(side="left",padx=(0,10))
        sb_btn(br,"Genera Audio",self.run_chatterbox,color=C["success"]).pack(side="left",padx=(0,10))
        sb_btn(br,"Copia Tutti",self.copy_all,color=C["text_dim"]).pack(side="left")
        self.cbox=sf(self.chunksec); self.cbox.pack(fill="x")

    def _guide_sec(self,r):
        outer=tk.Frame(r,bg=C["bg"],padx=18,pady=10); outer.pack(fill="x")
        hr=tk.Frame(outer,bg=C["bg"]); hr.pack(fill="x",pady=(0,8))
        tk.Label(hr,text="Guida Tag — v2.4",font=FH2,fg=C["accent"],bg=C["bg"]).pack(side="left")
        bf=tk.Frame(hr,bg=C["bg"]); bf.pack(side="right")
        sb_btn(bf,"Copia Prompt AI",self._copy_prompt,color=C["success"]).pack(side="left",padx=(0,8))
        sb_btn(bf,"Scarica Prompt",self._save_prompt,color=C["accent2"]).pack(side="left")
        inner=tk.Frame(outer,bg=C["surface"],bd=0,highlightthickness=1,
                       highlightbackground=C["border"],padx=20,pady=16)
        inner.pack(fill="x")
        wf=tk.Frame(inner,bg="#1a0a00",highlightthickness=1,
                    highlightbackground=C["danger"],padx=14,pady=10)
        wf.pack(fill="x",pady=(0,16))
        tk.Label(wf,text="REGOLA ANTI-RIPETIZIONE: ogni chunk deve avere almeno 5 parole pulite.\n"
                         "Battute brevi (\"Bene.\",\"Si.\") vanno unite alla riga successiva.",
                 font=FS,fg=C["warning"],bg="#1a0a00",justify="left",anchor="w").pack(fill="x")
        cols=tk.Frame(inner,bg=C["surface"]); cols.pack(fill="x")
        cols.columnconfigure(0,weight=1); cols.columnconfigure(1,weight=1)
        lc=tk.Frame(cols,bg=C["surface"]); lc.grid(row=0,column=0,sticky="nw",padx=(0,16))
        rc=tk.Frame(cols,bg=C["surface"]); rc.grid(row=0,column=1,sticky="nw")

        def sl(parent,txt):
            tk.Label(parent,text=txt,font=FL,fg=C["accent"],bg=C["surface"],pady=6).pack(anchor="w")

        def tg(parent,data):
            f=tk.Frame(parent,bg=C["surface"]); f.pack(fill="x",pady=(0,10))
            for ci,(tag,col,desc) in enumerate(data):
                cell=tk.Frame(f,bg=C["surface2"],highlightthickness=1,highlightbackground=col)
                cell.grid(row=0,column=ci,padx=3,pady=2,sticky="ew"); f.columnconfigure(ci,weight=1)
                tk.Label(cell,text=tag,font=("Courier New",9,"bold"),fg=col,
                         bg=C["surface2"],pady=4,padx=5).pack()
                tk.Label(cell,text=desc,font=FS,fg=C["text_dim"],
                         bg=C["surface2"],padx=4,pady=2,justify="center").pack()

        # Sinistra
        sl(lc,"TAG VOCE (V1/V2/V3)")
        tg(lc,[("[v1]",C["v1"],"Voce 1"),("[v2]",C["v2"],"Voce 2"),("[v3]",C["v3"],"Voce 3"),
               ("[V1_e]",C["v1"],"V1+emo"),("[V2_e]",C["v2"],"V2+emo"),("[V3_e]",C["v3"],"V3+emo")])

        # Etichetta ruoli
        rl=tk.Frame(lc,bg="#0d1a0d",highlightthickness=1,highlightbackground=C["v3"],padx=10,pady=8)
        rl.pack(fill="x",pady=(0,10))
        tk.Label(rl,text="V1 = Narratore/A   |   V2 = Personaggio B   |   V3 = Personaggio C / voce interiore",
                 font=FS,fg=C["v3"],bg="#0d1a0d",anchor="w").pack(fill="x")

        sl(lc,"STATI EMOTIVI")
        br2=tk.Frame(lc,bg=C["surface"]); br2.pack(fill="x",pady=(0,12))
        for emo in ALL_EMO:
            tk.Label(br2,text=" {} ".format(emo),font=FS,fg="#fff",
                     bg=EMO_C.get(emo,C["text_dim"]),padx=4,pady=2).pack(side="left",padx=2,pady=2)

        sl(lc,"PAUSE INLINE — 6 livelli")
        fp=tk.Frame(lc,bg=C["surface"]); fp.pack(fill="x",pady=(0,4))
        for ci,(tag,col,desc) in enumerate([
            ("[p1]","#4a9080","~0.18s\nmicro\nvirgola"),
            ("[p2]","#2980b9","~0.40s\nbreve\npunto ."),
            ("[p3]","#8e44ad","~0.65s\nmedia\nrifless ;"),
            ("[b]","#27ae60","~1.00s\nlunga\nidea :"),
            ("[bd]","#e84357","~1.60s\ndrammat\nclimax"),
            ("[cap]","#e67e22","~2.00s\ncapovers\nreset"),
        ]):
            cell=tk.Frame(fp,bg=C["surface2"],highlightthickness=1,highlightbackground=col)
            cell.grid(row=0,column=ci,padx=2,pady=2,sticky="ew"); fp.columnconfigure(ci,weight=1)
            tk.Label(cell,text=tag,font=("Courier New",9,"bold"),fg=col,
                     bg=C["surface2"],pady=4,padx=3).pack()
            tk.Label(cell,text=desc,font=FS,fg=C["text_dim"],
                     bg=C["surface2"],padx=2,pady=2,justify="center").pack()
        tk.Label(lc,text="  gauss clamp±40% [60%-140% base] -> anti-freeze anti-negativo",
                 font=FS,fg=C["success"],bg=C["surface"],pady=4,anchor="w").pack(fill="x")
        sl(lc,"ENFASI")
        tg(lc,[("[e1]","#e67e22","Leggera\n+0.10"),("[e2]","#e84357","Forte\n+0.25")])
        sl(lc,"LEGACY")
        tg(lc,[("[pausa]","#7f8c8d","~0.50s"),("[pausa_lunga]","#7f8c8d","~1.20s"),
               ("[silenzio]","#7f8c8d","~2.00s")])

        # Destra
        sl(rc,"GIUNZIONI — 8 livelli (+ cambio3 per V3)")
        fj=tk.Frame(rc,bg=C["surface"]); fj.pack(fill="x",pady=(0,6))
        for ci,(tag,col,desc) in enumerate([
            ("[join]","#00cec9","0.00s\noverlap\nstessa fr."),
            ("[cont]","#74b9ff","0.12s\nsmooth\nstessa id."),
            ("[cambio]","#a29bfe","0.50s\ncrossf.\nV1/V2"),
            ("[cambio3]","#00b894","0.50s\ncrossf.\ncon V3"),
            ("[para]","#fdcb6e","0.90s\nsilenzio\nfine §"),
            ("[stacco]","#fd79a8","1.40s\nfsf\nidea"),
            ("[lungo]","#e17055","1.80s\nfsf\nrifl."),
            ("[scena]","#636e72","2.40s\nhard\nscena"),
        ]):
            cell=tk.Frame(fj,bg=C["surface2"],highlightthickness=1,highlightbackground=col)
            cell.grid(row=0,column=ci,padx=2,pady=2,sticky="ew"); fj.columnconfigure(ci,weight=1)
            tk.Label(cell,text=tag,font=("Courier New",8,"bold"),fg=col,
                     bg=C["surface2"],pady=4,padx=2).pack()
            tk.Label(cell,text=desc,font=FS,fg=C["text_dim"],
                     bg=C["surface2"],padx=2,pady=2,justify="center").pack()

        tk.Label(rc,text="  [cambio]=V1<->V2  |  [cambio3]=entra/esce V3  |  [stacco][lungo]=fade+sil+fade",
                 font=FS,fg=C["v3"],bg=C["surface"],pady=4,anchor="w").pack(fill="x")

        sl(rc,"Struttura base con V3")
        sb2=tk.Text(rc,height=13,bg="#060e1a",fg=C["text_dim"],font=("Courier New",9),
                    relief="flat",bd=0,highlightthickness=1,highlightbackground=C["border"],
                    wrap="none",state="normal",cursor="arrow")
        sb2.pack(fill="x",pady=(0,10))
        sb2.insert("1.0",
            "[inizio][V1_calmo]\n"
            "Narratore parla qui.[p3][stacco]\n"
            "[/V1_calmo][fine]\n\n"
            "[inizio][V2_arrabbiato]\n"
            "Personaggio B risponde![bd][cambio3]\n"
            "[/V2_arrabbiato][fine]\n\n"
            "[inizio][V3_sussurrato]\n"
            "Voce interiore o personaggio C.[p3][para]\n"
            "[/V3_sussurrato][fine]\n\n"
            "REGOLE V3:\n"
            "  [cambio]  = V1 <-> V2\n"
            "  [cambio3] = V3 entra o esce\n"
            "  V3 opzionale: se vuota -> fallback V1"
        )
        sb2.config(state="disabled")

        sl(rc,"Guida scelta pausa")
        gb=tk.Text(rc,height=9,bg="#060e1a",fg=C["text_dim"],font=("Courier New",9),
                   relief="flat",bd=0,highlightthickness=1,highlightbackground=C["border"],
                   wrap="none",state="normal",cursor="arrow")
        gb.pack(fill="x",pady=(0,10))
        gb.insert("1.0",
            "Virgola, inciso         [p1]  ~0.18s  [0.11-0.25]\n"
            "Punto normale           [p2]  ~0.40s  [0.24-0.56]\n"
            "Riflessione, ; domanda  [p3]  ~0.65s  [0.39-0.91]\n"
            "Cambio idea, :          [b]   ~1.00s  [0.60-1.40]\n"
            "Rivelazione, climax     [bd]  ~1.60s  [0.96-2.24]\n"
            "Reset, capoverso        [cap] ~2.00s  [1.20-2.80]\n"
            "\n"
            "Narrazione base:        [p2]  ~0.40s\n"
            "Filosofia/riflessione:  [p3]  ~0.65s\n"
            "Passaggi profondi:      [b]+  ~1.00s+")
        gb.config(state="disabled")
        tk.Label(inner,text="Usa 'Copia Prompt AI' per le istruzioni complete v2.4 (V3, cambio3, anti-accumulo, emozione->ritmo).",
                 font=FS,fg=C["success"],bg=C["surface"],pady=10,justify="left",anchor="w"
                 ).pack(fill="x",pady=(12,0))

    def _copy_prompt(self):
        self.clipboard_clear(); self.clipboard_append(GUIDE_PROMPT)
        messagebox.showinfo("Copiato!","Prompt v2.4 copiato!\nIncollalo in Claude/GPT e aggiungi il testo.")

    def _save_prompt(self):
        dest=pathlib.Path(self.vdir.get() or str(pathlib.Path.cwd()))
        p=dest/"PROMPT_GUIDA_CHATTERTEXT_v2.4.txt"
        p.write_text(GUIDE_PROMPT,encoding="utf-8")
        messagebox.showinfo("Salvato!","Salvato in:\n{}".format(p))

    def _footer(self,r):
        ft=tk.Frame(r,bg=C["bg"],pady=20); ft.pack(fill="x")
        tk.Label(ft,text="2026 (c) ChatterText v2.4 by Gerardo D'Orrico  —  3 Voci | Gauss clamp±40% | 8L Join | dynpause emo",
                 font=FS,fg=C["text_dim"],bg=C["bg"]).pack()

    # ---- DEVICE ----
    def _detect_device(self):
        def _d():
            dev,info=detect_device()
            col=C["gpu"] if dev=="cuda" else C["cpu"]
            self.after(0,lambda:self._set_badge(("GPU " if dev=="cuda" else "CPU ")+info,col))
        threading.Thread(target=_d,daemon=True).start()

    def _set_badge(self,txt,col):
        self.badge_var.set(txt); self.badge.config(bg=col)

    # ---- PROCESS ----
    def process(self):
        raw=self.txt.get("1.0","end-1c").strip()
        if not raw or "Incolla qui" in raw:
            messagebox.showwarning("Attenzione","Inserisci testo!"); return
        has_t=bool(re.search(r"\[inizio\]",raw,re.IGNORECASE))
        norm=(re.sub(r"\[inizio\]([\s\S]*?)\[fine\]",
                     lambda m:"[inizio]"+normalize_text(m.group(1))+"[fine]",
                     raw,flags=re.IGNORECASE)
              if has_t else normalize_text(raw))
        errs=analyze_text(norm)
        ws=[w for w in norm.split() if w]
        self.vwords.set(str(len(ws))); self.vchars.set(str(len(norm))); self.verrs.set(str(len(errs)))
        self.stats.pack(fill="x")
        tc=len(re.findall(r"\[inizio\]",norm,re.IGNORECASE))
        ec=len(re.findall(r"\[(?:(?:v1|v2|v3)_)?(?:"+" |".join(ALL_EMO)+r")\]",norm,re.IGNORECASE))
        pc=len(re.findall(r"\[(?:p[123]|b(?:d)?|cap|pausa(?:_lunga)?|silenzio)\]",norm,re.IGNORECASE))
        enc=len(re.findall(r"\[e[12]\]",norm,re.IGNORECASE))
        jc=len(re.findall(r"\[(?:join|cont|cambio|cambio3|para|stacco|lungo|scena)\]",norm,re.IGNORECASE))
        v3c=len(re.findall(r"\[(?:v3|V3_\w+)\]",norm,re.IGNORECASE))  # conteggio V3
        pts=[]
        if tc: pts.append("{} blocchi".format(tc))
        if ec: pts.append("{} emozioni".format(ec))
        if pc: pts.append("{} pause".format(pc))
        if enc: pts.append("{} enfasi".format(enc))
        if jc: pts.append("{} giunzioni".format(jc))
        if v3c: pts.append("{} blocchi V3".format(v3c))  # badge V3 nelle statistiche
        self.tag_lbl.config(text="  ".join(pts) if pts else "Modalita automatica",
                            fg=C["success"] if pts else C["warning"])
        self.err_box.config(state="normal"); self.err_box.delete("1.0","end")
        if errs:
            for et,msg in errs: self.err_box.insert("end",("{} {}\n".format(
                "ATTENZIONE:" if et=="warning" else "INFO:",msg)))
        else:
            self.err_box.insert("end","Nessun problema!"); self.err_box.config(fg=C["success"])
        self.err_box.config(state="disabled")
        try: minw,maxw,maxc=int(self.vminw.get()),int(self.vmaxw.get()),int(self.vmaxc.get())
        except: minw,maxw,maxc=20,40,240
        chunks=chunk_text(norm,minw,maxw,maxc)
        self.chunks=chunks; self.vchunks.set(str(len(chunks)))
        short=[i+1 for i,c in enumerate(chunks)
               if len(_protected().sub("",c).strip().split())<CHUNK_MIN_W]
        if short:
            messagebox.showwarning("Chunk corti!",
                "Chunk con meno di {} parole (rischio ripetizioni):\n{}\n\n"
                "Uniscili o usa il Prompt Guida.".format(CHUNK_MIN_W,", ".join(str(n) for n in short[:10])))
        self._render(); self.chunksec.pack(fill="x")

    def _render(self):
        for w in self.cbox.winfo_children(): w.destroy()
        self.chunk_vars=[]
        for i,chunk in enumerate(self.chunks):
            cl=_protected().sub("",chunk).strip()
            words=len(cl.split()); chars=len(cl)
            status,stxt=chunk_status(words,chars)
            sc={"success":C["success"],"warning":C["warning"],"danger":C["danger"]}[status]
            voice,emo=detect_voice_emo(chunk)
            emphs=detect_emph(chunk); pauses=detect_pauses(chunk); jt=detect_join(chunk)

            # Badge voce con supporto V3 (turchese)
            if voice=="v3":   vl,vc="V3",C["v3"]
            elif voice=="v2": vl,vc="V2",C["v2"]
            elif voice=="v1": vl,vc="V1",C["v1"]
            else:             vl,vc="Auto",C["text_dim"]

            card=tk.Frame(self.cbox,bg=C["chunk_bg"],bd=0,highlightthickness=1,
                          highlightbackground=C["border"])
            card.pack(fill="x",pady=(0,10))
            hdr=tk.Frame(card,bg=C["hdr_bg"],pady=8,padx=12); hdr.pack(fill="x")
            tk.Label(hdr,text="Chunk {}".format(i+1),font=FL,fg=C["accent"],bg=C["hdr_bg"]).pack(side="left")
            tk.Label(hdr,text=" {} ".format(vl),font=FS,fg="#fff",bg=vc,padx=6,pady=2).pack(side="left",padx=4)
            if emo:
                ec=EMO_C.get(emo,C["text_dim"])
                tk.Label(hdr,text=" {} ".format(emo),font=FS,fg="#fff",bg=ec,padx=6,pady=2).pack(side="left",padx=2)
            for et in emphs:
                ec2="#e84357" if et=="e2" else "#e67e22"
                tk.Label(hdr,text=" {} ".format(et),font=FS,fg="#fff",bg=ec2,padx=5,pady=2).pack(side="left",padx=2)
            shown=[]
            for ptag,_ in pauses:
                if ptag not in shown: shown.append(ptag)
                if len(shown)>=3: break
            for ptag in shown:
                pn=ptag.strip("[]")
                pc2=PAUSE_BADGE_C.get(pn,"#7f8c8d")
                tk.Label(hdr,text=" {} ".format(ptag),font=FS,fg="#fff",bg=pc2,padx=5,pady=2).pack(side="left",padx=1)
            if jt:
                jn=jt.strip("[]")
                jcol=JOIN_BADGE_C.get(jn,C["text_dim"])
                jfg="#000" if jn=="para" else "#fff"
                tk.Label(hdr,text=" {} ".format(jt),font=FS,fg=jfg,bg=jcol,padx=5,pady=2).pack(side="left",padx=1)
            inf=tk.Frame(hdr,bg=C["hdr_bg"]); inf.pack(side="right")
            tk.Label(inf,text="{} par. {} car.".format(words,chars),font=FS,
                     fg=C["text_dim"],bg=C["hdr_bg"]).pack(side="left",padx=8)
            tk.Label(inf,text=stxt,font=FS,fg=sc,bg=C["hdr_bg"]).pack(side="left")
            self.chunk_vars.append(tk.StringVar(value=chunk))
            tf=tk.Frame(card,bg=C["chunk_bg"],padx=8,pady=6); tf.pack(fill="x")
            ta=tk.Text(tf,height=4,bg=C["surface2"],fg=C["text"],font=FM,relief="flat",bd=0,
                       wrap="word",insertbackground=C["accent"],
                       highlightthickness=1,highlightbackground=C["border"])
            ta.insert("1.0",chunk); ta.pack(fill="x")
            ta.bind("<KeyRelease>",lambda e,t=ta,ix=i:self._edit(t,ix))
            af=tk.Frame(card,bg=C["chunk_bg"],padx=8,pady=6); af.pack(fill="x")
            sb_btn(af,"Copia",lambda ix=i:self._copy_c(ix)).pack(side="left",padx=(0,6))
            sb_btn(af,"Dividi",lambda ix=i:self._split(ix),color=C["warning"]).pack(side="left",padx=(0,6))
            if i<len(self.chunks)-1:
                sb_btn(af,"Unisci",lambda ix=i:self._merge(ix),color="#17a2b8").pack(side="left")

    def _edit(self,ta,idx): self.chunks[idx]=ta.get("1.0","end-1c")
    def _copy_c(self,idx): self.clipboard_clear(); self.clipboard_append(self.chunks[idx]); messagebox.showinfo("Copiato","Chunk {} copiato!".format(idx+1))
    def copy_all(self): self.clipboard_clear(); self.clipboard_append("\n\n---\n\n".join(self.chunks)); messagebox.showinfo("Copiato","Tutti i chunk copiati!")
    def _split(self,idx):
        t=self.chunks[idx]; mid=len(t)//2
        win=t[max(0,mid-100):min(len(t),mid+100)]
        m=re.search(r"[.!?;:]\s",win)
        sp=max(0,mid-100)+m.start()+2 if m else mid
        self.chunks[idx:idx+1]=[t[:sp].strip(),t[sp:].strip()]
        self._render(); self.vchunks.set(str(len(self.chunks)))
    def _merge(self,idx):
        if idx>=len(self.chunks)-1: return
        self.chunks[idx:idx+2]=[self.chunks[idx]+" "+self.chunks[idx+1]]
        self._render(); self.vchunks.set(str(len(self.chunks)))

    # ---- SCRIPT ----
    def _mk_script(self):
        if not self.chunks: messagebox.showwarning("Attenzione","Processa prima!"); return None
        try: ex,cg,tp=float(self.vexag.get()),float(self.vcfg.get()),float(self.vtemp.get())
        except: ex,cg,tp=0.62,0.70,0.58
        return build_python_script(
            self.chunks, ex, cg, tp,
            self.vv1.get().strip() or "3l14n.wav",
            self.vv2.get().strip(),
            self.vv3.get().strip(),   # <-- passa V3
            self.epreset,
            self.vdev.get()
        )

    def save_script(self):
        s=self._mk_script()
        if not s: return
        p=pathlib.Path(self.vdir.get() or str(pathlib.Path.cwd()))/"chatterbox_auto.py"
        p.write_text(s,encoding="utf-8"); self.script_path=str(p)
        messagebox.showinfo("Salvato","Script:\n{}".format(p))

    def run_chatterbox(self):
        if self._proc and self._proc.poll() is None:
            messagebox.showwarning("In corso","Generazione gia in corso! Premi Stop."); return
        s=self._mk_script()
        if not s: return
        dest=pathlib.Path(self.vdir.get() or str(pathlib.Path.cwd()))
        sf2=dest/"chatterbox_auto.py"; sf2.write_text(s,encoding="utf-8")
        tot=len(self.chunks)
        self.logsec.pack(fill="x"); self.progv.set(0)
        self.vprog.set("0 / {} chunk".format(tot)); self.veta.set("Avvio...")
        dm=self.vdev.get()
        self.vdevl.set("GPU CUDA" if dm=="cuda" else ("CPU" if dm=="cpu" else "Auto-detect..."))
        self.log.config(state="normal"); self.log.delete("1.0","end")
        self.log.insert("end","Avvio: {}\n Cartella: {}\n".format(sf2,dest))
        self.log.config(state="disabled"); self.stopbtn.config(state="normal")
        self._t0=time.time()
        def _run():
            try:
                env=os.environ.copy(); env["PYTHONIOENCODING"]="utf-8"
                proc=subprocess.Popen([sys.executable,str(sf2)],cwd=str(dest),
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                    text=True,encoding="utf-8",errors="replace",env=env)
                self._proc=proc
                for line in proc.stdout:
                    self._alog(line)
                    m=re.search(r"Chunk\s+(\d+)/(\d+)",line)
                    if m:
                        n,t2=int(m.group(1)),int(m.group(2)); pct=int(n/t2*100)
                        el=time.time()-self._t0; av=el/n if n>0 else 0; rm=av*(t2-n)
                        self.after(0,lambda p=pct,nn=n,t=t2,r=rm:self._uprog(p,nn,t,r))
                    if "GPU" in line and "CUDA" in line.upper():
                        self.after(0,lambda:self.vdevl.set("GPU CUDA attivo"))
                    elif "CPU" in line and "dispositivo" in line.lower():
                        self.after(0,lambda:self.vdevl.set("CPU attivo"))
                proc.wait(); rc=proc.returncode
                self._alog("\n"+"-"*55+"\n")
                if rc==0:
                    el=time.time()-self._t0
                    self._alog("Completato in {:.1f}s!\n".format(el))
                    self.after(0,lambda:self.progv.set(100))
                    self.after(0,lambda:self.vprog.set("{}/{} COMPLETATO".format(tot,tot)))
                    self.after(0,lambda:self.veta.set("Totale: {:.1f}s".format(el)))
                    if self.vsound.get(): threading.Thread(target=play_sound,daemon=True).start()
                    self.after(0,lambda:messagebox.showinfo("Completato!",
                        "Audio creato!\nChunk: {}/{}\nTempo: {:.1f}s".format(tot,tot,el)))
                else: self._alog("Errore (code {})\n".format(rc))
            except Exception as ex: self._alog("\nErrore: {}\n".format(ex))
            finally: self.after(0,lambda:self.stopbtn.config(state="disabled"))
        threading.Thread(target=_run,daemon=True).start()

    def _uprog(self,pct,n,tot,rem):
        self.progv.set(pct); self.vprog.set("{}/{} chunk".format(n,tot))
        if rem>0: self.veta.set("ETA: {:.0f}s".format(rem))

    def _stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate(); self._alog("\nStop.\n")
            self.stopbtn.config(state="disabled"); self.vprog.set("Interrotto")

    def _alog(self,text):
        def _d():
            self.log.config(state="normal"); self.log.insert("end",text)
            self.log.see("end"); self.log.config(state="disabled")
        self.after(0,_d)

    def clear_all(self):
        self.txt.delete("1.0","end")
        self.txt.insert("1.0","Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.chunks=[]; self.chunk_vars=[]
        for v in (self.vwords,self.vchars,self.vchunks,self.verrs): v.set("0")
        self.vcc.set("0 / 10000")
        self.stats.pack_forget(); self.chunksec.pack_forget(); self.logsec.pack_forget()
        for w in self.cbox.winfo_children(): w.destroy()

    def _browse(self):
        d=filedialog.askdirectory(title="Seleziona cartella Chatterbox")
        if d: self.vdir.set(d)

    def _presets(self):
        PresetWindow(self,self.epreset,on_save=lambda p:self.epreset.update(p))


if __name__=="__main__":
    App().mainloop()