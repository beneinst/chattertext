# Script generato da ChatterText v3.0 + Chatterbox Multilingual V3
# Stile: narrativa  |  Pause Naturali: True  |  Noise gate: -50.0dB
# RMS target: -18.0dB  |  Pause scale: 1.00x  |  Pulizia aggressiva: False
import os,re,sys,random,inspect,torch,torchaudio as ta,pathlib,time
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
print('Caricamento Chatterbox Multilingual V3...')
print("Al primo avvio il modello viene scaricato: l'operazione puo richiedere alcuni minuti.")
if 't3_model' not in inspect.signature(ChatterboxMultilingualTTS.from_pretrained).parameters:
    print('ERRORE V3: la libreria Chatterbox installata e troppo vecchia e non supporta Multilingual V3.')
    exit(2)
try:
    model=ChatterboxMultilingualTTS.from_pretrained(device=DEVICE.type,t3_model='v3')
except Exception as e:
    print('ERRORE V3: impossibile caricare Multilingual V3: {}'.format(e))
    exit(2)
print('Modello su {}!'.format(DEVICE.type.upper()))
chunks=[
  "[V1_solenne]\nCapitolo sesto.\nFrancesco rinuncia ai suoi beni.\n.\n.\n.\n.\n.\n[/V1_solenne]",
  "[V1_calmo]\nQuando il padre è lontano,\nla madre libera Francesco dalla prigionia in casa.\nLui torna subito a San Damiano,\npiù deciso e sereno.\n.\n.\n[/V1_calmo]",
  "[V1_serio]\nAl ritorno, il padre cerca ancora di farlo desistere\ne pretende di riavere il denaro\nche Francesco aveva offerto al sacerdote.\n.\n.\n[/V1_serio]",
  "[V1_riflessivo]\nFrancesco non si oppone\nquando il padre lo conduce davanti al vescovo\nper rinunciare ai suoi beni.\n.\n.\n[/V1_riflessivo]",
  "[V1_deciso][e1]\nDavanti a tutti, si spoglia\ne restituisce al padre\nperfino gli abiti che indossa.\n.\n.\n.\n[/V1_deciso]",
  "[V1_gentile]\nIl vescovo, colpito dalla sua fermezza,\nlo abbraccia\ne lo copre con il proprio mantello.\n.\n.\n[/V1_gentile]",
  "[V1_riflessivo]\nPer Tommaso da Celano,\nquel gesto segna una rottura completa con la vita precedente.\nFrancesco sceglie la povertà\ne si affida a Dio.\n.\n.\n[/V1_riflessivo]",
  "[V1_gentile][lento]\nDa quel momento il vescovo gli sarà vicino\ne lo sosterrà nel suo nuovo cammino.\n.\n.\n.\n.\n[/V1_gentile]"
]
AUDIO_V1="2.Voci/2raff-nora.wav"
AUDIO_V2="2.Voci/2raff-nora.wav"
AUDIO_V3="2.Voci/2raff-nora.wav"
AUDIO_V4="2.Voci/2raff-nora.wav"
AUDIO_V5="2.Voci/2raff-nora.wav"
AUDIO_V6="2.Voci/2raff-nora.wav"
AUDIO_V7="2.Voci/2raff-nora.wav"
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
    },
    "solenne": {
        "exaggeration": 0.55,
        "cfg_weight": 0.8,
        "temperature": 0.38,
        "top_p": 0.68,
        "min_p": 0.2
    },
    "estatico": {
        "exaggeration": 0.85,
        "cfg_weight": 0.52,
        "temperature": 0.72,
        "top_p": 0.88,
        "min_p": 0.07
    },
    "malinconico": {
        "exaggeration": 0.48,
        "cfg_weight": 0.82,
        "temperature": 0.43,
        "top_p": 0.7,
        "min_p": 0.18
    },
    "vibrante": {
        "exaggeration": 0.88,
        "cfg_weight": 0.48,
        "temperature": 0.78,
        "top_p": 0.9,
        "min_p": 0.06
    },
    "intimo": {
        "exaggeration": 0.3,
        "cfg_weight": 0.88,
        "temperature": 0.36,
        "top_p": 0.65,
        "min_p": 0.22
    }
}
DEF_P={'exaggeration':0.5,'cfg_weight':0.58,'temperature':0.6,'top_p':0.75,'min_p':0.15}
SAMPLER_TOP_P=0.75
SAMPLER_MIN_P=0.15
REPETITION_PENALTY=1.2
SEED=0
SETTINGS_ID='4461ac7a7a79c108bc8abc24'
REGEN=set(int(x) for x in re.findall(r'\d+',os.environ.get('CHATTERTEXT_REGEN','')))
def _rcfg():
    try: return max(0.0,min(1.0,float(os.environ.get('CHATTERTEXT_REGEN_CFG','').replace(',','.'))))
    except ValueError: return None
REGEN_CFG=_rcfg()
SEEN={}
if REGEN: print('RIGENERAZIONE FORZATA blocchi {}{}'.format(sorted(REGEN),'  (cfg_weight '+str(REGEN_CFG)+')' if REGEN_CFG is not None else ''),flush=True)
PAUSE_SCALE=1.0
PRESET_SCALE=1.0
NOISE_GATE_DB=-50.0
RMS_TARGET_DB=-18.0
TRIM_DB=-45.0
AGGRESSIVE_CLEAN=False
NATURAL_PAUSES=True
INNER_PAUSES=True
INNER_SCALE=1.0
TEMPO=1.0
CUR_RATE=[TEMPO]

RR=re.compile(r'\[r([1-4])\]',re.IGNORECASE)
RMERGED=[]
def split_reads(t):
    # [(testo, letture)] : il tag vale fino al tag successivo; prima del primo tag = 1.
    # Guardia: se la parte prima del tag non finisce con punteggiatura, il confine taglia una
    # frase in mezzo (soggetto|verbo, verbo|oggetto...): le due parti restano sulla stessa riga
    # nella modalita' della prima e il tag viene ignorato.
    out=[]; mode=1; pos=0
    def push(seg,md):
        if out and out[-1][0].rstrip('"\'»”)]')[-1:] not in ',.;:!?…—–':
            RMERGED.append(out[-1][0][-30:]); out[-1]=(out[-1][0]+' '+seg,out[-1][1])
        else:
            out.append((seg,md))
    for m in RR.finditer(t):
        seg=t[pos:m.start()].strip()
        if seg: push(seg,mode)
        mode=int(m.group(1)); pos=m.end()
    seg=t[pos:].strip()
    if seg: push(seg,mode)
    return out
R2_CFG_MAX=0.60; R2_EXAG_MAX=0.65; R2_TEMP_MIN=0.60; R2_TOPP_MIN=0.85; R2_MINP_MAX=0.10
R2_MAX_WORDS=16
def safe_params(p):
    # Parametri stabili per i blocchi con [r2]-[r4]: restano vicini ai default ufficiali di
    # Chatterbox (cfg 0.5, exaggeration 0.5, temperature 0.8, top_p 1.0, min_p 0.05) per ridurre
    # accento straniero e voce robotica. Si applicano a TUTTE le parti del blocco, cosi' r1 e r2
    # restano coerenti tra loro.
    q=dict(p); ch=[]
    for k,f,v in (('cfg_weight',min,R2_CFG_MAX),('exaggeration',min,R2_EXAG_MAX),
                  ('temperature',max,R2_TEMP_MIN),('top_p',max,R2_TOPP_MIN),('min_p',min,R2_MINP_MAX)):
        n=f(q[k],v)
        if abs(n-q[k])>1e-9: ch.append('{} {:.2f}->{:.2f}'.format(k,q[k],n)); q[k]=n
    return q, ', '.join(ch)
def carry_reads(piece, mode):
    # Quando una pausa spezza il blocco, il pezzo successivo eredita la modalita' corrente.
    ms=RR.findall(piece); new=int(ms[-1]) if ms else mode
    if not RR.sub('',piece).strip(): return '', new
    if mode>1 and not RR.match(piece.lstrip()): piece='[r%d] '%mode+piece
    return piece, new

CUR_READS=[1]
COMPARE_R=False
COMPARE_GAP=2.0
SAFE_R=True
MERGE_LINES=True
TEMPO_TAGS={'[lento]':0.93,'[lentissimo]':0.86,'[veloce]':1.06}

import re as _re

# Modulo condiviso tra app e script generato (solo Python puro, nessuna dipendenza).
# Regola d'oro: NON cambia mai le parole, aggiunge solo virgole e sceglie dove tagliare.

# Parole DAVANTI alle quali un respiro e' naturale.
STRONG_BOUNDARY = {
    "ma", "però", "pero", "perché", "perche", "mentre", "quando", "finché", "finche",
    "sebbene", "benché", "benche", "poiché", "poiche", "affinché", "affinche",
    "oppure", "eppure", "tuttavia", "dunque", "anzi", "bensì", "bensi", "cioè", "cioe",
    "ovvero", "altrimenti", "nonostante", "siccome", "giacché", "giacche", "quindi",
}
SOFT_BOUNDARY = {"e", "ed", "che", "o", "né", "dove", "cui", "come"}

# Parole con cui un frammento NON deve mai terminare (articoli, preposizioni, ausiliari...).
NO_END = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in", "con",
    "su", "per", "tra", "fra", "del", "dello", "della", "dei", "degli", "delle", "al",
    "allo", "alla", "ai", "agli", "alle", "dal", "dallo", "dalla", "dai", "dagli",
    "dalle", "nel", "nello", "nella", "nei", "negli", "nelle", "sul", "sullo", "sulla",
    "sui", "sugli", "sulle", "non", "si", "mi", "ti", "ci", "vi", "è", "era", "e", "ed",
    "o", "ma", "che", "se", "come", "più", "molto", "tanto", "mio", "tuo", "suo",
    "nostro", "vostro", "loro", "mia", "tua", "sua", "nostra", "vostra", "miei", "tuoi",
    "suoi", "ha", "hanno", "aveva", "avevano", "sono", "fu", "furono", "sarà", "sarebbe",
}

_END_PUNCT = ",;:.!?"
_TAG_RE = _re.compile(r"(\[[^\]\n]*\])")
_STRIP = ",.;:!?\"'«»“”()…"


def _wkey(word):
    return word.lower().strip(_STRIP)


def _ends_punct(word):
    return word.rstrip("\"'»”)")[-1:] in _END_PUNCT and word.rstrip("\"'»”)") != ""


def smart_cut(words, max_words=22, max_chars=180):
    """Quante parole tenere nel primo frammento (>=1), tagliando dove il respiro e' naturale."""
    n_total = len(words)
    limit, chars = 0, 0
    for i, w in enumerate(words):
        chars += len(w) + (1 if i else 0)
        if i + 1 > max_words or chars > max_chars:
            break
        limit = i + 1
    limit = max(1, limit)
    if n_total <= limit:
        return n_total
    lo = max(3, limit // 2)
    best = None
    for n in range(limit, lo - 1, -1):          # dal piu' lungo al piu' corto
        prev = _wkey(words[n - 1])
        nxt = _wkey(words[n]) if n < n_total else ""
        if _ends_punct(words[n - 1]):
            score = 4
        elif nxt in STRONG_BOUNDARY:
            score = 3
        elif nxt in SOFT_BOUNDARY:
            score = 2
        elif prev not in NO_END:
            score = 1
        else:
            score = 0
        if n_total - n < 3:
            score -= 2                             # evita code di 1-2 parole
        if best is None or score > best[0]:
            best = (score, n)
    return best[1] if best else limit


def auto_rhythm(text, strong_run=7, soft_run=12, min_tail=3):
    """Aggiunge virgole di respiro nei tratti lunghi senza punteggiatura.
    Restituisce (testo, numero_virgole_aggiunte). Non tocca tag, accapo o parole."""
    added = 0
    out_lines = []
    for line in text.split("\n"):
        res = []
        run = 0
        for part in _TAG_RE.split(line):
            if _TAG_RE.fullmatch(part):
                res.append(part)
                run = 0
                continue
            tokens = _re.split(r"(\s+)", part)
            idx = [i for i, t in enumerate(tokens) if t and not t.isspace()]
            for k, i in enumerate(idx):
                w = tokens[i]
                key = _wkey(w)
                if k > 0 and run > 0:
                    pi = idx[k - 1]
                    pw = tokens[pi]
                    if key in STRONG_BOUNDARY:
                        need = strong_run
                    elif key in SOFT_BOUNDARY:
                        need = soft_run
                    else:
                        need = None
                    if (need and run >= need and len(idx) - k >= min_tail + 1
                            and not _ends_punct(pw) and _wkey(pw) not in NO_END):
                        tokens[pi] = pw + ","
                        added += 1
                        run = 0
                run += 1
                if _ends_punct(w):
                    run = 0
            res.append("".join(tokens))
        out_lines.append("".join(res))
    return "\n".join(out_lines), added


def split_units(text, max_words=22, max_chars=180, merge=False):
    """Divide il testo in unita da sintetizzare. Le righe di soli segni (es. '.') restano
    unita a parte: sono pause esplicite. Le frasi lunghe si tagliano ai confini naturali
    e il frammento tagliato riceve una virgola (intonazione 'continua').
    merge=True: le righe consecutive (a capo semplici) della stessa frase si uniscono in UNA
    sola generazione: ogni generazione riparte con intonazione da 'inizio discorso', quindi
    meno generazioni = voce piu' continua. Le righe vuote e quelle di soli punti spezzano."""
    units = []
    acc = []

    def flush():
        if not acc:
            return
        para = " ".join(acc)
        del acc[:]
        for sentence in _re.split(r"(?<=[.!?;])\s+", para):
            words = sentence.split()
            while words:
                n = smart_cut(words, max_words, max_chars - 1)
                piece = " ".join(words[:n])
                words = words[n:]
                if words and piece[-1] not in _END_PUNCT + "]":
                    piece += ","
                units.append(piece)

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            if merge:
                flush()
            continue
        if not any(c.isalnum() for c in line):
            flush()
            units.append(line)
            continue
        acc.append(line)
        if not merge:
            flush()
    flush()
    return units


def pauses_to_natural_text(text):
    """
    v3.0 - Converte tag pausa in punteggiatura naturale + newline reali.
    Chatterbox usa i newline come guide respiratorie: ogni riga = unità di respiro.
    """
    PTABLE = {
        "[metro]":("",0),"[enjambement]":("",0),
        "[p1]":(",",1),"[verso]":(",",1),"[cesura]":(",",1),
        "[p2]":(".",1),"[pausa]":(".",1),
        "[p3]":(".",2),"[b]":(".",2),"[strofa]":(".",2),"[pausa_lunga]":(".",2),
        "[bd]":(".",3),"[cap]":(".",3),"[silenzio]":(".",3),
    }
    ORDER=["[silenzio]","[cap]","[bd]","[pausa_lunga]","[strofa]","[b]",
           "[p3]","[pausa]","[p2]","[cesura]","[verso]","[p1]","[enjambement]","[metro]"]
    for tag in ORDER:
        if tag not in PTABLE: continue
        punct,nlcount=PTABLE[tag]
        ph="__PNLT__{}__NL{}__".format(punct.replace(".","DOT").replace(",","COMMA"),nlcount)
        text=re.sub(re.escape(tag),ph,text,flags=re.IGNORECASE)
    def resolve(m):
        rp=m.group(1).replace("DOT",".").replace("COMMA",",")
        nl="\n"*int(m.group(2))
        pos=m.start(); before=text[:pos].rstrip()
        if rp and before and before[-1] in ".,!?:;": return nl if nl else " "
        return (rp+nl) if rp else (nl if nl else " ")
    text=re.sub(r"__PNLT__([\w]*)__NL(\d)__",resolve,text)
    text=re.sub(r"\n{4,}","\n\n\n",text)
    text=re.sub(r"[ \t]+\n","\n",text)
    text=re.sub(r"\n[ \t]+","\n",text)
    text=re.sub(r"([.,!?])\s*([.,])",r"\1",text)
    text=re.sub(r"[ \t]{2,}"," ",text)
    text=re.sub(r" +([,.])\n",r"\1\n",text)
    text=re.sub(r" +([,.])\s*$",r"\1",text)
    return text.strip()

PM={
    '[p1]':(0.18,0.03), '[p2]':(0.40,0.05), '[p3]':(0.65,0.07),
    '[b]': (1.00,0.10), '[bd]':(1.60,0.15), '[cap]':(2.00,0.20),
    '[pausa]':(0.50,0.05),'[pausa_lunga]':(1.20,0.10),'[silenzio]':(2.00,0.15),
    '[verso]':(0.30,0.04),'[strofa]':(1.20,0.12),'[metro]':(0.08,0.01),
    '[enjambement]':(0.05,0.01),'[cesura]':(0.45,0.05),
}
def gp(tag):
    b,s=PM.get(tag.lower(),(0.40,0.05))
    b=b*PAUSE_SCALE
    raw=random.gauss(b,s*PAUSE_SCALE)
    return max(b*0.60, min(raw, b*1.40))
JM={'[join]':(0.00,'overlap'),'[cont]':(0.12,'smooth'),
    '[cambio]':(0.50,'cambio'),'[cambio3]':(0.50,'cambio'),
    '[cambio4]':(0.50,'cambio'),'[cambio5]':(0.50,'cambio'),
    '[cambio6]':(0.50,'cambio'),'[cambio7]':(0.50,'cambio'),
    '[para]':(0.90,'silence'),'[stacco]':(1.40,'fade_sil_fade'),
    '[lungo]':(1.80,'fade_sil_fade'),'[scena]':(2.40,'hard'),
    '[dissolvenza]':(1.60,'fade_sil_fade')}
EP={'e1':{'exaggeration_delta':0.10,'cfg_weight_delta':-0.05},'e2':{'exaggeration_delta':0.25,'cfg_weight_delta':-0.12},'ep':{'exaggeration_delta':0.15,'cfg_weight_delta':-0.08}}
EN=r"calmo|appassionato|arrabbiato|triste|ironico|sussurrato|riflessivo|deciso|preoccupato|gentile|serio|solenne|estatico|malinconico|vibrante|intimo"
PR=re.compile(r'(\[p[123]\]|\[b(?:d)?\]|\[cap\]|\[pausa(?:_lunga)?\]|\[silenzio\]|\[verso\]|\[strofa\]|\[metro\]|\[enjambement\]|\[cesura\])',re.IGNORECASE)
ER=re.compile(r'\[e[12p]\]',re.IGNORECASE)
TR=re.compile(r'\[(?:lento|lentissimo|veloce)\]',re.IGNORECASE)
JR=re.compile(r'\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\]',re.IGNORECASE)
def pc(chunk):
    rp=PR.findall(chunk)
    ps=[(p,gp(p)) for p in rp]; tp=sum(d for _,d in ps)
    et=ER.findall(chunk); ek=et[-1].lower().strip('[]') if et else None
    jt=JR.findall(chunk); jk=jt[-1].lower() if jt else None
    # si_meta: rimuove SOLO tag voce/emozione/enfasi/giunzioni
    # LASCIA i tag pausa [p1][p2][b]... intatti: servono a prepare_text_for_tts()
    def si_meta(t):
        t=ER.sub('',t); t=JR.sub('',t); t=TR.sub('',t); return t.strip()
    # si_voice: rimuove anche i tag voce dal testo pulito
    def si_voice(t):
        t=re.sub(r'\[/?(?:v1|v2|v3|v4|v5|v6|v7)(?:_'+EN+r')?\]','',t,flags=re.IGNORECASE)
        return si_meta(t)
    m=re.search(r'\[(v1|v2|v3|v4|v5|v6|v7)_(' +EN+r')\]',chunk,re.IGNORECASE)
    if m:
        v,e=m.group(1).lower(),m.group(2).lower()
        cl=re.sub(r'\[(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\]','',chunk,flags=re.IGNORECASE)
        cl=re.sub(r'\[/(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\]','',cl,flags=re.IGNORECASE)
        return si_meta(cl),v,e,ps,tp,ek,jk
    m=re.search(r'\[(v1|v2|v3|v4|v5|v6|v7)\]',chunk,re.IGNORECASE)
    if m:
        v=m.group(1).lower()
        cl=re.sub(r'\[/?(?:v1|v2|v3|v4|v5|v6|v7)\]','',chunk,flags=re.IGNORECASE)
        return si_meta(cl),v,None,ps,tp,ek,jk
    m=re.search(r'\[('+EN+r')\]',chunk,re.IGNORECASE)
    if m:
        e=m.group(1).lower()
        cl=re.sub(r'\[(?:'+EN+r')\]','',chunk,flags=re.IGNORECASE)
        cl=re.sub(r'\[/(?:'+EN+r')\]','',cl,flags=re.IGNORECASE)
        return si_meta(cl),'v1',e,ps,tp,ek,jk
    return si_meta(chunk),'v1',None,ps,tp,ek,jk
def pp(emo,ek=None):
    if emo and emo in EPRESET:
        p=EPRESET[emo].copy()
        # Lo stile amplifica/attenua lo scarto del preset rispetto ai parametri base.
        for key,lo,hi in [('exaggeration',0.0,2.0),('cfg_weight',0.0,1.0),
                          ('temperature',0.05,2.0),('top_p',0.0,1.0),('min_p',0.0,1.0)]:
            scale=min(PRESET_SCALE,1.0) if key in ('top_p','min_p') else PRESET_SCALE
            base=DEF_P[key]; p[key]=max(lo,min(hi,base+(p[key]-base)*scale))
    else:
        p=DEF_P.copy()
        p['top_p']=SAMPLER_TOP_P; p['min_p']=SAMPLER_MIN_P
    if ek and ek in EP:
        p['exaggeration']=min(1.0,p['exaggeration']+EP[ek]['exaggeration_delta'])
        p['cfg_weight']=max(0.1,p['cfg_weight']+EP[ek]['cfg_weight_delta'])
    return p
if SEED and not REGEN:
    random.seed(SEED); torch.manual_seed(SEED)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(SEED)
tc=[]
for chunk in chunks:
    txt,vo,em,ps,tp,ek,jk=pc(chunk)
    _tt=TR.findall(chunk); tmf=TEMPO_TAGS[_tt[-1].lower()] if _tt else 1.0
    # Ogni pausa resta nel punto del testo in cui e' stata richiesta.
    cursor=0; parts=[]; _rm=1
    for match,(_,duration) in zip(PR.finditer(txt),ps):
        piece=txt[cursor:match.start()].strip()
        if piece: piece,_rm=carry_reads(piece,_rm)
        if piece:
            parts.append([piece,vo,em,[],duration,ek,None,tmf])
        elif parts:
            parts[-1][4]+=duration
        elif tc:
            tc[-1][4]+=duration
        cursor=match.end()
    tail=txt[cursor:].strip()
    if tail: tail,_rm=carry_reads(tail,_rm)
    if tail: parts.append([tail,vo,em,[],0.0,ek,None,tmf])
    if parts:
        parts[-1][6]=jk
        tc.extend(parts)
def noise_gate(wav, sr, gate_db=NOISE_GATE_DB, hpz=80, attack_ms=8, release_ms=60):
    thr=10**(gate_db/20)
    if wav.dim()==1: wav=wav.unsqueeze(0)
    wav=ta.functional.highpass_biquad(wav, sr, cutoff_freq=hpz)
    env=torch.abs(wav[0])
    att=int(sr*attack_ms/1000); rel=int(sr*release_ms/1000)
    gate=torch.zeros_like(env)
    g=0.0
    for i in range(len(env)):
        if env[i]>thr: target=1.0
        else: target=0.0
        if target>g: g=g+(1.0-g)/max(1,att)
        else: g=g*(1.0-1.0/max(1,rel))
        gate[i]=g
    wav=wav*gate.unsqueeze(0)
    return wav
def rms_normalize(wav, target_db=RMS_TARGET_DB):
    # Guadagno lineare con margine di picco: non satura e non amplifica i silenzi.
    if wav.dim()==1: wav=wav.unsqueeze(0)
    peak=wav.abs().max().item()
    if peak<=1e-8: return wav
    active=wav[ wav.abs()>max(1e-5,peak*0.01) ]
    rms=torch.sqrt(torch.mean(active**2)+1e-12).item()
    gain=min(10**(target_db/20)/rms, 0.95/peak, 3.0)
    return wav*gain
def declick(wav, sr, window_ms=3):
    w=int(sr*window_ms/1000)
    if w%2==0: w+=1
    if w<3 or wav.shape[-1]<w*2: return wav
    n=wav.shape[-1]
    kern=torch.ones(1,1,w)/w
    smoothed=torch.nn.functional.conv1d(wav.float().unsqueeze(0), kern, padding=w//2).squeeze(0)[...,:n]
    diff=torch.abs(wav-smoothed)
    thr=diff.mean()*3.0
    mask=(diff>thr).float()
    k2=int(sr*1/1000)+1
    if k2%2==0: k2+=1
    k2t=torch.ones(1,1,k2)/k2
    mask=torch.nn.functional.conv1d(mask.unsqueeze(0),k2t,padding=k2t.shape[-1]//2).squeeze(0).clamp(0,1)[...,:n]
    return wav*(1-mask)+smoothed*mask
def trim_silence(wav, sr, threshold_db=TRIM_DB, pad_ms=30):
    thr=10**(threshold_db/20)
    mg=int(sr*pad_ms/1000)
    mo=wav[0] if wav.dim()>1 else wav; en=torch.abs(mo)
    indices=(en>thr).nonzero(as_tuple=True)[0]
    if len(indices)==0: return wav
    s=max(0, indices[0].item()-mg); e=min(len(en), indices[-1].item()+mg)
    return wav[...,s:e]
def apply_fade(wav, sr, fade_ms=14):
    f=min(int(sr*fade_ms/1000),wav.shape[-1]); wav=wav.clone()
    if f<=0: return wav
    wav[...,:f]*=torch.linspace(0,1,f)
    wav[...,-f:]*=torch.linspace(1,0,f)
    return wav
import math
def spectral_balance(wav, sr, presence_gain=2.5, presence_freq=3000, mud_cut_db=-2.5, mud_freq=300):
    wav=ta.functional.equalizer_biquad(wav, sr, center_freq=presence_freq, gain=presence_gain, Q=0.8)
    wav=ta.functional.equalizer_biquad(wav, sr, center_freq=mud_freq, gain=mud_cut_db, Q=0.8)
    return wav
def gentle_compressor(wav, sr, threshold_db=-20, ratio=2.5, attack_ms=8, release_ms=120, makeup_db=2.5, block_ms=10):
    if wav.dim()==1: wav=wav.unsqueeze(0)
    thr=10**(threshold_db/20)
    block=max(1,int(sr*block_ms/1000))
    absw=torch.abs(wav[0]); n=absw.shape[0]
    pad=(-n)%block
    if pad: absw=torch.nn.functional.pad(absw,(0,pad))
    blocks=absw.view(-1,block)
    brms=torch.sqrt(torch.mean(blocks**2,dim=1)+1e-9)
    att=math.exp(-block_ms/attack_ms); rel=math.exp(-block_ms/release_ms)
    env=torch.zeros_like(brms); level=0.0
    for i in range(brms.shape[0]):
        v=brms[i].item()
        level=att*level+(1-att)*v if v>level else rel*level+(1-rel)*v
        env[i]=level
    gain=torch.ones_like(env)
    over=env>thr
    gain[over]=(thr+(env[over]-thr)/ratio)/(env[over]+1e-8)
    gs=gain.repeat_interleave(block)[:n]
    if gs.shape[0]<n: gs=torch.nn.functional.pad(gs,(0,n-gs.shape[0]))
    makeup=10**(makeup_db/20)
    out=wav.clone(); out[0]=out[0]*gs*makeup
    return out.clamp(-0.98,0.98)
def full_process(wav, sr):
    # Protegge consonanti e riprese dopo una pausa: niente gate o compressore a scatti.
    wav=trim_silence(wav, sr, threshold_db=min(TRIM_DB,-55), pad_ms=80)
    if AGGRESSIVE_CLEAN: wav=declick(wav, sr)
    return apply_fade(wav, sr, fade_ms=5)

def repeat_text(t, n):
    # n copie dello stesso testo in UNA generazione: la 1a suona come inizio di discorso, la 2a
    # come continuazione, la 3a/4a piu' espressive. Si tiene solo l'ultima. Le copie scartate
    # chiudono con un punto (confine piu' netto); l'ULTIMA e' il testo originale identico.
    t = t.strip()
    lc = t.rstrip('"\'»”)')[-1:]
    head = t if lc in '.!?…' else (t.rstrip(' ,;:') + '.')
    return '\n'.join([head] * (n - 1) + [t])

def take_last_copy(wav, sr, n):
    # Taglia via le prime n-1 letture; restituisce (ultima_copia, None) oppure (None, motivo).
    env = wav.detach().cpu().abs().amax(dim=0)
    fr = max(1, int(sr * 0.010))
    pad = (-env.numel()) % fr
    lv = torch.nn.functional.pad(env, (0, pad)).reshape(-1, fr).amax(dim=1)
    peak = lv.max().item()
    if peak < 1e-6: return None, 'audio silenzioso'
    voiced = (lv > max(1e-5, peak * 0.02)).tolist()
    if True not in voiced: return None, 'nessun parlato'
    first = voiced.index(True); last = len(voiced) - 1 - voiced[::-1].index(True)
    cum = []; c = 0
    for v in voiced:
        c += 1 if v else 0
        cum.append(c)
    total_v = cum[last]
    min_gap = 14                     # 140 ms di silenzio minimo tra due letture
    gaps = []; i = first
    while i <= last:
        if not voiced[i]:
            j = i
            while j <= last and not voiced[j]: j += 1
            if j - i >= min_gap: gaps.append((i, j, cum[i] / total_v))
            i = j
        else:
            i += 1
    cuts = []; prev_end = -1
    for k in range(1, n):
        target = k / n
        cand = [(abs(f - target) - min(e - s, 80) * 0.0015, s, e) for s, e, f in gaps
                if s > prev_end and abs(f - target) <= 0.15]
        if not cand: return None, 'confine tra le letture non trovato ({}/{})'.format(k, n - 1)
        _, s_, e_ = min(cand)
        cuts.append((s_ + e_) // 2); prev_end = e_
    # Tra le due letture il modello a volte inserisce un respiro/rumore a bassa energia: se il
    # primo tratto dopo il confine e' breve e debole (< 8% del picco) lo si salta.
    st = cuts[-1]
    while True:
        i = st
        while i <= last and not voiced[i]: i += 1
        if i > last: return None, 'nessun parlato dopo il confine'
        j = i
        while j <= last and voiced[j]: j += 1
        if (j - i) <= 60 and j <= last and lv[i:j].max().item() < peak * 0.08:
            st = j
            continue
        break
    st = max(cuts[-1], i - 5)                  # parte 50 ms prima dell'attacco del parlato
    tail_v = total_v - cum[st]
    if not (0.5 / n <= tail_v / total_v <= 1.8 / n):
        return None, 'ultima lettura sproporzionata ({:.0f}% del parlato)'.format(100 * tail_v / total_v)
    out = wav[..., st * fr:].clone()
    nf = min(out.shape[-1], int(sr * 0.008))   # dissolvenza d'ingresso di 8 ms contro i click
    if nf > 1: out[..., :nf] *= torch.linspace(0.0, 1.0, nf)
    return out, None

def inner_gap(prev):
    # Pausa automatica DOPO una unita di parlato, in base alla punteggiatura finale.
    # Le righe con solo "." (pause esplicite) la sostituiscono: vedi generate_recoverable.
    t = prev.strip()
    lc = t.rstrip('"\'»”)')[-1:]
    base = {'.': 0.38, '?': 0.46, '!': 0.42, ';': 0.30, ':': 0.32, ',': 0.17}.get(lc, 0.12)
    if t.endswith('...'): base = 0.60
    n = len(t.split())
    if n < 5: base *= 0.80
    elif n > 20: base *= 1.12
    base *= PAUSE_SCALE * INNER_SCALE
    raw = random.gauss(base, base * 0.15)
    return max(base * 0.60, min(raw, base * 1.40))

_TEMPO_WARNED = [False]
def apply_tempo(wav, rate):
    # rate < 1 = piu' lento, > 1 = piu' veloce. Usa WSOLA (nel dominio del tempo): sul parlato
    # non produce l'effetto "eco metallico" del vocoder di fase. Se pytsmod manca, NON applica
    # nulla (meglio una voce pulita che una voce con riverbero robotico).
    if abs(rate - 1.0) < 0.01:
        return wav
    try:
        import numpy as np, pytsmod
        y = wav.detach().cpu().numpy().astype('float32')
        out = [np.asarray(pytsmod.wsola(ch, 1.0 / rate), dtype='float32') for ch in y]
        n = min(len(o) for o in out)
        return torch.from_numpy(np.stack([o[:n] for o in out]))
    except Exception as e:
        if not _TEMPO_WARNED[0]:
            print('   Tempo di lettura NON applicato (serve: pip install pytsmod): {}'.format(e), flush=True)
            _TEMPO_WARNED[0] = True
        return wav

def prepare_text_for_tts(txt):
    '''
    v3.0: se NATURAL_PAUSES attivo, converte i tag pausa in
    punteggiatura + newline reali PRIMA di passare a model.generate().
    I tag enfasi/giunzioni vengono rimossi (già usati in parametri).
    '''
    if NATURAL_PAUSES:
        txt = pauses_to_natural_text(txt)
    else:
        # Vecchio comportamento: rimuovi solo i tag pausa senza conversione
        txt = re.sub(r'\[(?:p[123]|b(?:d)?|cap|pausa(?:_lunga)?|silenzio|verso|strofa|metro|enjambement|cesura)\]','',txt,flags=re.IGNORECASE)
    # Rimuovi eventuali tag residui (enfasi, giunzioni) che non devono andare al TTS
    txt = re.sub(r'\[e[12p]\]','',txt,flags=re.IGNORECASE)
    txt = re.sub(r'\[(?:lento|lentissimo|veloce)\]','',txt,flags=re.IGNORECASE)
    txt = re.sub(r'\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\]','',txt,flags=re.IGNORECASE)
    return txt.strip()
def speech_units(text, max_words=22, max_chars=180):
    if MERGE_LINES: max_words=max(max_words,28); max_chars=max(max_chars,230)
    return split_units(text, max_words, max_chars, MERGE_LINES)

def generate_recoverable(tts_txt, vp, attempts, depth=0):
    # I separatori senza parole sono pause, mai input da far pronunciare.
    if not any(char.isalnum() for char in RR.sub('',tts_txt)):
        return torch.zeros((1, max(1, int(model.sr*0.40*PAUSE_SCALE))))
    if depth==0:
        units=[]
        for _st,_sr in split_reads(tts_txt):
            units+= [(_u,_sr) for _u in speech_units(_st)]
        if RMERGED:
            print('   [r] tag ignorato: la parte prima non finisce con punteggiatura ("...'+RMERGED[0]+'"), le due parti restano unite',flush=True); RMERGED.clear()
        if len(units)==1: tts_txt=units[0][0]; CUR_READS[0]=units[0][1]
        if len(units)>1 or (COMPARE_R and any(_u[1]>1 for _u in units)):
            print('   Generazione in {} frasi/parti brevi.'.format(len(units)),flush=True)
            audio=[]; prev=None
            for unit,_ur in units:
                has=any(c.isalnum() for c in unit)
                if has: CUR_READS[0]=_ur
                # pausa automatica solo tra due unita di parlato: una riga con '.' e' una pausa esplicita
                if audio and has and prev is not None and INNER_PAUSES:
                    gap=inner_gap(prev)
                    if gap>0: audio.append(torch.zeros((1,int(model.sr*gap))))
                if has and COMPARE_R and _ur>1:
                    print('   [CONFRONTO] stessa parte in lettura singola, {:.0f} s di silenzio, poi {}x'.format(COMPARE_GAP,_ur),flush=True)
                    CUR_READS[0]=1
                    audio.append(generate_recoverable(unit,vp,attempts,depth=1))
                    audio.append(torch.zeros((1,int(model.sr*COMPARE_GAP))))
                    CUR_READS[0]=_ur
                audio.append(generate_recoverable(unit,vp,attempts,depth=1))
                prev=unit if has else None
            return torch.cat(audio,dim=-1)
    words_n=max(1,len(tts_txt.split()))
    letters_n=sum(c.isalnum() for c in RR.sub('',tts_txt))
    min_dur=max(0.18, letters_n/27.0)  # velocita massima plausibile ~27 lettere/s: sotto, probabile testo saltato
    best=None
    last_err=None
    r_eff=CUR_READS[0]
    if r_eff>1 and words_n>R2_MAX_WORDS:
        print('   [r] parte di {} parole (> {}): lettura singola, la doppia lettura su testi lunghi e meno stabile'.format(words_n,R2_MAX_WORDS),flush=True); r_eff=1
    for attempt_i,ap in enumerate(attempts):
        try:
            n_r=r_eff if attempt_i<len(attempts)-1 else 1  # ultimo tentativo: lettura singola
            gen_txt=repeat_text(tts_txt,n_r) if n_r>1 else tts_txt
            wav=model.generate(gen_txt,language_id='it',audio_prompt_path=vp,
                exaggeration=ap['exaggeration'],cfg_weight=ap['cfg_weight'],
                temperature=ap['temperature'],min_p=ap['min_p'],top_p=ap['top_p'],repetition_penalty=REPETITION_PENALTY)
            wav=wav.detach().cpu()
            if wav.dim()==1: wav=wav.unsqueeze(0)
            if not wav.numel() or not torch.isfinite(wav).all() or wav.abs().max()<1e-6:
                raise ValueError('Audio vuoto, silenzioso o non valido')
            if n_r>1:
                wav,_why=take_last_copy(wav,model.sr,n_r)
                if wav is None: raise ValueError('doppia lettura: '+_why)
            wav=full_process(wav, model.sr)
            # I silenzi interni non devono mascherare una frase saltata.
            frame=max(1,int(model.sr*0.02))
            envelope=wav.abs().amax(dim=0)
            padded=torch.nn.functional.pad(envelope,(0,(-envelope.numel())%frame))
            levels=padded.reshape(-1,frame).amax(dim=1)
            threshold=max(1e-5,envelope.max().item()*0.015)
            got_dur=(levels>threshold).sum().item()*frame/model.sr
            if got_dur < min_dur:
                print('   SOSPETTO: {:.1f}s per {} parole (atteso >= {:.1f}s) - possibile testo saltato, riprovo'.format(got_dur, words_n, min_dur))
                if best is None or got_dur>best[0]: best=(got_dur,wav)
                last_err='audio troppo corto rispetto al testo (possibile salto)'
                continue
            return apply_tempo(wav,CUR_RATE[0])
        except Exception as e:
            last_err=e
            print('   ERR tentativo {}: {}'.format(attempt_i+1, e), flush=True)
    words=list(re.finditer(r'\S+', tts_txt))
    if depth < 3 and len(words) >= 8:
        middle=len(words)//2
        boundaries=[n for n in range(3,len(words)-2)
                    if tts_txt[:words[n].start()].rstrip().endswith(('.', '!', '?', ';', ':', ','))]
        cut_word=min(boundaries,key=lambda n:abs(n-middle)) if boundaries else middle
        cut=words[cut_word].start()
        print('   Recupero: divido il blocco in due parti (livello {}).'.format(depth+1), flush=True)
        try:
            left=generate_recoverable(tts_txt[:cut].strip(),vp,attempts,depth+1)
            right=generate_recoverable(tts_txt[cut:].strip(),vp,attempts,depth+1)
            return torch.cat([left,right],dim=-1)
        except Exception as _se:
            if best is not None and best[0]>=0.5*min_dur:
                print('   Divisione non riuscita ({}): accetto la versione piu lunga ({:.1f}s), controlla questo punto all ascolto.'.format(str(_se)[:50],best[0]),flush=True)
                return apply_tempo(best[1],CUR_RATE[0])
            raise
    if best is not None and best[0]>=0.5*min_dur:
        print('   Accetto la versione piu lunga ({:.1f}s) dopo i tentativi: controlla questo punto all ascolto.'.format(best[0]),flush=True)
        return apply_tempo(best[1],CUR_RATE[0])
    raise RuntimeError('Recupero esaurito per {!r}: {}'.format(tts_txt[:100],last_err))
print('Warm-up del modello (evita la perdita delle prime parole nel primo chunk)...')
try:
    _warm = model.generate('Prova.', language_id='it', audio_prompt_path=AUDIO_V1,
        exaggeration=DEF_P['exaggeration'], cfg_weight=DEF_P['cfg_weight'],
        temperature=DEF_P['temperature'], min_p=DEF_P['min_p'], top_p=DEF_P['top_p'],
        repetition_penalty=REPETITION_PENALTY)
    del _warm
except Exception as _warm_err:
    print('Warm-up non riuscito (non blocca la generazione): {}'.format(_warm_err))

import hashlib
import json
import soundfile as sf
import numpy as np


def file_digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda: stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def save_progress():
    temp=job_dir/'stato.tmp'
    with open(temp,'w',encoding='utf-8') as stream:
        json.dump(progress,stream,ensure_ascii=False,indent=2)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temp,job_dir/'stato.json')


def initialize_job():
    global job_dir,progress,job_lock,tc
    # Script, modelli e campioni voce identificano la configurazione esatta.
    identity=[SETTINGS_ID]
    for voice in sorted(set([AUDIO_V1]+[p for p,enabled in
            [(AUDIO_V2,HAS2),(AUDIO_V3,HAS3),(AUDIO_V4,HAS4),
             (AUDIO_V5,HAS5),(AUDIO_V6,HAS6),(AUDIO_V7,HAS7)] if enabled])):
        identity.append((str(pathlib.Path(voice).resolve()),file_digest(voice)))
    source=inspect.getsourcefile(type(model))
    if source: identity.append(file_digest(source))
    identity.append(model.sr)
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:24]
    job_dir=pathlib.Path('1.Output')/'sessioni'/key
    job_dir.mkdir(parents=True,exist_ok=True)
    job_lock=open(job_dir/'session.lock','a+b')
    job_lock.seek(0); job_lock.write(b'0'); job_lock.flush(); job_lock.seek(0)
    try:
        if sys.platform=='win32':
            import msvcrt
            msvcrt.locking(job_lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(job_lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        raise RuntimeError('Questa sessione e gia in esecuzione: attendi o arrestala.')
    state=job_dir/'stato.json'
    if state.exists():
        progress=json.loads(state.read_text(encoding='utf-8'))
        if progress['sample_rate']!=model.sr:
            raise RuntimeError('Stato di ripresa incompatibile: '+str(state))
        # v3.3: la sessione dipende dalle IMPOSTAZIONI, non dal testo. I blocchi si
        # riconoscono dal contenuto: se modifichi una parola si rigenera solo quel blocco.
        progress['chunks']=tc
    else:
        progress=dict(sample_rate=model.sr,chunks=tc,completed={},errors={},status='in_corso')
    progress['status']='in_corso'
    save_progress()
    print('SALVATAGGIO PROGRESSIVO: {}'.format(job_dir.resolve()),flush=True)


def block_sig(txt,vo,em,ek,rate,occ):
    raw=json.dumps([txt,vo,em,ek,round(rate,3),occ],ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


def cached_chunk(index,sig,force=False):
    if force:
        print('   Rigenerazione forzata del blocco {}.'.format(index+1),flush=True)
        return None
    record=progress['completed'].get(sig)
    if not record: return None
    path=job_dir/record['file']
    if path.exists():
        try:
            info=sf.info(path)
            if (info.samplerate==model.sr and info.frames==record['frames']
                    and info.channels==record['channels'] and file_digest(path)==record['sha256']):
                return path
        except (OSError,RuntimeError): pass
    progress['completed'].pop(sig,None); save_progress()
    print('   Blocco salvato non valido: rigenerazione.',flush=True)
    return None


def save_chunk(index,sig,wav):
    path=job_dir/('blocco_{:05d}_{}.wav'.format(index+1,sig[:8]))
    temp=path.with_suffix('.tmp.wav')
    data=wav.detach().cpu().numpy().T
    if not data.size or not np.isfinite(data).all(): raise ValueError('Audio non valido al salvataggio')
    sf.write(temp,data,model.sr,subtype='FLOAT')
    os.replace(temp,path)
    old=progress['completed'].get(sig)
    if old and old.get('file')!=path.name:
        (job_dir/old['file']).unlink(missing_ok=True)
    progress['completed'][sig]=dict(file=path.name,frames=len(data),channels=data.shape[1],sha256=file_digest(path))
    progress['errors'].pop(str(index+1),None)
    save_progress()
    return path


def publish_numbered(temp,directory):
    # Numerazione progressiva dei file finali: audiolibro_001.wav, 002, 003...
    # Non sovrascrive mai file esistenti (anche con due sessioni in parallelo).
    numbers=[]
    for path in directory.glob('audiolibro_*.wav'):
        match=re.fullmatch(r'audiolibro_(\d{1,6})\.wav',path.name,re.IGNORECASE)
        if match: numbers.append(int(match.group(1)))
    number=max(numbers,default=0)+1
    while True:
        output=directory/('audiolibro_{:03d}.wav'.format(number))
        try:
            os.link(temp,output)
        except FileExistsError:
            number+=1
            continue
        except OSError:
            # Filesystem senza hard link (exFAT, alcune unita di rete o cloud):
            # prenota il nome in modo esclusivo e poi sostituisce.
            try:
                with open(output,'xb'): pass
            except FileExistsError:
                number+=1
                continue
            os.replace(temp,output)
            return output
        temp.unlink()
        return output


def fmt_t(s):
    h=int(s//3600); m=int(s%3600//60); sec=s%60
    return '{:d}:{:02d}:{:04.1f}'.format(h,m,sec) if h else '{:02d}:{:04.1f}'.format(m,sec)


def write_map(out,marks,duration):
    try:
        lines=['MAPPA DEI BLOCCHI - {}'.format(out.name),'Durata totale: {}'.format(fmt_t(duration)),
               'Tempi indicativi (+/- mezzo secondo). Per rigenerare: scrivi i numeri in "Rigenera blocchi".','']
        for i,(a,b) in enumerate(marks):
            body=tc[i][0].strip()
            body=re.sub(r'(?:\n\.)+(?=\n|$)',lambda m:' [pausa x{}]'.format(m.group(0).count('\n.')),body)
            body=body.replace('\n',' / ')
            lines.append('{:04d}  {} - {}  {}  {}'.format(i+1,fmt_t(a/model.sr),fmt_t(b/model.sr),tc[i][1].upper(),body[:180]))
        path=out.parent/(out.stem+'_mappa.txt')
        path.write_text('\n'.join(lines),encoding='utf-8')
        print('MAPPA: {}'.format(path),flush=True)
    except Exception as e:
        print('Mappa blocchi non scritta: {}'.format(e),flush=True)


def assemble_saved(paths,out):
    # Conserva in memoria solo un blocco e la coda necessaria alle giunzioni.
    raw=job_dir/'assemblaggio.tmp.wav'
    tail=None; hold=max(1,int(model.sr*.25)); written=0; marks=[]
    with sf.SoundFile(raw,'w',samplerate=model.sr,channels=1,subtype='FLOAT',format='WAV') as stream:
        for i,path in enumerate(paths):
            data,sr=sf.read(path,dtype='float32',always_2d=True)
            if sr!=model.sr or data.shape[1]!=1: raise ValueError('Formato del blocco incompatibile')
            seg=torch.from_numpy(data.T.copy())
            if tail is None:
                tail=seg; start=0
            else:
                previous=tc[i-1]
                joined=asmb(tail,seg,model.sr,previous[6],existing_pause=previous[4])
                if joined is None:
                    pause=0 if previous[4]>0 else dyn_pause(previous[0],emo=previous[2])
                    joined=torch.cat([tail,torch.zeros((1,int(model.sr*pause))),seg],dim=-1)
                tail=joined
                start=written+tail.shape[-1]-seg.shape[-1]
            marks.append((start,start+seg.shape[-1]))
            if tail.shape[-1]>hold:
                stream.write(tail[...,:-hold].numpy().T)
                written+=tail.shape[-1]-hold
                tail=tail[...,-hold:].clone()
        if tail is not None: stream.write(tail.numpy().T)
    # Normalizzazione globale in streaming: i silenzi non aumentano il guadagno.
    peak=0.0
    with sf.SoundFile(raw) as stream:
        for block in stream.blocks(blocksize=262144,dtype='float32'):
            peak=max(peak,float(np.abs(block).max()))
    total=0.0; count=0
    with sf.SoundFile(raw) as stream:
        for block in stream.blocks(blocksize=262144,dtype='float32'):
            active=block[np.abs(block)>max(1e-5,peak*.01)].astype('float64')
            total+=float(np.sum(active*active)); count+=active.size
    gain=min(10**(RMS_TARGET_DB/20)/max((total/max(count,1))**.5,1e-8),.95/max(peak,1e-8),3.0)
    temp=out.with_suffix('.tmp.wav')
    with sf.SoundFile(raw) as source, sf.SoundFile(temp,'w',samplerate=model.sr,channels=1,subtype='PCM_16',format='WAV') as dest:
        for block in source.blocks(blocksize=262144,dtype='float32'): dest.write(block*gain)
        duration=len(source)/model.sr
    out=publish_numbered(temp,out.parent)
    raw.unlink(missing_ok=True)
    progress['status']='completato'; progress['output']=str(out.resolve()); save_progress()
    write_map(out,marks,duration)
    return duration

initialize_job()
segs=[]; fail=[]
st=time.time()
print('\n'+'='*55)
print('AVVIO GENERAZIONE [{}]'.format(DEVICE.type.upper()))
print('Pause Naturali: {}'.format('ATTIVE' if NATURAL_PAUSES else 'disattive'))
print('Pause tra frasi: {} (x{})  |  Tempo lettura: x{}'.format('ATTIVE' if INNER_PAUSES else 'disattive',INNER_SCALE,TEMPO))
print('Righe della stessa frase: {}'.format('UNITE in una generazione' if MERGE_LINES else 'una generazione per riga'))
print('='*55)
for i,(txt,vo,em,ps,tp,ek,jk,tmf) in enumerate(tc):
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
    if tp>0: print('   pausa audio: {:.2f}s (gauss x{:.2f})'.format(tp, PAUSE_SCALE))
    if len(txt.split())<5: print('   ATTENZIONE: chunk corto!')
    tts_txt = prepare_text_for_tts(txt)
    if NATURAL_PAUSES and tts_txt != txt:
        _nl_count = tts_txt.count('\n')
        print('   Testo TTS ({} righe natural):'.format(_nl_count+1))
        for _ln in tts_txt[:120].split('\n'):
            if _ln.strip(): print('     |', _ln.strip()[:70])
    if   vo=='v7' and HAS7: vp=AUDIO_V7
    elif vo=='v6' and HAS6: vp=AUDIO_V6
    elif vo=='v5' and HAS5: vp=AUDIO_V5
    elif vo=='v4' and HAS4: vp=AUDIO_V4
    elif vo=='v3' and HAS3: vp=AUDIO_V3
    elif vo=='v2' and HAS2: vp=AUDIO_V2
    else:                   vp=AUDIO_V1
    p=pp(em,ek); ok=False
    if SAFE_R and RR.search(txt) and REGEN_CFG is None:
        p,_ch=safe_params(p)
        if _ch: print('   [r] parametri di sicurezza per questo blocco: '+_ch,flush=True)
    if RR.search(txt): print('   Letture per parte: '+' | '.join('{}x'.format(_r) for _,_r in split_reads(txt))); RMERGED.clear()
    CUR_RATE[0]=max(0.80,min(1.15,TEMPO*tmf))
    if abs(CUR_RATE[0]-1.0)>=0.01: print('   tempo lettura: x{:.2f}'.format(CUR_RATE[0]))
    _bk=(tts_txt,vo,em,ek,round(CUR_RATE[0],3))
    _occ=SEEN.get(_bk,0); SEEN[_bk]=_occ+1
    sig=block_sig(tts_txt,vo,em,ek,CUR_RATE[0],_occ)
    attempts=[dict(p) for _ in range(3)]
    if (i+1) in REGEN and REGEN_CFG is not None:
        for _a in attempts: _a['cfg_weight']=REGEN_CFG
    last_err=None
    try:
        saved=cached_chunk(i,sig,(i+1) in REGEN)
        if saved is None:
            wav=generate_recoverable(tts_txt,vp,attempts)
            if tp>0:
                wav=torch.cat([wav,torch.zeros((wav.shape[0],int(model.sr*tp)))],dim=-1)
            saved=save_chunk(i,sig,wav)
            del wav
            print('   OK! Blocco salvato.',flush=True)
        else:
            print('   OK! Recuperato dal salvataggio.',flush=True)
        segs.append(saved); ok=True
    except Exception as e:
        last_err=e
    if not ok:
        print('   FALLITO:{}'.format(last_err)); fail.append(i)
        progress['errors'][str(i+1)]=dict(text=tts_txt,error=str(last_err))
        save_progress()
if fail:
    progress['status']='incompleto'; save_progress()
    print('Generazione incompleta: chunk falliti {}'.format([n+1 for n in fail]))
    print('Blocchi riusciti salvati in: {}'.format(job_dir.resolve()))
    print('Premi Genera con lo stesso testo e impostazioni per riprovare solo i blocchi mancanti.')
    print('__CHATTERTEXT_INCOMPLETE__',flush=True)
    exit(3)
if not segs: print('Nessun testo pronunciabile.'); exit(1)
od=pathlib.Path('1.Output'); od.mkdir(exist_ok=True)
out=od/('audiolibro_'+job_dir.name+'.wav')
SCENE=[
        "poi" ,"quando" ,"all'improvviso" ,"improvvisamente" ,"in quel momento" ,"mentre" ,"subito dopo" ,"intanto" ,"nel frattempo" ,"a quel punto" ,"alla fine"
    ]
DIALOG=[
        "disse" ,"penso" ,"grido" ,"urlo" ,"sussurro" ,"domando" ,"rispose" ,"chiese" ,"mormoro" ,"esclamo" ,"borbotto" ,"annuncio" ,"replico" ,"aggiunse" ,"continuo" ,"riprese"
    ]
EMOW=[
        "paura" ,"orrore" ,"ansia" ,"terrore" ,"pianto" ,"felice" ,"gioia" ,"triste" ,"disperato" ,"sconvolto" ,"agitato" ,"sorpreso" ,"commosso" ,"morte" ,"vita" ,"anima" ,"silenzio" ,"infinito" ,"luce" ,"buio" ,"voce" ,"cuore" ,"sogno"
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
    if emo in ('riflessivo','calmo','triste','preoccupato','malinconico','solenne'): base*=1.18
    elif emo in ('arrabbiato','deciso','vibrante'):                                 base*=0.72
    elif emo in ('sussurrato','intimo'):                                            base*=1.10
    base=base*PAUSE_SCALE
    raw=random.gauss(base, sig*PAUSE_SCALE)
    return max(base*0.60, min(raw, base*1.40))
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
def fsf(s1,s2,sr,ss,foms=80,fims=60):
    fl=int(sr*foms/1000); il=int(sr*fims/1000)
    sl=max(0,int(sr*ss))
    s1=s1.clone()
    if s1.shape[-1]>=fl: s1[...,-fl:]*=torch.linspace(1.0,0.0,fl)**1.8
    sil=torch.zeros((s2.shape[0],sl),dtype=s2.dtype)
    s2=s2.clone()
    if s2.shape[-1]>=il: s2[...,:il]*=torch.linspace(0.0,1.0,il)**1.8
    return torch.cat([s1,sil,s2],dim=-1)
def asmb(s1,s2,sr,jt,existing_pause=0.0):
    if jt is None: return None
    ss,mode=JM.get(jt,(0.5,'silence'))
    ss=max(0.0,ss*PAUSE_SCALE-existing_pause)
    if mode=='overlap': return torch.cat([s1,s2],dim=-1) if existing_pause>0 else ov(s1,s2,sr)
    if mode=='fade_sil_fade': return fsf(s1,s2,sr,ss,foms=5,fims=5)
    sil=torch.zeros((s2.shape[0],int(sr*ss))) if ss>0 else None
    if mode=='smooth': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)
    if mode=='cambio': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)
    if mode=='silence': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)
    if mode=='hard': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)
    return cf(s1,s2,sr)
print('Unione dei blocchi salvati...',flush=True)
dur=assemble_saved(segs,out); tot=time.time()-st
out=pathlib.Path(progress['output'])
print(f'\n FILE: {out}')
print(f'   Durata: {dur:.1f}s ({dur/60:.1f} min)')
print(f'   Tempo:  {tot:.1f}s ({tot/60:.1f} min)')
print(f'   Device: {DEVICE.type.upper()}')
print(f'   Pause Naturali: {"ATTIVE" if NATURAL_PAUSES else "disattive"}')
voci_attive=[('V2',HAS2),('V3',HAS3),('V4',HAS4),('V5',HAS5),('V6',HAS6),('V7',HAS7)]
voci_str=' | '.join(n for n,a in voci_attive if a) or '-'
print(f'   Voci: V1 + {voci_str}')
print(f'   OK: {len(segs)}/{len(tc)}')
if fail: print(f'   FAIL: {fail}')
print('\nProcesso completato!')
print('__CHATTERTEXT_DONE__')