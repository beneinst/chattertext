#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatterText - App Desktop Python v3.0 + Multilingual V3
Posizionare nella root di Chatterbox ed eseguire con: python chattertext_app.py

NOVITA v3.0 (Sistema Pause Naturali per Chatterbox):
  - PAUSE NATURALI (nuovo sistema "Natural Pause Mode"):
    I tag pausa vengono ora convertiti in punteggiatura reale + newline
    prima di essere passati a model.generate(). Questo sfrutta il modo
    in cui Chatterbox internamente gestisce le respirazioni naturali:
      [p1]  ->  virgola + \\n       (respiro breve, frase continua)
      [p2]  ->  punto   + \\n       (fine frase naturale)
      [p3]  ->  punto   + \\n\\n    (riflessione/pausa media)
      [b]   ->  punto   + \\n\\n    (cambio idea, nuovo paragrafo)
      [bd]  ->  punto   + \\n\\n\\n  (climax/suspense)
      [cap] ->  punto   + \\n\\n\\n  (reset/capoverso)
      [verso] ->  virgola + \\n     (fine verso poetico)
      [cesura] -> virgola + \\n     (pausa interna verso)
      [strofa] -> punto   + \\n\\n  (fine strofa)
      [metro] / [enjambement] -> spazio (quasi nulli, solo ritmo)
    Il sistema mantiene ANCHE le pause audio in secondi come prima
    (i due approcci si sommano per la massima naturalezza).
  - OPZIONE UI "Pause Naturali": checkbox per attivare/disattivare
    la conversione tag->testo-naturale (default: attivo)
  - GUIDA AGGIORNATA con spiegazione del nuovo sistema

NOVITA v2.9 (integrate):
  - Accapo come pause (1/2/3+ Enter -> [p1]/[p2]/[b])
  - normalize_text avanzata: valuta, simboli, abbreviazioni IT, ordinali
  - 4 stili di lettura: Narrativa/Poesia/Teatro/Audiolibro lungo
  - Tag poetici: [verso] [strofa] [metro] [enjambement] [cesura]
  - 7 voci con fallback automatico su V1
  - Post-processing audio: noise gate, RMS normalize, trim, declick
  - Chatterbox Multilingual V3 con controllo di compatibilita
"""
import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import os, subprocess, threading, sys, re, json, pathlib, time


def _hidden_subprocess_kwargs():
    """Impedisce ai processi figli di aprire una console su Windows."""
    if sys.platform != "win32":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "startupinfo": startupinfo,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    }


HIDDEN_SUBPROCESS = _hidden_subprocess_kwargs()

# =========================================================
# PALETTE
# =========================================================
C = {
    "bg":       "#25221b", "surface":  "#303030", "surface2": "#383838",
    "border":   "#4a4a4a", "accent":   "#81ecec", "accent2":  "#4a90e2",
    "text":     "#ededed", "text_dim": "#a0a5a6", "success":  "#00b894",
    "warning":  "#fdcb6e", "danger":   "#e84357", "v1":       "#3498db",
    "v2":       "#e74c3c", "v3":       "#00b894",
    "v4":       "#e67e22", "v5":       "#9b59b6",
    "v6":       "#5d7a8a", "v7":       "#4a4a4a",
    "chunk_bg": "#2c2c2c", "hdr_bg":   "#333333",
    "gpu":      "#76b900", "cpu":      "#4a90e2",
    "style_narr":   "#3498db",
    "style_poesia": "#9b59b6",
    "style_teatro": "#e74c3c",
    "style_lungo":  "#00b894",
    "natural":  "#00cec9",   # colore per il nuovo sistema pause naturali
}
EMO_C = {
    "calmo":"#27ae60","appassionato":"#e67e22","arrabbiato":"#c0392b",
    "triste":"#8e44ad","ironico":"#16a085","sussurrato":"#546e7a",
    "riflessivo":"#2980b9","deciso":"#d35400","preoccupato":"#7f8c8d",
    "gentile":"#2ecc71","serio":"#34495e",
    "solenne":"#1a5276","estatico":"#d4ac0d","malinconico":"#5d6d7e",
    "vibrante":"#922b21","intimo":"#196f3d",
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
    "solenne":     {"exaggeration":0.55,"cfg_weight":0.80,"temperature":0.38,"top_p":0.68,"min_p":0.20},
    "estatico":    {"exaggeration":0.85,"cfg_weight":0.52,"temperature":0.72,"top_p":0.88,"min_p":0.07},
    "malinconico": {"exaggeration":0.48,"cfg_weight":0.82,"temperature":0.43,"top_p":0.70,"min_p":0.18},
    "vibrante":    {"exaggeration":0.88,"cfg_weight":0.48,"temperature":0.78,"top_p":0.90,"min_p":0.06},
    "intimo":      {"exaggeration":0.30,"cfg_weight":0.88,"temperature":0.36,"top_p":0.65,"min_p":0.22},
}
ALL_EMO = list(EMOTION_PRESETS.keys())

# =========================================================
# STILI DI LETTURA
# =========================================================
READING_STYLES = {
    "narrativa": {
        "label": "Narrativa",
        "color": "#3498db",
        "desc": "Romanzi, racconti, prosa standard",
        "exaggeration": 0.50, "cfg_weight": 0.58, "temperature": 0.60,
        "top_p": 0.75, "min_p": 0.15,
        "preset_scale": 1.0, "pause_scale": 1.0,
        "noise_gate_db": -50, "rms_target_db": -18, "trim_threshold_db": -45,
        "notes": "Stile bilanciato. Pause naturali. Emozioni moderate.",
    },
    "poesia": {
        "label": "Poesia",
        "color": "#9b59b6",
        "desc": "Poesie, versi, testi lirici — lettura recitata",
        "exaggeration": 0.72, "cfg_weight": 0.42, "temperature": 0.68,
        "top_p": 0.88, "min_p": 0.07,
        "preset_scale": 1.25, "pause_scale": 1.45,
        "noise_gate_db": -48, "rms_target_db": -16, "trim_threshold_db": -42,
        "notes": "Lettura recitata. Pause metriche amplificate. Massima espressività.",
        "extra_tags": ["verso","strofa","metro","enjambement","cesura"],
    },
    "teatro": {
        "label": "Teatro",
        "color": "#e74c3c",
        "desc": "Testi teatrali, monologhi, dialoghi drammatici",
        "exaggeration": 0.78, "cfg_weight": 0.38, "temperature": 0.72,
        "top_p": 0.90, "min_p": 0.05,
        "preset_scale": 1.35, "pause_scale": 1.20,
        "noise_gate_db": -46, "rms_target_db": -15, "trim_threshold_db": -40,
        "notes": "Dinamica ampia teatrale. Enfasi forti. Transizioni nette tra personaggi.",
    },
    "audiolibro_lungo": {
        "label": "Audiolibro lungo",
        "color": "#00b894",
        "desc": "Capitoli lunghi, saga, consistenza su ore di audio",
        "exaggeration": 0.48, "cfg_weight": 0.65, "temperature": 0.55,
        "top_p": 0.72, "min_p": 0.18,
        "preset_scale": 0.88, "pause_scale": 0.92,
        "noise_gate_db": -52, "rms_target_db": -20, "trim_threshold_db": -48,
        "notes": "Parametri stabili per lunghe sessioni. Meno varianza. Coerenza timbrica.",
    },
}

# =========================================================
# PAUSE
# =========================================================
PAUSE_MAP = {
    "[p1]":          (0.18, 0.03),
    "[p2]":          (0.40, 0.05),
    "[p3]":          (0.65, 0.07),
    "[b]":           (1.00, 0.10),
    "[bd]":          (1.60, 0.15),
    "[cap]":         (2.00, 0.20),
    "[pausa]":       (0.50, 0.05),
    "[pausa_lunga]": (1.20, 0.10),
    "[silenzio]":    (2.00, 0.15),
    "[verso]":       (0.30, 0.04),
    "[strofa]":      (1.20, 0.12),
    "[metro]":       (0.08, 0.01),
    "[enjambement]": (0.05, 0.01),
    "[cesura]":      (0.45, 0.05),
}
PAUSE_FLAT = {k: v[0] for k, v in PAUSE_MAP.items()}
ALL_PAUSE_NAMES = ["p1","p2","p3","b","bd","cap","pausa","pausa_lunga","silenzio",
                   "verso","strofa","metro","enjambement","cesura"]

# =========================================================
# TABELLA PAUSE NATURALI v3.0
# =========================================================
# Ogni tag pausa -> (punteggiatura_da_aggiungere, numero_newline)
# Questa tabella converte i tag in testo reale che Chatterbox
# interpreta come respirazioni naturali durante la sintesi.
PAUSE_TO_NATURAL = {
    # Quasi nulli - solo ritmo metrico, nessun newline
    "[metro]":       ("",  0),
    "[enjambement]": ("",  0),
    # Pause brevi - virgola + 1 newline (respiro, flusso continuo)
    "[p1]":          (",", 1),
    "[verso]":       (",", 1),
    "[cesura]":      (",", 1),
    # Pause medie - punto + 1 newline (fine frase completa)
    "[p2]":          (".", 1),
    "[pausa]":       (".", 1),
    # Pause medio-lunghe - punto + 2 newline (riflessione/cambio idea)
    "[p3]":          (".", 2),
    "[b]":           (".", 2),
    "[strofa]":      (".", 2),
    "[pausa_lunga]": (".", 2),
    # Pause lunghe/drammatiche - punto + 3 newline (climax/capoverso)
    "[bd]":          (".", 3),
    "[cap]":         (".", 3),
    "[silenzio]":    (".", 3),
}

# Ordine di processing: più specifici/lunghi PRIMA per evitare conflitti
NATURAL_PAUSE_ORDER = [
    "[silenzio]", "[cap]", "[bd]",
    "[pausa_lunga]", "[strofa]", "[b]",
    "[p3]", "[pausa]", "[p2]",
    "[cesura]", "[verso]", "[p1]",
    "[enjambement]", "[metro]",
]


def pauses_to_natural_text(text):
    """
    v3.0 - Converte i tag pausa ChatterText in punteggiatura naturale + newline reali.

    Chatterbox TTS usa i newline come guide respiratorie interne: il modello
    interpreta ogni riga come una unità di respiro. Usando questa conversione
    PRIMA di chiamare model.generate(), le pause diventano organiche e naturali
    invece di essere solo silenzio digitale aggiunto in post.

    Strategia di conversione:
      [p1]/[verso]/[cesura]    -> virgola + \\n      (respiro breve)
      [p2]/[pausa]             -> punto   + \\n      (fine frase)
      [p3]/[b]/[strofa]        -> punto   + \\n\\n   (nuovo paragrafo)
      [bd]/[cap]/[silenzio]    -> punto   + \\n\\n\\n (pausa drammatica)
      [metro]/[enjambement]    -> spazio              (quasi nullo)

    La punteggiatura NON viene duplicata se già presente nel testo.
    Questo sistema si SOMMA alle pause audio in secondi (non le sostituisce):
    ogni pausa beneficia sia della respirazione naturale del modello
    sia del silenzio audio aggiunto in post-processing.
    """
    ORDER = NATURAL_PAUSE_ORDER

    # Prima passata: sostituisci i tag con placeholder numerati
    # per poter poi risolvere il contesto correttamente
    for tag in ORDER:
        if tag not in PAUSE_TO_NATURAL:
            continue
        punct, nlcount = PAUSE_TO_NATURAL[tag]
        pattern = re.compile(re.escape(tag), re.IGNORECASE)
        placeholder = "__PNLT__{}__NL{}__".format(punct.replace(".", "DOT").replace(",", "COMMA"), nlcount)
        text = pattern.sub(placeholder, text)

    # Seconda passata: risolvi i placeholder con context check
    def resolve(m):
        raw_punct = m.group(1).replace("DOT", ".").replace("COMMA", ",")
        nlcount_r = int(m.group(2))
        nl = "\n" * nlcount_r

        # Guarda il testo prima di questo placeholder (già parzialmente risolto)
        pos = m.start()
        before = text[:pos].rstrip()

        # Non duplicare punteggiatura se già presente
        if raw_punct and before and before[-1] in '.,!?:;':
            return nl if nl else " "
        else:
            if raw_punct:
                return raw_punct + nl
            else:
                return nl if nl else " "

    text = re.sub(r'__PNLT__([\w]*)__NL(\d)__', resolve, text)

    # Pulizie finali
    text = re.sub(r'\n{4,}', '\n\n\n', text)           # max 3 newline consecutivi
    text = re.sub(r'[ \t]+\n', '\n', text)             # no spazi prima di newline
    text = re.sub(r'\n[ \t]+', '\n', text)             # no spazi dopo newline
    text = re.sub(r'([.,!?])\s*([.,])', r'\1', text)   # no punteggiatura doppia
    text = re.sub(r'[ \t]{2,}', ' ', text)             # spazi multipli -> uno
    # Virgola/punto orfani con spazio prima: "parola ,\n" -> "parola,\n"
    text = re.sub(r' +([,.])\n', r'\1\n', text)
    text = re.sub(r' +([,.])\s*$', r'\1', text)
    return text.strip()


EMPH_PRESETS = {
    "e1": {"exaggeration_delta": +0.10, "cfg_weight_delta": -0.05},
    "e2": {"exaggeration_delta": +0.25, "cfg_weight_delta": -0.12},
    "ep": {"exaggeration_delta": +0.15, "cfg_weight_delta": -0.08},
}
ALL_EMPH_NAMES = ["e1","e2","ep"]

# =========================================================
# GIUNZIONI
# =========================================================
JOIN_MAP = {
    "[join]":        (0.00, "overlap"),
    "[cont]":        (0.12, "smooth"),
    "[cambio]":      (0.50, "cambio"),
    "[cambio3]":     (0.50, "cambio"),
    "[cambio4]":     (0.50, "cambio"),
    "[cambio5]":     (0.50, "cambio"),
    "[cambio6]":     (0.50, "cambio"),
    "[cambio7]":     (0.50, "cambio"),
    "[para]":        (0.90, "silence"),
    "[stacco]":      (1.40, "fade_sil_fade"),
    "[lungo]":       (1.80, "fade_sil_fade"),
    "[scena]":       (2.40, "hard"),
    "[dissolvenza]": (1.60, "fade_sil_fade"),
}
ALL_JOIN_NAMES = ["join","cont","cambio","cambio3","cambio4","cambio5","cambio6","cambio7",
                  "para","stacco","lungo","scena","dissolvenza"]

QUICK_TAGS = (
    ["[p1]", "[p2]", "[p3]", "[b]", "[bd]", "[cap]", "[pausa]", "[pausa_lunga]", "[silenzio]"]
    + ["[verso]", "[strofa]", "[metro]", "[enjambement]", "[cesura]"]
    + ["[e1]", "[e2]", "[ep]"]
    + ["[join]", "[cont]", "[cambio]", "[cambio3]", "[cambio4]", "[cambio5]",
       "[cambio6]", "[cambio7]", "[para]", "[stacco]", "[lungo]", "[scena]", "[dissolvenza]"]
    + ["[inizio]…[fine]"]
)

BREATH_MAX_W = 14; BREATH_MAX_C = 80
CHUNK_MIN_W  = 5;  CHUNK_MIN_C  = 20

PAUSE_BADGE_C = {
    "p1":"#4a9080","p2":"#2980b9","p3":"#8e44ad",
    "b":"#27ae60","bd":"#e84357","cap":"#e67e22",
    "verso":"#9b59b6","strofa":"#6c3483","metro":"#a9cce3",
    "enjambement":"#d7bde2","cesura":"#7d3c98",
}
JOIN_BADGE_C = {
    "join":"#00cec9","cont":"#74b9ff","cambio":"#a29bfe","cambio3":"#00b894",
    "cambio4":"#e67e22","cambio5":"#9b59b6","cambio6":"#5d7a8a","cambio7":"#4a4a4a",
    "para":"#fdcb6e","stacco":"#fd79a8","lungo":"#e17055","scena":"#636e72",
    "dissolvenza":"#a29bfe",
}

# =========================================================
# HELPERS TESTO
# =========================================================
def _protected():
    emo = "|".join(ALL_EMO)
    return re.compile(
        r"\[/?(?:v1|v2|v3|v4|v5|v6|v7|inizio|fine|pausa|pausa_lunga|silenzio"
        r"|p1|p2|p3|b|bd|cap|e1|e2|ep"
        r"|verso|strofa|metro|enjambement|cesura|dissolvenza"
        r"|join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena"
        r"|(?:(?:v1|v2|v3|v4|v5|v6|v7)_)?(?:"+emo+r"))\]", re.IGNORECASE)

_UNITA = ["", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove"]
_DIECI = ["dieci","undici","dodici","tredici","quattordici","quindici","sedici","diciassette","diciotto","diciannove"]
_DECINE = ["", "", "venti", "trenta", "quaranta", "cinquanta", "sessanta", "settanta", "ottanta", "novanta"]

def _tre_cifre_it(n):
    if n == 0: return ""
    c, r = n // 100, n % 100
    s = ""
    if c:
        s += "cento" if c == 1 else _UNITA[c] + "cento"
    if r:
        if r < 10:
            s += _UNITA[r]
        elif r < 20:
            s += _DIECI[r-10]
        else:
            d, u = r // 10, r % 10
            dec = _DECINE[d]
            if u in (1, 8) and dec:
                dec = dec[:-1]  # ventuno, ventotto (elisione vocale)
            s += dec + (_UNITA[u] if u else "")
    return s

def number_to_italian_words(n):
    if n == 0: return "zero"
    neg = n < 0; n = abs(n)
    if n >= 10**9: return str(n)  # oltre il miliardo: lascia invariato
    parts = []
    miliardi, n = divmod(n, 10**9)
    milioni, n  = divmod(n, 10**6)
    migliaia, resto = divmod(n, 1000)
    if miliardi:
        parts.append(("un " if miliardi==1 else _tre_cifre_it(miliardi)+" ") + ("miliardo" if miliardi==1 else "miliardi"))
    if milioni:
        parts.append(("un " if milioni==1 else _tre_cifre_it(milioni)+" ") + ("milione" if milioni==1 else "milioni"))
    if migliaia:
        parts.append("mille" if migliaia==1 else _tre_cifre_it(migliaia)+"mila")
    if resto:
        parts.append(_tre_cifre_it(resto))
    return ("meno " if neg else "") + " ".join(p for p in parts if p)

def _expand_number_match(m):
    intpart, dec = int(m.group(1)), m.group(2)
    words = number_to_italian_words(intpart)
    if dec:
        digs = " ".join(_UNITA[int(d)] if d != "0" else "zero" for d in dec)
        words += " virgola " + digs
    return words

def normalize_text(text):
    """
    Pulizia testo avanzata v2.9 per Chatterbox TTS.
    (invariata dalla v2.9 - vedi commenti originali)
    """
    tm = {}; idx = [0]; pat = _protected()

    def sv(m):
        ph = "ZZCHT{}ZZCHT".format(idx[0])
        tm[ph] = m.group(0); idx[0] += 1; return ph
    text = pat.sub(sv, text)

    # Virgolette tipografiche -> standard ASCII
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u00ab', '"').replace('\u00bb', '"')
    text = text.replace('\u201e', '"').replace('\u201a', "'")
    # Apostrofi speciali -> apostrofo ASCII dritto  <<< PRIMA del charset filter >>>
    # \u2019 (apostrofo curvo chiuso da Word/iOS/Mac) è il più comune:
    # se non convertito qui, il charset filter lo rimuove -> "l'anima" diventa "lanima"
    text = text.replace('\u2019', "'")
    text = text.replace('\u2018', "'")
    text = text.replace('\u02bc', "'")
    text = text.replace('\u02b9', "'")
    text = text.replace('\u0060', "'")
    text = text.replace('\u00b4', "'")
    text = re.sub(r"[\u02bc\u02b9\u0060\u00b4\u2018\u2019]", "'", text)
    text = re.sub(r"-\s*\n\s*([a-z\u00c0-\u00f9])", r"\1", text)
    text = re.sub(r"^\s*[\u2014\u2013]\s*", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"(?<=\w)\s*[\u2014\u2013]\s*(?=\w)", ", ", text)
    text = re.sub(r"\s*[\u2014\u2013]\s*", ", ", text)
    text = re.sub(r"\s*--\s*", ", ", text)
    text = re.sub(r"(?<=\w)\s+-\s+(?=\w)", ", ", text)
    text = text.replace('\u2026', '.')
    text = re.sub(r"\.{2,}", '.', text)
    text = re.sub(r"\.\s*\.\s*\.", '.', text)
    text = re.sub(r'(\d)\s*€',  r'\1 euro',     text)
    text = re.sub(r'€\s*(\d)',  r'\1 euro',     text)
    text = re.sub(r'€',         'euro',          text)
    text = re.sub(r'(\d)\s*\$', r'\1 dollari',  text)
    text = re.sub(r'\$\s*(\d)', r'\1 dollari',  text)
    text = re.sub(r'\$',        'dollari',       text)
    text = re.sub(r'(\d)\s*£',  r'\1 sterline', text)
    text = re.sub(r'£\s*(\d)',  r'\1 sterline', text)
    text = re.sub(r'£',         'sterline',      text)
    text = re.sub(r'(\d)\s*%',  r'\1 percento', text)
    text = re.sub(r'%',         ' percento',    text)
    text = re.sub(r'\s*&\s*',   ' e ',          text)
    text = re.sub(r'#(\d+)',    r'numero \1',   text)
    text = re.sub(r'#(\w+)',    r'\1',          text)
    text = re.sub(r'(?<!\w)@(?!\w)', ' at ', text)
    text = text.replace('\u00d7', ' per ')
    text = text.replace('\u00f7', ' diviso ')
    text = text.replace('\u00b1', ' piu o meno ')
    text = text.replace('\u00bd', ' mezzo ')
    text = text.replace('\u00bc', ' un quarto ')
    text = text.replace('\u00be', ' tre quarti ')
    _ordinali = {
        '1': 'primo',  '2': 'secondo', '3': 'terzo',   '4': 'quarto',
        '5': 'quinto', '6': 'sesto',   '7': 'settimo', '8': 'ottavo',
        '9': 'nono',  '10': 'decimo',
    }
    def _fix_ordinale(m):
        n = m.group(1)
        return _ordinali.get(n, n + '-esimo')
    text = re.sub(r'\b(\d{1,2})\u00b0(?!\s*[CF\d])', _fix_ordinale, text)
    text = re.sub(r'(\d+)\s*\u00b0\s*[Cc]', r'\1 gradi', text)
    text = re.sub(r'(\d+)\s*\u00b0\s*[Ff]', r'\1 gradi', text)
    text = re.sub(r'(\d+)\s*\u00b0', r'\1 gradi', text)
    text = text.replace('\u00b0', '')
    abbr = [
        (r'\bDott\.\s*ssa\b', 'dottoressa'), (r'\bDott\.', 'dottor'),
        (r'\bdott\.\s*ssa\b', 'dottoressa'), (r'\bdott\.', 'dottor'),
        (r'\bProf\.\s*ssa\b', 'professoressa'), (r'\bProf\.', 'professore'),
        (r'\bprof\.\s*ssa\b', 'professoressa'), (r'\bprof\.', 'professore'),
        (r'\bSig\.\s*ra\b', 'signora'), (r'\bSig\.', 'signor'),
        (r'\bsig\.\s*ra\b', 'signora'), (r'\bsig\.', 'signor'),
        (r'\bAvv\.', 'avvocato'), (r'\bavv\.', 'avvocato'),
        (r'\bIng\.', 'ingegnere'), (r'\bing\.', 'ingegnere'),
        (r'\bArch\.', 'architetto'), (r'\barch\.', 'architetto'),
        (r'\bGen\.', 'generale'), (r'\bCap\.', 'capitano'),
        (r'\bNr\.', 'numero'), (r'\bnr\.', 'numero'),
        (r'\bN\.\s*(?=\d)', 'numero '), (r'\bn\.\s*(?=\d)', 'numero '),
        (r'\bArt\.', 'articolo'), (r'\bart\.', 'articolo'),
        (r'\becc\.', 'eccetera'), (r'\bEcc\.', 'eccetera'),
        (r'\bes\.', 'per esempio'), (r'\bEs\.', 'per esempio'),
        (r'\bvs\.', 'contro'), (r'\bVs\.', 'contro'),
        (r'\bcf\.', 'confronta'), (r'\bCf\.', 'confronta'),
        (r'\bp\.\s*es\.', 'per esempio'),
        (r'\bvol\.', 'volume'), (r'\bpag\.', 'pagina'),
        (r'\bcap\.', 'capitolo'),
        (r'\bott\.', 'ottobre'), (r'\bgen\.', 'gennaio'),
        (r'\bfeb\.', 'febbraio'), (r'\bmar\.', 'marzo'),
        (r'\bapr\.', 'aprile'), (r'\bmag\.', 'maggio'),
        (r'\bgiu\.', 'giugno'), (r'\blug\.', 'luglio'),
        (r'\bago\.', 'agosto'), (r'\bset\.', 'settembre'),
        (r'\bnov\.', 'novembre'), (r'\bdic\.', 'dicembre'),
        (r'\bkm/h\b', 'chilometri orari'), (r'\bkm\b', 'chilometri'),
        (r'\bm/s\b', 'metri al secondo'), (r'\bcm\b', 'centimetri'),
        (r'\bmm\b', 'millimetri'), (r'\bkg\b', 'chilogrammi'),
        (r'\bg\b(?=\s)', 'grammi'), (r'\bml\b', 'millilitri'),
        (r'\bcal\b', 'calorie'), (r'\bkcal\b', 'kilocalorie'),
    ]
    for pattern, repl in abbr:
        text = re.sub(pattern, repl, text)
    def _fix_parens(m):
        inner = m.group(1).strip()
        if not inner: return ''
        return ', ' + inner + ','
    text = re.sub(r'\(([^)]{1,80})\)', _fix_parens, text)
    text = re.sub(r'\[[^\]]{1,80}\]', '', text)
    text = re.sub(r'[()]', '', text)
    text = text.replace(';', ',')
    text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+?)_{1,2}', r'\1', text)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    text = re.sub(r'(?<=\w)/(?=\w)', ' o ', text)
    for art in ["l'", "nell'", "dell'", "sull'", "all'", "dall'", "un'"]:
        pat_art = re.compile(re.escape(art) + r'([A-Z])(?!ZCHT)', re.IGNORECASE)
        text = pat_art.sub(lambda m, a=art: a + m.group(1).lower(), text)
    text = re.sub(r"'([A-Z])(?=[a-z\u00c0-\u00f9])(?!ZCHT)", lambda m: "'" + m.group(1).lower(), text)
    def _fix_allcaps(m):
        w = m.group(0)
        if len(w) >= 3 and w.isupper(): return w.capitalize()
        return w
    text = re.sub(r'\b[A-Z]{3,}\b', _fix_allcaps, text)
    for up, lo in [('À','à'),('È','è'),('É','é'),('Ì','ì'),('Î','î'),
                   ('Ò','ò'),('Ó','ó'),('Ù','ù'),('Ú','ú'),('Â','â'),
                   ('Ê','ê'),('Ô','ô'),('Û','û'),('Ä','ä'),('Ë','ë'),
                   ('Ï','ï'),('Ö','ö'),('Ü','ü')]:
        text = text.replace(up, lo)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    text = re.sub(r',{2,}', ',', text)
    text = re.sub(r'([!?])\.', r'\1', text)
    # Due punti -> punto (pausa naturale per Chatterbox)
    # Protegge: orari/ratio cifra:cifra (15:30, 1:2) e URL (http://)
    text = re.sub(r'(\d):(\d)', r'\1COLONNUMERO\2', text)   # salva XX:XX
    text = re.sub(r'\b(\d{1,6})(?:,(\d{1,4}))?\b', _expand_number_match, text)
    text = re.sub(r'://', 'COLONSLASH', text)                # salva ://
    text = text.replace(':', '.')                            # tutto il resto -> .
    text = text.replace('COLONNUMERO', ':')                  # ripristina XX:XX
    text = text.replace('COLONSLASH', '://')                 # ripristina ://
    # Mantiene ':' e '/' già protetti/ripristinati in orari, rapporti e URL.
    text = re.sub(r"[^\w\s.,!?'\":/\-\u00c0-\u00f9]", ' ', text)
    text = re.sub(r' +([.,!?])', r'\1', text)
    text = re.sub(r'([.,!?]) {2,}', r'\1 ', text)
    text = re.sub(r' {2,}', ' ', text)
    for ph, t in tm.items():
        text = text.replace(ph, t)
    return text.strip()


def newlines_to_pauses(text):
    """
    Converte gli accapo nel testo in tag pausa ChatterText.
    Da usare PRIMA di normalize_text, solo sul testo libero (non taggato).
    1 accapo -> [p1], 2 accapo -> [p2], 3+ accapo -> [b]
    """
    if re.search(r'\[inizio\]', text, re.IGNORECASE):
        return text
    text = re.sub(r'\n{3,}', ' [b] ', text)
    text = re.sub(r'\n{2}', ' [p2] ', text)
    text = re.sub(r'\n', ' [p1] ', text)
    text = re.sub(r'(\[p[123]\]|\[b\])\s*(\[p[123]\]|\[b\])', r'\2', text)
    text = re.sub(r'^\s*(\[p[123]\]|\[b\])\s*', '', text)
    text = re.sub(r'\s*(\[p[123]\]|\[b\])\s*$', '', text)
    return text


def analyze_text(text):
    errs = []
    if len(text) > 10000:
        errs.append(("warning", "Testo troppo lungo ({} car.)".format(len(text))))
    tnt = _protected().sub("", text)
    wc = {}
    for w in re.findall(r"\b\w+\b", tnt.lower()):
        wc[w] = wc.get(w, 0) + 1
    rep = sorted([(w,c) for w,c in wc.items() if c>3 and len(w)>3],
                 key=lambda x: -x[1])[:5]
    if rep:
        errs.append(("info", "Parole ripetute: "+", ".join('"{}"({}x)'.format(w,c) for w,c in rep)))
    raw_dots = re.findall(r"\.{2,}", tnt)
    if raw_dots:
        errs.append(("warning", "Puntini multipli residui: {} occorrenze".format(len(raw_dots))))
    sp = re.findall(r"[^\w\s.,!?\'\"\-\u00C0-\u00F9]", tnt)
    sp_uniq = list(dict.fromkeys(sp))[:10]
    if sp_uniq:
        errs.append(("warning", "Caratteri speciali residui: " + " ".join(sp_uniq)))
    caps = re.findall(r"[''`\u00b4]\w*[A-Z]\w*", text)
    if caps:
        errs.append(("info", "Maiuscole dopo apostrofo: " + ", ".join(caps[:3])))

    # Controllo strutturale dei tag voce/emozione.
    emo = "|".join(ALL_EMO)
    tag_re = re.compile(r"\[(/?)(v[1-7])(?:_("+emo+r"))?\]", re.IGNORECASE)
    stack = []
    for match in tag_re.finditer(text):
        closing, voice, emotion = match.group(1), match.group(2).lower(), (match.group(3) or "").lower()
        if not closing:
            stack.append((voice, emotion, match.group(0)))
        elif not stack:
            errs.append(("error", "Tag di chiusura senza apertura: {}".format(match.group(0))))
        else:
            open_voice, open_emotion, open_tag = stack.pop()
            if (voice, emotion) != (open_voice, open_emotion):
                errs.append(("error", "Tag discordanti: {} chiuso da {}".format(open_tag, match.group(0))))
    for _, _, open_tag in stack:
        errs.append(("error", "Tag senza chiusura: {}".format(open_tag)))

    starts = len(re.findall(r"\[inizio\]", text, re.IGNORECASE))
    ends = len(re.findall(r"\[fine\]", text, re.IGNORECASE))
    if starts != ends:
        errs.append(("error", "Blocchi non bilanciati: {} [inizio], {} [fine]".format(starts, ends)))
    return errs


def chunk_text(text, min_w, max_w, max_c):
    tms = list(re.finditer(r"\[inizio\]([\s\S]*?)\[fine\]", text, re.IGNORECASE))
    if tms:
        chunks = []; emo = "|".join(ALL_EMO)
        vpat = re.compile(
            r"\[(v[1-7])(?:_("+emo+r"))?\]([\s\S]*?)\[/(v[1-7])(?:_("+emo+r"))?\]",
            re.IGNORECASE)
        for m in tms:
            cont = m.group(1).strip()
            if not cont: continue
            vml = list(vpat.finditer(cont))
            if vml:
                for vm in vml:
                    open_key = (vm.group(1).lower(), (vm.group(2) or "").lower())
                    close_key = (vm.group(4).lower(), (vm.group(5) or "").lower())
                    if open_key == close_key and vm.group(3).strip():
                        chunks.append(vm.group(0).strip())
                    elif cont:
                        # Non perde il testo: la discordanza viene segnalata da analyze_text().
                        chunks.append(cont)
                        break
            else:
                if cont: chunks.append(cont)
        return chunks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []

    def split_oversized(piece):
        words = piece.split()
        if not words:
            return []
        result, buf = [], []
        for word in words:
            candidate = " ".join(buf + [word])
            if buf and (len(candidate.split()) > max_w or len(candidate) > max_c):
                result.append(" ".join(buf))
                buf = [word]
            else:
                buf.append(word)
        if buf:
            result.append(" ".join(buf))
        return result

    for p in paragraphs:
        if len(p) <= max_c and len(p.split()) <= max_w:
            chunks.append(p); continue
        paragraph_start = len(chunks)
        # Include anche l'ultima frase priva di punteggiatura finale.
        sentences = [s.strip() for s in re.findall(r"[^.!?]+(?:[.!?]+|$)", p) if s.strip()]
        buf = ""
        for sentence in sentences:
            pieces = split_oversized(sentence) if (len(sentence) > max_c or len(sentence.split()) > max_w) else [sentence]
            for fr in pieces:
                test = (buf+" "+fr).strip() if buf else fr
                if len(test) > max_c or len(test.split()) > max_w:
                    if buf.strip(): chunks.append(buf.strip())
                    buf = fr
                else:
                    buf = test
        if buf.strip(): chunks.append(buf.strip())

        # Se resta una coda troppo corta, ridistribuisce le parole con il chunk
        # precedente senza superare i limiti massimi e senza attraversare paragrafi.
        local = chunks[paragraph_start:]
        if len(local) >= 2 and len(local[-1].split()) < min_w:
            words = (local[-2] + " " + local[-1]).split()
            choices = []
            for split_at in range(min_w, len(words) - min_w + 1):
                left, right = " ".join(words[:split_at]), " ".join(words[split_at:])
                if (len(left.split()) <= max_w and len(right.split()) <= max_w and
                        len(left) <= max_c and len(right) <= max_c):
                    choices.append((abs(len(left.split()) - len(right.split())), left, right))
            if choices:
                _, left, right = min(choices, key=lambda item: item[0])
                chunks[-2:] = [left, right]
    return chunks


def chunk_status(words, chars):
    if words > 60 or chars > 350: return "danger", "Troppo lungo"
    if words > BREATH_MAX_W or chars > BREATH_MAX_C:
        return "warning", "Supera blocco-respiro ({}/14)".format(words)
    if words < CHUNK_MIN_W or chars < CHUNK_MIN_C:
        return "danger", "TROPPO CORTO ({} par.)".format(words)
    return "success", "Ottimale"


def detect_emph(chunk):
    return [t for t in ALL_EMPH_NAMES if re.search(r"\["+t+r"\]", chunk, re.IGNORECASE)]


def detect_pauses(chunk):
    res = []
    for n in ALL_PAUSE_NAMES:
        tag = "[{}]".format(n)
        for _ in re.findall(re.escape(tag), chunk, re.IGNORECASE):
            res.append((tag, PAUSE_FLAT.get(tag, 0.4)))
    return res


def detect_voice_emo(chunk):
    emo = "|".join(ALL_EMO)
    m = re.search(r"\[(v1|v2|v3|v4|v5|v6|v7)_("+emo+r")\]", chunk, re.IGNORECASE)
    if m: return m.group(1).lower(), m.group(2).lower()
    m = re.search(r"\[(v1|v2|v3|v4|v5|v6|v7)\]", chunk, re.IGNORECASE)
    if m: return m.group(1).lower(), None
    m = re.search(r"\[("+emo+r")\]", chunk, re.IGNORECASE)
    if m: return None, m.group(1).lower()
    return None, None


def detect_join(chunk):
    for n in ALL_JOIN_NAMES:
        if re.search(r"\["+n+r"\]", chunk, re.IGNORECASE): return "[{}]".format(n)
    return None

# =========================================================
# SUONO
# =========================================================
def play_sound():
    try:
        if sys.platform == "win32":
            import winsound
            for f, d in [(523, 60), (659, 60), (784, 100), (1047, 175)]:
                winsound.Beep(f, d); time.sleep(0.04)
        elif sys.platform == "darwin":
            subprocess.run(["afplay", "-v", "0.5", "/System/Library/Sounds/Glass.aiff"],
                           capture_output=True)
        else:
            if subprocess.run(["which","paplay"], capture_output=True).returncode == 0:
                subprocess.run(["paplay", "--volume=32768",
                     "/usr/share/sounds/freedesktop/stereo/complete.oga"], capture_output=True)
            elif subprocess.run(["which","aplay"], capture_output=True).returncode == 0:
                subprocess.run(["aplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                                capture_output=True)
            else:
                print("\a", end="", flush=True)
    except Exception:
        pass

# =========================================================
# GPU
# =========================================================
def detect_device():
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory // (1024**3)
            return "cuda", "GPU: {} ({}GB VRAM)".format(name, vram)
    except ImportError:
        pass
    return "cpu", "CPU: nessuna GPU CUDA rilevata"

# =========================================================
# PROMPT GUIDA NARRATIVA
# =========================================================
GUIDE_PROMPT = '''# PREPARAZIONE FEDELE PER CHATTERTEXT TTS v3.0 — NARRATIVA

Sei un editor tecnico per la lettura ad alta voce con Chatterbox TTS.
Devi preparare il testo ricevuto aggiungendo esclusivamente struttura, tag e respiro.

## REGOLA ASSOLUTA: LE PAROLE NON SI TOCCANO
- Non aggiungere, eliminare, sostituire, correggere, parafrasare o riordinare parole.
- Non riassumere, semplificare, censurare, completare o inventare contenuti.
- Conserva esattamente nomi, dialoghi, ripetizioni, lessico, tempi verbali e ordine originale.
- Puoi intervenire soltanto su tag ChatterText, accapo, righe vuote, spazi e
  punteggiatura strettamente necessaria alla lettura.
- Se trovi un possibile errore nel testo, lascialo invariato.

## FORMATO DELLA RISPOSTA
- Restituisci soltanto il testo ChatterText pronto da incollare.
- Non aggiungere introduzioni, commenti, CASTING, spiegazioni o riepiloghi.
- Non usare Markdown e non racchiudere il risultato in blocchi di codice.
- Separa ogni blocco con una riga vuota.
- Ogni blocco deve avere questa struttura esatta:

[inizio]
[V1_emozione]
testo originale con eventuali tag interni
[/V1_emozione]
[fine]

## DIMENSIONE E RESPIRO
- Crea blocchi semantici di circa 20-35 parole e mai oltre 240 caratteri, quando possibile.
- Non spezzare nomi propri, locuzioni, citazioni o frasi in punti innaturali.
- Un blocco corto è accettabile per una battuta breve o un effetto drammatico.
- Usa gli accapo soltanto tra elementi strutturali; usa i tag per le pause interne.
- Non mettere virgola o punto immediatamente prima di un tag pausa: il tag genera
  automaticamente la punteggiatura e il respiro necessari.

## VOCI ED EMOZIONI
- V1: narratore principale.
- V2-V7: personaggi o voci differenti, assegnati in modo coerente per tutto il testo.
- Non inventare personaggi e non cambiare voce allo stesso personaggio.
- Usa una sola voce e una sola emozione principale per blocco.
- Formato obbligatorio: [V1_calmo]...[/V1_calmo]. La chiusura deve essere identica.
- Emozioni disponibili:
  calmo | appassionato | arrabbiato | triste | ironico | sussurrato |
  riflessivo | deciso | preoccupato | gentile | serio | solenne |
  estatico | malinconico | vibrante | intimo

## PAUSE INTERNE
[p1] respiro breve | [p2] fine frase | [p3] riflessione
[b] cambio idea | [bd] climax/suspense | [cap] chiusura lunga
[e1] enfasi leggera | [e2] enfasi forte | [ep] enfasi poetica

- Inserisci le pause solo dove il significato e la sintassi originali le giustificano.
- Non aggiungere tag a ogni frase: evita una lettura frammentata o artificiale.
- Usa [e2] con parsimonia, al massimo una volta ogni 2-3 blocchi.

## GIUNZIONE TRA BLOCCHI
[join] continuità immediata | [cont] passaggio morbido
[cambio] cambio V1/V2 | [cambio3]...[cambio7] cambio verso altre voci
[para] fine paragrafo | [stacco] cambio pensiero | [lungo] pausa teatrale
[scena] cambio scena/capitolo | [dissolvenza] transizione in dissolvenza

- Il tag di giunzione va alla fine del testo ma PRIMA del tag di chiusura voce.
- Sul confine tra due blocchi usa una pausa finale oppure una giunzione, mai entrambe.
- Le pause interne possono invece essere usate normalmente nello stesso blocco.

## ESEMPIO DI SOLA STRUTTURA
[inizio]
[V1_riflessivo]
Era una sera strana[p2] il tipo di sera in cui l\'aria sembrava ferma.[para]
[/V1_riflessivo]
[fine]

[inizio]
[V2_deciso]
Non posso aspettare ancora.[cambio]
[/V2_deciso]
[fine]

## CONTROLLO OBBLIGATORIO PRIMA DELLA RISPOSTA
1. Confronta tutte le parole con l'originale: devono essere identiche e nello stesso ordine.
2. Controlla che ogni [inizio] abbia un [fine].
3. Controlla che ogni tag voce/emozione abbia una chiusura identica.
4. Controlla che pause e giunzioni siano dentro il tag voce.
5. Rimuovi qualsiasi spiegazione esterna al testo preparato.

TESTO DA PREPARARE:

[INCOLLA QUI IL TESTO]
'''

# =========================================================
# PROMPT GUIDA POETICA
# =========================================================
POETRY_PROMPT = '''# PREPARAZIONE FEDELE PER CHATTERTEXT TTS v3.0 — POESIA

Sei un editor tecnico per la lettura poetica ad alta voce con Chatterbox TTS.
Devi aggiungere struttura, respiro ed espressività senza riscrivere la poesia.

## REGOLA ASSOLUTA: LE PAROLE NON SI TOCCANO
- Non aggiungere, eliminare, sostituire, correggere, parafrasare o riordinare parole.
- Conserva esattamente versi, ripetizioni, lessico, maiuscole intenzionali e ordine originale.
- Non trasformare versi in prosa e non completare immagini o frasi sospese.
- Puoi intervenire soltanto su tag ChatterText, accapo, righe vuote, spazi e
  punteggiatura strettamente necessaria alla lettura.
- Se trovi un possibile errore, lascialo invariato.

## FORMATO DELLA RISPOSTA
- Restituisci soltanto la poesia ChatterText pronta da incollare.
- Non aggiungere spiegazioni, analisi, titoli non presenti o blocchi Markdown.
- Mantieni un verso per riga e una riga vuota tra le strofe.
- Racchiudi ogni strofa o unità espressiva in un blocco completo:

[inizio]
[V1_emozione]
versi originali con tag poetici
[/V1_emozione]
[fine]

## VOCE ED EMOZIONE
- Usa una sola voce e una sola emozione principale per blocco.
- Formato obbligatorio: [V1_malinconico]...[/V1_malinconico].
- Emozioni poetiche consigliate: solenne | estatico | malinconico | vibrante | intimo.
- Sono disponibili anche: calmo | appassionato | triste | sussurrato |
  riflessivo | gentile | serio e gli altri preset ChatterText.
- La chiusura deve coincidere esattamente con l'apertura.

## TAG POETICI
[verso] fine verso con respiro breve
[strofa] fine strofa con pausa ampia
[metro] micro-pausa metrica quasi impercettibile
[enjambement] continuità tra due versi sintatticamente legati
[cesura] pausa interna al verso
[e1] enfasi leggera | [e2] enfasi forte | [ep] enfasi poetica

- Inserisci [verso] alla fine di un verso concluso.
- Usa [enjambement] al posto di [verso] quando il senso continua nel verso seguente.
- Usa [cesura] soltanto per una pausa interna realmente suggerita dal verso.
- Usa [strofa] alla fine della strofa quando desideri silenzio.
- Usa [dissolvenza] al posto di [strofa] quando desideri una transizione sfumata.
- Non usare [strofa] e [dissolvenza] insieme sullo stesso confine.
- Non mettere punteggiatura immediatamente prima di un tag pausa poetico.
- Non sovraccaricare ogni verso con più tag.

## PAUSE STANDARD E GIUNZIONI
Sono validi anche [p1] [p2] [p3] [b] [bd] [cap], ma usali solo quando
i tag poetici non descrivono meglio il respiro.
[cont] mantiene continuità tra blocchi; [lungo] crea una pausa teatrale;
[scena] separa sezioni molto distinte.
Sul confine usa una pausa oppure una giunzione, mai entrambe.
Ogni tag operativo deve stare prima della chiusura della voce.

## ESEMPIO DI SOLA STRUTTURA
[inizio]
[V1_malinconico]
Scende la sera[cesura] senza rumore[verso]
e il vento porta via[enjambement]
l\'ultima voce[strofa]
[/V1_malinconico]
[fine]

## CONTROLLO OBBLIGATORIO PRIMA DELLA RISPOSTA
1. Confronta tutte le parole con l'originale: devono essere identiche e nello stesso ordine.
2. Controlla che versi e strofe mantengano la struttura originale.
3. Controlla che ogni [inizio] abbia un [fine].
4. Controlla che ogni tag voce/emozione abbia una chiusura identica.
5. Controlla che tutti i tag operativi siano dentro il tag voce.
6. Rimuovi qualsiasi spiegazione esterna alla poesia preparata.

POESIA DA PREPARARE:

[INCOLLA QUI LA POESIA]
'''

# =========================================================
# BUILD SCRIPT PYTHON v3.0
# =========================================================
def build_python_script(chunks, exag, cfg, temp, v1, v2, v3, v4, v5, v6, v7,
                        epreset, devmode="auto", reading_style="narrativa",
                        noise_gate_db=-50, rms_target_db=-18, trim_threshold_db=-45,
                        pause_scale=1.0, preset_scale=1.0, aggressive_clean=False,
                        natural_pauses=True, min_p=0.05,
                        top_p=1.0, repetition_penalty=1.2, seed=0):
    """
    Genera lo script Python per Chatterbox.
    natural_pauses=True: converte i tag pausa in punteggiatura+newline
                         prima di passare il testo a model.generate().
    """
    has2   = bool(v2.strip()); has3 = bool(v3.strip()); has4 = bool(v4.strip())
    has5   = bool(v5.strip()); has6 = bool(v6.strip()); has7 = bool(v7.strip())
    v2eff  = v2.strip() if has2 else v1; v3eff = v3.strip() if has3 else v1
    v4eff  = v4.strip() if has4 else v1; v5eff = v5.strip() if has5 else v1
    v6eff  = v6.strip() if has6 else v1; v7eff = v7.strip() if has7 else v1
    ep_r   = json.dumps(epreset, ensure_ascii=False, indent=4)
    emop   = "|".join(ALL_EMO)

    scene   = ["poi","quando","all'improvviso","improvvisamente","in quel momento",
               "mentre","subito dopo","intanto","nel frattempo","a quel punto","alla fine"]
    dialog  = ["disse","penso","grido","urlo","sussurro","domando","rispose","chiese",
               "mormoro","esclamo","borbotto","annuncio","replico","aggiunse","continuo","riprese"]
    emow    = ["paura","orrore","ansia","terrore","pianto","felice","gioia","triste",
               "disperato","sconvolto","agitato","sorpreso","commosso","morte","vita",
               "anima","silenzio","infinito","luce","buio","voce","cuore","sogno"]
    concsh  = ["tuttavia","eppure","nonostante","al contrario","invece","d'altra parte",
               "in realta","in verita","dunque","quindi","pertanto","di conseguenza"]
    reflc   = ["forse","chissa","davvero","possibile che","si chiese","si domando",
               "aveva senso","non aveva senso","significava","voleva dire"]
    philos  = ["verita","giustizia","anima","essere","nulla","infinito","eternita",
               "ragione","sapienza","virtu","bene","male","conoscenza","ignoranza","logos"]

    def pl(lst): return "[\n        "+" ,".join('"{}"'.format(s) for s in lst)+"\n    ]"

    if devmode == "cpu":
        devl = ["DEVICE=torch.device('cpu')", "print('Dispositivo: CPU')"]
    elif devmode == "cuda":
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

    # Funzione pauses_to_natural_text da includere nello script generato
    natural_fn = r'''
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
'''

    L = [
"# Script generato da ChatterText v3.0 + Chatterbox Multilingual V3",
"# Stile: {}  |  Pause Naturali: {}  |  Noise gate: {}dB".format(reading_style, natural_pauses, noise_gate_db),
"# RMS target: {}dB  |  Pause scale: {:.2f}x  |  Pulizia aggressiva: {}".format(rms_target_db, pause_scale, aggressive_clean),
"import os,re,sys,random,inspect,torch,torchaudio as ta,pathlib,time",
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
"print('Caricamento Chatterbox Multilingual V3...')",
"print(\"Al primo avvio il modello viene scaricato: l'operazione puo richiedere alcuni minuti.\")",
"if 't3_model' not in inspect.signature(ChatterboxMultilingualTTS.from_pretrained).parameters:",
"    print('ERRORE V3: la libreria Chatterbox installata e troppo vecchia e non supporta Multilingual V3.')",
"    exit(2)",
"try:",
"    model=ChatterboxMultilingualTTS.from_pretrained(device=DEVICE.type,t3_model='v3')",
"except Exception as e:",
"    print('ERRORE V3: impossibile caricare Multilingual V3: {}'.format(e))",
"    exit(2)",
"print('Modello su {}!'.format(DEVICE.type.upper()))",
"chunks={}".format(json.dumps(chunks, ensure_ascii=False, indent=2)),
'AUDIO_V1="2.Voci/{}"'.format(v1),
'AUDIO_V2="2.Voci/{}"'.format(v2eff),
'AUDIO_V3="2.Voci/{}"'.format(v3eff),
'AUDIO_V4="2.Voci/{}"'.format(v4eff),
'AUDIO_V5="2.Voci/{}"'.format(v5eff),
'AUDIO_V6="2.Voci/{}"'.format(v6eff),
'AUDIO_V7="2.Voci/{}"'.format(v7eff),
"HAS2={}".format(str(has2)),
"HAS3={}".format(str(has3)),
"HAS4={}".format(str(has4)),
"HAS5={}".format(str(has5)),
"HAS6={}".format(str(has6)),
"HAS7={}".format(str(has7)),
"for p,lbl,en in [(AUDIO_V1,'V1',True),(AUDIO_V2,'V2',HAS2),(AUDIO_V3,'V3',HAS3),(AUDIO_V4,'V4',HAS4),(AUDIO_V5,'V5',HAS5),(AUDIO_V6,'V6',HAS6),(AUDIO_V7,'V7',HAS7)]:",
"    if en and not os.path.exists(p): print(f'NON TROVATO [{lbl}]: {p}'); exit(1)",
"EPRESET={}".format(ep_r),
"DEF_P={{'exaggeration':{},'cfg_weight':{},'temperature':{},'top_p':{},'min_p':{}}}".format(exag,cfg,temp,top_p,min_p),
"SAMPLER_TOP_P={}".format(top_p),
"SAMPLER_MIN_P={}".format(min_p),
"REPETITION_PENALTY={}".format(repetition_penalty),
"SEED={}".format(seed),
"PAUSE_SCALE={}".format(pause_scale),
"PRESET_SCALE={}".format(preset_scale),
"NOISE_GATE_DB={}".format(noise_gate_db),
"RMS_TARGET_DB={}".format(rms_target_db),
"TRIM_DB={}".format(trim_threshold_db),
"AGGRESSIVE_CLEAN={}".format(aggressive_clean),
"NATURAL_PAUSES={}".format(natural_pauses),
natural_fn,
"PM={",
"    '[p1]':(0.18,0.03), '[p2]':(0.40,0.05), '[p3]':(0.65,0.07),",
"    '[b]': (1.00,0.10), '[bd]':(1.60,0.15), '[cap]':(2.00,0.20),",
"    '[pausa]':(0.50,0.05),'[pausa_lunga]':(1.20,0.10),'[silenzio]':(2.00,0.15),",
"    '[verso]':(0.30,0.04),'[strofa]':(1.20,0.12),'[metro]':(0.08,0.01),",
"    '[enjambement]':(0.05,0.01),'[cesura]':(0.45,0.05),",
"}",
"def gp(tag):",
"    b,s=PM.get(tag.lower(),(0.40,0.05))",
"    b=b*PAUSE_SCALE",
"    raw=random.gauss(b,s*PAUSE_SCALE)",
"    return max(b*0.60, min(raw, b*1.40))",
"JM={'[join]':(0.00,'overlap'),'[cont]':(0.12,'smooth'),",
"    '[cambio]':(0.50,'cambio'),'[cambio3]':(0.50,'cambio'),",
"    '[cambio4]':(0.50,'cambio'),'[cambio5]':(0.50,'cambio'),",
"    '[cambio6]':(0.50,'cambio'),'[cambio7]':(0.50,'cambio'),",
"    '[para]':(0.90,'silence'),'[stacco]':(1.40,'fade_sil_fade'),",
"    '[lungo]':(1.80,'fade_sil_fade'),'[scena]':(2.40,'hard'),",
"    '[dissolvenza]':(1.60,'fade_sil_fade')}",
"EP={'e1':{'exaggeration_delta':0.10,'cfg_weight_delta':-0.05},'e2':{'exaggeration_delta':0.25,'cfg_weight_delta':-0.12},'ep':{'exaggeration_delta':0.15,'cfg_weight_delta':-0.08}}",
'EN=r"{}"'.format(emop),
"PR=re.compile(r'(\\[p[123]\\]|\\[b(?:d)?\\]|\\[cap\\]|\\[pausa(?:_lunga)?\\]|\\[silenzio\\]|\\[verso\\]|\\[strofa\\]|\\[metro\\]|\\[enjambement\\]|\\[cesura\\])',re.IGNORECASE)",
"ER=re.compile(r'\\[e[12p]\\]',re.IGNORECASE)",
"JR=re.compile(r'\\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\\]',re.IGNORECASE)",
"def pc(chunk):",
"    rp=PR.findall(chunk)",
"    ps=[(p,gp(p)) for p in rp]; tp=sum(d for _,d in ps)",
"    et=ER.findall(chunk); ek=et[-1].lower().strip('[]') if et else None",
"    jt=JR.findall(chunk); jk=jt[-1].lower() if jt else None",
"    # si_meta: rimuove SOLO tag voce/emozione/enfasi/giunzioni",
"    # LASCIA i tag pausa [p1][p2][b]... intatti: servono a prepare_text_for_tts()",
"    def si_meta(t):",
"        t=ER.sub('',t); t=JR.sub('',t); return t.strip()",
"    # si_voice: rimuove anche i tag voce dal testo pulito",
"    def si_voice(t):",
"        t=re.sub(r'\\[/?(?:v1|v2|v3|v4|v5|v6|v7)(?:_'+EN+r')?\\]','',t,flags=re.IGNORECASE)",
"        return si_meta(t)",
"    m=re.search(r'\\[(v1|v2|v3|v4|v5|v6|v7)_(' +EN+r')\\]',chunk,re.IGNORECASE)",
"    if m:",
"        v,e=m.group(1).lower(),m.group(2).lower()",
"        cl=re.sub(r'\\[(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\\]','',chunk,flags=re.IGNORECASE)",
"        cl=re.sub(r'\\[/(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\\]','',cl,flags=re.IGNORECASE)",
"        return si_meta(cl),v,e,ps,tp,ek,jk",
"    m=re.search(r'\\[(v1|v2|v3|v4|v5|v6|v7)\\]',chunk,re.IGNORECASE)",
"    if m:",
"        v=m.group(1).lower()",
"        cl=re.sub(r'\\[/?(?:v1|v2|v3|v4|v5|v6|v7)\\]','',chunk,flags=re.IGNORECASE)",
"        return si_meta(cl),v,None,ps,tp,ek,jk",
"    m=re.search(r'\\[('+EN+r')\\]',chunk,re.IGNORECASE)",
"    if m:",
"        e=m.group(1).lower()",
"        cl=re.sub(r'\\[(?:'+EN+r')\\]','',chunk,flags=re.IGNORECASE)",
"        cl=re.sub(r'\\[/(?:'+EN+r')\\]','',cl,flags=re.IGNORECASE)",
"        return si_meta(cl),'v1',e,ps,tp,ek,jk",
"    return si_meta(chunk),'v1',None,ps,tp,ek,jk",
"def pp(emo,ek=None):",
"    if emo and emo in EPRESET:",
"        p=EPRESET[emo].copy()",
"        # Lo stile amplifica/attenua lo scarto del preset rispetto ai parametri base.",
"        for key,lo,hi in [('exaggeration',0.0,2.0),('cfg_weight',0.0,1.0),('temperature',0.05,2.0)]:",
"            base=DEF_P[key]; p[key]=max(lo,min(hi,base+(p[key]-base)*PRESET_SCALE))",
"        p['top_p']=max(0.0,min(1.0,p['top_p']))",
"        p['min_p']=max(0.0,min(1.0,p['min_p']))",
"    else:",
"        p=DEF_P.copy()",
"        p['top_p']=SAMPLER_TOP_P; p['min_p']=SAMPLER_MIN_P",
"    if ek and ek in EP:",
"        p['exaggeration']=min(1.0,p['exaggeration']+EP[ek]['exaggeration_delta'])",
"        p['cfg_weight']=max(0.1,p['cfg_weight']+EP[ek]['cfg_weight_delta'])",
"    return p",
"if SEED:",
"    random.seed(SEED); torch.manual_seed(SEED)",
"    if torch.cuda.is_available(): torch.cuda.manual_seed_all(SEED)",
"tc=[pc(c) for c in chunks]",
"def noise_gate(wav, sr, gate_db=NOISE_GATE_DB, hpz=80, attack_ms=8, release_ms=60):",
"    thr=10**(gate_db/20)",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    wav=ta.functional.highpass_biquad(wav, sr, cutoff_freq=hpz)",
"    env=torch.abs(wav[0])",
"    att=int(sr*attack_ms/1000); rel=int(sr*release_ms/1000)",
"    gate=torch.zeros_like(env)",
"    g=0.0",
"    for i in range(len(env)):",
"        if env[i]>thr: target=1.0",
"        else: target=0.0",
"        if target>g: g=g+(1.0-g)/max(1,att)",
"        else: g=g*(1.0-1.0/max(1,rel))",
"        gate[i]=g",
"    wav=wav*gate.unsqueeze(0)",
"    return wav",
"def rms_normalize(wav, target_db=RMS_TARGET_DB):",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    rms=torch.sqrt(torch.mean(wav**2)+1e-8)",
"    target_rms=10**(target_db/20)",
"    gain=target_rms/rms; gain=min(gain, 10.0)",
"    wav=wav*gain",
"    wav=torch.tanh(wav*0.9)*1.1",
"    return wav.clamp(-0.98, 0.98)",
"def declick(wav, sr, window_ms=3):",
"    w=int(sr*window_ms/1000)",
"    if w%2==0: w+=1",
"    if w<3 or wav.shape[-1]<w*2: return wav",
"    n=wav.shape[-1]",
"    kern=torch.ones(1,1,w)/w",
"    smoothed=torch.nn.functional.conv1d(wav.float().unsqueeze(0), kern, padding=w//2).squeeze(0)[...,:n]",
"    diff=torch.abs(wav-smoothed)",
"    thr=diff.mean()*3.0",
"    mask=(diff>thr).float()",
"    k2=int(sr*1/1000)+1",
"    if k2%2==0: k2+=1",
"    k2t=torch.ones(1,1,k2)/k2",
"    mask=torch.nn.functional.conv1d(mask.unsqueeze(0),k2t,padding=k2t.shape[-1]//2).squeeze(0).clamp(0,1)[...,:n]",
"    return wav*(1-mask)+smoothed*mask",
"def trim_silence(wav, sr, threshold_db=TRIM_DB, pad_ms=30):",
"    thr=10**(threshold_db/20)",
"    mg=int(sr*pad_ms/1000)",
"    mo=wav[0] if wav.dim()>1 else wav; en=torch.abs(mo)",
"    indices=(en>thr).nonzero(as_tuple=True)[0]",
"    if len(indices)==0: return wav",
"    s=max(0, indices[0].item()-mg); e=min(len(en), indices[-1].item()+mg)",
"    return wav[...,s:e]",
"def apply_fade(wav, sr, fade_ms=14):",
"    f=int(sr*fade_ms/1000); wav=wav.clone()",
"    wav[...,:f]*=torch.linspace(0,1,f)",
"    wav[...,-f:]*=torch.linspace(1,0,f)",
"    return wav",
"import math",
"def spectral_balance(wav, sr, presence_gain=2.5, presence_freq=3000, mud_cut_db=-2.5, mud_freq=300):",
"    wav=ta.functional.equalizer_biquad(wav, sr, center_freq=presence_freq, gain=presence_gain, Q=0.8)",
"    wav=ta.functional.equalizer_biquad(wav, sr, center_freq=mud_freq, gain=mud_cut_db, Q=0.8)",
"    return wav",
"def gentle_compressor(wav, sr, threshold_db=-20, ratio=2.5, attack_ms=8, release_ms=120, makeup_db=2.5, block_ms=10):",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    thr=10**(threshold_db/20)",
"    block=max(1,int(sr*block_ms/1000))",
"    absw=torch.abs(wav[0]); n=absw.shape[0]",
"    pad=(-n)%block",
"    if pad: absw=torch.nn.functional.pad(absw,(0,pad))",
"    blocks=absw.view(-1,block)",
"    brms=torch.sqrt(torch.mean(blocks**2,dim=1)+1e-9)",
"    att=math.exp(-block_ms/attack_ms); rel=math.exp(-block_ms/release_ms)",
"    env=torch.zeros_like(brms); level=0.0",
"    for i in range(brms.shape[0]):",
"        v=brms[i].item()",
"        level=att*level+(1-att)*v if v>level else rel*level+(1-rel)*v",
"        env[i]=level",
"    gain=torch.ones_like(env)",
"    over=env>thr",
"    gain[over]=(thr+(env[over]-thr)/ratio)/(env[over]+1e-8)",
"    gs=gain.repeat_interleave(block)[:n]",
"    if gs.shape[0]<n: gs=torch.nn.functional.pad(gs,(0,n-gs.shape[0]))",
"    makeup=10**(makeup_db/20)",
"    out=wav.clone(); out[0]=out[0]*gs*makeup",
"    return out.clamp(-0.98,0.98)",
"def full_process(wav, sr):",
"    wav=noise_gate(wav, sr)",
"    if AGGRESSIVE_CLEAN: wav=declick(wav, sr)",
"    wav=trim_silence(wav, sr)",
"    wav=spectral_balance(wav, sr)",
"    wav=gentle_compressor(wav, sr)",
"    wav=apply_fade(wav, sr)",
"    wav=rms_normalize(wav)",
"    return wav",
# --- Nuova sezione: generazione con pause naturali ---
"def prepare_text_for_tts(txt):",
"    '''",
"    v3.0: se NATURAL_PAUSES attivo, converte i tag pausa in",
"    punteggiatura + newline reali PRIMA di passare a model.generate().",
"    I tag enfasi/giunzioni vengono rimossi (già usati in parametri).",
"    '''",
"    if NATURAL_PAUSES:",
"        txt = pauses_to_natural_text(txt)",
"    else:",
"        # Vecchio comportamento: rimuovi solo i tag pausa senza conversione",
"        txt = re.sub(r'\\[(?:p[123]|b(?:d)?|cap|pausa(?:_lunga)?|silenzio|verso|strofa|metro|enjambement|cesura)\\]','',txt,flags=re.IGNORECASE)",
"    # Rimuovi eventuali tag residui (enfasi, giunzioni) che non devono andare al TTS",
"    txt = re.sub(r'\\[e[12p]\\]','',txt,flags=re.IGNORECASE)",
"    txt = re.sub(r'\\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\\]','',txt,flags=re.IGNORECASE)",
"    return txt.strip()",
"segs=[]; fail=[]",
"st=time.time()",
"print('\\n'+'='*55)",
"print('AVVIO GENERAZIONE [{}]'.format(DEVICE.type.upper()))",
"print('Pause Naturali: {}'.format('ATTIVE' if NATURAL_PAUSES else 'disattive'))",
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
"    if tp>0: print('   pausa audio: {:.2f}s (gauss x{:.2f})'.format(tp, PAUSE_SCALE))",
"    if len(txt.split())<5: print('   ATTENZIONE: chunk corto!')",
"    tts_txt = prepare_text_for_tts(txt)",
"    if NATURAL_PAUSES and tts_txt != txt:",
"        _nl_count = tts_txt.count('\\n')",
"        print('   Testo TTS ({} righe natural):'.format(_nl_count+1))",
"        for _ln in tts_txt[:120].split('\\n'):",
"            if _ln.strip(): print('     |', _ln.strip()[:70])",
"    if   vo=='v7' and HAS7: vp=AUDIO_V7",
"    elif vo=='v6' and HAS6: vp=AUDIO_V6",
"    elif vo=='v5' and HAS5: vp=AUDIO_V5",
"    elif vo=='v4' and HAS4: vp=AUDIO_V4",
"    elif vo=='v3' and HAS3: vp=AUDIO_V3",
"    elif vo=='v2' and HAS2: vp=AUDIO_V2",
"    else:                   vp=AUDIO_V1",
"    p=pp(em,ek); ok=False",
"    attempts=[dict(p), dict(exaggeration=0.0,cfg_weight=0.25,temperature=0.22,min_p=0.20,top_p=0.65), dict(exaggeration=0.0,cfg_weight=0.30,temperature=0.15,min_p=0.25,top_p=0.60)]",
"    last_err=None",
"    for attempt_i,ap in enumerate(attempts):",
"        try:",
"            wav=model.generate(tts_txt,language_id='it',audio_prompt_path=vp,",
"                exaggeration=ap['exaggeration'],cfg_weight=ap['cfg_weight'],",
"                temperature=ap['temperature'],min_p=ap['min_p'],top_p=ap['top_p'],repetition_penalty=REPETITION_PENALTY)",
"            if DEVICE.type=='cuda': wav=wav.cpu()",
"            wav=full_process(wav, model.sr)",
"            if tp>0:",
"                sil=torch.zeros((wav.shape[0],int(model.sr*tp)))",
"                wav=torch.cat([wav,sil],dim=-1)",
"            segs.append(wav); ok=True",
"            print('   OK!' if attempt_i==0 else '   Recuperato al tentativo {}!'.format(attempt_i+1))",
"            break",
"        except Exception as e:",
"            last_err=e",
"            print('   ERR tentativo {}: {} ...'.format(attempt_i+1, e))",
"    if not ok:",
"        print('   FALLITO:{}'.format(last_err)); fail.append(i)",
"if not segs: print('Nessun audio.'); exit(1)",
"if fail:",
"    print('Generazione annullata: chunk falliti {}'.format([n+1 for n in fail]))",
"    print('Nessun file parziale è stato salvato.')",
"    exit(1)",
"od=pathlib.Path('1.Output'); od.mkdir(exist_ok=True)",
"used=[]",
"for fp in od.glob('audiolibro_*.wav'):",
"    m=re.fullmatch(r'audiolibro_(\\d+)\\.wav',fp.name,re.IGNORECASE)",
"    if m: used.append(int(m.group(1)))",
"num=(max(used) if used else 0)+1",
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
"    if emo in ('riflessivo','calmo','triste','preoccupato','malinconico','solenne'): base*=1.18",
"    elif emo in ('arrabbiato','deciso','vibrante'):                                 base*=0.72",
"    elif emo in ('sussurrato','intimo'):                                            base*=1.10",
"    base=base*PAUSE_SCALE",
"    raw=random.gauss(base, sig*PAUSE_SCALE)",
"    return max(base*0.60, min(raw, base*1.40))",
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
"    ss=ss*PAUSE_SCALE",
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
"    if fa is None: fa=seg; continue",
"    jt=jl[i-1]; res=asmb(fa,seg,model.sr,jt)",
"    if res is None:",
"        if tc[i-1][4]>0:",
"            # La pausa esplicita è già stata aggiunta al segmento precedente.",
"            fa=cf(fa,seg,model.sr); js='tag-pausa'",
"        else:",
"            pau=dyn_pause(chunks[i-1], emo=tc[i-1][2])",
"            sil=torch.zeros((seg.shape[0],int(model.sr*pau)))",
"            fa=cf(fa,torch.cat([sil,seg],dim=-1),model.sr)",
"            js='auto({:.2f}s)'.format(pau)",
"    else: fa=res; js=jt if jt else 'auto'",
"    print(f'   -> join {i}: {js}')",
"fa=rms_normalize(fa)",
"ta.save(out,fa,model.sr)",
"dur=fa.shape[-1]/model.sr; tot=time.time()-st",
"print(f'\\n FILE: {out}')",
"print(f'   Durata: {dur:.1f}s ({dur/60:.1f} min)')",
"print(f'   Tempo:  {tot:.1f}s ({tot/60:.1f} min)')",
"print(f'   Device: {DEVICE.type.upper()}')",
"print(f'   Pause Naturali: {\"ATTIVE\" if NATURAL_PAUSES else \"disattive\"}')",
"voci_attive=[('V2',HAS2),('V3',HAS3),('V4',HAS4),('V5',HAS5),('V6',HAS6),('V7',HAS7)]",
"voci_str=' | '.join(n for n,a in voci_attive if a) or '-'",
"print(f'   Voci: V1 + {voci_str}')",
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
    def _dim(hex_col):
        h = hex_col.lstrip('#')
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        br,bg_,bb = 0x1a,0x1a,0x1a
        nr = int(r*0.28 + br*0.72); ng = int(g*0.28 + bg_*0.72); nb = int(b*0.28 + bb*0.72)
        return '#{:02x}{:02x}{:02x}'.format(nr,ng,nb)
    rest_bg = _dim(co)
    kw.setdefault("padx", 14); kw.setdefault("pady", 8)
    b = tk.Button(parent, text=text, command=cmd,
                  bg=rest_bg, fg=C["text"],
                  activebackground=co, activeforeground="#fff",
                  relief="flat", bd=0, cursor="hand2", font=FL, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=co, fg="#fff"))
    b.bind("<Leave>", lambda e: b.config(bg=rest_bg, fg=C["text"]))
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
        self.resizable(True, True); self.on_save = on_save
        self.vs = {}
        for emo, vals in presets.items():
            self.vs[emo] = {}
            for p in self.PARAMS:
                self.vs[emo][p] = tk.StringVar(value=str(vals.get(p, "")))
        self._build(); self.grab_set()

    def _build(self):
        tk.Label(self, text="Parametri Prosodici per Emozione", font=FH2,
                 fg=C["accent"], bg=C["bg"], pady=14).pack(fill="x")
        hdr = tk.Frame(self, bg=C["hdr_bg"]); hdr.pack(fill="x", padx=16)
        for ci, (h, w) in enumerate(zip(["Emozione"]+self.PARAMS, [14]+[13]*5)):
            tk.Label(hdr, text=h, font=FL, fg=C["accent"], bg=C["hdr_bg"],
                     width=w, anchor="center", pady=6).grid(row=0, column=ci, padx=2)
        for ri, emo in enumerate(ALL_EMO):
            bg = C["surface"] if ri%2==0 else C["surface2"]
            rf = tk.Frame(self, bg=bg); rf.pack(fill="x", padx=16, pady=1)
            tk.Label(rf, text="  "+emo, font=FL, fg=EMO_C.get(emo, C["text_dim"]),
                     bg=bg, width=14, anchor="w", pady=5).grid(row=0, column=0, padx=2)
            for ci, param in enumerate(self.PARAMS):
                tk.Entry(rf, textvariable=self.vs[emo][param], width=10,
                         bg=C["surface2"], fg=C["text"], insertbackground=C["accent"],
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=C["border"], font=FB,
                         justify="center").grid(row=0, column=ci+1, padx=4, pady=3)
        br = tk.Frame(self, bg=C["bg"], pady=14); br.pack()
        sb_btn(br, "Salva e Chiudi", self._save, color=C["success"]).pack(side="left", padx=8)
        sb_btn(br, "Ripristina", self._reset, color=C["warning"]).pack(side="left", padx=8)
        sb_btn(br, "Annulla", self.destroy, color=C["danger"]).pack(side="left", padx=8)

    def _save(self):
        r = {}
        limits = {
            "exaggeration": (0.0, 2.0), "cfg_weight": (0.0, 1.0),
            "temperature": (0.05, 2.0), "top_p": (0.0, 1.0), "min_p": (0.0, 1.0),
        }
        for emo in ALL_EMO:
            r[emo] = {}
            for p in self.PARAMS:
                try:
                    value = float(self.vs[emo][p].get())
                    lo, hi = limits[p]
                    r[emo][p] = round(max(lo, min(hi, value)), 3)
                except (TypeError, ValueError):
                    r[emo][p] = EMOTION_PRESETS[emo][p]
        self.on_save(r); self.destroy()

    def _reset(self):
        for emo in ALL_EMO:
            for p in self.PARAMS:
                self.vs[emo][p].set(str(EMOTION_PRESETS[emo][p]))

# =========================================================
# APP PRINCIPALE
# =========================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatterText v3.0 + Multilingual V3")
        self.geometry("1100x980"); self.minsize(900,700)
        self.configure(bg=C["bg"])
        self._app_icon = None
        self._set_app_icon()
        self._configure_ttk_style()
        self.chunks = []; self.chunk_vars = []; self.script_path = None
        self.epreset = {k: v.copy() for k, v in EMOTION_PRESETS.items()}
        self._proc = None; self._t0 = None
        self.vwords   = tk.StringVar(value="0")
        self.vchars   = tk.StringVar(value="0")
        self.vchunks  = tk.StringVar(value="0")
        self.verrs    = tk.StringVar(value="0")
        self.vdev     = tk.StringVar(value="auto")
        self.vsound   = tk.BooleanVar(value=True)
        self.vreadstyle  = tk.StringVar(value="narrativa")
        self.vaggclean   = tk.BooleanVar(value=False)
        self.vnatpauses  = tk.BooleanVar(value=True)   # nuovo v3.0
        self._build_ui(); self._detect_device()

    # ---- LAYOUT ----
    def _configure_ttk_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dark.Vertical.TScrollbar",
                        background="#505050", troughcolor=C["bg"],
                        bordercolor=C["bg"], lightcolor="#505050",
                        darkcolor="#505050", arrowcolor=C["text"])
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", "#666666"), ("pressed", "#737373")])
        style.configure("TCombobox", fieldbackground=C["surface2"],
                        background="#505050", foreground=C["text"],
                        arrowcolor=C["text"], bordercolor=C["border"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", C["surface2"])],
                  foreground=[("readonly", C["text"])])

    def _darken_text_scrollbar(self, widget):
        try:
            widget.vbar.config(bg="#505050", activebackground="#666666",
                               troughcolor=C["surface"], bd=0, relief="flat",
                               highlightthickness=0, width=13)
        except (AttributeError, tk.TclError):
            pass

    def _set_app_icon(self):
        app_dir = pathlib.Path(__file__).resolve().parent
        png_path = app_dir / "chattertext_icon.png"
        ico_path = app_dir / "favicon.ico"
        try:
            if png_path.exists():
                self._app_icon = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, self._app_icon)
            elif ico_path.exists() and sys.platform == "win32":
                self.iconbitmap(default=str(ico_path))
        except tk.TclError:
            pass

    def _build_ui(self):
        canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        scr    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview,
                               style="Dark.Vertical.TScrollbar")
        self.sf = tk.Frame(canvas, bg=C["bg"])
        self.sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._cw = canvas.create_window((0,0), window=self.sf, anchor="nw")
        def _rsz(e):
            cw = min(e.width, 1080); x = (e.width-cw)//2
            canvas.itemconfig(self._cw, width=cw); canvas.coords(self._cw, x, 0)
        canvas.bind("<Configure>", _rsz)
        canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side="left", fill="both", expand=True); scr.pack(side="right", fill="y")
        self.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        r = self.sf
        self._hdr(r); self._style_sec(r)
        self._inp_sec(r)
        self._voices_sec(r)
        self._param_sec(r)
        self._action_bar(r)
        self._stats_sec(r); self._log_sec(r); self._chunks_sec(r)
        self._dev_sec(r)
        self._footer(r)

    def _action_bar(self, r):
        sec = self._sec(r, "Azioni")
        br = sf(sec); br.pack(fill="x", pady=(8,0))
        b_gen = tk.Button(br, text=">> Genera Audio", command=self.run_chatterbox,
                          bg="#1a3d2b", fg=C["text"],
                          activebackground=C["success"], activeforeground="#fff",
                          relief="flat", bd=0, cursor="hand2",
                          font=("Segoe UI",11,"bold"), padx=26, pady=12)
        b_gen.pack(side="left", padx=(0,8))
        b_gen.bind("<Enter>", lambda e: b_gen.config(bg=C["success"], fg="#fff"))
        b_gen.bind("<Leave>", lambda e: b_gen.config(bg="#1a3d2b", fg=C["text"]))
        sb_btn(br, "Analizza e Processa", self.process, color=C["accent2"]).pack(side="left", padx=(0,8))
        sb_btn(br, "Incolla", self.paste_text, color="#6c5ce7").pack(side="left", padx=(0,8))
        self.stopbtn = sb_btn(br, "■ Stop", self._stop, color=C["danger"])
        self.stopbtn.pack(side="left", padx=(0,8))
        self.stopbtn.config(state="disabled")
        sb_btn(br, "Cancella", self.clear_all, color="#555555").pack(side="left")

    def _sec(self, parent, title):
        o = tk.Frame(parent, bg=C["bg"], padx=18, pady=10); o.pack(fill="x")
        tk.Label(o, text=title, font=FH2, fg=C["accent"], bg=C["bg"]).pack(anchor="w", pady=(0,8))
        i = tk.Frame(o, bg=C["surface"], bd=0, highlightthickness=1,
                     highlightbackground=C["border"], padx=20, pady=16)
        i.pack(fill="x"); return i

    def _le(self, parent, label, default, wide=False):
        g = sf(parent); g.pack(side="left", padx=(0,16))
        tk.Label(g, text=label, font=FL, fg=C["accent"], bg=C["surface"]).pack(anchor="w")
        v = tk.StringVar(value=default)
        se(g, width=30 if wide else 10, textvariable=v).pack(anchor="w", pady=(2,0))
        return v

    def _hdr(self, r):
        h = tk.Frame(r, bg="#332f2c", pady=24); h.pack(fill="x")
        title_row = tk.Frame(h, bg="#332f2c"); title_row.pack(fill="x", padx=28)
        if self._app_icon is not None:
            tk.Label(title_row, image=self._app_icon, bg="#332f2c").pack(side="left", padx=(0,12))
        title_text = tk.Frame(title_row, bg="#332f2c"); title_text.pack(side="left")
        tk.Label(title_text, text="ChatterText", font=FH1, fg="#fff", bg="#332f2c",
                 anchor="w").pack(fill="x")
        tk.Label(title_text, text="Analizza e prepara il testo per Chatterbox TTS",
                 font=FB, fg=C["text_dim"], bg="#332f2c", anchor="w").pack(fill="x", pady=(4,0))
        tk.Label(title_text,
                 text="v3.0 + V3  |  Pause Naturali  |  4 Stili  |  Tag Poetici  |  Post-proc Audio  |  7 Voci",
                 font=FS, fg=C["natural"], bg="#332f2c", anchor="w").pack(fill="x", pady=(2,0))

    def _dev_sec(self, r):
        sec = self._sec(r, "Dispositivo di Calcolo")
        top = sf(sec); top.pack(fill="x", pady=(0,10))
        self.badge_var = tk.StringVar(value="Rilevamento...")
        self.badge = tk.Label(top, textvariable=self.badge_var, font=FL,
                              fg="#fff", bg=C["cpu"], padx=12, pady=6)
        self.badge.pack(side="left", padx=(0,20))
        sf2 = sf(top); sf2.pack(side="left")
        tk.Label(sf2, text="Modalita:", font=FL, fg=C["accent"], bg=C["surface"]).pack(side="left", padx=(0,8))
        for val, lbl in [("auto","Auto"),("cuda","Forza GPU"),("cpu","Forza CPU")]:
            tk.Radiobutton(sf2, text=lbl, variable=self.vdev, value=val, font=FB,
                           fg=C["text"], bg=C["surface"], selectcolor=C["surface2"],
                           activeforeground=C["accent"], activebackground=C["surface"],
                           cursor="hand2").pack(side="left", padx=6)
        tk.Label(sec, text="Chatterbox Multilingual V3 attivo: piu stabilita, meno ripetizioni e pause naturali invariate.",
                 font=FS, fg=C["text_dim"], bg=C["surface"]).pack(anchor="w", pady=(0,4))
        nf = sf(top); nf.pack(side="right")
        tk.Checkbutton(nf, text="Suono fine generazione", variable=self.vsound,
                       font=FB, fg=C["text"], bg=C["surface"], selectcolor=C["surface2"],
                       activeforeground=C["accent"], activebackground=C["surface"],
                       cursor="hand2").pack(side="left")
        sb_btn(nf, "Test", lambda: threading.Thread(target=play_sound, daemon=True).start(),
               color=C["text_dim"]).pack(side="left", padx=(8,0))

    def _style_sec(self, r):
        sec = self._sec(r, "Stile di Lettura")
        sf_top = sf(sec); sf_top.pack(fill="x", pady=(0,12))
        self._style_btns = {}
        for key, st in READING_STYLES.items():
            col = st["color"]
            btn = sb_btn(sf_top, "{} {}".format(
                {"narrativa":"📖","poesia":"✒","teatro":"🎭","audiolibro_lungo":"🎧"}.get(key,""),
                st["label"]
            ), lambda k=key: self._set_style(k), color=col, padx=18, pady=10)
            btn.pack(side="left", padx=(0,8))
            self._style_btns[key] = btn

        self.style_info_f = tk.Frame(sec, bg="#0d1a0d", highlightthickness=1,
                                     highlightbackground=C["success"], padx=14, pady=10)
        self.style_info_f.pack(fill="x", pady=(0,10))
        self.style_name_lbl = tk.Label(self.style_info_f, text="Narrativa",
                                       font=FH2, fg=C["success"], bg="#0d1a0d", anchor="w")
        self.style_name_lbl.pack(fill="x")
        self.style_desc_lbl = tk.Label(self.style_info_f,
                                       text=READING_STYLES["narrativa"]["desc"],
                                       font=FB, fg=C["text_dim"], bg="#0d1a0d", anchor="w")
        self.style_desc_lbl.pack(fill="x")
        self.style_notes_lbl = tk.Label(self.style_info_f,
                                        text=READING_STYLES["narrativa"]["notes"],
                                        font=FS, fg=C["warning"], bg="#0d1a0d", anchor="w")
        self.style_notes_lbl.pack(fill="x")
        self.style_scale_lbl = tk.Label(self.style_info_f, text="",
                                        font=FS, fg=C["natural"], bg="#0d1a0d", anchor="w")
        self.style_scale_lbl.pack(fill="x", pady=(3,0))

        pf = sf(sec); pf.pack(fill="x", pady=(4,0))
        tk.Label(pf, text="Post-processing:", font=FL, fg=C["accent"], bg=C["surface"]).pack(side="left", padx=(0,12))
        self.vng  = self._le(pf, "Noise gate (dB)", "-50")
        self.vrms = self._le(pf, "RMS target (dB)", "-18")
        self.vtrim = self._le(pf, "Trim threshold (dB)", "-45")
        tk.Checkbutton(pf, text="Pulizia aggressiva\n(de-click)", variable=self.vaggclean,
                       font=FS, fg=C["warning"], bg=C["surface"], selectcolor=C["surface2"],
                       activeforeground=C["warning"], activebackground=C["surface"],
                       cursor="hand2").pack(side="left", padx=(12,0))

        # --- NUOVO v3.0: Pause Naturali checkbox ---
        npf = sf(sec); npf.pack(fill="x", pady=(12,0))
        np_frame = tk.Frame(npf, bg="#0a1a0a", highlightthickness=1,
                            highlightbackground=C["natural"], padx=14, pady=10)
        np_frame.pack(fill="x")
        np_top = tk.Frame(np_frame, bg="#0a1a0a"); np_top.pack(fill="x")
        tk.Checkbutton(np_top, text="🎙 Pause Naturali (v3.0) — CONSIGLIATO",
                       variable=self.vnatpauses,
                       font=("Segoe UI",10,"bold"), fg=C["natural"], bg="#0a1a0a",
                       selectcolor="#0a1a0a", activeforeground=C["natural"],
                       activebackground="#0a1a0a", cursor="hand2"
                       ).pack(side="left")
        tk.Label(np_top,
                 text="  Converte i tag pausa in punteggiatura+newline prima di Chatterbox",
                 font=FS, fg=C["text_dim"], bg="#0a1a0a").pack(side="left", padx=(8,0))
        np_desc = tk.Frame(np_frame, bg="#0a1a0a"); np_desc.pack(fill="x", pady=(6,0))
        pause_examples = [
            ("[p1] → virgola+↵", C["natural"]),
            ("[p2] → punto+↵",   "#74b9ff"),
            ("[b]  → punto+↵↵",  "#00b894"),
            ("[bd] → punto+↵↵↵", "#e84357"),
            ("[verso] → virgola+↵", "#9b59b6"),
            ("[strofa] → punto+↵↵", "#6c3483"),
        ]
        for txt, col in pause_examples:
            tk.Label(np_desc, text=txt, font=("Courier New",8,"bold"),
                     fg=col, bg="#0a1a0a", padx=6, pady=2).pack(side="left", padx=2)
        tk.Label(np_frame,
                 text="Le pause audio in secondi vengono mantenute: i due sistemi si sommano per la massima naturalezza.",
                 font=FS, fg=C["warning"], bg="#0a1a0a").pack(anchor="w", pady=(4,0))

        prf = sf(sec); prf.pack(fill="x", pady=(10,0))
        sb_btn(prf, "Copia Prompt NARRATIVA", lambda: self._copy_prompt("narrativa"),
               color=C["style_narr"]).pack(side="left", padx=(0,8))
        sb_btn(prf, "Copia Prompt POESIA", lambda: self._copy_prompt("poesia"),
               color=C["style_poesia"]).pack(side="left", padx=(0,8))
        sb_btn(prf, "Salva entrambi", self._save_all_prompts,
               color=C["text_dim"]).pack(side="left", padx=(0,8))
        self.guide_toggle_btn = sb_btn(prf, "▾ Mostra Guida Tag", self._toggle_guide,
                                       color="#2d6073")
        self.guide_toggle_btn.pack(side="left")

        self._guide_sec(sec)
        self.guide_outer.pack_forget()

        self._set_style("narrativa")

    def _set_style(self, key):
        self.vreadstyle.set(key)
        st = READING_STYLES[key]; col = st["color"]
        self.style_name_lbl.config(text=st["label"], fg=col)
        self.style_desc_lbl.config(text=st["desc"])
        self.style_notes_lbl.config(text=st["notes"])
        self.style_scale_lbl.config(text="Intensità preset emotivi: {:.2f}x  •  Durata pause: {:.2f}x".format(
            st["preset_scale"], st["pause_scale"]))
        self.style_info_f.config(highlightbackground=col)
        if hasattr(self, 'vexag'):
            self.vexag.set(str(st["exaggeration"]))
            self.vcfg.set(str(st["cfg_weight"]))
            self.vtemp.set(str(st["temperature"]))
        if hasattr(self, 'vminp'):
            self.vminp.set(str(st["min_p"]))
            self.vtopp.set(str(st["top_p"]))
        if hasattr(self, 'vng'):
            self.vng.set(str(st["noise_gate_db"]))
            self.vrms.set(str(st["rms_target_db"]))
            self.vtrim.set(str(st["trim_threshold_db"]))

    def _copy_prompt(self, style):
        if style == "poesia":
            self.clipboard_clear(); self.clipboard_append(POETRY_PROMPT)
            messagebox.showinfo("Copiato!", "Prompt POESIA v3.0 copiato!")
        else:
            self.clipboard_clear(); self.clipboard_append(GUIDE_PROMPT)
            messagebox.showinfo("Copiato!", "Prompt NARRATIVA v3.0 copiato!")

    def _save_all_prompts(self):
        default = pathlib.Path(self.vdir.get() if hasattr(self,'vdir') else str(pathlib.Path.cwd()))
        initial = default if default.is_dir() else pathlib.Path(__file__).resolve().parent
        selected = filedialog.askdirectory(title="Scegli dove salvare i prompt v3.0",
                                            initialdir=str(initial))
        if not selected:
            return
        dest = pathlib.Path(selected)
        try:
            dest.mkdir(parents=True, exist_ok=True)
            p1 = dest / "PROMPT_NARRATIVA_v3.0.txt"
            p2 = dest / "PROMPT_POESIA_v3.0.txt"
            p1.write_text(GUIDE_PROMPT, encoding="utf-8")
            p2.write_text(POETRY_PROMPT, encoding="utf-8")
        except OSError as ex:
            messagebox.showerror("Salvataggio non riuscito", "Impossibile salvare i prompt:\n{}".format(ex))
            return
        messagebox.showinfo("Prompt salvati", "File aggiornati salvati in:\n{}\n\n• {}\n• {}".format(
            dest, p1.name, p2.name))

    def _inp_sec(self, r):
        sec = self._sec(r, "Testo")
        emo_bar = tk.Frame(sec, bg="#111827", highlightthickness=1,
                           highlightbackground="#3b4a67", padx=12, pady=9)
        emo_bar.pack(fill="x", pady=(0,10))
        tk.Label(emo_bar, text="Preset emotivo nel testo", font=FL,
                 fg=C["accent"], bg="#111827").pack(side="left", padx=(0,12))
        tk.Label(emo_bar, text="Voce", font=FS, fg=C["text_dim"],
                 bg="#111827").pack(side="left", padx=(0,4))
        self.vtagvoice = tk.StringVar(value="V1")
        voice_box = ttk.Combobox(emo_bar, textvariable=self.vtagvoice,
                                 values=["V{}".format(i) for i in range(1,8)],
                                 width=5, state="readonly")
        voice_box.pack(side="left", padx=(0,10))
        tk.Label(emo_bar, text="Emozione", font=FS, fg=C["text_dim"],
                 bg="#111827").pack(side="left", padx=(0,4))
        self.vtagemotion = tk.StringVar(value="calmo")
        emotion_box = ttk.Combobox(emo_bar, textvariable=self.vtagemotion,
                                   values=ALL_EMO, width=16, state="readonly")
        emotion_box.pack(side="left", padx=(0,10))
        sb_btn(emo_bar, "Applica alla selezione", self.apply_emotion_tag,
               color="#8e44ad", padx=12, pady=5).pack(side="left")
        tk.Label(emo_bar, text="Se non selezioni testo, inserisce i tag nel punto del cursore.",
                 font=FS, fg=C["text_dim"], bg="#111827").pack(side="left", padx=(10,0))
        tag_bar = tk.Frame(sec, bg="#10201d", highlightthickness=1,
                           highlightbackground="#285c50", padx=12, pady=8)
        tag_bar.pack(fill="x", pady=(0,10))
        tk.Label(tag_bar, text="Altri tag", font=FL, fg=C["natural"],
                 bg="#10201d").pack(side="left", padx=(0,12))
        self.vquicktag = tk.StringVar(value="[p2]")
        quick_box = ttk.Combobox(tag_bar, textvariable=self.vquicktag,
                                 values=QUICK_TAGS, width=19, state="readonly")
        quick_box.pack(side="left", padx=(0,8))
        sb_btn(tag_bar, "Inserisci tag", self.insert_quick_tag,
               color="#168a74", padx=12, pady=5).pack(side="left", padx=(0,10))
        tk.Label(tag_bar, text="Pause • enfasi • giunzioni • poesia • blocco [inizio]/[fine]",
                 font=FS, fg=C["text_dim"], bg="#10201d").pack(side="left")
        self.txt = scrolledtext.ScrolledText(
            sec, height=14,
            bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", bd=0,
            font=FM, wrap="word",
            highlightthickness=1, highlightbackground=C["border"]
        )
        self._darken_text_scrollbar(self.txt)
        self.txt.pack(fill="x", pady=(0,10))
        self.txt.insert("1.0", "Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.txt.bind("<FocusIn>", lambda e: self.txt.delete("1.0","end")
                      if "Incolla qui" in self.txt.get("1.0","end-1c") else None)
        self.vcc = tk.StringVar(value="0 / 10000")
        tk.Label(sec, textvariable=self.vcc, font=FS, fg=C["text_dim"],
                 bg=C["surface"], anchor="e").pack(fill="x")
        self.txt.bind("<KeyRelease>", lambda e: self.vcc.set(
            "{} / 10000".format(len(self.txt.get("1.0","end-1c")))))

    def _param_sec(self, r):
        sec = self._sec(r, "Parametri di Generazione")
        r1 = sf(sec); r1.pack(fill="x", pady=(0,10))
        self.vminw = self._le(r1, "Min parole/chunk", "20")
        self.vmaxw = self._le(r1, "Max parole/chunk", "40")
        self.vmaxc = self._le(r1, "Max caratteri", "240")

        adv_head = sf(sec); adv_head.pack(fill="x", pady=(2,0))
        self.advanced_param_btn = sb_btn(adv_head, "▾ Mostra parametri avanzati",
                                         self._toggle_advanced_params, color="#596780",
                                         padx=12, pady=6)
        self.advanced_param_btn.pack(side="left")
        tk.Label(adv_head, text="I valori consigliati vengono impostati automaticamente dallo stile di lettura.",
                 font=FS, fg=C["text_dim"], bg=C["surface"]).pack(side="left", padx=(10,0))

        self.advanced_param_frame = sf(sec)
        self.advanced_param_frame.pack(fill="x", pady=(10,0))
        r3 = sf(self.advanced_param_frame); r3.pack(fill="x", pady=(0,10))
        self.vexag = self._le(r3, "Exaggeration", "0.50")
        self.vcfg  = self._le(r3, "CFG Weight", "0.58")
        self.vtemp = self._le(r3, "Temperature", "0.60")
        self.vminp = self._le(r3, "Min-P", "0.05")
        self.vtopp = self._le(r3, "Top-P", "1.00")
        self.vrep  = self._le(r3, "Anti-ripetizioni", "1.20")
        self.vseed = self._le(r3, "Seed (0 casuale)", "0")
        tk.Label(self.advanced_param_frame,
                 text="I preset emotivi si applicano direttamente nella sezione Testo.",
                 font=FS, fg=C["text_dim"], bg=C["surface"], anchor="w").pack(fill="x")
        self.advanced_param_frame.pack_forget()
        self._set_style(self.vreadstyle.get())

    def _toggle_advanced_params(self):
        if self.advanced_param_frame.winfo_manager():
            self.advanced_param_frame.pack_forget()
            self.advanced_param_btn.config(text="▾ Mostra parametri avanzati")
        else:
            self.advanced_param_frame.pack(fill="x", pady=(10,0))
            self.advanced_param_btn.config(text="▴ Nascondi parametri avanzati")

    def _voices_sec(self, r):
        sec = self._sec(r, "Voci e Cartella Chatterbox")
        r2 = sf(sec); r2.pack(fill="x", pady=(0,4))
        self.vv1 = self._le(r2, "Voce 1 - Narratore (2.Voci/)", "1Opier.wav", wide=True)
        self.vv2 = self._le(r2, "Voce 2 - Personaggio B (opz.)", "", wide=True)
        self.vv3 = self._le(r2, "Voce 3 - Personaggio C (opz.)", "", wide=True)
        r2b = sf(sec); r2b.pack(fill="x", pady=(0,4))
        self.vv4 = self._le(r2b, "Voce 4 - Antagonista (opz.)", "", wide=True)
        self.vv5 = self._le(r2b, "Voce 5 - Narratore esterno (opz.)", "", wide=True)
        r2c = sf(sec); r2c.pack(fill="x", pady=(0,10))
        self.vv6 = self._le(r2c, "Voce 6 - Pers. minore (opz.)", "", wide=True)
        self.vv7 = self._le(r2c, "Voce 7 - Pers. minore (opz.)", "", wide=True)
        tk.Label(r2c, text="V6/V7: se vuote → fallback V1", font=FS,
                 fg=C["v6"], bg=C["surface"]).pack(side="left", padx=(8,0), anchor="s", pady=(0,4))
        gv = sf(r2c); gv.pack(side="right", padx=(8,0), anchor="s")
        sb_btn(gv, "Verifica voci", self._verify_voices, color=C["text_dim"]).pack(pady=(18,0))

        r4 = sf(sec); r4.pack(fill="x", pady=(0,14))
        tk.Label(r4, text="Cartella Chatterbox:", font=FL, fg=C["accent"], bg=C["surface"]).pack(side="left", padx=(0,8))
        try:
            _app_dir = str(pathlib.Path(__file__).resolve().parent)
        except NameError:
            _app_dir = str(pathlib.Path.cwd())
        self.vdir = tk.StringVar(value=_app_dir)
        se(r4, width=55, textvariable=self.vdir).pack(side="left", padx=(0,8))
        sb_btn(r4, "Sfoglia", self._browse, color=C["text_dim"]).pack(side="left")

    def _verify_voices(self):
        base = pathlib.Path(self.vdir.get()) / "2.Voci"
        res = []
        for v, lbl, ruolo in [
            (self.vv1,"V1","Narratore"),
            (self.vv2,"V2","Personaggio B"),
            (self.vv3,"V3","Personaggio C"),
            (self.vv4,"V4","Antagonista"),
            (self.vv5,"V5","Narratore esterno"),
            (self.vv6,"V6","Pers. minore (->V1 se vuota)"),
            (self.vv7,"V7","Pers. minore (->V1 se vuota)"),
        ]:
            fn = v.get().strip()
            if not fn:
                res.append("  -- {} ({}) - non specificata".format(lbl, ruolo)); continue
            p = base / fn
            if p.exists():
                res.append("  OK {} ({}) - {} ({} KB)".format(lbl, ruolo, fn, p.stat().st_size//1024))
            else:
                res.append("  NO MANCANTE {} ({}) - {}".format(lbl, ruolo, p))
        messagebox.showinfo("Verifica Voci", "\n".join(res))

    def _stats_sec(self, r):
        self.stats = self._sec(r, "Statistiche"); self.stats.pack_forget()
        cards = sf(self.stats); cards.pack(fill="x")
        for ci in range(4): cards.columnconfigure(ci, weight=1)
        for ci, (v,l) in enumerate([(self.vwords,"Parole"),(self.vchars,"Caratteri"),
                                     (self.vchunks,"Chunk"),(self.verrs,"Problemi")]):
            stat_card(cards, v, l).grid(row=0, column=ci, sticky="ew", padx=6, pady=4)
        self.tag_lbl = tk.Label(self.stats, text="", font=FB, fg=C["warning"], bg=C["surface"], pady=6)
        self.tag_lbl.pack()
        self.err_box = tk.Text(self.stats, height=4, bg=C["surface2"], fg=C["warning"],
                               font=FS, relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=C["border"], state="disabled", wrap="word")
        self.err_box.pack(fill="x", pady=(8,0))

    def _log_sec(self, r):
        self.logsec = self._sec(r, "Output"); self.logsec.pack_forget()
        pf = sf(self.logsec); pf.pack(fill="x", pady=(0,8))
        self.progv = tk.DoubleVar(value=0)
        sty = ttk.Style(); sty.theme_use("default")
        sty.configure("G.Horizontal.TProgressbar", troughcolor=C["surface2"],
                       background=C["success"], darkcolor=C["success"],
                       lightcolor=C["success"], bordercolor=C["border"])
        ttk.Progressbar(pf, variable=self.progv, maximum=100,
                        style="G.Horizontal.TProgressbar", length=400
                        ).pack(side="left", fill="x", expand=True, padx=(0,10))
        self.vprog = tk.StringVar(value="In attesa...")
        tk.Label(pf, textvariable=self.vprog, font=FS, fg=C["text_dim"], bg=C["surface"]).pack(side="left")
        er = sf(self.logsec); er.pack(fill="x", pady=(0,6))
        self.veta  = tk.StringVar(value="")
        self.vdevl = tk.StringVar(value="")
        tk.Label(er, textvariable=self.veta,  font=FS, fg=C["warning"], bg=C["surface"]).pack(side="left")
        tk.Label(er, textvariable=self.vdevl, font=FS, fg=C["gpu"],     bg=C["surface"]).pack(side="right")
        self.log = scrolledtext.ScrolledText(
            self.logsec, height=20,
            bg="#050505", fg=C["success"],
            font=("Courier New",9), relief="flat", bd=0, state="disabled",
            highlightthickness=1, highlightbackground=C["border"]
        )
        self._darken_text_scrollbar(self.log)
        self.log.pack(fill="x")

    def _chunks_sec(self, r):
        self.chunksec = self._sec(r, "Chunk Generati"); self.chunksec.pack_forget()
        br = sf(self.chunksec); br.pack(fill="x", pady=(0,14))
        sb_btn(br, "Salva Script .py", self.save_script, color=C["accent2"]).pack(side="left", padx=(0,10))
        sb_btn(br, "Copia Tutti", self.copy_all, color=C["text_dim"]).pack(side="left")
        self.cbox = sf(self.chunksec); self.cbox.pack(fill="x")

    def _guide_sec(self, r):
        outer = tk.Frame(r, bg=C["surface"], pady=12)
        self.guide_outer = outer
        outer.pack(fill="x", pady=(10,0))
        hr = tk.Frame(outer, bg=C["surface"]); hr.pack(fill="x", pady=(0,8))
        tk.Label(hr, text="Guida Tag — ChatterText v3.0", font=FH2,
                 fg=C["accent"], bg=C["surface"]).pack(side="left")
        tk.Label(hr, text="Riferimento sincronizzato con i tag elaborati dal programma",
                 font=FS, fg=C["text_dim"], bg=C["surface"]).pack(side="right")
        inner = tk.Frame(outer, bg=C["surface"], bd=0, highlightthickness=1,
                         highlightbackground=C["border"], padx=20, pady=16)
        inner.pack(fill="x")

        # --- NUOVA SEZIONE: Pause Naturali ---
        np_sec = tk.Frame(inner, bg="#0a1a0a", highlightthickness=1,
                          highlightbackground=C["natural"], padx=14, pady=10)
        np_sec.pack(fill="x", pady=(0,14))
        tk.Label(np_sec, text="PAUSE NATURALI v3.0 — come i tag pausa diventano testo per Chatterbox",
                 font=FL, fg=C["natural"], bg="#0a1a0a").pack(anchor="w")
        np_grid = tk.Frame(np_sec, bg="#0a1a0a"); np_grid.pack(fill="x", pady=(8,0))
        np_data = [
            ("[metro]",      "→  spazio",       "quasi zero",      "#a9cce3"),
            ("[enjambement]","→  spazio",        "scorrimento",     "#d7bde2"),
            ("[p1]",         "→  virgola + ↵",   "respiro breve",   C["natural"]),
            ("[verso]",      "→  virgola + ↵",   "fine verso",      "#9b59b6"),
            ("[cesura]",     "→  virgola + ↵",   "pausa interna",   "#7d3c98"),
            ("[p2]",         "→  punto   + ↵",   "fine frase",      "#74b9ff"),
            ("[pausa]",      "→  punto   + ↵",   "pausa media",     "#4a90e2"),
            ("[p3]",         "→  punto   + ↵↵",  "riflessione",     "#8e44ad"),
            ("[b]",          "→  punto   + ↵↵",  "cambio idea",     "#27ae60"),
            ("[strofa]",     "→  punto   + ↵↵",  "fine strofa",     "#6c3483"),
            ("[pausa_lunga]", "→  punto   + ↵↵", "pausa lunga",     "#3867a8"),
            ("[bd]",         "→  punto   + ↵↵↵", "climax",          "#e84357"),
            ("[cap]",        "→  punto   + ↵↵↵", "capoverso",       "#e67e22"),
            ("[silenzio]",   "→  punto   + ↵↵↵", "silenzio",        "#636e72"),
        ]
        for ci, (tag, conv, desc, col) in enumerate(np_data):
            row = ci // 4; col_i = ci % 4
            cell = tk.Frame(np_grid, bg="#111", highlightthickness=1, highlightbackground=col)
            cell.grid(row=row, column=col_i, padx=3, pady=3, sticky="ew")
            np_grid.columnconfigure(col_i, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",8,"bold"),
                     fg=col, bg="#111", padx=5, pady=3).pack(anchor="w")
            tk.Label(cell, text=conv, font=("Courier New",8),
                     fg="#fff", bg="#111", padx=5).pack(anchor="w")
            tk.Label(cell, text=desc, font=FS,
                     fg=C["text_dim"], bg="#111", padx=5, pady=2).pack(anchor="w")
        tk.Label(np_sec,
                 text="La punteggiatura NON viene duplicata se già presente nel testo.\n"
                      "Pause audio in secondi MANTENUTE: i due sistemi si sommano.\n"
                      "Il log di generazione mostra il testo TTS riga per riga (visibile durante la generazione).",
                 font=FS, fg=C["text_dim"], bg="#0a1a0a", justify="left").pack(anchor="w", pady=(8,0))

        cols = tk.Frame(inner, bg=C["surface"]); cols.pack(fill="x")
        cols.columnconfigure(0, weight=1); cols.columnconfigure(1, weight=1)
        lc = tk.Frame(cols, bg=C["surface"]); lc.grid(row=0, column=0, sticky="nw", padx=(0,16))
        rc = tk.Frame(cols, bg=C["surface"]); rc.grid(row=0, column=1, sticky="nw")

        def sl(parent, txt):
            tk.Label(parent, text=txt, font=FL, fg=C["accent"], bg=C["surface"], pady=6).pack(anchor="w")

        def tg(parent, data):
            f = tk.Frame(parent, bg=C["surface"]); f.pack(fill="x", pady=(0,10))
            for ci, (tag, col, desc) in enumerate(data):
                cell = tk.Frame(f, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
                cell.grid(row=0, column=ci, padx=3, pady=2, sticky="ew"); f.columnconfigure(ci, weight=1)
                tk.Label(cell, text=tag, font=("Courier New",9,"bold"), fg=col,
                         bg=C["surface2"], pady=4, padx=5).pack()
                tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                         bg=C["surface2"], padx=4, pady=2, justify="center").pack()

        sl(lc, "STILI DI LETTURA")
        for key, st in READING_STYLES.items():
            sf3 = tk.Frame(lc, bg=C["surface2"], highlightthickness=1,
                           highlightbackground=st["color"], padx=10, pady=5)
            sf3.pack(fill="x", pady=1)
            tk.Label(sf3, text=st["label"], font=FL, fg=st["color"], bg=C["surface2"],
                     width=16, anchor="w").pack(side="left")
            tk.Label(sf3, text=st["notes"], font=FS, fg=C["text_dim"],
                     bg=C["surface2"]).pack(side="left", padx=(8,0))

        sl(lc, "TAG VOCE")
        tg(lc, [("[v1]",C["v1"],"Narratore"),("[v2]",C["v2"],"Pers.B"),("[v3]",C["v3"],"Pers.C"),
                ("[v4]",C["v4"],"Antag."),("[v5]",C["v5"],"Narr.est.")])
        tg(lc, [("[v6]",C["v6"],"->V1"),("[v7]",C["v7"],"->V1")])

        sl(lc, "EMOZIONI")
        br2 = tk.Frame(lc, bg=C["surface"]); br2.pack(fill="x", pady=(0,4))
        for emo in ["solenne","estatico","malinconico","vibrante","intimo"]:
            tk.Label(br2, text=" {} ".format(emo), font=FS, fg="#fff",
                     bg=EMO_C.get(emo, C["text_dim"]), padx=4, pady=2).pack(side="left", padx=2, pady=2)
        br3 = tk.Frame(lc, bg=C["surface"]); br3.pack(fill="x", pady=(0,10))
        for emo in ["calmo","appassionato","arrabbiato","triste","ironico",
                    "sussurrato","riflessivo","deciso","preoccupato","gentile","serio"]:
            tk.Label(br3, text=" {} ".format(emo), font=FS, fg="#fff",
                     bg=EMO_C.get(emo, C["text_dim"]), padx=4, pady=2).pack(side="left", padx=2, pady=2)
        tk.Label(lc, text="Formato: [V1_calmo]testo[/V1_calmo]\n"
                          "Il preset regola Exaggeration, CFG, Temperature, Top-P e Min-P.",
                 font=FS, fg=C["natural"], bg=C["surface"], justify="left").pack(
                     anchor="w", pady=(0,8))

        sl(lc, "PAUSE INLINE (durate originali)")
        fp = tk.Frame(lc, bg=C["surface"]); fp.pack(fill="x", pady=(0,4))
        for ci, (tag, col, desc) in enumerate([
            ("[p1]","#4a9080","~0.18s\nvirgola"),
            ("[p2]","#2980b9","~0.40s\npunto"),
            ("[p3]","#8e44ad","~0.65s\nrifless"),
            ("[b]","#27ae60","~1.00s\nidea"),
            ("[bd]","#e84357","~1.60s\nclimax"),
            ("[cap]","#e67e22","~2.00s\ncapovers"),
        ]):
            cell = tk.Frame(fp, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
            cell.grid(row=0, column=ci, padx=2, pady=2, sticky="ew"); fp.columnconfigure(ci, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",9,"bold"), fg=col,
                     bg=C["surface2"], pady=4, padx=3).pack()
            tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], padx=2, pady=2, justify="center").pack()

        # Colonna destra
        sl(rc, "TAG POETICI (solo stile Poesia)")
        fp2 = tk.Frame(rc, bg=C["surface"]); fp2.pack(fill="x", pady=(0,8))
        for ci, (tag, col, desc) in enumerate([
            ("[verso]",    "#9b59b6","~0.30s\nfine verso"),
            ("[strofa]",   "#6c3483","~1.20s\nfine strofa"),
            ("[cesura]",   "#7d3c98","~0.45s\npausa interna"),
            ("[metro]",    "#a9cce3","~0.08s\naccento"),
            ("[enjambement]","#d7bde2","~0.05s\nscorre"),
        ]):
            cell = tk.Frame(fp2, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
            cell.grid(row=0, column=ci, padx=2, pady=2, sticky="ew"); fp2.columnconfigure(ci, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",8,"bold"), fg=col,
                     bg=C["surface2"], pady=4, padx=2).pack()
            tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], padx=2, pady=2, justify="center").pack()

        sl(rc, "ENFASI")
        tg(rc, [("[e1]","#e67e22","Leggera\n+0.10"),("[e2]","#e84357","Forte\n+0.25"),
                ("[ep]","#9b59b6","Poetica\n+0.15")])

        sl(rc, "GIUNZIONI")
        fj = tk.Frame(rc, bg=C["surface"]); fj.pack(fill="x", pady=(0,6))
        for ci, (tag, col, desc) in enumerate([
            ("[join]","#00cec9","overlap\n0.00s"),
            ("[cont]","#74b9ff","smooth\n0.12s"),
            ("[cambio]","#a29bfe","V1<->V2\n0.50s"),
            ("[cambio3]","#00b894","fino a V7\n0.50s"),
            ("[para]","#fdcb6e","fine par\n0.90s"),
            ("[stacco]","#fd79a8","pensiero\n1.40s"),
            ("[lungo]","#e17055","teatrale\n1.80s"),
            ("[scena]","#636e72","scena\n2.40s"),
            ("[dissolvenza]","#a29bfe","strofe\n1.60s"),
        ]):
            cell = tk.Frame(fj, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
            row, col_i = divmod(ci, 5)
            cell.grid(row=row, column=col_i, padx=2, pady=2, sticky="ew")
            fj.columnconfigure(col_i, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",7,"bold"), fg=col,
                     bg=C["surface2"], pady=4, padx=1).pack()
            tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], padx=1, pady=2, justify="center").pack()
        tk.Label(fj, text="Cambi voce disponibili: [cambio], [cambio3], [cambio4], [cambio5], [cambio6], [cambio7]",
                 font=FS, fg=C["text_dim"], bg=C["surface"], anchor="w").grid(
                     row=2, column=0, columnspan=5, sticky="w", pady=(3,0))

        sl(rc, "Pulizia testo automatica v3.0")
        cleanup_info = tk.Frame(rc, bg=C["surface2"], highlightthickness=1,
                                highlightbackground=C["success"], padx=10, pady=8)
        cleanup_info.pack(fill="x", pady=(0,8))
        cleanup_lines = [
            # --- ACCAPO come pause naturali ---
            ("↵",        "→ virgola+\\n   (1 invio: respiro breve, frase continua)"),
            ("↵↵",       "→ punto+\\n     (2 invii: fine frase, pausa media)"),
            ("↵↵↵",      "→ punto+\\n\\n  (3+ invii: nuovo pensiero, riga vuota)"),
            # --- Due punti (NUOVO v3.0) ---
            ("testo:",   "→ testo.   (due punti → punto, pausa naturale)"),
            ("15:30",    "→ 15:30    (orari/numeri: invariati)"),
            # --- Punteggiatura ---
            ("...",      "→ .   (tre puntini → punto singolo)"),
            ("…",        "→ .   (ellipsis unicode)"),
            ("— –",      "→ ,   (trattini em/en)"),
            ("--",       "→ ,   (doppio trattino)"),
            ("a - b",    "→ a, b  (trattino isolato tra parole)"),
            (";",        "→ ,   (punto e virgola)"),
            ("!!! ???",  "→ ! ?  (punteggiatura multipla)"),
            # --- Apostrofo (FIX v3.0) ---
            ("l\u2019anima", "→ l'anima  (apostrofo curvo Word/iOS → dritto)"),
            ("l`anima",  "→ l'anima  (backtick usato come apostrofo)"),
            # --- Simboli ---
            ("€ $ £",    "→ euro dollari sterline"),
            ("%",        "→ percento"),
            ("&",        "→ e"),
            ("#5",       "→ numero 5"),
            ("× ÷",      "→ per / diviso"),
            ("½ ¼ ¾",    "→ mezzo un quarto tre quarti"),
            ("37°C",     "→ 37 gradi"),
            ("1° 2°",    "→ primo secondo"),
            # --- Abbreviazioni ---
            ("dott.",    "→ dottor"),
            ("sig.",     "→ signor"),
            ("prof.",    "→ professore"),
            ("ecc.",     "→ eccetera"),
            ("km",       "→ chilometri"),
            # --- Testo ---
            ("(testo)",  "→ , testo,  (parentesi → virgole)"),
            ("*testo*",  "→ testo  (markdown rimosso)"),
            ("a/b",      "→ a o b  (barra tra parole)"),
            ("CIA",      "→ Cia  (ALLCAPS → Prima lettera)"),
        ]
        for tag_txt, desc_txt in cleanup_lines:
            row = tk.Frame(cleanup_info, bg=C["surface2"]); row.pack(fill="x", pady=1)
            tk.Label(row, text=tag_txt, font=("Courier New",8,"bold"), fg=C["accent"],
                     bg=C["surface2"], width=9, anchor="w").pack(side="left")
            tk.Label(row, text=desc_txt, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], anchor="w").pack(side="left")

        tk.Label(inner,
                 text="v3.0: Pause Naturali — [p1][p2][b]... → virgole/punti+newline per Chatterbox.\n"
                      "Accapo → pause (↵=respiro  ↵↵=fine frase  ↵↵↵=nuovo pensiero).\n"
                      "Due punti → punto. Apostrofo curvo Word/iOS → corretto. Simboli e abbreviazioni IT convertiti.",
                 font=FS, fg=C["natural"], bg=C["surface"], pady=10, justify="left", anchor="w"
                 ).pack(fill="x", pady=(12,0))

    def _toggle_guide(self):
        if self.guide_outer.winfo_manager():
            self.guide_outer.pack_forget()
            self.guide_toggle_btn.config(text="▾ Mostra Guida Tag")
        else:
            self.guide_outer.pack(fill="x", pady=(10,0))
            self.guide_toggle_btn.config(text="▴ Nascondi Guida Tag")

    def _footer(self, r):
        ft = tk.Frame(r, bg=C["bg"], pady=20); ft.pack(fill="x")
        tk.Label(ft,
                 text="2026 (c) ChatterText v3.0 + Multilingual V3 by Gerardo D'Orrico  --  "
                      "Pause Naturali | 4 Stili | Tag Poetici | Post-proc Audio | 7 Voci | Pulizia testo avanzata",
                 font=FS, fg=C["text_dim"], bg=C["bg"]).pack()

    # ---- DEVICE ----
    def _detect_device(self):
        def _d():
            py = self._chatterbox_python()
            probe = (
                "import torch; "
                "print('CUDA|{}|{}|{}'.format(torch.cuda.is_available(), "
                "torch.cuda.get_device_name(0) if torch.cuda.is_available() else '', "
                "torch.cuda.get_device_properties(0).total_memory//(1024**3) if torch.cuda.is_available() else 0))"
            )
            try:
                result = subprocess.run([py, "-c", probe], capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=20,
                                        **HIDDEN_SUBPROCESS)
                parts = result.stdout.strip().split("|")
                if result.returncode == 0 and len(parts) == 4 and parts[1] == "True":
                    dev, info = "cuda", "GPU: {} ({}GB VRAM)".format(parts[2], parts[3])
                else:
                    dev, info = "cpu", "CPU: CUDA non disponibile nell'ambiente Chatterbox"
            except Exception:
                dev, info = "cpu", "CPU: impossibile verificare PyTorch nell'ambiente Chatterbox"
            col = C["gpu"] if dev == "cuda" else C["cpu"]
            self.after(0, lambda: self._set_badge(("GPU " if dev=="cuda" else "CPU ")+info, col))
        threading.Thread(target=_d, daemon=True).start()

    def _set_badge(self, txt, col):
        self.badge_var.set(txt); self.badge.config(bg=col)

    def _chatterbox_python(self):
        """Trova l'interprete dell'ambiente Chatterbox senza modificarlo."""
        base = pathlib.Path(self.vdir.get() or pathlib.Path.cwd()).resolve()
        app_dir = pathlib.Path(__file__).resolve().parent
        candidates = [
            base / "venv_chatterbox" / "Scripts" / "python.exe",
            base / "chatterbox-env" / "Scripts" / "python.exe",
            base / "chatterbox_env" / "Scripts" / "python.exe",
            base / "venv" / "Scripts" / "python.exe",
            app_dir / "venv_chatterbox" / "Scripts" / "python.exe",
            app_dir / "chatterbox-env" / "Scripts" / "python.exe",
            pathlib.Path(sys.executable),
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    check = subprocess.run([str(candidate), "-c", "import sys; print(sys.executable)"],
                                           capture_output=True, timeout=10,
                                           **HIDDEN_SUBPROCESS)
                    if check.returncode == 0:
                        return str(candidate)
                except Exception:
                    continue
        return sys.executable

    # ---- PROCESS ----
    def process(self):
        raw = self.txt.get("1.0","end-1c").strip()
        if not raw or "Incolla qui" in raw:
            messagebox.showwarning("Attenzione", "Inserisci testo!"); return

        has_t = bool(re.search(r"\[inizio\]", raw, re.IGNORECASE))

        if has_t:
            norm = re.sub(r"\[inizio\]([\s\S]*?)\[fine\]",
                          lambda m: "[inizio]" + normalize_text(m.group(1)) + "[fine]",
                          raw, flags=re.IGNORECASE)
        else:
            with_pauses = newlines_to_pauses(raw)
            norm = normalize_text(with_pauses)

        errs = analyze_text(norm)
        ws = [w for w in norm.split() if w]
        self.vwords.set(str(len(ws))); self.vchars.set(str(len(norm))); self.verrs.set(str(len(errs)))
        self.stats.pack(fill="x")
        tc  = len(re.findall(r"\[inizio\]", norm, re.IGNORECASE))
        ec  = len(re.findall(r"\[(?:(?:v1|v2|v3|v4|v5|v6|v7)_)?(?:"+"|".join(ALL_EMO)+r")\]", norm, re.IGNORECASE))
        pc  = len(re.findall(r"\[(?:p[123]|b(?:d)?|cap|pausa(?:_lunga)?|silenzio|verso|strofa|metro|enjambement|cesura)\]", norm, re.IGNORECASE))
        enc = len(re.findall(r"\[e[12p]\]", norm, re.IGNORECASE))
        jc  = len(re.findall(r"\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\]", norm, re.IGNORECASE))
        pts = []
        if tc:  pts.append("{} blocchi".format(tc))
        if ec:  pts.append("{} emozioni".format(ec))
        if pc:  pts.append("{} pause".format(pc))
        if enc: pts.append("{} enfasi".format(enc))
        if jc:  pts.append("{} giunzioni".format(jc))

        # Mostra anteprima pause naturali se attive
        np_active = self.vnatpauses.get()
        if np_active and pc > 0:
            pts.append("→ Pause Naturali ON")

        self.tag_lbl.config(text="  ".join(pts) if pts else "Modalita automatica",
                            fg=C["natural"] if np_active and pc>0 else
                               (C["success"] if pts else C["warning"]))
        self.err_box.config(state="normal"); self.err_box.delete("1.0","end")
        if errs:
            for et, msg in errs:
                self.err_box.insert("end", "{} {}\n".format(
                    "ERRORE:" if et=="error" else ("ATTENZIONE:" if et=="warning" else "INFO:"), msg))
        else:
            self.err_box.insert("end", "Nessun problema!"); self.err_box.config(fg=C["success"])
        self.err_box.config(state="disabled")
        structural = [msg for et, msg in errs if et == "error"]
        if structural:
            self.chunksec.pack_forget()
            messagebox.showerror("Tag non validi",
                                 "Correggi la struttura dei tag prima di generare i chunk:\n\n" +
                                 "\n".join("• " + msg for msg in structural[:8]))
            return
        try: minw,maxw,maxc = int(self.vminw.get()),int(self.vmaxw.get()),int(self.vmaxc.get())
        except: minw,maxw,maxc = 20,40,240
        chunks = chunk_text(norm, minw, maxw, maxc)
        self.chunks = chunks; self.vchunks.set(str(len(chunks)))
        short = [i+1 for i,c in enumerate(chunks)
                 if len(_protected().sub("",c).strip().split()) < minw]
        if short:
            messagebox.showwarning("Chunk corti!",
                "Chunk con meno di {} parole (rischio ripetizioni):\n{}\n\n"
                "Uniscili o usa il Prompt Guida.".format(minw, ", ".join(str(n) for n in short[:10])))
        self._render(); self.chunksec.pack(fill="x")

    def _render(self):
        for w in self.cbox.winfo_children(): w.destroy()
        self.chunk_vars = []
        for i, chunk in enumerate(self.chunks):
            cl = _protected().sub("", chunk).strip()
            words = len(cl.split()); chars = len(cl)
            status, stxt = chunk_status(words, chars)
            sc = {"success":C["success"],"warning":C["warning"],"danger":C["danger"]}[status]
            voice, emo = detect_voice_emo(chunk)
            emphs = detect_emph(chunk); pauses = detect_pauses(chunk); jt = detect_join(chunk)

            voice_colors = {"v1":C["v1"],"v2":C["v2"],"v3":C["v3"],"v4":C["v4"],"v5":C["v5"],
                            "v6":C["v6"],"v7":C["v7"]}
            voice_labels = {"v1":"V1","v2":"V2","v3":"V3","v4":"V4","v5":"V5",
                            "v6":"V6->V1","v7":"V7->V1"}
            vl = voice_labels.get(voice, "Auto")
            vc = voice_colors.get(voice, C["text_dim"])

            card = tk.Frame(self.cbox, bg=C["chunk_bg"], bd=0, highlightthickness=1,
                            highlightbackground=C["border"])
            card.pack(fill="x", pady=(0,10))
            hdr = tk.Frame(card, bg=C["hdr_bg"], pady=8, padx=12); hdr.pack(fill="x")
            tk.Label(hdr, text="Chunk {}".format(i+1), font=FL, fg=C["accent"], bg=C["hdr_bg"]).pack(side="left")
            tk.Label(hdr, text=" {} ".format(vl), font=FS, fg="#fff", bg=vc, padx=6, pady=2).pack(side="left", padx=4)
            if emo:
                ec = EMO_C.get(emo, C["text_dim"])
                tk.Label(hdr, text=" {} ".format(emo), font=FS, fg="#fff", bg=ec, padx=6, pady=2).pack(side="left", padx=2)
            for et in emphs:
                ec2 = {"e2":"#e84357","ep":"#9b59b6"}.get(et,"#e67e22")
                tk.Label(hdr, text=" {} ".format(et), font=FS, fg="#fff", bg=ec2, padx=5, pady=2).pack(side="left", padx=2)
            shown = []
            for ptag, _ in pauses:
                if ptag not in shown: shown.append(ptag)
                if len(shown) >= 3: break
            for ptag in shown:
                pn = ptag.strip("[]")
                pc2 = PAUSE_BADGE_C.get(pn, "#7f8c8d")
                tk.Label(hdr, text=" {} ".format(ptag), font=FS, fg="#fff", bg=pc2, padx=5, pady=2).pack(side="left", padx=1)
            if jt:
                jn = jt.strip("[]")
                jcol = JOIN_BADGE_C.get(jn, C["text_dim"])
                jfg = "#000" if jn == "para" else "#fff"
                tk.Label(hdr, text=" {} ".format(jt), font=FS, fg=jfg, bg=jcol, padx=5, pady=2).pack(side="left", padx=1)
            # Badge pause naturali attive
            if self.vnatpauses.get() and pauses:
                tk.Label(hdr, text=" 🎙NP ", font=FS, fg="#000",
                         bg=C["natural"], padx=4, pady=2).pack(side="left", padx=1)

            # Anteprima testo naturale su hover (info nel footer card)
            inf = tk.Frame(hdr, bg=C["hdr_bg"]); inf.pack(side="right")
            tk.Label(inf, text="{} par. {} car.".format(words,chars), font=FS,
                     fg=C["text_dim"], bg=C["hdr_bg"]).pack(side="left", padx=8)
            tk.Label(inf, text=stxt, font=FS, fg=sc, bg=C["hdr_bg"]).pack(side="left")
            self.chunk_vars.append(tk.StringVar(value=chunk))
            tf = tk.Frame(card, bg=C["chunk_bg"], padx=8, pady=6); tf.pack(fill="x")
            ta_w = tk.Text(tf, height=4, bg=C["surface2"], fg=C["text"], font=FM, relief="flat", bd=0,
                         wrap="word", insertbackground=C["accent"],
                         highlightthickness=1, highlightbackground=C["border"])
            ta_w.insert("1.0", chunk); ta_w.pack(fill="x")
            ta_w.bind("<KeyRelease>", lambda e, t=ta_w, ix=i: self._edit(t, ix))

            # Anteprima Pause Naturali sotto il chunk
            if self.vnatpauses.get() and pauses:
                preview_txt = pauses_to_natural_text(cl)
                if preview_txt != cl:
                    pf2 = tk.Frame(card, bg="#0a1a0a", padx=8, pady=4); pf2.pack(fill="x")
                    tk.Label(pf2, text="🎙 Testo a Chatterbox:", font=FS,
                             fg=C["natural"], bg="#0a1a0a").pack(anchor="w")
                    preview_lines = preview_txt[:200].split('\n')
                    for ln in preview_lines[:6]:
                        if ln.strip():
                            tk.Label(pf2, text="  │ "+ln.strip()[:80], font=("Courier New",8),
                                     fg="#a0d0c0", bg="#0a1a0a", anchor="w").pack(fill="x")

            af = tk.Frame(card, bg=C["chunk_bg"], padx=8, pady=6); af.pack(fill="x")
            sb_btn(af, "Copia", lambda ix=i: self._copy_c(ix)).pack(side="left", padx=(0,6))
            sb_btn(af, "Dividi", lambda ix=i: self._split(ix), color=C["warning"]).pack(side="left", padx=(0,6))
            if i < len(self.chunks)-1:
                sb_btn(af, "Unisci", lambda ix=i: self._merge(ix), color="#17a2b8").pack(side="left")

    def _edit(self, ta, idx): self.chunks[idx] = ta.get("1.0","end-1c")
    def _copy_c(self, idx):
        self.clipboard_clear(); self.clipboard_append(self.chunks[idx])
        messagebox.showinfo("Copiato", "Chunk {} copiato!".format(idx+1))
    def copy_all(self):
        self.clipboard_clear(); self.clipboard_append("\n\n---\n\n".join(self.chunks))
        messagebox.showinfo("Copiato", "Tutti i chunk copiati!")
    def _split(self, idx):
        t = self.chunks[idx]; mid = len(t)//2
        win = t[max(0,mid-100):min(len(t),mid+100)]
        m = re.search(r"[.!?;:]\s", win)
        sp = max(0,mid-100)+m.start()+2 if m else mid
        self.chunks[idx:idx+1] = [t[:sp].strip(), t[sp:].strip()]
        self._render(); self.vchunks.set(str(len(self.chunks)))
    def _merge(self, idx):
        if idx >= len(self.chunks)-1: return
        self.chunks[idx:idx+2] = [self.chunks[idx]+" "+self.chunks[idx+1]]
        self._render(); self.vchunks.set(str(len(self.chunks)))

    # ---- SCRIPT ----
    def _mk_script(self):
        if not self.chunks:
            messagebox.showwarning("Attenzione", "Processa prima!"); return None
        try: ex, cg, tp = float(self.vexag.get()), float(self.vcfg.get()), float(self.vtemp.get())
        except: ex, cg, tp = 0.50, 0.58, 0.60
        try: min_p = float(self.vminp.get())
        except: min_p = 0.05
        try: top_p = float(self.vtopp.get())
        except: top_p = 1.00
        try: repetition_penalty = float(self.vrep.get())
        except: repetition_penalty = 1.20
        try: seed = int(self.vseed.get())
        except: seed = 0
        try: ng = float(self.vng.get())
        except: ng = -50
        try: rms = float(self.vrms.get())
        except: rms = -18
        try: trim = float(self.vtrim.get())
        except: trim = -45
        style_key = self.vreadstyle.get()
        style = READING_STYLES.get(style_key, READING_STYLES["narrativa"])
        pause_scale = style["pause_scale"]
        preset_scale = style["preset_scale"]
        return build_python_script(
            self.chunks, ex, cg, tp,
            self.vv1.get().strip() or "1Opier.wav",
            self.vv2.get().strip(), self.vv3.get().strip(),
            self.vv4.get().strip(), self.vv5.get().strip(),
            self.vv6.get().strip(), self.vv7.get().strip(),
            self.epreset, self.vdev.get(),
            reading_style=style_key,
            noise_gate_db=ng, rms_target_db=rms, trim_threshold_db=trim,
            pause_scale=pause_scale, preset_scale=preset_scale,
            aggressive_clean=self.vaggclean.get(),
            natural_pauses=self.vnatpauses.get(), min_p=min_p, top_p=top_p,
            repetition_penalty=repetition_penalty, seed=seed
        )

    def save_script(self):
        s = self._mk_script()
        if not s: return
        p = pathlib.Path(self.vdir.get() or str(pathlib.Path.cwd())) / "chatterbox_auto.py"
        p.write_text(s, encoding="utf-8"); self.script_path = str(p)
        messagebox.showinfo("Salvato", "Script:\n{}".format(p))

    def run_chatterbox(self):
        if self._proc and self._proc.poll() is None:
            messagebox.showwarning("In corso", "Generazione già in corso! Premi Stop."); return
        s = self._mk_script()
        if not s: return
        dest = pathlib.Path(self.vdir.get() or str(pathlib.Path.cwd()))
        sf2 = dest / "chatterbox_auto.py"; sf2.write_text(s, encoding="utf-8")
        tot = len(self.chunks)
        self.logsec.pack(fill="x"); self.progv.set(0)
        model_lbl = "V3"
        self.vprog.set("0 / {} chunk".format(tot)); self.veta.set("Caricamento modello {}...".format(model_lbl))
        dm = self.vdev.get()
        self.vdevl.set("GPU CUDA" if dm=="cuda" else ("CPU" if dm=="cpu" else "Auto-detect..."))
        self.log.config(state="normal"); self.log.delete("1.0","end")
        style_lbl = READING_STYLES.get(self.vreadstyle.get(), {}).get("label","?")
        np_lbl = "Pause Naturali: ATTIVE" if self.vnatpauses.get() else "Pause Naturali: disattive"
        self.log.insert("end", "Avvio: {}\n Modello: Chatterbox Multilingual {}\n Stile: {}  |  {}\n Cartella: {}\n".format(
            sf2, model_lbl, style_lbl, np_lbl, dest))
        self.log.config(state="disabled")
        self.stopbtn.config(state="normal")
        self._t0 = time.time()
        def _run():
            try:
                env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.Popen([self._chatterbox_python(), str(sf2)], cwd=str(dest),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", env=env,
                    **HIDDEN_SUBPROCESS)
                self._proc = proc
                for line in proc.stdout:
                    self._alog(line)
                    if "Caricamento Chatterbox" in line:
                        self.after(0, lambda m=model_lbl: self.veta.set("Caricamento modello {}...".format(m)))
                    elif "Modello su" in line:
                        self.after(0, lambda: self.veta.set("Modello pronto: inizio sintesi..."))
                    elif "ERRORE V3:" in line:
                        self.after(0, lambda: self.veta.set("V3 non disponibile: aggiorna Chatterbox"))
                    m = re.search(r"Chunk\s+(\d+)/(\d+)", line)
                    if m:
                        n, t2 = int(m.group(1)), int(m.group(2)); pct = int(n/t2*100)
                        el = time.time()-self._t0; av = el/n if n>0 else 0; rm = av*(t2-n)
                        self.after(0, lambda p=pct, nn=n, t=t2, r=rm: self._uprog(p,nn,t,r))
                    if "GPU" in line and "CUDA" in line.upper():
                        self.after(0, lambda: self.vdevl.set("GPU CUDA attivo"))
                    elif "CPU" in line and "dispositivo" in line.lower():
                        self.after(0, lambda: self.vdevl.set("CPU attivo"))
                proc.wait(); rc = proc.returncode
                self._alog("\n"+"-"*55+"\n")
                if rc == 0:
                    el = time.time()-self._t0
                    self._alog("Completato in {:.1f}s!\n".format(el))
                    self.after(0, lambda: self.progv.set(100))
                    self.after(0, lambda: self.vprog.set("{}/{} COMPLETATO".format(tot,tot)))
                    self.after(0, lambda: self.veta.set("Totale: {:.1f}s".format(el)))
                    if self.vsound.get():
                        threading.Thread(target=play_sound, daemon=True).start()
                    self._alog(">>> FILE SALVATO in 1.Output/\n")
                else:
                    self._alog("Errore (code {})\n".format(rc))
            except Exception as ex:
                self._alog("\nErrore: {}\n".format(ex))
            finally:
                self.after(0, lambda: self.stopbtn.config(state="disabled"))
        threading.Thread(target=_run, daemon=True).start()

    def _uprog(self, pct, n, tot, rem):
        self.progv.set(pct); self.vprog.set("{}/{} chunk".format(n,tot))
        if rem > 0: self.veta.set("ETA: {:.0f}s".format(rem))

    def _stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._alog("\nStop richiesto dall'utente.\n")
            self.stopbtn.config(state="disabled")
            self.vprog.set("Interrotto")

    def _alog(self, text):
        def _d():
            self.log.config(state="normal"); self.log.insert("end", text)
            self.log.see("end"); self.log.config(state="disabled")
        self.after(0, _d)

    def clear_all(self):
        self.txt.delete("1.0","end")
        self.txt.insert("1.0", "Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.chunks = []; self.chunk_vars = []
        for v in (self.vwords, self.vchars, self.vchunks, self.verrs): v.set("0")
        self.vcc.set("0 / 10000")
        self.stats.pack_forget(); self.chunksec.pack_forget(); self.logsec.pack_forget()
        self.stopbtn.config(state="disabled")
        for w in self.cbox.winfo_children(): w.destroy()

    def paste_text(self):
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("Appunti vuoti", "Negli appunti non c'è testo da incollare.")
            return

        current = self.txt.get("1.0", "end-1c")
        if "Incolla qui" in current:
            self.txt.delete("1.0", "end")
        self.txt.insert("insert", text)
        self.txt.focus_set()
        self.txt.see("insert")
        self.vcc.set("{} / 10000".format(len(self.txt.get("1.0", "end-1c"))))

    def apply_emotion_tag(self):
        voice = self.vtagvoice.get().strip().upper() or "V1"
        emotion = self.vtagemotion.get().strip().lower() or "calmo"
        if voice not in {"V{}".format(i) for i in range(1, 8)} or emotion not in ALL_EMO:
            messagebox.showwarning("Preset non valido", "Seleziona una voce e un'emozione valide.")
            return

        opening = "[{}_{}]".format(voice, emotion)
        closing = "[/{}_{}]".format(voice, emotion)
        current = self.txt.get("1.0", "end-1c")
        if "Incolla qui" in current:
            self.txt.delete("1.0", "end")
            self.txt.mark_set("insert", "1.0")

        if self.txt.tag_ranges("sel"):
            start, end = self.txt.index("sel.first"), self.txt.index("sel.last")
            selected = self.txt.get(start, end)
            wrapped = opening + selected + closing
            self.txt.delete(start, end)
            self.txt.insert(start, wrapped)
            self.txt.mark_set("insert", "{}+{}c".format(start, len(wrapped)))
        else:
            pos = self.txt.index("insert")
            self.txt.insert(pos, opening + closing)
            self.txt.mark_set("insert", "{}+{}c".format(pos, len(opening)))

        self.txt.focus_set()
        self.txt.see("insert")
        self.vcc.set("{} / 10000".format(len(self.txt.get("1.0", "end-1c"))))

    def insert_quick_tag(self):
        tag = self.vquicktag.get().strip()
        if tag not in QUICK_TAGS:
            messagebox.showwarning("Tag non valido", "Seleziona un tag dall'elenco.")
            return

        current = self.txt.get("1.0", "end-1c")
        if "Incolla qui" in current:
            self.txt.delete("1.0", "end")
            self.txt.mark_set("insert", "1.0")

        if tag == "[inizio]…[fine]":
            opening, closing = "[inizio]", "[fine]"
            if self.txt.tag_ranges("sel"):
                start, end = self.txt.index("sel.first"), self.txt.index("sel.last")
                selected = self.txt.get(start, end)
                wrapped = opening + selected + closing
                self.txt.delete(start, end)
                self.txt.insert(start, wrapped)
                self.txt.mark_set("insert", "{}+{}c".format(start, len(wrapped)))
            else:
                pos = self.txt.index("insert")
                self.txt.insert(pos, opening + closing)
                self.txt.mark_set("insert", "{}+{}c".format(pos, len(opening)))
        else:
            pos = self.txt.index("sel.last") if self.txt.tag_ranges("sel") else self.txt.index("insert")
            self.txt.insert(pos, tag)
            self.txt.mark_set("insert", "{}+{}c".format(pos, len(tag)))

        self.txt.focus_set()
        self.txt.see("insert")
        self.vcc.set("{} / 10000".format(len(self.txt.get("1.0", "end-1c"))))

    def _browse(self):
        d = filedialog.askdirectory(title="Seleziona cartella Chatterbox")
        if d: self.vdir.set(d)

    def _presets(self):
        PresetWindow(self, self.epreset, on_save=lambda p: self.epreset.update(p))


if __name__ == "__main__":
    App().mainloop()
