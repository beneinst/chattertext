#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatterText - App Desktop Python v3.0
Posizionare nella root di Chatterbox ed eseguire con: python chattertext_app.py

NOVITA v2.9 (normalize_text avanzata + accapo come pause):
  - ACCAPO COME PAUSE (nuovo comportamento in Analizza e Processa):
    * 1 accapo  (Enter)    -> [p1] pausa breve  ~0.18s  (pausa naturale nel discorso)
    * 2 accapo  (Invio x2) -> [p2] pausa media  ~0.40s  (fine frase / separatore)
    * 3+ accapo (Invio x3+)-> [b]  pausa lunga  ~1.00s  (cambio idea / paragrafo)
    Permette di strutturare le pause semplicemente premendo Invio durante la scrittura.
    I tag [inizio]/[fine] vengono rispettati (non modificati).
  - NORMALIZE_TEXT v2.9 - nuove conversioni automatiche:
    * Simboli valuta:  € -> euro, $ -> dollari, £ -> sterline
    * Simboli comuni:  % -> percento, & -> e, @ -> at, # -> numero
    * Simboli matematici: × -> per, ÷ -> diviso, ± -> piu o meno
    * Simbolo gradi:   37° -> 37 gradi, ma solo dopo numero
    * Frazioni unicode: ½ -> mezzo, ¼ -> un quarto, ¾ -> tre quarti
    * Ordinali numerici: 1° 2° 3° -> primo secondo terzo (italiano)
    * Abbreviazioni comuni IT: dott. sig. prof. ecc. es. vs. nr. art.
    * Punto e virgola:  ; -> , (Chatterbox spesso lo ignora o fa pausa strana)
    * Parentesi (testo) -> virgola testo virgola (rende il contenuto leggibile)
    * Trattino corto tra parole non-dialogo -> virgola (pausa naturale)
    * Doppio trattino -- -> virgola
    * Asterischi *testo* -> testo (rimuove markdown enfasi)
    * Underscore _testo_ -> testo (rimuove markdown enfasi)
    * Barra / tra parole -> o (es. "e/o" -> "e o")
    * Numero + spazio + unita comuni: "10 km" gestito correttamente
  - GUIDA AGGIORNATA: tabella pulizia espansa con tutti i nuovi caratteri

NOVITA v2.8 (UI):
  - Tasto Stop sempre visibile in sezione Parametri
  - Input text height 14, output log height 20
  - Volume suono fine generazione -50%

NOVITA v2.7 (modalita poetica + stili lettura):
  - STILI DI LETTURA: Narrativa / Poesia / Teatro / Audiolibro lungo
  - TAG POETICI: [verso] [strofa] [metro] [enjambement] [cesura]

NOVITA v2.6:
  - Aggiunta Voce 6 [v6] / Voce 7 [v7] con fallback automatico su V1
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
    "v2":       "#e74c3c", "v3":       "#00b894",
    "v4":       "#e67e22", "v5":       "#9b59b6",
    "v6":       "#5d7a8a", "v7":       "#4a4a4a",
    "chunk_bg": "#111111", "hdr_bg":   "#181818",
    "gpu":      "#76b900", "cpu":      "#4a90e2",
    "style_narr":   "#3498db",
    "style_poesia": "#9b59b6",
    "style_teatro": "#e74c3c",
    "style_lungo":  "#00b894",
    "antiart":      "#00cec9",
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
        "exaggeration": 0.62, "cfg_weight": 0.70, "temperature": 0.58,
        "top_p": 0.75, "min_p": 0.15,
        "preset_scale": 1.0, "pause_scale": 1.0,
        "noise_gate_db": -50, "rms_target_db": -18, "trim_threshold_db": -45,
        "notes": "Stile bilanciato. Pause naturali. Emozioni moderate.",
    },
    "poesia": {
        "label": "Poesia",
        "color": "#9b59b6",
        "desc": "Poesie, versi, testi lirici — lettura recitata",
        "exaggeration": 0.82, "cfg_weight": 0.52, "temperature": 0.72,
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
        "exaggeration": 0.90, "cfg_weight": 0.45, "temperature": 0.80,
        "top_p": 0.90, "min_p": 0.05,
        "preset_scale": 1.35, "pause_scale": 1.20,
        "noise_gate_db": -46, "rms_target_db": -15, "trim_threshold_db": -40,
        "notes": "Dinamica ampia teatrale. Enfasi forti. Transizioni nette tra personaggi.",
    },
    "audiolibro_lungo": {
        "label": "Audiolibro lungo",
        "color": "#00b894",
        "desc": "Capitoli lunghi, saga, consistenza su ore di audio",
        "exaggeration": 0.52, "cfg_weight": 0.78, "temperature": 0.45,
        "top_p": 0.72, "min_p": 0.18,
        "preset_scale": 0.88, "pause_scale": 0.92,
        "noise_gate_db": -52, "rms_target_db": -20, "trim_threshold_db": -48,
        "notes": "Parametri stabili per lunghe sessioni. Meno varianza. Coerenza timbrica.",
    },
}

# =========================================================
# PRESET ANTI-ARTEFATTI v3.0
# =========================================================
ANTIARTI_PRESETS = {
    "leggero": {
        "label": "Leggero",
        "desc": "Tocco minimo - preserva al massimo l'audio originale",
        "noise_gate_db": -55, "rms_target_db": -18, "trim_db": -50,
        "strip_lead_ms": 80,  "strip_tail_ms": 60,
        "spectral_gate": False, "declick": False,
        "fade_ms": 10, "boundary_smooth_ms": 20,
    },
    "standard": {
        "label": "Standard",
        "desc": "Bilanciato - rimuove artefatti comuni senza degradare",
        "noise_gate_db": -50, "rms_target_db": -18, "trim_db": -45,
        "strip_lead_ms": 120, "strip_tail_ms": 80,
        "spectral_gate": False, "declick": True,
        "fade_ms": 14, "boundary_smooth_ms": 35,
    },
    "aggressivo": {
        "label": "Aggressivo",
        "desc": "Pulizia massima - per audio con molti artefatti",
        "noise_gate_db": -46, "rms_target_db": -18, "trim_db": -42,
        "strip_lead_ms": 180, "strip_tail_ms": 120,
        "spectral_gate": True, "declick": True,
        "fade_ms": 18, "boundary_smooth_ms": 50,
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


def normalize_text(text):
    """
    Pulizia testo avanzata v2.9 per Chatterbox TTS.

    ACCAPO COME PAUSE (gestito PRIMA di questa funzione in process()):
      1 accapo  -> [p1]  pausa breve  ~0.18s
      2 accapo  -> [p2]  pausa media  ~0.40s
      3+ accapo -> [b]   pausa lunga  ~1.00s

    Ordine operazioni interne:
      1.  Protezione tag ChatterText
      2.  Virgolette tipografiche -> standard
      3.  Apostrofi speciali -> standard
      4.  Trattini em/en -> virgola (dialogo: trattino normale)
      5.  Trattino corto e doppio trattino -> virgola
      6.  Trattino di sillabazione a fine riga -> ricongiunge parola
      7.  Tre puntini / ellipsis -> punto singolo
      8.  Simboli valuta: € $ £
      9.  Simboli comuni: % & @ #
      10. Simboli matematici: × ÷ ± e frazioni ½ ¼ ¾
      11. Gradi °: dopo numero -> "gradi", standalone -> rimosso
      12. Ordinali numerici italiani: 1° 2° 3° ... -> primo secondo terzo
      13. Abbreviazioni italiane comuni
      14. Parentesi -> virgole
      15. Punto e virgola -> virgola
      16. Markdown *testo* _testo_ -> testo
      17. Barra / tra parole -> o
      18. Apostrofi + maiuscole dopo articoli
      19. Parole ALLCAPS -> Prima lettera maiuscola
      20. Accenti maiuscoli -> minuscoli (italiano)
      21. Punteggiatura multipla -> singola
      22. Pulizia caratteri non TTS-safe
      23. Normalizzazione spazi finali
      24. Ripristino tag protetti
    """
    tm = {}; idx = [0]; pat = _protected()

    # 1. Proteggi i tag ChatterText (non toccare mai [p1] [v1_calmo] ecc.)
    #    IMPORTANTE: il placeholder NON deve contenere underscore ne caratteri speciali
    #    perché i passi successivi (markdown strip, pulizia caratteri) li distruggerebbero.
    #    "ZZCHT0ZZCHT" è solo alfanumerico -> sopravvive a tutti i passi.
    def sv(m):
        ph = "ZZCHT{}ZZCHT".format(idx[0])
        tm[ph] = m.group(0); idx[0] += 1; return ph
    text = pat.sub(sv, text)

    # 2. Virgolette tipografiche -> virgolette standard ASCII
    text = text.replace('\u201c', '"').replace('\u201d', '"')   # " "  -> "
    text = text.replace('\u2018', "'").replace('\u2019', "'")   # ' '  -> '
    text = text.replace('\u00ab', '"').replace('\u00bb', '"')   # « »  -> "
    text = text.replace('\u201e', '"').replace('\u201a', "'")   # „ ‚  -> " '

    # 3. Apostrofi speciali -> apostrofo standard
    text = text.replace('\u02bc', "'").replace('\u02b9', "'")   # ʼ ʹ
    text = text.replace('\u0060', "'").replace('\u00b4', "'")   # ` ´
    text = re.sub(r"[\u02bc\u02b9\u0060\u00b4]", "'", text)

    # 4. Trattini em/en (— –) -> virgola o trattino dialogo
    text = re.sub(r"-\s*\n\s*([a-z\u00c0-\u00f9])", r"\1", text)  # sillabazione a fine riga
    text = re.sub(r"^\s*[\u2014\u2013]\s*", "- ", text, flags=re.MULTILINE)  # dialogo inizio riga
    text = re.sub(r"(?<=\w)\s*[\u2014\u2013]\s*(?=\w)", ", ", text)          # tra parole
    text = re.sub(r"\s*[\u2014\u2013]\s*", ", ", text)                        # resto

    # 5. Doppio trattino -- e trattino corto isolato tra parole -> virgola
    text = re.sub(r"\s*--\s*", ", ", text)                                    # -- -> ,
    text = re.sub(r"(?<=\w)\s+-\s+(?=\w)", ", ", text)                       # " - " -> ", "

    # 6. Tre puntini / ellipsis unicode -> punto singolo
    #    Chatterbox genera una micropausa glitch su "..." invece usa un punto normale.
    text = text.replace('\u2026', '.')           # ellipsis unicode U+2026
    text = re.sub(r"\.{2,}", '.', text)          # .. o ... o .... -> .
    text = re.sub(r"\.\s*\.\s*\.", '.', text)    # . . . -> .

    # 7. Simboli valuta -> parola leggibile
    # Attenzione: il simbolo può precedere o seguire il numero
    text = re.sub(r'(\d)\s*€',  r'\1 euro',     text)   # 10€   -> 10 euro
    text = re.sub(r'€\s*(\d)',  r'\1 euro',     text)   # €10   -> 10 euro
    text = re.sub(r'€',         'euro',          text)   # euro standalone
    text = re.sub(r'(\d)\s*\$', r'\1 dollari',  text)   # 10$   -> 10 dollari
    text = re.sub(r'\$\s*(\d)', r'\1 dollari',  text)   # $10   -> 10 dollari
    text = re.sub(r'\$',        'dollari',       text)
    text = re.sub(r'(\d)\s*£',  r'\1 sterline', text)   # 10£   -> 10 sterline
    text = re.sub(r'£\s*(\d)',  r'\1 sterline', text)
    text = re.sub(r'£',         'sterline',      text)

    # 8. Simboli comuni -> parola
    text = re.sub(r'(\d)\s*%',  r'\1 percento', text)   # 10%  -> 10 percento
    text = re.sub(r'%',         ' percento',    text)
    text = re.sub(r'\s*&\s*',   ' e ',          text)   # & -> e
    text = re.sub(r'#(\d+)',    r'numero \1',   text)   # #5  -> numero 5
    text = re.sub(r'#(\w+)',    r'\1',          text)   # #hashtag -> hashtag
    # @ : in indirizzi email lascia, altrimenti "at"
    text = re.sub(r'(?<!\w)@(?!\w)', ' at ', text)

    # 9. Simboli matematici e frazioni unicode
    text = text.replace('\u00d7', ' per ')      # × -> per
    text = text.replace('\u00f7', ' diviso ')   # ÷ -> diviso
    text = text.replace('\u00b1', ' piu o meno ') # ± -> piu o meno
    text = text.replace('\u00bd', ' mezzo ')    # ½ -> mezzo
    text = text.replace('\u00bc', ' un quarto ') # ¼ -> un quarto
    text = text.replace('\u00be', ' tre quarti ') # ¾ -> tre quarti

    # 10. Ordinali numerici italiani (PRIMA del simbolo grado generico)
    #     1° -> primo, 2° -> secondo, ... 10° -> decimo, poi -> N-esimo
    _ordinali = {
        '1': 'primo',  '2': 'secondo', '3': 'terzo',   '4': 'quarto',
        '5': 'quinto', '6': 'sesto',   '7': 'settimo', '8': 'ottavo',
        '9': 'nono',  '10': 'decimo',
    }
    def _fix_ordinale(m):
        n = m.group(1)
        return _ordinali.get(n, n + '-esimo')
    # Pattern: numero seguito da ° con/senza spazio, non preceduto da spazio isolato
    text = re.sub(r'\b(\d{1,2})\u00b0(?!\s*[CF\d])', _fix_ordinale, text)
    # 10.b Gradi di temperatura: 37°C -> 37 gradi, 37° C -> 37 gradi
    text = re.sub(r'(\d+)\s*\u00b0\s*[Cc]', r'\1 gradi', text)   # °C
    text = re.sub(r'(\d+)\s*\u00b0\s*[Ff]', r'\1 gradi', text)   # °F
    # Gradi rimasti (angoli, coordinate): 45° -> 45 gradi
    text = re.sub(r'(\d+)\s*\u00b0', r'\1 gradi', text)
    # Simbolo grado standalone (raro) -> rimosso
    text = text.replace('\u00b0', '')

    # 11. Abbreviazioni italiane comuni -> forma estesa
    #     Attenzione: sostituire PRIMA della pulizia caratteri speciali
    #     Ordine: più specifiche prima
    abbr = [
        (r'\bDott\.\s*ssa\b', 'dottoressa'),  # Dott.ssa (prima di dott.)
        (r'\bDott\.',         'dottor'),
        (r'\bdott\.\s*ssa\b', 'dottoressa'),
        (r'\bdott\.',         'dottor'),
        (r'\bProf\.\s*ssa\b', 'professoressa'),
        (r'\bProf\.',         'professore'),
        (r'\bprof\.\s*ssa\b', 'professoressa'),
        (r'\bprof\.',         'professore'),
        (r'\bSig\.\s*ra\b',   'signora'),    # Sig.ra
        (r'\bSig\.',          'signor'),
        (r'\bsig\.\s*ra\b',   'signora'),
        (r'\bsig\.',          'signor'),
        (r'\bAvv\.',          'avvocato'),
        (r'\bavv\.',          'avvocato'),
        (r'\bIng\.',          'ingegnere'),
        (r'\bing\.',          'ingegnere'),
        (r'\bArch\.',         'architetto'),
        (r'\barch\.',         'architetto'),
        (r'\bGen\.',          'generale'),
        (r'\bCap\.',          'capitano'),
        (r'\bNr\.',           'numero'),
        (r'\bnr\.',           'numero'),
        (r'\bN\.\s*(?=\d)',   'numero '),    # N.5 -> numero 5
        (r'\bn\.\s*(?=\d)',   'numero '),
        (r'\bArt\.',          'articolo'),
        (r'\bart\.',          'articolo'),
        (r'\becc\.',          'eccetera'),
        (r'\bEcc\.',          'eccetera'),
        (r'\bes\.',           'per esempio'),
        (r'\bEs\.',           'per esempio'),
        (r'\bvs\.',           'contro'),
        (r'\bVs\.',           'contro'),
        (r'\bcf\.',           'confronta'),
        (r'\bCf\.',           'confronta'),
        (r'\bp\.\s*es\.',     'per esempio'),  # p.es.
        (r'\bvol\.',          'volume'),
        (r'\bpag\.',          'pagina'),
        (r'\bcap\.',          'capitolo'),     # minuscolo (Cap. = capitano sopra)
        (r'\bpag\.',          'pagina'),
        (r'\bott\.',          'ottobre'),      # mesi abbreviati
        (r'\bgen\.',          'gennaio'),
        (r'\bfeb\.',          'febbraio'),
        (r'\bmar\.',          'marzo'),
        (r'\bapr\.',          'aprile'),
        (r'\bmag\.',          'maggio'),
        (r'\bgiu\.',          'giugno'),
        (r'\blug\.',          'luglio'),
        (r'\bago\.',          'agosto'),
        (r'\bset\.',          'settembre'),
        (r'\bnov\.',          'novembre'),
        (r'\bdic\.',          'dicembre'),
        (r'\bkm\b',           'chilometri'),
        (r'\bkm/h\b',         'chilometri orari'),
        (r'\bm/s\b',          'metri al secondo'),
        (r'\bcm\b',           'centimetri'),
        (r'\bmm\b',           'millimetri'),
        (r'\bkg\b',           'chilogrammi'),
        (r'\bg\b(?=\s)',       'grammi'),      # "g" isolata dopo numero
        (r'\bml\b',           'millilitri'),
        (r'\bcal\b',          'calorie'),
        (r'\bkcal\b',         'kilocalorie'),
    ]
    for pattern, repl in abbr:
        text = re.sub(pattern, repl, text)

    # 12. Parentesi tonde: (contenuto) -> , contenuto,
    #     Rende il contenuto parentetico leggibile senza glitch
    def _fix_parens(m):
        inner = m.group(1).strip()
        if not inner: return ''
        # Se il contenuto è solo numeri/simboli già convertiti: lascia
        return ', ' + inner + ','
    text = re.sub(r'\(([^)]{1,80})\)', _fix_parens, text)
    text = re.sub(r'\[[^\]]{1,80}\]', '', text)   # [note a piè di pagina] -> rimosso
    # Rimuove parentesi rimaste non chiuse
    text = re.sub(r'[()]', '', text)

    # 13. Punto e virgola -> virgola
    #     Chatterbox tende a ignorarlo o fare una pausa anomala
    text = text.replace(';', ',')

    # 14. Markdown inline: *testo* **testo** _testo_ -> testo
    text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+?)_{1,2}', r'\1', text)
    text = re.sub(r'`([^`]+?)`', r'\1', text)    # `codice` -> codice

    # 15. Barra / tra parole -> " o " (e/o, e/o -> e o)
    text = re.sub(r'(?<=\w)/(?=\w)', ' o ', text)

    # 16. Apostrofi + maiuscole dopo articoli italiani
    for art in ["l'", "nell'", "dell'", "sull'", "all'", "dall'", "un'"]:
        pat_art = re.compile(re.escape(art) + r'([A-Z])', re.IGNORECASE)
        text = pat_art.sub(lambda m, a=art: a + m.group(1).lower(), text)
    # Apostrofo + maiuscola generica residua
    text = re.sub(r"'([A-Z])(?=[a-z\u00c0-\u00f9])", lambda m: "'" + m.group(1).lower(), text)

    # 17. Parole TUTTO_MAIUSCOLO (3+ lettere) -> Prima lettera maiuscola
    #     Evita che Chatterbox deleteri lo spelling (CIA -> Cia)
    def _fix_allcaps(m):
        w = m.group(0)
        if len(w) >= 3 and w.isupper():
            return w.capitalize()
        return w
    text = re.sub(r'\b[A-Z]{3,}\b', _fix_allcaps, text)

    # 18. Accenti su maiuscole -> minuscole accentate (italiano + comuni europei)
    for up, lo in [('À','à'),('È','è'),('É','é'),('Ì','ì'),('Î','î'),
                   ('Ò','ò'),('Ó','ó'),('Ù','ù'),('Ú','ú'),('Â','â'),
                   ('Ê','ê'),('Ô','ô'),('Û','û'),('Ä','ä'),('Ë','ë'),
                   ('Ï','ï'),('Ö','ö'),('Ü','ü')]:
        text = text.replace(up, lo)

    # 19. Punteggiatura multipla -> singola
    text = re.sub(r'!{2,}', '!', text)     # !!! -> !
    text = re.sub(r'\?{2,}', '?', text)    # ??? -> ?
    text = re.sub(r',{2,}', ',', text)     # ,,, -> ,
    text = re.sub(r'([!?])\.', r'\1', text) # !. -> !

    # 20. Pulizia caratteri non TTS-safe
    #     Mantieni: lettere, numeri, spazi, punteggiatura base, accentate IT
    text = re.sub(r"[^\w\s.,!?'\"\-\u00c0-\u00f9]", ' ', text)

    # 21. Normalizzazione spazi e punteggiatura
    text = re.sub(r' +([.,!?])', r'\1', text)    # spazio prima di punteggiatura
    text = re.sub(r'([.,!?]) {2,}', r'\1 ', text) # doppi spazi dopo punteggiatura
    text = re.sub(r' {2,}', ' ', text)            # spazi multipli -> uno

    # 22. Ripristina tag protetti
    for ph, t in tm.items():
        text = text.replace(ph, t)

    return text.strip()


def newlines_to_pauses(text):
    """
    Converte gli accapo nel testo in tag pausa ChatterText.
    Da usare PRIMA di normalize_text, solo sul testo libero (non taggato).

    Regola:
      1 accapo   (\\n)     -> [p1]  pausa breve  ~0.18s
      2 accapo   (\\n\\n)  -> [p2]  pausa media  ~0.40s
      3+ accapo  (\\n\\n\\n+) -> [b] pausa lunga ~1.00s

    I blocchi [inizio]...[fine] vengono ignorati (già strutturati dall'utente).
    """
    # Se il testo ha già la struttura [inizio]/[fine], non toccare nulla
    if re.search(r'\[inizio\]', text, re.IGNORECASE):
        return text

    # 3+ accapo -> [b] pausa lunga
    text = re.sub(r'\n{3,}', ' [b] ', text)
    # 2 accapo -> [p2] pausa media
    text = re.sub(r'\n{2}', ' [p2] ', text)
    # 1 accapo -> [p1] pausa breve
    text = re.sub(r'\n', ' [p1] ', text)

    # Pulizia: rimuovi tag pausa duplicati o a inizio/fine
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
    # Puntini multipli residui (non dovrebbero esserci dopo normalize)
    raw_dots = re.findall(r"\.{2,}", tnt)
    if raw_dots:
        errs.append(("warning", "Puntini multipli residui: {} occorrenze".format(len(raw_dots))))
    # Caratteri speciali residui non TTS-safe
    sp = re.findall(r"[^\w\s.,!?\'\"\-\u00C0-\u00F9]", tnt)
    sp_uniq = list(dict.fromkeys(sp))[:10]
    if sp_uniq:
        errs.append(("warning", "Caratteri speciali residui: " + " ".join(sp_uniq)))
    caps = re.findall(r"[''`\u00b4]\w*[A-Z]\w*", text)
    if caps:
        errs.append(("info", "Maiuscole dopo apostrofo: " + ", ".join(caps[:3])))
    return errs


def chunk_text(text, min_w, max_w, max_c):
    tms = list(re.finditer(r"\[inizio\]([\s\S]*?)\[fine\]", text, re.IGNORECASE))
    if tms:
        chunks = []; emo = "|".join(ALL_EMO)
        vpat = re.compile(
            r"\[(v1|v2|v3|v4|v5|v6|v7)(?:_(?:"+emo+r"))?\]([\s\S]*?)\[/(?:v1|v2|v3|v4|v5|v6|v7)(?:_(?:"+emo+r"))?\]",
            re.IGNORECASE)
        for m in tms:
            cont = m.group(1).strip()
            if not cont: continue
            vml = list(vpat.finditer(cont))
            if vml:
                for vm in vml:
                    ft = vm.group(0).strip()
                    if vm.group(2).strip(): chunks.append(ft)
            else:
                if cont: chunks.append(cont)
        return chunks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for p in paragraphs:
        if len(p) <= max_c and len(p.split()) <= max_w:
            chunks.append(p); continue
        sentences = re.findall(r"[^.!?]+[.!?]+", p) or [p]; buf = ""
        for fr in sentences:
            test = (buf+" "+fr).strip() if buf else fr
            if len(test) > max_c or len(test.split()) > max_w:
                if buf.strip(): chunks.append(buf.strip())
                buf = fr
            else: buf = test
        if buf.strip(): chunks.append(buf.strip())
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
# SUONO (v2.8: volume ridotto del 50%)
# =========================================================
def play_sound():
    """
    Suono di completamento con volume ridotto del 50% rispetto a v2.7.
    Windows: durate Beep dimezzate (da [120,120,200,350] a [60,60,100,175])
    Mac:     afplay con volume -v 0.5
    Linux:   paplay con volume ridotto, fallback su print(\a)
    """
    try:
        if sys.platform == "win32":
            import winsound
            # Volume percepito ridotto dimezzando la durata di ogni tono
            for f, d in [(523, 60), (659, 60), (784, 100), (1047, 175)]:
                winsound.Beep(f, d)
                time.sleep(0.04)
        elif sys.platform == "darwin":
            # -v 0.5 = 50% volume su afplay
            subprocess.run(
                ["afplay", "-v", "0.5", "/System/Library/Sounds/Glass.aiff"],
                capture_output=True
            )
        else:
            if subprocess.run(["which","paplay"], capture_output=True).returncode == 0:
                # --volume=32768 = 50% del massimo 65536
                subprocess.run(
                    ["paplay", "--volume=32768",
                     "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                    capture_output=True
                )
            elif subprocess.run(["which","aplay"], capture_output=True).returncode == 0:
                subprocess.run(
                    ["aplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                    capture_output=True
                )
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
# PROMPT GUIDA NARRATIVA (v2.9)
# =========================================================
GUIDE_PROMPT = '''# PROMPT PER RISCRITTURA CAPITOLO - ChatterText TTS v2.9 - STILE NARRATIVA

Sei un editor specializzato nella preparazione di testi per la sintesi vocale con Chatterbox TTS.
Riscrivi il capitolo applicando il sistema di tag ChatterText v3.0 - STILE NARRATIVA.

## CASTING (opzionale ma consigliato)
  CASTING:
  V1 = Narratore
  V2 = Marco
  V3 = Elena
  V4 = Il Dottore   (antagonista)
  V5 = Voce narrante esterna
  V6 = Luigi        (personaggio minore)
  V7 = Anna         (personaggio minore)

## TAG VOCE (7 voci)
  [v1]...[/v1]  V1 = Narratore principale
  [v2]...[/v2]  V2 = Personaggio B / interlocutore
  [v3]...[/v3]  V3 = Personaggio C / voce interiore
  [v4]...[/v4]  V4 = Antagonista / voce oscura
  [v5]...[/v5]  V5 = Narratore esterno / voce onnisciente
  [v6]...[/v6]  V6 = Personaggio minore (fallback V1 se non configurato)
  [v7]...[/v7]  V7 = Personaggio minore (fallback V1 se non configurato)
  Con emozione: [V1_calmo]...[/V1_calmo]

## STATI EMOTIVI
  calmo | appassionato | arrabbiato | triste | ironico
  sussurrato | riflessivo | deciso | preoccupato | gentile | serio
  solenne | estatico | malinconico | vibrante | intimo

## PAUSE INLINE - 6 livelli standard
  [p1] ~0.18s  virgola, inciso breve
  [p2] ~0.40s  punto normale - la piu usata
  [p3] ~0.65s  riflessione, domanda, cambio tono
  [b]  ~1.00s  cambio idea importante, due punti
  [bd] ~1.60s  climax, rivelazione, suspense
  [cap]~2.00s  reset mentale, nuovo paragrafo

## ENFASI
  [e1]  enfasi leggera  (+0.10)
  [e2]  enfasi forte    (+0.25 - max 1 ogni 2-3 blocchi)
  [ep]  enfasi poetica  (+0.15 - per parole chiave emotive)

## GIUNZIONI
  [cambio]     V1<->V2  cambio voce principale
  [cambio3..7] cambio con le altre voci
  [para]       fine paragrafo stessa voce
  [stacco]     cambio pensiero stessa voce
  [lungo]      pausa teatrale
  [scena]      cambio scena / capitolo
  [dissolvenza] fade lungo tra sezioni (1.60s)

## PULIZIA AUTOMATICA v2.9 - NON usare questi caratteri nel testo taggato
  ChatterText li converte automaticamente durante "Analizza e Processa":
  "..."  ->  .    (tre puntini: usa [p3] [b] [bd] per le pause lunghe)
  ";"    ->  ,    (punto e virgola: gia convertito, non aggiungere ;)
  "--"   ->  ,    (doppio trattino)
  "ecc." ->  eccetera   (e tutte le abbreviazioni comuni)
  "€ $ %" -> euro dollari percento
  "(testo)" -> , testo,  (parentesi trasformate in virgole)
  "*testo*" -> testo     (markdown rimosso)

## NOTA IMPORTANTE - ACCAPO COME PAUSE
  Nel testo SENZA tag strutturali ([inizio]/[fine]) gli accapo diventano pause:
    1 accapo (Enter)    -> [p1] pausa breve ~0.18s
    2 accapo (Enter x2) -> [p2] pausa media ~0.40s
    3+ accapo           -> [b]  pausa lunga ~1.00s
  Nei testi con tag [inizio]/[fine] gli accapo vengono ignorati:
  usa sempre i tag pause espliciti ([p1] [p2] [p3] [b] [bd]).

## REGOLA ANTI-GLITCH
  MAI blocchi con meno di 5 parole pulite.
  SEMPRE un tag giunzione prima di [/Vn_emozione][fine].
  MAI punto e virgola ";" nel testo (viene gia convertito ma e meglio evitarlo).
  MAI tre puntini "..." nel testo (usa i tag pausa al loro posto).

## ESEMPIO STRUTTURA CORRETTA

[inizio][V1_riflessivo]
Era una sera strana,[p2] il tipo di sera in cui l'aria sembra ferma.[b]
[/V1_riflessivo][para]
[V1_preoccupato]
Marco si fermo sul portone[p1] e guardo il cielo.[p2][stacco]
[/V1_preoccupato][fine]

[inizio][V2_deciso]
Non posso aspettare ancora,[p2] disse.[cambio]
[/V2_deciso][fine]

---
Ora riscrivi il seguente capitolo:

[INCOLLA QUI IL TESTO]
'''

# =========================================================
# PROMPT GUIDA POETICA (v2.9)
# =========================================================
POETRY_PROMPT = '''# PROMPT PER TESTO POETICO - ChatterText TTS v2.9 - STILE POESIA

Sei un editor specializzato nella preparazione di POESIE per la sintesi vocale Chatterbox TTS.
Riscrivi la poesia applicando il sistema di tag ChatterText v3.0 - STILE POESIA.

In modalita POESIA i parametri TTS sono ottimizzati per:
  - Esaggerazione alta (0.82) per massima espressivita
  - Temperature alta (0.72) per naturalezza recitata
  - Pause scale 1.45x: tutte le pause durano il 45% in piu del normale
  - Stile recitato, non letto: ogni verso ha un arco emotivo

## TAG POETICI SPECIALI (solo in modalita Poesia)
  [verso]       ~0.44s effettivi  fine verso con respiro leggero
  [strofa]      ~1.74s effettivi  fine strofa, pausa piena, reset emotivo
  [metro]       ~0.12s effettivi  micro-pausa sull'accento metrico
  [enjambement] ~0.07s effettivi  verso che scorre nel successivo (quasi zero)
  [cesura]      ~0.65s effettivi  pausa interna al verso (tra emistichi)
  [dissolvenza]                   giunzione fade lungo tra strofe (1.60s)

## TAG VOCE PER POESIA
  [v1]...[/v1]  Voce principale del poema
  [v2]...[/v2]  Voce seconda (es: interlocutore nel dialogo lirico)
  Con emozioni poetiche: solenne | estatico | malinconico | vibrante | intimo
  E standard:            calmo | appassionato | triste | riflessivo | sussurrato

## PAUSE INLINE (con scale 1.45x in modalita Poesia)
  [p1] ~0.26s effettivi  virgola leggera dentro il verso
  [p2] ~0.58s effettivi  fine verso con punto
  [p3] ~0.94s effettivi  riflessione profonda
  [b]  ~1.45s effettivi  cambio di immagine poetica
  [bd] ~2.32s effettivi  culmine, rivelazione, silenzio drammatico

## PULIZIA AUTOMATICA v2.9 - NON usare questi caratteri nel testo taggato
  ChatterText li converte automaticamente durante "Analizza e Processa":
  "..."  ->  .    (tre puntini: usa [cesura] [p3] [b] per le sospensioni)
  ";"    ->  ,    (punto e virgola: usa i tag pausa invece)
  "(nota)" -> , nota,  (parentesi trasformate in virgole)
  "--"   ->  ,    (doppio trattino)
  Simboli €%&×°  -> parole (euro, percento, per, gradi...)

## NOTA IMPORTANTE - ACCAPO NEL TESTO POETICO
  Con tag [inizio]/[fine] gli accapo vengono ignorati: usa sempre i tag
  poetici espliciti al posto degli a capo naturali del verso.
  CORRETTO:
    [inizio][V1_malinconico]
    Scende la sera[cesura] senza rumore.[verso]
    [/V1_malinconico][fine]
  SBAGLIATO: non lasciare accapo nudi sperando che diventino pause,
  nei blocchi taggati non funziona: usa [verso] [cesura] [strofa].

## STRUTTURA BASE PER POESIA

[inizio][V1_malinconico]
Scende la sera[cesura] senza rumore.[verso]
[/V1_malinconico][fine]

[inizio][V1_malinconico]
Ogni finestra[cesura] nasconde un dolore.[verso]
[/V1_malinconico][fine]

Fine strofa con dissolvenza:
[inizio][V1_solenne]
E il vento porta via[ep] l'ultima voce.[p3][dissolvenza]
[/V1_solenne][fine]

Enjambement (verso che scorre):
[inizio][V1_vibrante]
Il cielo si apre[enjambement]
[/V1_vibrante][fine]

[inizio][V1_vibrante]
come una ferita di luce.[verso]
[/V1_vibrante][fine]

## REGOLE OBBLIGATORIE PER POESIA
  1. MAI blocchi con meno di 5 parole pulite
  2. Ogni verso termina con [verso] OPPURE [enjambement] OPPURE [strofa]
  3. SEMPRE giunzione ([verso]/[strofa]/[dissolvenza]) prima di [/Vn_emozione][fine]
  4. Emozione costante per strofa (non cambiare emozione verso per verso)
  5. [ep] sulle parole-immagine piu forti (max 2-3 per strofa)
  6. [e2] solo al culmine emotivo del poema (1-2 volte totali)
  7. MAI "..." nel testo: usa [cesura] per la sospensione poetica
  8. MAI ";" nel testo: usa [p1] o [cesura] al suo posto
  9. Rispondere SOLO con il testo taggato, senza spiegazioni

---
Ora prepara la seguente poesia:

[INCOLLA QUI LA POESIA]
'''

# =========================================================
# BUILD SCRIPT PYTHON (v2.9)
# =========================================================
def build_python_script(chunks, exag, cfg, temp, v1, v2, v3, v4, v5, v6, v7,
                        epreset, devmode="auto", reading_style="narrativa",
                        noise_gate_db=-50, rms_target_db=-18, trim_threshold_db=-45,
                        pause_scale=1.0, aggressive_clean=False,
                        strip_lead_ms=120, strip_tail_ms=80,
                        spectral_gate=False, declick=True,
                        fade_ms=14, boundary_smooth_ms=35):
    has2   = bool(v2.strip())
    has3   = bool(v3.strip())
    has4   = bool(v4.strip())
    has5   = bool(v5.strip())
    has6   = bool(v6.strip())
    has7   = bool(v7.strip())
    v2eff  = v2.strip() if has2 else v1
    v3eff  = v3.strip() if has3 else v1
    v4eff  = v4.strip() if has4 else v1
    v5eff  = v5.strip() if has5 else v1
    v6eff  = v6.strip() if has6 else v1
    v7eff  = v7.strip() if has7 else v1
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

    L = [
"# Script generato da ChatterText v3.0",
"# Stile: {}  |  Anti-artefatti: strip_lead={}ms strip_tail={}ms".format(reading_style, strip_lead_ms, strip_tail_ms),
"# spectral_gate={}  declick={}  boundary_smooth={}ms".format(spectral_gate, declick, boundary_smooth_ms),
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
"DEF_P={{'exaggeration':{},'cfg_weight':{},'temperature':{},'top_p':0.75,'min_p':0.15}}".format(exag,cfg,temp),
"PAUSE_SCALE={}".format(pause_scale),
"NOISE_GATE_DB={}".format(noise_gate_db),
"RMS_TARGET_DB={}".format(rms_target_db),
"TRIM_DB={}".format(trim_threshold_db),
"STRIP_LEAD_MS={}".format(strip_lead_ms),
"STRIP_TAIL_MS={}".format(strip_tail_ms),
"USE_SPECTRAL_GATE={}".format(spectral_gate),
"USE_DECLICK={}".format(declick),
"FADE_MS={}".format(fade_ms),
"BOUNDARY_SMOOTH_MS={}".format(boundary_smooth_ms),
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
"    def si(t):",
"        t=PR.sub('',t); t=ER.sub('',t); t=JR.sub('',t); return t.strip()",
"    m=re.search(r'\\[(v1|v2|v3|v4|v5|v6|v7)_(' +EN+r')\\]',chunk,re.IGNORECASE)",
"    if m:",
"        v,e=m.group(1).lower(),m.group(2).lower()",
"        cl=re.sub(r'\\[(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\\]','',chunk,flags=re.IGNORECASE)",
"        cl=re.sub(r'\\[/(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\\]','',cl,flags=re.IGNORECASE)",
"        return si(cl),v,e,ps,tp,ek,jk",
"    m=re.search(r'\\[(v1|v2|v3|v4|v5|v6|v7)\\]',chunk,re.IGNORECASE)",
"    if m:",
"        v=m.group(1).lower()",
"        cl=re.sub(r'\\[/?(?:v1|v2|v3|v4|v5|v6|v7)\\]','',chunk,flags=re.IGNORECASE)",
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
"# ============================================================",
"# ANTI-ARTEFATTI v3.0",
"# ============================================================",
"def noise_gate(wav, sr, gate_db=NOISE_GATE_DB, hpz=80, attack_ms=8, release_ms=60):",
"    thr=10**(gate_db/20)",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    wav=ta.functional.highpass_biquad(wav, sr, cutoff_freq=hpz)",
"    env=torch.abs(wav[0])",
"    att=int(sr*attack_ms/1000); rel=int(sr*release_ms/1000)",
"    gate=torch.zeros_like(env); g=0.0",
"    for i in range(len(env)):",
"        target=1.0 if env[i]>thr else 0.0",
"        if target>g: g=g+(1.0-g)/max(1,att)",
"        else: g=g*(1.0-1.0/max(1,rel))",
"        gate[i]=g",
"    return wav*gate.unsqueeze(0)",
"def strip_leading_artifacts(wav, sr, max_ms=STRIP_LEAD_MS):",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    w=wav[0]; max_samp=int(sr*max_ms/1000)",
"    if max_samp<2 or w.shape[-1]<max_samp*3: return wav",
"    win=int(sr*0.010); zone=w[:max_samp*2]",
"    frames=zone.unfold(0,win,win//2) if zone.shape[0]>=win else zone.unsqueeze(0)",
"    rms_frames=torch.sqrt((frames**2).mean(dim=-1)+1e-10)",
"    body_start=int(sr*0.1); body_end=min(int(sr*1.0),w.shape[-1])",
"    body_rms=torch.sqrt((w[body_start:body_end]**2).mean()+1e-10) if body_end>body_start else rms_frames.max()",
"    threshold=body_rms*0.12",
"    above=(rms_frames>threshold).nonzero(as_tuple=True)",
"    if len(above[0])==0: return wav",
"    first_frame=above[0][0].item()",
"    cut=min(first_frame*(win//2), max_samp)",
"    result=wav[...,cut:].clone()",
"    fi=min(int(sr*0.008),result.shape[-1])",
"    if fi>0: result[...,:fi]*=torch.linspace(0,1,fi)",
"    return result",
"def strip_trailing_artifacts(wav, sr, max_ms=STRIP_TAIL_MS):",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    w=wav[0]; max_samp=int(sr*max_ms/1000)",
"    if max_samp<2 or w.shape[-1]<max_samp*3: return wav",
"    win=int(sr*0.010); zone=w[-max_samp*2:]",
"    frames=zone.unfold(0,win,win//2) if zone.shape[0]>=win else zone.unsqueeze(0)",
"    rms_frames=torch.sqrt((frames**2).mean(dim=-1)+1e-10)",
"    body_start=max(0,w.shape[-1]-int(sr*1.0)); body_end=max(0,w.shape[-1]-int(sr*0.1))",
"    body_rms=torch.sqrt((w[body_start:body_end]**2).mean()+1e-10) if body_end>body_start else rms_frames.max()",
"    threshold=body_rms*0.10",
"    above=(rms_frames>threshold).nonzero(as_tuple=True)",
"    if len(above[0])==0: return wav",
"    last_frame=above[0][-1].item(); n_frames=rms_frames.shape[0]",
"    cut_from_end=min((n_frames-1-last_frame)*(win//2), max_samp)",
"    end_idx=wav.shape[-1]-cut_from_end",
"    if end_idx<=0: return wav",
"    result=wav[...,:end_idx].clone()",
"    fo=min(int(sr*0.008),result.shape[-1])",
"    if fo>0: result[...,-fo:]*=torch.linspace(1,0,fo)",
"    return result",
"def spectral_gate_fn(wav, sr, reduction_db=10):",
"    if not USE_SPECTRAL_GATE: return wav",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    n_fft=1024; hop=256",
"    try:",
"        spec=torch.stft(wav[0],n_fft=n_fft,hop_length=hop,win_length=n_fft,",
"                        return_complex=True,window=torch.hann_window(n_fft))",
"        mag=spec.abs(); phase=spec.angle()",
"        noise_profile=mag[:,:5].mean(dim=-1,keepdim=True)",
"        reduction=10**(reduction_db/20)",
"        mask=(mag/(noise_profile*reduction+1e-8)).clamp(0,1)",
"        k=torch.ones(1,1,5)/5",
"        mask_s=torch.nn.functional.conv1d(mask.unsqueeze(0).float(),k,padding=2).squeeze(0).clamp(0,1)",
"        spec_out=torch.polar(mag*mask_s,phase)",
"        out=torch.istft(spec_out,n_fft=n_fft,hop_length=hop,win_length=n_fft,",
"                        window=torch.hann_window(n_fft),length=wav.shape[-1])",
"        return out.unsqueeze(0)",
"    except: return wav",
"def declick_v3(wav, sr):",
"    if not USE_DECLICK: return wav",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    w=int(sr*0.003)+1",
"    if w<2 or wav.shape[-1]<w*2: return wav",
"    kern=torch.ones(1,1,w)/w",
"    smoothed=torch.nn.functional.conv1d(wav.float().unsqueeze(0),kern,padding=w//2).squeeze(0)",
"    diff=torch.abs(wav-smoothed); thr=diff.std()*4.0",
"    mask=(diff>thr).float()",
"    k2=max(3,int(sr*0.001))",
"    if k2%2==0: k2+=1",
"    k2t=torch.ones(1,1,k2)/k2",
"    mask=torch.nn.functional.conv1d(mask.unsqueeze(0),k2t,padding=k2//2).squeeze(0).clamp(0,1)",
"    return wav*(1-mask)+smoothed*mask",
"def adaptive_trim(wav, sr, threshold_db=TRIM_DB, pad_ms=30):",
"    thr=10**(threshold_db/20); mg=int(sr*pad_ms/1000)",
"    mo=wav[0] if wav.dim()>1 else wav; en=torch.abs(mo)",
"    indices=(en>thr).nonzero(as_tuple=True)[0]",
"    if len(indices)==0: return wav",
"    s=max(0,indices[0].item()-mg); e=min(len(en),indices[-1].item()+mg)",
"    return wav[...,s:e]",
"def smooth_boundary(wav, sr, ms=BOUNDARY_SMOOTH_MS):",
"    n=int(sr*ms/1000)",
"    if n<2 or wav.shape[-1]<n*4: return wav",
"    wav=wav.clone(); t=torch.linspace(0,1,n)",
"    s_curve=3*t**2-2*t**3",
"    wav[...,:n]*=s_curve; wav[...,-n:]*=(1-s_curve)",
"    return wav",
"def apply_fade(wav, sr, fade_ms=FADE_MS):",
"    f=int(sr*fade_ms/1000); wav=wav.clone()",
"    if f>0 and wav.shape[-1]>f*2:",
"        wav[...,:f]*=torch.linspace(0,1,f)",
"        wav[...,-f:]*=torch.linspace(1,0,f)",
"    return wav",
"def rms_normalize(wav, target_db=RMS_TARGET_DB):",
"    if wav.dim()==1: wav=wav.unsqueeze(0)",
"    rms=torch.sqrt(torch.mean(wav**2)+1e-8)",
"    target_rms=10**(target_db/20)",
"    gain=min(target_rms/rms, 10.0)",
"    wav=wav*gain; wav=torch.tanh(wav*0.9)*1.1",
"    return wav.clamp(-0.98,0.98)",
"def full_process(wav, sr):",
"    wav=noise_gate(wav, sr)              # 1. noise gate energetico",
"    wav=strip_leading_artifacts(wav, sr)  # 2. rimuovi artefatti inizio",
"    wav=strip_trailing_artifacts(wav, sr) # 3. rimuovi artefatti fine",
"    wav=spectral_gate_fn(wav, sr)         # 4. gate spettrale (se abilitato)",
"    wav=declick_v3(wav, sr)               # 5. de-click adattivo (se abilitato)",
"    wav=adaptive_trim(wav, sr)            # 6. trim adattivo",
"    wav=smooth_boundary(wav, sr)          # 7. smooth boundary",
"    wav=apply_fade(wav, sr)               # 8. fade in/out",
"    wav=rms_normalize(wav)                # 9. normalizzazione RMS",
"    return wav",
"segs=[]; fail=[]",
"st=time.time()",
"print('\\n'+'='*55)",
"print('AVVIO GENERAZIONE [{}]  Anti-artefatti v3.0'.format(DEVICE.type.upper()))",
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
"    if tp>0: print('   pausa: {:.2f}s (gauss x{:.2f})'.format(tp, PAUSE_SCALE))",
"    if len(txt.split())<5: print('   ATTENZIONE: chunk corto!')",
"    if   vo=='v7' and HAS7: vp=AUDIO_V7",
"    elif vo=='v6' and HAS6: vp=AUDIO_V6",
"    elif vo=='v5' and HAS5: vp=AUDIO_V5",
"    elif vo=='v4' and HAS4: vp=AUDIO_V4",
"    elif vo=='v3' and HAS3: vp=AUDIO_V3",
"    elif vo=='v2' and HAS2: vp=AUDIO_V2",
"    else:                   vp=AUDIO_V1",
"    p=pp(em,ek); ok=False",
"    try:",
"        wav=model.generate(txt,language_id='it',audio_prompt_path=vp,",
"            exaggeration=p['exaggeration'],cfg_weight=p['cfg_weight'],",
"            temperature=p['temperature'],min_p=p['min_p'],top_p=p['top_p'])",
"        if DEVICE.type=='cuda': wav=wav.cpu()",
"        wav=full_process(wav, model.sr)",
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
"            wav=full_process(wav, model.sr)",
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
"        pau=dyn_pause(chunks[i-1], emo=tc[i-1][2])",
"        sil=torch.zeros((seg.shape[0],int(model.sr*pau)))",
"        fa=cf(fa,torch.cat([sil,seg],dim=-1),model.sr)",
"        js='auto({:.2f}s)'.format(pau)",
"    else: fa=res; js=jt if jt else 'auto'",
"    print(f'   -> join {i}: {js}')",
"fa=rms_normalize(fa)",
"ta.save(out,fa,model.sr)",
"dur=fa.shape[-1]/model.sr; tot=time.time()-st",
"print(f'\\n FILE: {out}')",
"print(f'   Durata: {dur:.1f}s ({dur/60:.1f} min)')",
"print(f'   Tempo:  {tot:.1f}s ({tot/60:.1f} min)')",
"print(f'   Device: {DEVICE.type.upper()}')",
"print(f'   Anti-artefatti: strip_lead={STRIP_LEAD_MS}ms  strip_tail={STRIP_TAIL_MS}ms  declick={USE_DECLICK}')",
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
        for emo in ALL_EMO:
            r[emo] = {}
            for p in self.PARAMS:
                try: r[emo][p] = round(float(self.vs[emo][p].get()), 3)
                except: r[emo][p] = EMOTION_PRESETS[emo][p]
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
        self.title("ChatterText v3.0")
        self.geometry("1100x1040"); self.minsize(900,700)
        self.configure(bg=C["bg"])
        self.chunks = []; self.chunk_vars = []; self.script_path = None
        self.epreset = {k: v.copy() for k, v in EMOTION_PRESETS.items()}
        self._proc = None; self._t0 = None
        self.vwords   = tk.StringVar(value="0")
        self.vchars   = tk.StringVar(value="0")
        self.vchunks  = tk.StringVar(value="0")
        self.verrs    = tk.StringVar(value="0")
        self.vdev     = tk.StringVar(value="auto")
        self.vsound   = tk.BooleanVar(value=True)
        self.vreadstyle = tk.StringVar(value="narrativa")
        self.vaggclean  = tk.BooleanVar(value=False)
        # Anti-artefatti v3.0
        self.vantipre      = tk.StringVar(value="standard")
        self.vstrip_lead   = tk.StringVar(value="120")
        self.vstrip_tail   = tk.StringVar(value="80")
        self.vspec_gate    = tk.BooleanVar(value=False)
        self.vdeclick      = tk.BooleanVar(value=True)
        self.vfade_ms      = tk.StringVar(value="14")
        self.vbsm          = tk.StringVar(value="35")
        self._build_ui(); self._detect_device()

    # ---- LAYOUT ----
    def _build_ui(self):
        canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        scr    = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
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
        self._hdr(r); self._dev_sec(r)
        self._inp_sec(r); self._ctrl_sec(r)
        self._style_sec(r); self._antiarti_sec(r)
        self._stats_sec(r); self._log_sec(r); self._chunks_sec(r)
        self._guide_sec(r); self._footer(r)

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
        h = tk.Frame(r, bg="#0a1628", pady=24); h.pack(fill="x")
        tk.Label(h, text="ChatterText", font=FH1, fg="#fff", bg="#0a1628").pack()
        tk.Label(h, text="Analizza e prepara il testo per Chatterbox TTS",
                 font=FB, fg=C["text_dim"], bg="#0a1628").pack(pady=(4,0))
        tk.Label(h, text="v3.0  |  Anti-Artefatti  |  4 Stili  |  Tag Poetici  |  7 Voci  |  Accapo come pause  |  Pulizia testo avanzata",
                 font=FS, fg=C["gpu"], bg="#0a1628").pack(pady=(2,0))

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
        nf = sf(top); nf.pack(side="right")
        tk.Checkbutton(nf, text="Suono fine generazione (vol -50%)", variable=self.vsound,
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
                {"narrativa":"📖","poesia":"🎭","teatro":"🎪","audiolibro_lungo":"📚"}.get(key,""),
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

        self._set_style("narrativa")

    def _set_style(self, key):
        self.vreadstyle.set(key)
        st = READING_STYLES[key]
        col = st["color"]
        self.style_name_lbl.config(text=st["label"], fg=col)
        self.style_desc_lbl.config(text=st["desc"])
        self.style_notes_lbl.config(text=st["notes"])
        self.style_info_f.config(highlightbackground=col)
        if hasattr(self, 'vexag'):
            self.vexag.set(str(st["exaggeration"]))
            self.vcfg.set(str(st["cfg_weight"]))
            self.vtemp.set(str(st["temperature"]))
        if hasattr(self, 'vng'):
            self.vng.set(str(st["noise_gate_db"]))
            self.vrms.set(str(st["rms_target_db"]))
            self.vtrim.set(str(st["trim_threshold_db"]))

    def _copy_prompt(self, style):
        if style == "poesia":
            self.clipboard_clear(); self.clipboard_append(POETRY_PROMPT)
            messagebox.showinfo("Copiato!", "Prompt POESIA v3.0 copiato!\n"
                                "Include tag poetici: [verso] [strofa] [metro] [enjambement] [cesura]")
        else:
            self.clipboard_clear(); self.clipboard_append(GUIDE_PROMPT)
            messagebox.showinfo("Copiato!", "Prompt NARRATIVA v3.0 copiato!")

    def _save_all_prompts(self):
        dest = pathlib.Path(self.vdir.get() if hasattr(self,'vdir') else str(pathlib.Path.cwd()))
        p1 = dest / "PROMPT_NARRATIVA_v3.0.txt"
        p2 = dest / "PROMPT_POESIA_v3.0.txt"
        p1.write_text(GUIDE_PROMPT, encoding="utf-8")
        p2.write_text(POETRY_PROMPT, encoding="utf-8")
        messagebox.showinfo("Salvati!", "Salvati:\n{}\n{}".format(p1, p2))

    # ---- ANTI-ARTEFATTI v3.0 ----
    def _antiarti_sec(self, r):
        sec = self._sec(r, "Anti-Artefatti v3.0")

        # Info box
        info = tk.Frame(sec, bg="#001a1a", highlightthickness=1,
                        highlightbackground=C["antiart"], padx=14, pady=10)
        info.pack(fill="x", pady=(0,12))
        tk.Label(info, text="[AA] Pipeline di pulizia audio su ogni chunk — elimina click, parole spurie e rumore di fondo",
                 font=FL, fg=C["antiart"], bg="#001a1a").pack(anchor="w")
        rows = [
            ("strip_leading",   "rimuove parole/click spurie ALL'INIZIO del chunk (max N ms)"),
            ("strip_trailing",  "rimuove rumori/click ALLA FINE del chunk (max N ms)"),
            ("smooth_boundary", "curva-S sui bordi per zero click di giunzione tra chunk"),
            ("spectral_gate",   "riduce hiss/rumore stazionario (opzionale, solo audio rumorosi)"),
            ("declick_v3",      "corregge picchi impulsivi con soglia adattiva 4x std"),
            ("adaptive_trim",   "trim intelligente basato su energia locale del segnale"),
            ("rms_normalize",   "livello coerente tra tutti i chunk dell'audiolibro"),
        ]
        for name, desc in rows:
            row = tk.Frame(info, bg="#001a1a"); row.pack(fill="x", pady=1)
            tk.Label(row, text=name, font=("Courier New",8,"bold"), fg=C["antiart"],
                     bg="#001a1a", width=18, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=FS, fg=C["text_dim"],
                     bg="#001a1a", anchor="w").pack(side="left")

        # Preset buttons
        prow = sf(sec); prow.pack(fill="x", pady=(0,8))
        tk.Label(prow, text="Preset:", font=FL, fg=C["antiart"], bg=C["surface"]).pack(side="left", padx=(0,10))
        self._anti_btns = {}
        for key, pr in ANTIARTI_PRESETS.items():
            col = {"leggero": C["success"], "standard": C["antiart"], "aggressivo": C["danger"]}[key]
            btn = sb_btn(prow, pr["label"], lambda k=key: self._set_antiarti(k), color=col, padx=16, pady=8)
            btn.pack(side="left", padx=(0,8))
            self._anti_btns[key] = btn

        self.anti_desc = tk.Label(sec, text=ANTIARTI_PRESETS["standard"]["desc"],
                                  font=FS, fg=C["text_dim"], bg=C["surface"], anchor="w")
        self.anti_desc.pack(fill="x", pady=(0,10))

        # Parametri manuali
        pr1 = sf(sec); pr1.pack(fill="x", pady=(0,6))
        tk.Label(pr1, text="Strip inizio (ms):", font=FL, fg=C["antiart"], bg=C["surface"]).pack(side="left", padx=(0,6))
        se(pr1, width=6, textvariable=self.vstrip_lead).pack(side="left", padx=(0,18))
        tk.Label(pr1, text="Strip fine (ms):", font=FL, fg=C["antiart"], bg=C["surface"]).pack(side="left", padx=(0,6))
        se(pr1, width=6, textvariable=self.vstrip_tail).pack(side="left", padx=(0,18))
        tk.Label(pr1, text="Fade (ms):", font=FL, fg=C["antiart"], bg=C["surface"]).pack(side="left", padx=(0,6))
        se(pr1, width=6, textvariable=self.vfade_ms).pack(side="left", padx=(0,18))
        tk.Label(pr1, text="Boundary smooth (ms):", font=FL, fg=C["antiart"], bg=C["surface"]).pack(side="left", padx=(0,6))
        se(pr1, width=6, textvariable=self.vbsm).pack(side="left")

        pr2 = sf(sec); pr2.pack(fill="x", pady=(6,0))
        tk.Checkbutton(pr2, text="Spectral Gate (riduce hiss, solo per audio molto rumorosi)",
                       variable=self.vspec_gate, font=FB, fg=C["warning"], bg=C["surface"],
                       selectcolor=C["surface2"], activeforeground=C["warning"],
                       activebackground=C["surface"], cursor="hand2").pack(side="left", padx=(0,20))
        tk.Checkbutton(pr2, text="De-click v3 (corregge picchi impulsivi)",
                       variable=self.vdeclick, font=FB, fg=C["text"], bg=C["surface"],
                       selectcolor=C["surface2"], activeforeground=C["accent"],
                       activebackground=C["surface"], cursor="hand2").pack(side="left")

        # Post-processing classico (noise gate, rms, trim)
        pp_row = sf(sec); pp_row.pack(fill="x", pady=(10,0))
        tk.Label(pp_row, text="Post-proc:", font=FL, fg=C["accent"], bg=C["surface"]).pack(side="left", padx=(0,10))
        self.vng   = self._le(pp_row, "Noise gate (dB)", "-50")
        self.vrms  = self._le(pp_row, "RMS target (dB)", "-18")
        self.vtrim = self._le(pp_row, "Trim threshold (dB)", "-45")

        self._set_antiarti("standard")

    def _set_antiarti(self, key):
        self.vantipre.set(key)
        pr = ANTIARTI_PRESETS[key]
        self.anti_desc.config(text=pr["desc"])
        self.vstrip_lead.set(str(pr["strip_lead_ms"]))
        self.vstrip_tail.set(str(pr["strip_tail_ms"]))
        self.vspec_gate.set(pr["spectral_gate"])
        self.vdeclick.set(pr["declick"])
        self.vfade_ms.set(str(pr["fade_ms"]))
        self.vbsm.set(str(pr["boundary_smooth_ms"]))
        if hasattr(self, "vng"):
            self.vng.set(str(pr["noise_gate_db"]))
            self.vrms.set(str(pr["rms_target_db"]))
            self.vtrim.set(str(pr["trim_db"]))

    def _inp_sec(self, r):
        sec = self._sec(r, "Testo")
        # v2.8: altezza aumentata da 10 a 14
        self.txt = scrolledtext.ScrolledText(
            sec, height=14,
            bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", bd=0,
            font=FM, wrap="word",
            highlightthickness=1, highlightbackground=C["border"]
        )
        self.txt.pack(fill="x", pady=(0,10))
        self.txt.insert("1.0", "Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.txt.bind("<FocusIn>", lambda e: self.txt.delete("1.0","end")
                      if "Incolla qui" in self.txt.get("1.0","end-1c") else None)
        self.vcc = tk.StringVar(value="0 / 10000")
        tk.Label(sec, textvariable=self.vcc, font=FS, fg=C["text_dim"],
                 bg=C["surface"], anchor="e").pack(fill="x")
        self.txt.bind("<KeyRelease>", lambda e: self.vcc.set(
            "{} / 10000".format(len(self.txt.get("1.0","end-1c")))))

    def _ctrl_sec(self, r):
        sec = self._sec(r, "Parametri")
        r1 = sf(sec); r1.pack(fill="x", pady=(0,10))
        self.vminw = self._le(r1, "Min parole/chunk", "20")
        self.vmaxw = self._le(r1, "Max parole/chunk", "40")
        self.vmaxc = self._le(r1, "Max caratteri", "240")

        # Voci
        r2 = sf(sec); r2.pack(fill="x", pady=(0,4))
        self.vv1 = self._le(r2, "Voce 1 - Narratore (2.Voci/)", "3l14n.wav", wide=True)
        self.vv2 = self._le(r2, "Voce 2 - Personaggio B (opz.)", "", wide=True)
        self.vv3 = self._le(r2, "Voce 3 - Personaggio C (opz.)", "", wide=True)
        r2b = sf(sec); r2b.pack(fill="x", pady=(0,4))
        self.vv4 = self._le(r2b, "Voce 4 - Antagonista (opz.)", "", wide=True)
        self.vv5 = self._le(r2b, "Voce 5 - Narratore esterno (opz.)", "", wide=True)
        r2c = sf(sec); r2c.pack(fill="x", pady=(0,10))
        self.vv6 = self._le(r2c, "Voce 6 - Pers. minore (opz.)", "", wide=True)
        self.vv7 = self._le(r2c, "Voce 7 - Pers. minore (opz.)", "", wide=True)
        tk.Label(r2c, text="  V6/V7: se vuote -> fallback V1", font=FS,
                 fg=C["v6"], bg=C["surface"]).pack(side="left", padx=(4,0), anchor="s", pady=(0,4))
        gv = sf(r2c); gv.pack(side="right", padx=(8,0), anchor="s")
        sb_btn(gv, "Verifica voci", self._verify_voices, color=C["text_dim"]).pack(pady=(18,0))

        # Parametri TTS
        r3 = sf(sec); r3.pack(fill="x", pady=(0,10))
        self.vexag = self._le(r3, "Exaggeration", "0.62")
        self.vcfg  = self._le(r3, "CFG Weight", "0.70")
        self.vtemp = self._le(r3, "Temperature", "0.58")
        gp = sf(r3); gp.pack(side="left", padx=(16,0))
        tk.Label(gp, text="Preset emotivi", font=FL, fg=C["accent"], bg=C["surface"]).pack(anchor="w")
        sb_btn(gp, "Modifica", self._presets, color="#8e44ad").pack(anchor="w", pady=(4,0))

        r4 = sf(sec); r4.pack(fill="x", pady=(0,14))
        tk.Label(r4, text="Cartella Chatterbox:", font=FL, fg=C["accent"], bg=C["surface"]).pack(side="left", padx=(0,8))
        try:
            _app_dir = str(pathlib.Path(__file__).resolve().parent)
        except NameError:
            _app_dir = str(pathlib.Path.cwd())
        self.vdir = tk.StringVar(value=_app_dir)
        se(r4, width=55, textvariable=self.vdir).pack(side="left", padx=(0,8))
        sb_btn(r4, "Sfoglia", self._browse, color=C["text_dim"]).pack(side="left")

        # ---- PULSANTI AZIONE v2.8 ----
        # Ordine: [Genera Audio]  [Analizza e Processa]  [Stop]  [Cancella]
        br = sf(sec); br.pack(fill="x", pady=(10,0))

        # Genera Audio
        b_gen = tk.Button(br, text=">> Genera Audio", command=self.run_chatterbox,
                          bg="#1a3d2b", fg=C["text"],
                          activebackground=C["success"], activeforeground="#fff",
                          relief="flat", bd=0, cursor="hand2",
                          font=("Segoe UI",11,"bold"), padx=26, pady=12)
        b_gen.pack(side="left", padx=(0,8))
        b_gen.bind("<Enter>", lambda e: b_gen.config(bg=C["success"], fg="#fff"))
        b_gen.bind("<Leave>", lambda e: b_gen.config(bg="#1a3d2b", fg=C["text"]))

        # Analizza e Processa
        sb_btn(br, "Analizza e Processa", self.process, color=C["accent2"]).pack(side="left", padx=(0,8))

        # STOP (spostato qui da _log_sec, sempre visibile)
        self.stopbtn = sb_btn(br, "■ Stop", self._stop, color=C["danger"])
        self.stopbtn.pack(side="left", padx=(0,8))
        self.stopbtn.config(state="disabled")

        # Cancella
        sb_btn(br, "Cancella", self.clear_all, color="#555555").pack(side="left")

        # Applica lo stile iniziale ai parametri TTS
        self._set_style("narrativa")

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
        # v2.8: sezione output — Stop rimosso da qui (è ora in _ctrl_sec)
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
        # v2.8: log più alto (height 14 -> 20)
        self.log = scrolledtext.ScrolledText(
            self.logsec, height=20,
            bg="#050505", fg=C["success"],
            font=("Courier New",9), relief="flat", bd=0, state="disabled",
            highlightthickness=1, highlightbackground=C["border"]
        )
        self.log.pack(fill="x")

    def _chunks_sec(self, r):
        self.chunksec = self._sec(r, "Chunk Generati"); self.chunksec.pack_forget()
        br = sf(self.chunksec); br.pack(fill="x", pady=(0,14))
        sb_btn(br, "Salva Script .py", self.save_script, color=C["accent2"]).pack(side="left", padx=(0,10))
        sb_btn(br, "Copia Tutti", self.copy_all, color=C["text_dim"]).pack(side="left")
        self.cbox = sf(self.chunksec); self.cbox.pack(fill="x")

    def _guide_sec(self, r):
        outer = tk.Frame(r, bg=C["bg"], padx=18, pady=10); outer.pack(fill="x")

        # Intestazione con titolo e pulsanti prompt (unica posizione)
        hr = tk.Frame(outer, bg=C["bg"]); hr.pack(fill="x", pady=(0,8))
        tk.Label(hr, text="Guida Tag - v3.0", font=FH2, fg=C["accent"], bg=C["bg"]).pack(side="left")
        bf = tk.Frame(hr, bg=C["bg"]); bf.pack(side="right")
        sb_btn(bf, "📋 Prompt Narrativa", lambda: self._copy_prompt("narrativa"),
               color=C["style_narr"]).pack(side="left", padx=(0,6))
        sb_btn(bf, "🎭 Prompt Poesia", lambda: self._copy_prompt("poesia"),
               color=C["style_poesia"]).pack(side="left", padx=(0,6))
        sb_btn(bf, "💾 Salva entrambi", self._save_all_prompts,
               color=C["text_dim"]).pack(side="left")

        inner = tk.Frame(outer, bg=C["surface"], bd=0, highlightthickness=1,
                         highlightbackground=C["border"], padx=20, pady=16)
        inner.pack(fill="x")

        # ── helpers locali ──────────────────────────────────────────
        def sl(parent, txt, col=None):
            tk.Label(parent, text=txt, font=FL, fg=col or C["accent"],
                     bg=C["surface"], pady=6).pack(anchor="w")

        def tg(parent, data):
            f = tk.Frame(parent, bg=C["surface"]); f.pack(fill="x", pady=(0,8))
            for ci, (tag, col, desc) in enumerate(data):
                cell = tk.Frame(f, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
                cell.grid(row=0, column=ci, padx=3, pady=2, sticky="ew")
                f.columnconfigure(ci, weight=1)
                tk.Label(cell, text=tag, font=("Courier New",9,"bold"), fg=col,
                         bg=C["surface2"], pady=4, padx=5).pack()
                tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                         bg=C["surface2"], padx=4, pady=2, justify="center").pack()

        def badge_row(parent, items, bg_fn=None):
            f = tk.Frame(parent, bg=C["surface"]); f.pack(fill="x", pady=(0,8))
            for label, bg in items:
                tk.Label(f, text=" {} ".format(label), font=FS, fg="#fff",
                         bg=bg, padx=4, pady=2).pack(side="left", padx=2, pady=2)

        # ── LAYOUT A DUE COLONNE ───────────────────────────────────
        cols = tk.Frame(inner, bg=C["surface"]); cols.pack(fill="x")
        cols.columnconfigure(0, weight=1); cols.columnconfigure(1, weight=1)
        lc = tk.Frame(cols, bg=C["surface"]); lc.grid(row=0, column=0, sticky="nw", padx=(0,16))
        rc = tk.Frame(cols, bg=C["surface"]); rc.grid(row=0, column=1, sticky="nw")

        # ── COLONNA SINISTRA ───────────────────────────────────────

        sl(lc, "TAG VOCE  (7 voci)")
        tg(lc, [("[v1]",C["v1"],"Narratore"),("[v2]",C["v2"],"Pers.B"),("[v3]",C["v3"],"Pers.C"),
                ("[v4]",C["v4"],"Antag."),("[v5]",C["v5"],"Narr.est.")])
        tg(lc, [("[v6]",C["v6"],"-> V1 se vuota"),("[v7]",C["v7"],"-> V1 se vuota")])

        sl(lc, "EMOZIONI POETICHE / TEATRALI")
        badge_row(lc, [(e, EMO_C.get(e, C["text_dim"])) for e in
                       ["solenne","estatico","malinconico","vibrante","intimo"]])

        sl(lc, "EMOZIONI STANDARD")
        badge_row(lc, [(e, EMO_C.get(e, C["text_dim"])) for e in
                       ["calmo","appassionato","arrabbiato","triste","ironico",
                        "sussurrato","riflessivo","deciso","preoccupato","gentile","serio"]])

        sl(lc, "PAUSE STANDARD")
        fp = tk.Frame(lc, bg=C["surface"]); fp.pack(fill="x", pady=(0,8))
        for ci, (tag, col, desc) in enumerate([
            ("[p1]","#4a9080","~0.18s\nvirgola"),
            ("[p2]","#2980b9","~0.40s\npunto"),
            ("[p3]","#8e44ad","~0.65s\nrifless."),
            ("[b]", "#27ae60","~1.00s\nidea"),
            ("[bd]","#e84357","~1.60s\nclimax"),
            ("[cap]","#e67e22","~2.00s\ncapovers."),
        ]):
            cell = tk.Frame(fp, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
            cell.grid(row=0, column=ci, padx=2, pady=2, sticky="ew"); fp.columnconfigure(ci, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",9,"bold"), fg=col,
                     bg=C["surface2"], pady=4, padx=3).pack()
            tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], padx=2, pady=2, justify="center").pack()

        sl(lc, "STILI DI LETTURA")
        for key, st in READING_STYLES.items():
            rf = tk.Frame(lc, bg=C["surface2"], highlightthickness=1,
                          highlightbackground=st["color"], padx=10, pady=4)
            rf.pack(fill="x", pady=1)
            tk.Label(rf, text=st["label"], font=FL, fg=st["color"],
                     bg=C["surface2"], width=16, anchor="w").pack(side="left")
            tk.Label(rf, text=st["notes"], font=FS, fg=C["text_dim"],
                     bg=C["surface2"]).pack(side="left", padx=(6,0))

        sl(lc, "ANTI-ARTEFATTI v3.0", col=C["antiart"])
        aa_frame = tk.Frame(lc, bg=C["surface2"], highlightthickness=1,
                            highlightbackground=C["antiart"], padx=10, pady=8)
        aa_frame.pack(fill="x", pady=(0,8))
        aa_rows = [
            ("strip_lead",    "rimuove click/parole spurie INIZIO chunk"),
            ("strip_trail",   "rimuove rumori/click FINE chunk"),
            ("smooth_bound",  "curva-S sui bordi → zero click giunzione"),
            ("declick_v3",    "corregge picchi impulsivi (soglia 4x std)"),
            ("spectral_gate", "riduce hiss stazionario via STFT (opt.)"),
            ("adaptive_trim", "trim su energia locale del segnale"),
            ("rms_normalize", "livello coerente tra tutti i chunk"),
        ]
        for name, desc in aa_rows:
            row = tk.Frame(aa_frame, bg=C["surface2"]); row.pack(fill="x", pady=1)
            tk.Label(row, text=name, font=("Courier New",8,"bold"), fg=C["antiart"],
                     bg=C["surface2"], width=14, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], anchor="w").pack(side="left")
        tk.Label(lc, text="  Preset: Leggero / Standard / Aggressivo — configurabili manualmente",
                 font=FS, fg=C["antiart"], bg=C["surface"], anchor="w").pack(fill="x", pady=(0,8))

        # ── COLONNA DESTRA ─────────────────────────────────────────

        sl(rc, "TAG POETICI  (stile Poesia — pause x1.45)")
        fp2 = tk.Frame(rc, bg=C["surface"]); fp2.pack(fill="x", pady=(0,4))
        for ci, (tag, col, desc) in enumerate([
            ("[verso]",     "#9b59b6","~0.44s\nfine verso"),
            ("[strofa]",    "#6c3483","~1.74s\nfine strofa"),
            ("[cesura]",    "#7d3c98","~0.65s\ninterna"),
            ("[metro]",     "#a9cce3","~0.12s\naccento"),
            ("[enjamb.]",   "#d7bde2","~0.07s\nscorre"),
        ]):
            cell = tk.Frame(fp2, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
            cell.grid(row=0, column=ci, padx=2, pady=2, sticky="ew"); fp2.columnconfigure(ci, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",8,"bold"), fg=col,
                     bg=C["surface2"], pady=4, padx=2).pack()
            tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], padx=2, pady=2, justify="center").pack()
        tk.Label(rc, text="  [dissolvenza] = giunzione fade tra strofe (1.60s)",
                 font=FS, fg=C["style_poesia"], bg=C["surface"], pady=2, anchor="w").pack(fill="x")

        sl(rc, "ENFASI")
        tg(rc, [("[e1]","#e67e22","Leggera\n+0.10"),
                ("[e2]","#e84357","Forte\n+0.25"),
                ("[ep]","#9b59b6","Poetica\n+0.15")])

        sl(rc, "GIUNZIONI")
        fj = tk.Frame(rc, bg=C["surface"]); fj.pack(fill="x", pady=(0,8))
        for ci, (tag, col, desc) in enumerate([
            ("[join]",    "#00cec9","overlap\n0.00s"),
            ("[cont]",    "#74b9ff","smooth\n0.12s"),
            ("[cambio]",  "#a29bfe","V1↔V2\n0.50s"),
            ("[para]",    "#fdcb6e","fine par.\n0.90s"),
            ("[stacco]",  "#fd79a8","pensiero\n1.40s"),
            ("[scena]",   "#636e72","scena\n2.40s"),
            ("[dissol.]", "#a29bfe","strofe\n1.60s"),
        ]):
            cell = tk.Frame(fj, bg=C["surface2"], highlightthickness=1, highlightbackground=col)
            cell.grid(row=0, column=ci, padx=1, pady=2, sticky="ew"); fj.columnconfigure(ci, weight=1)
            tk.Label(cell, text=tag, font=("Courier New",7,"bold"), fg=col,
                     bg=C["surface2"], pady=4, padx=1).pack()
            tk.Label(cell, text=desc, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], padx=1, pady=2, justify="center").pack()

        sl(rc, "Pulizia testo automatica v3.0")
        cleanup_info = tk.Frame(rc, bg=C["surface2"], highlightthickness=1,
                                highlightbackground=C["success"], padx=10, pady=8)
        cleanup_info.pack(fill="x", pady=(0,8))
        cleanup_lines = [
            ("↵",        "→ [p1] pausa breve (1 invio)"),
            ("↵↵",       "→ [p2] pausa media (2 invii)"),
            ("↵↵↵",      "→ [b]  pausa lunga (3+ invii)"),
            ("...",      "→ .  (punto singolo)"),
            ("…",        "→ .  (ellipsis unicode)"),
            ("— –",      "→ ,  (trattini em/en)"),
            ("--",       "→ ,  (doppio trattino)"),
            ("a - b",    "→ a, b (trattino isolato)"),
            (";",        "→ ,  (punto e virgola)"),
            ("!!! ??",   "→ ! ? (punteggiatura mult.)"),
            ("€ $ £",    "→ euro dollari sterline"),
            ("%",        "→ percento"),
            ("&",        "→ e"),
            ("#5",       "→ numero 5"),
            ("× ÷ ±",    "→ per / diviso / piu o meno"),
            ("½ ¼ ¾",    "→ mezzo / un quarto / tre quarti"),
            ("37°C",     "→ 37 gradi"),
            ("1° 2°",    "→ primo secondo"),
            ("dott.",    "→ dottor"),
            ("sig.",     "→ signor"),
            ("prof.",    "→ professore"),
            ("ecc.",     "→ eccetera"),
            ("km",       "→ chilometri"),
            ("(testo)",  "→ , testo, (parentesi)"),
            ("*testo*",  "→ testo (markdown)"),
            ("a/b",      "→ a o b (barra)"),
            ("CIA",      "→ Cia (ALLCAPS)"),
            ("À È",      "→ a e (accenti maiusc.)"),
        ]
        for tag_txt, desc_txt in cleanup_lines:
            row = tk.Frame(cleanup_info, bg=C["surface2"]); row.pack(fill="x", pady=1)
            tk.Label(row, text=tag_txt, font=("Courier New",8,"bold"), fg=C["accent"],
                     bg=C["surface2"], width=9, anchor="w").pack(side="left")
            tk.Label(row, text=desc_txt, font=FS, fg=C["text_dim"],
                     bg=C["surface2"], anchor="w").pack(side="left")

        # ── NOTA A PIE' ────────────────────────────────────────────
        tk.Label(inner,
                 text="v3.0: Testo → Parametri → Stile → Anti-Artefatti → Analizza → Genera Audio. "
                      "Anti-Artefatti agisce su ogni chunk: niente click, niente parole spurie. "
                      "Accapo come pause. Pulizia testo automatica al momento di Analizza e Processa.",
                 font=FS, fg=C["success"], bg=C["surface"],
                 pady=10, justify="left", anchor="w").pack(fill="x", pady=(12,0))

    def _footer(self, r):
        ft = tk.Frame(r, bg=C["bg"], pady=20); ft.pack(fill="x")
        tk.Label(ft,
                 text="2026 (c) ChatterText v3.0 by Gerardo D'Orrico  --  "
                      "Anti-Artefatti | 4 Stili | Tag Poetici | 7 Voci | Pulizia testo avanzata",
                 font=FS, fg=C["text_dim"], bg=C["bg"]).pack()

    # ---- DEVICE ----
    def _detect_device(self):
        def _d():
            dev, info = detect_device()
            col = C["gpu"] if dev == "cuda" else C["cpu"]
            self.after(0, lambda: self._set_badge(("GPU " if dev=="cuda" else "CPU ")+info, col))
        threading.Thread(target=_d, daemon=True).start()

    def _set_badge(self, txt, col):
        self.badge_var.set(txt); self.badge.config(bg=col)

    # ---- PROCESS ----
    def process(self):
        raw = self.txt.get("1.0","end-1c").strip()
        if not raw or "Incolla qui" in raw:
            messagebox.showwarning("Attenzione", "Inserisci testo!"); return

        has_t = bool(re.search(r"\[inizio\]", raw, re.IGNORECASE))

        if has_t:
            # Testo già strutturato con [inizio]/[fine]: normalizza solo il contenuto
            norm = re.sub(r"\[inizio\]([\s\S]*?)\[fine\]",
                          lambda m: "[inizio]" + normalize_text(m.group(1)) + "[fine]",
                          raw, flags=re.IGNORECASE)
        else:
            # Testo libero:
            #   1. Converti accapo in pause PRIMA di normalizzare
            #      (normalize_text rimuoverebbe i \n prima che diventino tag)
            #   2. Poi normalizza il testo risultante
            with_pauses = newlines_to_pauses(raw)
            norm = normalize_text(with_pauses)

        errs = analyze_text(norm)
        ws = [w for w in norm.split() if w]
        self.vwords.set(str(len(ws))); self.vchars.set(str(len(norm))); self.verrs.set(str(len(errs)))
        self.stats.pack(fill="x")
        tc  = len(re.findall(r"\[inizio\]", norm, re.IGNORECASE))
        ec  = len(re.findall(r"\[(?:(?:v1|v2|v3|v4|v5|v6|v7)_)?(?:"+" |".join(ALL_EMO)+r")\]", norm, re.IGNORECASE))
        pc  = len(re.findall(r"\[(?:p[123]|b(?:d)?|cap|pausa(?:_lunga)?|silenzio|verso|strofa|metro|enjambement|cesura)\]", norm, re.IGNORECASE))
        enc = len(re.findall(r"\[e[12p]\]", norm, re.IGNORECASE))
        jc  = len(re.findall(r"\[(?:join|cont|cambio|cambio3|para|stacco|lungo|scena|dissolvenza)\]", norm, re.IGNORECASE))
        pts = []
        if tc:  pts.append("{} blocchi".format(tc))
        if ec:  pts.append("{} emozioni".format(ec))
        if pc:  pts.append("{} pause".format(pc))
        if enc: pts.append("{} enfasi".format(enc))
        if jc:  pts.append("{} giunzioni".format(jc))
        self.tag_lbl.config(text="  ".join(pts) if pts else "Modalita automatica",
                            fg=C["success"] if pts else C["warning"])
        self.err_box.config(state="normal"); self.err_box.delete("1.0","end")
        if errs:
            for et, msg in errs:
                self.err_box.insert("end", "{} {}\n".format(
                    "ATTENZIONE:" if et=="warning" else "INFO:", msg))
        else:
            self.err_box.insert("end", "Nessun problema!"); self.err_box.config(fg=C["success"])
        self.err_box.config(state="disabled")
        try: minw,maxw,maxc = int(self.vminw.get()),int(self.vmaxw.get()),int(self.vmaxc.get())
        except: minw,maxw,maxc = 20,40,240
        chunks = chunk_text(norm, minw, maxw, maxc)
        self.chunks = chunks; self.vchunks.set(str(len(chunks)))
        short = [i+1 for i,c in enumerate(chunks)
                 if len(_protected().sub("",c).strip().split()) < CHUNK_MIN_W]
        if short:
            messagebox.showwarning("Chunk corti!",
                "Chunk con meno di {} parole (rischio ripetizioni):\n{}\n\n"
                "Uniscili o usa il Prompt Guida.".format(CHUNK_MIN_W, ", ".join(str(n) for n in short[:10])))
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
            inf = tk.Frame(hdr, bg=C["hdr_bg"]); inf.pack(side="right")
            tk.Label(inf, text="{} par. {} car.".format(words,chars), font=FS,
                     fg=C["text_dim"], bg=C["hdr_bg"]).pack(side="left", padx=8)
            tk.Label(inf, text=stxt, font=FS, fg=sc, bg=C["hdr_bg"]).pack(side="left")
            self.chunk_vars.append(tk.StringVar(value=chunk))
            tf = tk.Frame(card, bg=C["chunk_bg"], padx=8, pady=6); tf.pack(fill="x")
            ta = tk.Text(tf, height=4, bg=C["surface2"], fg=C["text"], font=FM, relief="flat", bd=0,
                         wrap="word", insertbackground=C["accent"],
                         highlightthickness=1, highlightbackground=C["border"])
            ta.insert("1.0", chunk); ta.pack(fill="x")
            ta.bind("<KeyRelease>", lambda e, t=ta, ix=i: self._edit(t, ix))
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
        except: ex, cg, tp = 0.62, 0.70, 0.58
        try: ng = float(self.vng.get())
        except: ng = -50
        try: rms = float(self.vrms.get())
        except: rms = -18
        try: trim = float(self.vtrim.get())
        except: trim = -45
        try: sl = int(self.vstrip_lead.get())
        except: sl = 120
        try: st = int(self.vstrip_tail.get())
        except: st = 80
        try: fm = int(self.vfade_ms.get())
        except: fm = 14
        try: bsm = int(self.vbsm.get())
        except: bsm = 35
        style_key = self.vreadstyle.get()
        style = READING_STYLES.get(style_key, READING_STYLES["narrativa"])
        return build_python_script(
            self.chunks, ex, cg, tp,
            self.vv1.get().strip() or "3l14n.wav",
            self.vv2.get().strip(), self.vv3.get().strip(),
            self.vv4.get().strip(), self.vv5.get().strip(),
            self.vv6.get().strip(), self.vv7.get().strip(),
            self.epreset, self.vdev.get(),
            reading_style=style_key,
            noise_gate_db=ng, rms_target_db=rms, trim_threshold_db=trim,
            pause_scale=style["pause_scale"],
            aggressive_clean=self.vaggclean.get(),
            strip_lead_ms=sl, strip_tail_ms=st,
            spectral_gate=self.vspec_gate.get(),
            declick=self.vdeclick.get(),
            fade_ms=fm, boundary_smooth_ms=bsm
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
        self.vprog.set("0 / {} chunk".format(tot)); self.veta.set("Avvio...")
        dm = self.vdev.get()
        self.vdevl.set("GPU CUDA" if dm=="cuda" else ("CPU" if dm=="cpu" else "Auto-detect..."))
        self.log.config(state="normal"); self.log.delete("1.0","end")
        style_lbl = READING_STYLES.get(self.vreadstyle.get(), {}).get("label","?")
        anti_lbl  = ANTIARTI_PRESETS.get(self.vantipre.get(), {}).get("label","custom")
        self.log.insert("end", "Avvio: {}\n Stile: {}  Anti-artefatti: {}\n Cartella: {}\n".format(
            sf2, style_lbl, anti_lbl, dest))
        self.log.config(state="disabled")
        # Abilita il tasto Stop (che ora è in _ctrl_sec)
        self.stopbtn.config(state="normal")
        self._t0 = time.time()
        def _run():
            try:
                env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.Popen([sys.executable, str(sf2)], cwd=str(dest),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", env=env)
                self._proc = proc
                for line in proc.stdout:
                    self._alog(line)
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
        # Disabilita Stop quando si cancella tutto
        self.stopbtn.config(state="disabled")
        for w in self.cbox.winfo_children(): w.destroy()

    def _browse(self):
        d = filedialog.askdirectory(title="Seleziona cartella Chatterbox")
        if d: self.vdir.set(d)

    def _presets(self):
        PresetWindow(self, self.epreset, on_save=lambda p: self.epreset.update(p))


if __name__ == "__main__":
    App().mainloop()