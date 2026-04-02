#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatterText - App Desktop Python v2.1
Analizza testo, genera chunk e lancia Chatterbox TTS direttamente.
Posizionare nella root di Chatterbox ed eseguire con: python chattertext_app.py

NOVITÀ v2.1 rispetto a v2.0:
  - RIMOSSI tag velocità [vv][v+][v-][vvv] e volume [ff][f+][f-][pp]
    (causavano artefatti e allucinazioni sui chunk brevi)
  - Validazione chunk: minimo 5 parole e 20 caratteri (puliti dai tag)
    per evitare che il modello TTS ripeta il testo
  - Guida Tag spostata nel footer (niente più finestra popup)
  - Pulsante "Copia Prompt Guida" per ottenere il prompt da dare a un'AI
    affinché riscriva il testo con i tag corretti
  - Sezione dispositivo e badge GPU/CPU mantenuti
  - Suono di notifica, barra progresso, ETA, pulsante Stop confermati

TAG SUPPORTATI:
  Voce:     [v1]...[/v1]   [v2]...[/v2]
  Blocchi:  [inizio]...[fine]
  Pause:    [p1] [p2] [p3] [b]  (+ legacy: [pausa] [pausa_lunga] [silenzio])
  Emotivi (voce neutra):        [calmo]...[/calmo]  ecc.
  Emotivi (voce specifica):     [V1_calmo]...[/V1_calmo]  [V2_calmo]...[/V2_calmo]
  Stati: calmo | appassionato | arrabbiato | triste | ironico
         sussurrato | riflessivo | deciso | preoccupato | gentile | serio
  Enfasi:   [e1]  [e2]
  Giunzione:[join] [cont] [cambio] [para] [scena]
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import os
import subprocess
import threading
import sys
import re
import json
import pathlib
import time

# ─────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────
COLORS = {
    "bg":        "#0d0d0d",
    "surface":   "#131313",
    "surface2":  "#1a1a1a",
    "border":    "#2a2a2a",
    "accent":    "#81ecec",
    "accent2":   "#4a90e2",
    "text":      "#e0e0e0",
    "text_dim":  "#7f8c8d",
    "success":   "#00b894",
    "warning":   "#fdcb6e",
    "danger":    "#e84357",
    "v1":        "#3498db",
    "v2":        "#e74c3c",
    "chunk_bg":  "#111111",
    "header_bg": "#181818",
    "gpu":       "#76b900",
    "cpu":       "#4a90e2",
}

EMOTION_COLORS = {
    "calmo":        "#27ae60",
    "appassionato": "#e67e22",
    "arrabbiato":   "#c0392b",
    "triste":       "#8e44ad",
    "ironico":      "#16a085",
    "sussurrato":   "#546e7a",
    "riflessivo":   "#2980b9",
    "deciso":       "#d35400",
    "preoccupato":  "#7f8c8d",
    "gentile":      "#2ecc71",
    "serio":        "#34495e",
}

FONT_MONO  = ("Courier New", 11)
FONT_BODY  = ("Segoe UI",    10)
FONT_LABEL = ("Segoe UI",     9, "bold")
FONT_H1    = ("Georgia",     18, "bold")
FONT_H2    = ("Segoe UI",    12, "bold")
FONT_STAT  = ("Courier New", 22, "bold")
FONT_SMALL = ("Segoe UI",     8)

# ─────────────────────────────────────────
#  PRESET PROSODICI PER EMOZIONE
# ─────────────────────────────────────────
EMOTION_PRESETS = {
    "calmo":        {"exaggeration": 0.35, "cfg_weight": 0.85, "temperature": 0.40, "top_p": 0.75, "min_p": 0.15},
    "appassionato": {"exaggeration": 0.75, "cfg_weight": 0.60, "temperature": 0.65, "top_p": 0.80, "min_p": 0.10},
    "arrabbiato":   {"exaggeration": 0.90, "cfg_weight": 0.50, "temperature": 0.75, "top_p": 0.85, "min_p": 0.08},
    "triste":       {"exaggeration": 0.45, "cfg_weight": 0.80, "temperature": 0.45, "top_p": 0.70, "min_p": 0.18},
    "ironico":      {"exaggeration": 0.65, "cfg_weight": 0.65, "temperature": 0.70, "top_p": 0.82, "min_p": 0.12},
    "sussurrato":   {"exaggeration": 0.25, "cfg_weight": 0.90, "temperature": 0.35, "top_p": 0.65, "min_p": 0.20},
    "riflessivo":   {"exaggeration": 0.40, "cfg_weight": 0.78, "temperature": 0.48, "top_p": 0.72, "min_p": 0.16},
    "deciso":       {"exaggeration": 0.80, "cfg_weight": 0.55, "temperature": 0.60, "top_p": 0.78, "min_p": 0.10},
    "preoccupato":  {"exaggeration": 0.55, "cfg_weight": 0.72, "temperature": 0.55, "top_p": 0.74, "min_p": 0.14},
    "gentile":      {"exaggeration": 0.42, "cfg_weight": 0.82, "temperature": 0.42, "top_p": 0.70, "min_p": 0.16},
    "serio":        {"exaggeration": 0.50, "cfg_weight": 0.75, "temperature": 0.50, "top_p": 0.73, "min_p": 0.15},
}

ALL_EMOTIONS = list(EMOTION_PRESETS.keys())

# ─────────────────────────────────────────
#  TAG PAUSE E ENFASI
# ─────────────────────────────────────────
PAUSE_TAGS = {
    "[p1]": 0.20,
    "[p2]": 0.40,
    "[p3]": 0.70,
    "[b]":  0.90,
    "[pausa]":       0.50,
    "[pausa_lunga]": 1.20,
    "[silenzio]":    2.00,
}

EMPHASIS_PRESETS = {
    "e1": {"exaggeration_delta": +0.10, "cfg_weight_delta": -0.05},
    "e2": {"exaggeration_delta": +0.25, "cfg_weight_delta": -0.12},
}

ALL_PAUSE_TAG_NAMES    = ["p1", "p2", "p3", "b", "pausa", "pausa_lunga", "silenzio"]
ALL_EMPHASIS_TAG_NAMES = ["e1", "e2"]

# ─────────────────────────────────────────
#  TAG DI GIUNZIONE
# ─────────────────────────────────────────
JOIN_TAGS = {
    "[join]":  (0.00, "overlap"),
    "[cont]":  (0.12, "smooth"),
    "[cambio]":(0.50, "cambio"),
    "[para]":  (0.90, "silence"),
    "[scena]": (2.00, "hard"),
}
ALL_JOIN_TAG_NAMES = ["join", "cont", "cambio", "para", "scena"]

BREATH_MAX_WORDS = 14
BREATH_MAX_CHARS = 80
# Soglia minima chunk per evitare allucinazioni TTS
CHUNK_MIN_WORDS = 5
CHUNK_MIN_CHARS = 20


def detect_join_tag(chunk):
    for name in ALL_JOIN_TAG_NAMES:
        if re.search(r"\[" + name + r"\]", chunk, re.IGNORECASE):
            return "[{}]".format(name)
    return None


# ─────────────────────────────────────────
#  SUONO DI NOTIFICA
# ─────────────────────────────────────────
def play_completion_sound():
    try:
        if sys.platform == "win32":
            import winsound
            for freq, dur in [(523, 120), (659, 120), (784, 200), (1047, 350)]:
                winsound.Beep(freq, dur)
                time.sleep(0.04)
        elif sys.platform == "darwin":
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], capture_output=True)
        else:
            if subprocess.run(["which", "paplay"], capture_output=True).returncode == 0:
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], capture_output=True)
            elif subprocess.run(["which", "beep"], capture_output=True).returncode == 0:
                subprocess.run(["beep", "-f", "523", "-l", "120", "-n", "-f", "784", "-l", "200",
                                 "-n", "-f", "1047", "-l", "350"], capture_output=True)
            else:
                print("\a\a\a", end="", flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────
#  RILEVAMENTO GPU
# ─────────────────────────────────────────
def detect_best_device():
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory // (1024**3)
            return "cuda", name, vram
    except ImportError:
        pass
    return "cpu", "CPU", None


def get_device_info_string():
    device, name, vram = detect_best_device()
    if device == "cuda":
        return "cuda", "GPU: {} ({}GB VRAM)".format(name, vram)
    return "cpu", "CPU: nessuna GPU CUDA rilevata"


# ─────────────────────────────────────────
#  LOGICA TESTO
# ─────────────────────────────────────────
def _protected_pattern():
    emo = "|".join(ALL_EMOTIONS)
    return re.compile(
        r"\[/?(?:v1|v2|inizio|fine|pausa|pausa_lunga|silenzio"
        r"|p1|p2|p3|b|e1|e2"
        r"|join|cont|cambio|para|scena"
        r"|(?:(?:v1|v2)_)?(?:" + emo + r"))\]",
        re.IGNORECASE
    )


def normalize_text(text):
    tag_map = {}
    idx = [0]
    pattern = _protected_pattern()

    def save_tag(m):
        ph = "__TAG{}__".format(idx[0])
        tag_map[ph] = m.group(0)
        idx[0] += 1
        return ph

    text = pattern.sub(save_tag, text)
    text = re.sub(r"l'Om\b", "l'om", text)
    text = re.sub(r"nell'(\w)", lambda m: "nell'" + m.group(1).lower(), text)
    text = re.sub(r"dell'(\w)", lambda m: "dell'" + m.group(1).lower(), text)
    text = re.sub(r"[`\u00b4]", "'", text)
    text = re.sub(r"[^\w\s.,;:!?\u00C0-\u00F9'\"\\-]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"([.!?])\1+", r"\1", text)
    for ph, tag in tag_map.items():
        text = text.replace(ph, tag)
    return text.strip()


def analyze_text(text):
    errors = []
    if len(text) > 10000:
        errors.append(("warning", "Testo troppo lungo ({} car.). Max 10000.".format(len(text))))
    caps = re.findall(r"[''`\u00b4]\w*[A-Z]\w*", text)
    if caps:
        errors.append(("warning", "Maiuscole dopo apostrofo ({}): {}".format(
            len(caps), ", ".join(caps[:3]))))
    text_no_tags = _protected_pattern().sub("", text)
    words = re.findall(r"\b\w+\b", text_no_tags.lower())
    wcount = {}
    for w in words:
        wcount[w] = wcount.get(w, 0) + 1
    repeated = sorted([(w, c) for w, c in wcount.items() if c > 3 and len(w) > 3],
                      key=lambda x: -x[1])[:5]
    if repeated:
        errors.append(("info", "Parole ripetute: " +
                       ", ".join('"{}" ({}x)'.format(w, c) for w, c in repeated)))
    specials = re.findall(r"[^\w\s.,;:!?\u00C0-\u00F9'\"\\-]", text_no_tags)
    if specials:
        errors.append(("warning", "Caratteri speciali: " + " ".join(list(dict.fromkeys(specials))[:10])))
    return errors


def chunk_text(text, min_words, max_words, max_chars):
    tag_matches = list(re.finditer(r"\[inizio\]([\s\S]*?)\[fine\]", text, re.IGNORECASE))
    if tag_matches:
        chunks = []
        emo = "|".join(ALL_EMOTIONS)
        voice_pat = re.compile(
            r"\[(v1|v2)(?:_(?:" + emo + r"))?\]([\s\S]*?)\[/(?:v1|v2)(?:_(?:" + emo + r"))?\]",
            re.IGNORECASE
        )
        for m in tag_matches:
            content = m.group(1).strip()
            if not content:
                continue
            vm_list = list(voice_pat.finditer(content))
            if vm_list:
                for vm in vm_list:
                    full_tag = vm.group(0).strip()
                    if vm.group(2).strip():
                        chunks.append(full_tag)
            else:
                if content:
                    chunks.append(content)
        return chunks

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for p in paragraphs:
        if len(p) <= max_chars and len(p.split()) <= max_words:
            chunks.append(p)
            continue
        sentences = re.findall(r"[^.!?]+[.!?]+", p) or [p]
        buffer = ""
        for frase in sentences:
            test = (buffer + " " + frase).strip() if buffer else frase
            if len(test) > max_chars or len(test.split()) > max_words:
                if buffer.strip():
                    chunks.append(buffer.strip())
                buffer = frase
            else:
                buffer = test
        if buffer.strip():
            chunks.append(buffer.strip())
    return chunks


def chunk_status(words, chars):
    """Valuta un chunk secondo la regola blocco-respiro."""
    if words > 60 or chars > 350:
        return "danger", "Troppo lungo"
    if words > BREATH_MAX_WORDS or chars > BREATH_MAX_CHARS:
        return "warning", "Supera blocco-respiro ({}/14 par.)".format(words)
    if words < CHUNK_MIN_WORDS or chars < CHUNK_MIN_CHARS:
        return "danger", "TROPPO CORTO — rischio ripetizione TTS ({} par.)".format(words)
    return "success", "Ottimale"


def detect_emphasis_tags(chunk):
    found = []
    for tag in ALL_EMPHASIS_TAG_NAMES:
        if re.search(r"\[" + tag + r"\]", chunk, re.IGNORECASE):
            found.append(tag)
    return found


def detect_pause_tags(chunk):
    result = []
    for tag_name in ALL_PAUSE_TAG_NAMES:
        tag = "[{}]".format(tag_name)
        for _ in re.findall(re.escape(tag), chunk, re.IGNORECASE):
            result.append((tag, PAUSE_TAGS.get(tag, 0.4)))
    return result


def detect_chunk_tags(chunk):
    emo = "|".join(ALL_EMOTIONS)
    m = re.search(r"\[(v1|v2)_(" + emo + r")\]", chunk, re.IGNORECASE)
    if m:
        return m.group(1).lower(), m.group(2).lower()
    m = re.search(r"\[(v1|v2)\]", chunk, re.IGNORECASE)
    if m:
        return m.group(1).lower(), None
    m = re.search(r"\[(" + emo + r")\]", chunk, re.IGNORECASE)
    if m:
        return None, m.group(1).lower()
    return None, None


# ─────────────────────────────────────────
#  TESTO DEL PROMPT GUIDA (da copiare/scaricare)
# ─────────────────────────────────────────
GUIDE_PROMPT = '''# PROMPT PER RISCRITTURA CAPITOLO — ChatterText TTS v2.1

Sei un editor specializzato nella preparazione di testi per la sintesi vocale con Chatterbox TTS.
Riscrivi il capitolo che ti fornirò applicando il sistema di tag di ChatterText.

## REGOLA FONDAMENTALE: BLOCCO-RESPIRO
Ogni blocco [inizio]...[fine] deve contenere UNA SOLA unità di respiro:
  • Minimo 5 parole (OBBLIGATORIO — chunk più corti causano ripetizioni nel TTS)
  • Massimo 14 parole / 80 caratteri (consigliato)
  • Una frase breve o una parte logica di frase

## STRUTTURA BASE
[inizio]
  [V1_emozione]
  Testo da leggere.[p3][para]
  [/V1_emozione]
[fine]

## TAG VOCE
  [v1]testo[/v1]              → Voce 1 (narratore / personaggio A)
  [v2]testo[/v2]              → Voce 2 (personaggio B)
  [V1_emozione]...[/V1_emozione] → Voce 1 con emozione specifica
  [V2_emozione]...[/V2_emozione] → Voce 2 con emozione specifica

## STATI EMOTIVI DISPONIBILI
  calmo | appassionato | arrabbiato | triste | ironico
  sussurrato | riflessivo | deciso | preoccupato | gentile | serio

## TAG PAUSE (dentro il testo)
  [p1]  pausa breve 0.20s   — dopo virgola
  [p2]  pausa media 0.40s   — dopo due punti / punto e virgola
  [p3]  pausa lunga 0.70s   — dopo punto / ? / !
  [b]   breath 0.90s        — respiro reale tra frasi importanti

## TAG ENFASI (dopo il testo, prima del tag di chiusura)
  [e1]  enfasi leggera
  [e2]  enfasi forte (climax, grido emotivo)

## TAG DI GIUNZIONE (prima di [fine], indica come unire al chunk successivo)
  [join]    stessa frase — flusso continuo senza pausa
  [cont]    stessa battuta — respiro minimo 0.12s
  [cambio]  cambio voce V1→V2 — pausa 0.50s + crossfade
  [para]    nuovo paragrafo — 0.90s pausa netta
  [scena]   cambio scena — 2.00s stacco secco

## ORDINE CORRETTO DEI TAG NEL BLOCCO
  [inizio]
    [V1_emozione]       ← 1. Voce apertura
    Testo...[p1/p2/p3]  ← 2. Testo con pause inline
    [e1/e2]             ← 3. Enfasi (opzionale, dopo il testo)
    [join/cont/para...] ← 4. Giunzione (prima della chiusura)
    [/V1_emozione]      ← 5. Voce chiusura
  [fine]                ← 6. Fine blocco

## ESEMPI PRATICI

Dialogo due voci:
  [inizio][V1_serio]
  E in quest'altra parte era giusto il ragionamento?[p3][b][para]
  [/V1_serio][fine]

  [inizio][V2_riflessivo]
  Dicevamo così noi:[p2][cont]
  [/V2_riflessivo][fine]

  [inizio][V2_riflessivo]
  che il giusto non può fare ingiustizia.[p3][para]
  [/V2_riflessivo][fine]

Climax emotivo:
  [inizio][V1_arrabbiato]
  No! Non è possibile![e2][p3][para]
  [/V1_arrabbiato][fine]

  [inizio][V1_riflessivo]
  Eppure... forse aveva ragione.[p3][b][para]
  [/V1_riflessivo][fine]

Frase spezzata su due blocchi (usa [join]):
  [inizio][V1_deciso]
  Ho detto che era necessario[join]
  [/V1_deciso][fine]

  [inizio][V1_deciso]
  farlo senza esitazione.[p3][para]
  [/V1_deciso][fine]

Cambio scena:
  [inizio][V1_triste]
  E così si congedò per sempre.[p3][b][scena]
  [/V1_triste][fine]

  [inizio][V2_calmo]
  Era il mattino del giorno seguente.[p2][para]
  [/V2_calmo][fine]

## REGOLE IMPORTANTI
  1. NESSUN chunk con meno di 5 parole pulite (esclusi i tag)
     → Se una battuta è breve (es. "Bene." / "Sì."), uniscila alla riga successiva
     → Esempio SBAGLIATO: [inizio][V1_serio]Bene.[p2][cont][/V1_serio][fine]
     → Esempio CORRETTO:  [inizio][V1_serio]Bene,[p1] diceva Critone,[p1] e ora?[p2][cont][/V1_serio][fine]
  2. Usa V1 per il narratore e le voci principali, V2 per interlocutori secondari
  3. Metti sempre un tag di giunzione prima di [fine]
  4. Le pause [p3][b] vanno alla fine delle frasi principali
  5. [cambio] si usa SOLO quando la voce cambia da V1 a V2 o viceversa

---
Ora riscrivi il seguente capitolo applicando tutti questi tag:

[INCOLLA QUI IL TESTO DEL CAPITOLO]
'''


# ─────────────────────────────────────────
#  GENERAZIONE SCRIPT PYTHON
# ─────────────────────────────────────────
def build_python_script(chunks, default_exag, default_cfg, default_temp,
                        voice1, voice2, emotion_presets, device_mode="auto"):
    has_two   = bool(voice2.strip())
    voice2eff = voice2.strip() if has_two else voice1

    scene_starters  = ["poi","quando","all'improvviso","improvvisamente",
                       "in quel momento","mentre","subito dopo","intanto"]
    dialog_verbs    = ["disse","penso","grido","urlo","sussurro","domando",
                       "rispose","chiese","mormoro","esclamo","borbotto","annuncio","replico"]
    emotional_words = ["paura","orrore","ansia","terrore","pianto","felice",
                       "gioia","triste","disperato","sconvolto","agitato","sorpreso"]

    def pylist(lst):
        return "[\n        " + ", ".join('"{}"'.format(s) for s in lst) + "\n    ]"

    emo_pipe = "|".join(ALL_EMOTIONS)
    presets_repr = json.dumps(emotion_presets, ensure_ascii=False, indent=4)

    if device_mode == "cpu":
        device_logic = [
            "DEVICE = torch.device('cpu')",
            "print('Dispositivo: CPU (forzato)')",
        ]
    elif device_mode == "cuda":
        device_logic = [
            "if not torch.cuda.is_available():",
            "    print('ERRORE: CUDA non disponibile! Usa modalità Auto o CPU.'); exit(1)",
            "DEVICE = torch.device('cuda')",
            "print(f'Dispositivo: GPU {torch.cuda.get_device_name(0)}')",
        ]
    else:
        device_logic = [
            "if torch.cuda.is_available():",
            "    DEVICE = torch.device('cuda')",
            "    gpu_name = torch.cuda.get_device_name(0)",
            "    vram = torch.cuda.get_device_properties(0).total_memory // (1024**3)",
            "    print(f'Dispositivo: GPU {gpu_name} ({vram}GB VRAM) — CUDA attivo!')",
            "else:",
            "    DEVICE = torch.device('cpu')",
            "    print('Dispositivo: CPU (nessuna GPU CUDA rilevata)')",
        ]

    lines = [
        "# Script generato automaticamente da ChatterText Desktop v2.1",
        "# Versione senza tag velocità/volume — stabile e senza artefatti",
        "import os, re, sys, torch, torchaudio as ta, pathlib, datetime, time",
        "",
        "if sys.platform == 'win32':",
        "    import io",
        "    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')",
        "    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')",
        "",
        "# ── SELEZIONE DISPOSITIVO ──────────────────────",
    ] + device_logic + [
        "",
        "_orig_torch_load = torch.load",
        "def _cpu_safe_load(*args, **kwargs):",
        "    if DEVICE.type == 'cpu':",
        "        kwargs.setdefault('map_location', torch.device('cpu'))",
        "    return _orig_torch_load(*args, **kwargs)",
        "torch.load = _cpu_safe_load",
        "",
        "from chatterbox.mtl_tts import ChatterboxMultilingualTTS",
        "",
        "print('Caricamento modello Chatterbox...')",
        "model = ChatterboxMultilingualTTS.from_pretrained(device=DEVICE.type)",
        "print('Modello caricato su {}!'.format(DEVICE.type.upper()))",
        "",
        "chunks = {}".format(json.dumps(chunks, ensure_ascii=False, indent=4)),
        "",
        'AUDIO_PROMPT_V1 = "2.Voci/{}"'.format(voice1),
        'AUDIO_PROMPT_V2 = "2.Voci/{}"'.format(voice2eff),
        "HAS_TWO_VOICES = {}".format(str(has_two)),
        "",
        "for prompt in ([AUDIO_PROMPT_V1, AUDIO_PROMPT_V2] if HAS_TWO_VOICES else [AUDIO_PROMPT_V1]):",
        "    if not os.path.exists(prompt):",
        "        print(f'File audio non trovato: {prompt}'); exit(1)",
        "",
        "EMOTION_PRESETS = {}".format(presets_repr),
        "DEFAULT_PARAMS  = {{'exaggeration':{},'cfg_weight':{},'temperature':{},'top_p':0.75,'min_p':0.15}}".format(
            default_exag, default_cfg, default_temp),
        "",
        "PAUSE_MAP = {",
        "    '[p1]': 0.20,",
        "    '[p2]': 0.40,",
        "    '[p3]': 0.70,",
        "    '[b]':  0.90,",
        "    '[pausa]': 0.50,",
        "    '[pausa_lunga]': 1.20,",
        "    '[silenzio]': 2.00,",
        "}",
        "JOIN_MAP = {",
        "    '[join]':   (0.00, 'overlap'),",
        "    '[cont]':   (0.12, 'smooth'),",
        "    '[cambio]': (0.50, 'cambio'),",
        "    '[para]':   (0.90, 'silence'),",
        "    '[scena]':  (2.00, 'hard'),",
        "}",
        "EMPHASIS_PRESETS = {",
        "    'e1': {'exaggeration_delta': 0.10, 'cfg_weight_delta': -0.05},",
        "    'e2': {'exaggeration_delta': 0.25, 'cfg_weight_delta': -0.12},",
        "}",
        'EMO_NAMES = r"{}"'.format(emo_pipe),
        "_ALL_PAUSE_RE = re.compile(",
        "    r'(\\[p[123]\\]|\\[b\\]|\\[pausa(?:_lunga)?\\]|\\[silenzio\\])',",
        "    re.IGNORECASE)",
        "_ALL_EMPH_RE  = re.compile(r'\\[e[12]\\]', re.IGNORECASE)",
        "_ALL_JOIN_RE  = re.compile(r'\\[(?:join|cont|cambio|para|scena)\\]', re.IGNORECASE)",
        "",
        "def parse_chunk(chunk):",
        "    raw_pauses  = _ALL_PAUSE_RE.findall(chunk)",
        "    pauses      = [('pause', PAUSE_MAP.get(p.lower(), 0.4)) for p in raw_pauses]",
        "    total_pause = sum(d for _, d in pauses)",
        "    emph_tags = _ALL_EMPH_RE.findall(chunk)",
        "    emph_key  = emph_tags[-1].lower().strip('[]') if emph_tags else None",
        "    join_tags = _ALL_JOIN_RE.findall(chunk)",
        "    join_tag  = join_tags[-1].lower() if join_tags else None",
        "    def strip_inline(t):",
        "        t = _ALL_PAUSE_RE.sub('', t)",
        "        t = _ALL_EMPH_RE.sub('', t)",
        "        t = _ALL_JOIN_RE.sub('', t)",
        "        return t.strip()",
        "    m = re.search(r'\\[(v1|v2)_(' + EMO_NAMES + r')\\]', chunk, re.IGNORECASE)",
        "    if m:",
        "        v, e = m.group(1).lower(), m.group(2).lower()",
        "        clean = re.sub(r'\\[(?:v1|v2)_(?:' + EMO_NAMES + r')\\]', '', chunk, flags=re.IGNORECASE)",
        "        clean = re.sub(r'\\[/(?:v1|v2)_(?:' + EMO_NAMES + r')\\]', '', clean, flags=re.IGNORECASE)",
        "        return strip_inline(clean), v, e, pauses, total_pause, emph_key, join_tag",
        "    m = re.search(r'\\[(v1|v2)\\]', chunk, re.IGNORECASE)",
        "    if m:",
        "        v = m.group(1).lower()",
        "        clean = re.sub(r'\\[/?(?:v1|v2)\\]', '', chunk, flags=re.IGNORECASE)",
        "        return strip_inline(clean), v, None, pauses, total_pause, emph_key, join_tag",
        "    m = re.search(r'\\[(' + EMO_NAMES + r')\\]', chunk, re.IGNORECASE)",
        "    if m:",
        "        e = m.group(1).lower()",
        "        clean = re.sub(r'\\[(?:' + EMO_NAMES + r')\\]', '', chunk, flags=re.IGNORECASE)",
        "        clean = re.sub(r'\\[/(?:' + EMO_NAMES + r')\\]', '', clean, flags=re.IGNORECASE)",
        "        return strip_inline(clean), 'v1', e, pauses, total_pause, emph_key, join_tag",
        "    return strip_inline(chunk), 'v1', None, pauses, total_pause, emph_key, join_tag",
        "",
        "def prosody_params(emotion, emph_key=None):",
        "    if emotion and emotion in EMOTION_PRESETS:",
        "        p = EMOTION_PRESETS[emotion].copy()",
        "        p.setdefault('top_p', 0.75); p.setdefault('min_p', 0.15)",
        "    else:",
        "        p = DEFAULT_PARAMS.copy()",
        "    if emph_key and emph_key in EMPHASIS_PRESETS:",
        "        ep = EMPHASIS_PRESETS[emph_key]",
        "        p['exaggeration'] = min(1.0, p['exaggeration'] + ep['exaggeration_delta'])",
        "        p['cfg_weight']   = max(0.1, p['cfg_weight']   + ep['cfg_weight_delta'])",
        "    return p",
        "",
        "tagged_chunks = [parse_chunk(c) for c in chunks]",
        "",
        "def reduce_noise(wav, sr, gate_threshold_db=-50, highpass_hz=80):",
        "    threshold = 10 ** (gate_threshold_db / 20)",
        "    if wav.dim() == 1: wav = wav.unsqueeze(0)",
        "    gate_mask = (torch.abs(wav) > threshold).float()",
        "    k = int(sr * 0.008)",
        "    if k % 2 == 0: k += 1",
        "    kernel = torch.ones(1, 1, k) / k",
        "    gate_mask = torch.nn.functional.conv1d(gate_mask.unsqueeze(0), kernel, padding=k//2).squeeze(0).clamp(0,1)",
        "    wav = wav * gate_mask",
        "    wav = ta.functional.highpass_biquad(wav, sr, cutoff_freq=highpass_hz)",
        "    return wav",
        "",
        "audio_segments = []; failed_chunks = []",
        "start_time = time.time()",
        "print('\\n' + '='*60)",
        "print('INIZIO GENERAZIONE AUDIO  [{}]'.format(DEVICE.type.upper()))",
        "print('='*60)",
        "",
        "for idx, (text, voice, emotion, pauses, total_pause, emph_key, join_tag) in enumerate(tagged_chunks):",
        "    emo_label  = '[{}]'.format(emotion) if emotion else ''",
        "    emph_label = '[{}]'.format(emph_key) if emph_key else ''",
        "    join_label = '[{}]'.format(join_tag.strip('[]')) if join_tag else ''",
        "    if idx > 0:",
        "        elapsed = time.time() - start_time",
        "        avg = elapsed / idx",
        "        remaining = avg * (len(tagged_chunks) - idx)",
        "        eta_str = '  ETA: {:.0f}s'.format(remaining)",
        "    else:",
        "        eta_str = ''",
        "    pct = int((idx / len(tagged_chunks)) * 100)",
        "    bar = '█' * (pct // 5) + '░' * (20 - pct // 5)",
        "    print(f'\\n [{bar}] {pct}%{eta_str}')",
        "    print(f' Chunk {idx+1}/{len(tagged_chunks)} [{voice.upper()}]{emo_label}{emph_label}{join_label} - {len(text.split())} parole')",
        "    suffix = '...' if len(text) > 80 else ''",
        "    print(f'   Testo pulito: {repr(text[:80])}{suffix}')",
        "    # Controllo lunghezza minima per evitare allucinazioni TTS",
        "    word_count = len(text.split())",
        "    if word_count < 5:",
        "        print(f'   ATTENZIONE: chunk troppo corto ({word_count} parole) — potrebbe causare ripetizioni!')",
        "    voice_prompt = AUDIO_PROMPT_V2 if (voice == 'v2' and HAS_TWO_VOICES) else AUDIO_PROMPT_V1",
        "    p = prosody_params(emotion, emph_key)",
        "    _chunk_ok = False",
        "    try:",
        "        wav = model.generate(text, language_id='it', audio_prompt_path=voice_prompt,",
        "            exaggeration=p['exaggeration'], cfg_weight=p['cfg_weight'],",
        "            temperature=p['temperature'], min_p=p['min_p'], top_p=p['top_p'])",
        "        if DEVICE.type == 'cuda': wav = wav.cpu()",
        "        wav = wav / (torch.max(torch.abs(wav)) + 1e-8) * 0.95",
        "        if total_pause > 0:",
        "            wav = torch.cat([wav, torch.zeros((wav.shape[0], int(model.sr * total_pause)))], dim=-1)",
        "        audio_segments.append(wav); _chunk_ok = True; print('   OK!')",
        "    except Exception as e:",
        "        print(f'   Errore: {e} - Retry...')",
        "    if not _chunk_ok:",
        "        try:",
        "            wav = model.generate(text, language_id='it', audio_prompt_path=voice_prompt,",
        "                exaggeration=0.0, cfg_weight=0.25, temperature=0.22, min_p=0.20, top_p=0.65)",
        "            if DEVICE.type == 'cuda': wav = wav.cpu()",
        "            wav = wav / (torch.max(torch.abs(wav)) + 1e-8) * 0.95",
        "            audio_segments.append(wav); print('   Recuperato!')",
        "        except Exception as e2:",
        "            print(f'   FALLITO: {e2}'); failed_chunks.append(idx)",
        "",
        "if not audio_segments: print('Nessun audio generato.'); exit(1)",
        "",
        "out_dir = pathlib.Path('1.Output'); out_dir.mkdir(exist_ok=True)",
        "num = len(list(out_dir.glob('audiolibro_*.wav'))) + 1",
        "out_name = out_dir / 'audiolibro_{:02d}.wav'.format(num)",
        "",
        "scene_starters  = {}".format(pylist(scene_starters)),
        "dialog_verbs    = {}".format(pylist(dialog_verbs)),
        "emotional_words = {}".format(pylist(emotional_words)),
        "",
        "def dynamic_pause(prev_text):",
        "    t = prev_text.strip(); lo = t.lower(); ln = len(t)",
        "    base = 1.3 if t.endswith('...') else 0.85 if t[-1:] in '.!?' else 0.35 if t[-1:] in ',;:' else 0.18",
        "    if ln > 700: base *= 1.55",
        "    elif ln > 500: base *= 1.35",
        "    elif ln > 300: base *= 1.20",
        "    elif ln < 120: base *= 0.85",
        "    if any(v in lo for v in dialog_verbs): base *= 0.82",
        "    if any(w in lo for w in emotional_words): base *= 1.18",
        "    if any(lo.startswith(s) for s in scene_starters): base *= 1.25",
        "    return max(0.12, min(base, 2.4))",
        "",
        "def trim_edges(wav, sr, threshold_db=-45, margin_ms=30):",
        "    margin = int(sr * margin_ms / 1000); threshold = 10 ** (threshold_db / 20)",
        "    mono = wav[0] if wav.dim() > 1 else wav; energy = torch.abs(mono)",
        "    start = next((max(0,i-margin) for i,v in enumerate(energy) if v>threshold), 0)",
        "    end = next((min(len(energy),i+margin) for i in range(len(energy)-1,-1,-1) if energy[i]>threshold), len(energy))",
        "    return wav[..., start:end]",
        "",
        "def crossfade_join(s1, s2, sr, fade_ms=55):",
        "    f = int(sr * fade_ms / 1000)",
        "    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)",
        "    fo = torch.linspace(1,0,f)**1.5; fi = torch.linspace(0,1,f)**1.5",
        "    return torch.cat([s1[...,:-f], s1[...,-f:]*fo + s2[...,:f]*fi, s2[...,f:]], dim=-1)",
        "",
        "def overlap_join(s1, s2, sr, overlap_ms=80):",
        "    f = int(sr * overlap_ms / 1000)",
        "    if s1.shape[-1] < f or s2.shape[-1] < f:",
        "        return torch.cat([s1, s2], dim=-1)",
        "    fo = torch.linspace(1, 0, f) ** 2",
        "    fi = torch.linspace(0, 1, f) ** 2",
        "    mixed = s1[..., -f:] * fo + s2[..., :f] * fi",
        "    return torch.cat([s1[..., :-f], mixed, s2[..., f:]], dim=-1)",
        "",
        "def apply_fade(wav, sr, fade_ms=14):",
        "    f = int(sr * fade_ms / 1000)",
        "    wav = wav.clone()",
        "    wav[...,:f] *= torch.linspace(0,1,f); wav[...,-f:] *= torch.linspace(1,0,f)",
        "    return wav",
        "",
        "def assemble(s1, s2, sr, join_tag):",
        "    if join_tag is None:",
        "        return None",
        "    sil_s, mode = JOIN_MAP.get(join_tag, (0.5, 'silence'))",
        "    if mode == 'overlap':",
        "        return overlap_join(s1, s2, sr, overlap_ms=80)",
        "    silence = torch.zeros((s2.shape[0], int(sr * sil_s))) if sil_s > 0 else None",
        "    if mode == 'smooth':",
        "        s2_with_sil = torch.cat([silence, s2], dim=-1) if silence is not None else s2",
        "        return crossfade_join(s1, s2_with_sil, sr, fade_ms=30)",
        "    if mode == 'cambio':",
        "        s2_with_sil = torch.cat([silence, s2], dim=-1) if silence is not None else s2",
        "        return crossfade_join(s1, s2_with_sil, sr, fade_ms=100)",
        "    if mode == 'silence':",
        "        s2_with_sil = torch.cat([silence, s2], dim=-1) if silence is not None else s2",
        "        return crossfade_join(s1, s2_with_sil, sr, fade_ms=55)",
        "    if mode == 'hard':",
        "        return torch.cat([s1, silence, s2], dim=-1) if silence is not None else torch.cat([s1, s2], dim=-1)",
        "    return crossfade_join(s1, s2, sr)",
        "",
        "join_tags_list = [tc[6] for tc in tagged_chunks]",
        "",
        "final_audio = None",
        "for i, seg in enumerate(audio_segments):",
        "    seg = reduce_noise(seg, model.sr)",
        "    seg = trim_edges(seg, model.sr)",
        "    seg = apply_fade(seg, model.sr)",
        "    if final_audio is None:",
        "        final_audio = seg",
        "        continue",
        "    jt = join_tags_list[i-1]",
        "    result = assemble(final_audio, seg, model.sr, jt)",
        "    if result is None:",
        "        pause = dynamic_pause(chunks[i-1])",
        "        silence = torch.zeros((seg.shape[0], int(model.sr * pause)))",
        "        final_audio = crossfade_join(final_audio, torch.cat([silence, seg], dim=-1), model.sr)",
        "        jt_str = 'auto({:.2f}s)'.format(pause)",
        "    else:",
        "        final_audio = result",
        "        jt_str = jt if jt else 'auto'",
        "    print(f'   → giunzione chunk {i}: {jt_str}')",
        "",
        "final_audio = final_audio / (torch.max(torch.abs(final_audio)) + 1e-8) * 0.95",
        "ta.save(out_name, final_audio, model.sr)",
        "duration = final_audio.shape[-1] / model.sr",
        "total_time = time.time() - start_time",
        "print(f'\\n FILE CREATO: {out_name}')",
        "print(f'   Durata audio: {duration:.1f}s ({duration/60:.1f} min)')",
        "print(f'   Tempo elaborazione: {total_time:.1f}s ({total_time/60:.1f} min)')",
        "print(f'   Dispositivo usato: {DEVICE.type.upper()}')",
        "print(f'   Chunk riusciti: {len(audio_segments)}/{len(chunks)}')",
        "if failed_chunks: print(f'   Chunk falliti: {failed_chunks}')",
        "print('\\nProcesso completato!')",
        "print('__CHATTERTEXT_DONE__')",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────
#  WIDGET HELPERS
# ─────────────────────────────────────────
def styled_frame(parent, **kw):
    kw.setdefault("bg", COLORS["surface"])
    kw.setdefault("bd", 0)
    return tk.Frame(parent, **kw)


def styled_entry(parent, width=18, **kw):
    return tk.Entry(parent, width=width,
                    bg=COLORS["surface2"], fg=COLORS["text"],
                    insertbackground=COLORS["accent"],
                    relief="flat", bd=0,
                    highlightthickness=1,
                    highlightcolor=COLORS["accent"],
                    highlightbackground=COLORS["border"],
                    font=FONT_BODY, **kw)


def styled_button(parent, text, command, color=None, **kw):
    c = color or COLORS["accent2"]
    btn = tk.Button(parent, text=text, command=command,
                    bg=COLORS["surface2"], fg=COLORS["text"],
                    activebackground=c, activeforeground="#fff",
                    relief="flat", bd=0, cursor="hand2",
                    font=FONT_LABEL, padx=14, pady=8, **kw)
    btn.bind("<Enter>", lambda e: btn.config(bg=c))
    btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["surface2"]))
    return btn


def stat_card(parent, var_text, label):
    f = styled_frame(parent, bg=COLORS["surface2"], padx=20, pady=16)
    f.config(highlightthickness=1, highlightbackground=COLORS["border"])
    tk.Label(f, textvariable=var_text, font=FONT_STAT,
             fg=COLORS["accent"], bg=COLORS["surface2"]).pack()
    tk.Label(f, text=label, font=FONT_SMALL,
             fg=COLORS["text_dim"], bg=COLORS["surface2"]).pack()
    return f


# ─────────────────────────────────────────
#  FINESTRA PRESET EMOTIVI
# ─────────────────────────────────────────
class EmotionPresetsWindow(tk.Toplevel):
    PARAMS = ["exaggeration", "cfg_weight", "temperature", "top_p", "min_p"]

    def __init__(self, parent, presets, on_save):
        super().__init__(parent)
        self.title("Preset Emotivi")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)
        self.on_save = on_save

        self.vars = {}
        for emo, vals in presets.items():
            self.vars[emo] = {}
            for p in self.PARAMS:
                self.vars[emo][p] = tk.StringVar(value=str(vals.get(p, "")))

        self._build()
        self.grab_set()

    def _build(self):
        tk.Label(self, text="Parametri Prosodici per Emozione",
                 font=FONT_H2, fg=COLORS["accent"], bg=COLORS["bg"],
                 pady=14).pack(fill="x")

        hdr = tk.Frame(self, bg=COLORS["header_bg"])
        hdr.pack(fill="x", padx=16)
        for col, (h, w) in enumerate(zip(["Emozione"] + self.PARAMS, [14]+[13]*5)):
            tk.Label(hdr, text=h, font=FONT_LABEL, fg=COLORS["accent"],
                     bg=COLORS["header_bg"], width=w, anchor="center",
                     pady=6).grid(row=0, column=col, padx=2)

        for row_i, emo in enumerate(ALL_EMOTIONS):
            bg = COLORS["surface"] if row_i % 2 == 0 else COLORS["surface2"]
            row_f = tk.Frame(self, bg=bg)
            row_f.pack(fill="x", padx=16, pady=1)
            color = EMOTION_COLORS.get(emo, COLORS["text_dim"])
            tk.Label(row_f, text="  {}".format(emo), font=FONT_LABEL,
                     fg=color, bg=bg, width=14, anchor="w",
                     pady=5).grid(row=0, column=0, padx=2)
            for col_i, param in enumerate(self.PARAMS):
                tk.Entry(row_f, textvariable=self.vars[emo][param],
                         width=10, bg=COLORS["surface2"], fg=COLORS["text"],
                         insertbackground=COLORS["accent"],
                         relief="flat", bd=0,
                         highlightthickness=1,
                         highlightbackground=COLORS["border"],
                         font=FONT_BODY, justify="center"
                         ).grid(row=0, column=col_i+1, padx=4, pady=3)

        btn_row = tk.Frame(self, bg=COLORS["bg"], pady=14)
        btn_row.pack()
        styled_button(btn_row, "Salva e Chiudi",
                      self._save, color=COLORS["success"]).pack(side="left", padx=8)
        styled_button(btn_row, "Ripristina Default",
                      self._reset, color=COLORS["warning"]).pack(side="left", padx=8)
        styled_button(btn_row, "Annulla",
                      self.destroy, color=COLORS["danger"]).pack(side="left", padx=8)

    def _save(self):
        result = {}
        for emo in ALL_EMOTIONS:
            result[emo] = {}
            for p in self.PARAMS:
                try:
                    result[emo][p] = round(float(self.vars[emo][p].get()), 3)
                except ValueError:
                    result[emo][p] = EMOTION_PRESETS[emo][p]
        self.on_save(result)
        self.destroy()

    def _reset(self):
        for emo in ALL_EMOTIONS:
            for p in self.PARAMS:
                self.vars[emo][p].set(str(EMOTION_PRESETS[emo][p]))


# ─────────────────────────────────────────
#  FINESTRA PRINCIPALE
# ─────────────────────────────────────────
class ChatterTextApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatterText v2.1")
        self.geometry("1100x900")
        self.minsize(900, 700)
        self.configure(bg=COLORS["bg"])

        self.processed_chunks = []
        self.chunk_vars = []
        self.script_path = None
        self.emotion_presets = {k: v.copy() for k, v in EMOTION_PRESETS.items()}
        self._running_proc = None
        self._gen_start_time = None

        self.var_total_words  = tk.StringVar(value="0")
        self.var_total_chars  = tk.StringVar(value="0")
        self.var_total_chunks = tk.StringVar(value="0")
        self.var_errors       = tk.StringVar(value="0")
        self.var_device_mode  = tk.StringVar(value="auto")
        self.var_notify_sound = tk.BooleanVar(value=True)

        self._build_ui()
        self._update_device_badge()

    def _build_ui(self):
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=COLORS["bg"])
        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._canvas_window = canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw")

        def _on_canvas_resize(e):
            w = e.width
            max_w = 1080
            content_w = min(w, max_w)
            x = (w - content_w) // 2
            canvas.itemconfig(self._canvas_window, width=content_w)
            canvas.coords(self._canvas_window, x, 0)

        canvas.bind("<Configure>", _on_canvas_resize)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        root = self.scroll_frame
        self._build_header(root)
        self._build_device_section(root)
        self._build_input_section(root)
        self._build_controls_section(root)
        self._build_stats_section(root)
        self._build_log_section(root)
        self._build_chunks_section(root)
        self._build_tag_reference(root)   # ← Guida tag nel footer
        self._build_footer(root)

    # ── HEADER ──────────────────────────────────────────────
    def _build_header(self, root):
        hdr = tk.Frame(root, bg="#0a1628", pady=24)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ChatterText", font=FONT_H1,
                 fg="#ffffff", bg="#0a1628").pack()
        tk.Label(hdr, text="Analizza e prepara il testo per Chatterbox TTS",
                 font=FONT_BODY, fg=COLORS["text_dim"], bg="#0a1628").pack(pady=(4, 0))
        tk.Label(hdr, text="v2.1 — GPU Ready  |  senza tag velocità/volume",
                 font=FONT_SMALL, fg=COLORS["gpu"], bg="#0a1628").pack(pady=(2, 0))

    # ── SEZIONE DISPOSITIVO ──────────────────────────────────
    def _build_device_section(self, root):
        sec = self._section(root, "Dispositivo di Calcolo")

        top = styled_frame(sec)
        top.pack(fill="x", pady=(0, 10))

        self.device_badge_var = tk.StringVar(value="Rilevamento...")
        self.device_badge = tk.Label(top, textvariable=self.device_badge_var,
                                     font=FONT_LABEL, fg="#fff",
                                     bg=COLORS["cpu"], padx=12, pady=6)
        self.device_badge.pack(side="left", padx=(0, 20))

        sel_frame = styled_frame(top)
        sel_frame.pack(side="left")
        tk.Label(sel_frame, text="Modalità:", font=FONT_LABEL,
                 fg=COLORS["accent"], bg=COLORS["surface"]).pack(side="left", padx=(0, 8))
        for val, lbl in [("auto", "Auto (consigliato)"), ("cuda", "Forza GPU"), ("cpu", "Forza CPU")]:
            tk.Radiobutton(sel_frame, text=lbl, variable=self.var_device_mode,
                           value=val, font=FONT_BODY,
                           fg=COLORS["text"], bg=COLORS["surface"],
                           selectcolor=COLORS["surface2"],
                           activeforeground=COLORS["accent"],
                           activebackground=COLORS["surface"],
                           cursor="hand2").pack(side="left", padx=6)

        notif_frame = styled_frame(top)
        notif_frame.pack(side="right")
        tk.Checkbutton(notif_frame, text="🔔 Suono a fine generazione",
                       variable=self.var_notify_sound,
                       font=FONT_BODY, fg=COLORS["text"],
                       bg=COLORS["surface"], selectcolor=COLORS["surface2"],
                       activeforeground=COLORS["accent"],
                       activebackground=COLORS["surface"],
                       cursor="hand2").pack(side="left")
        styled_button(notif_frame, "▶ Test suono",
                      lambda: threading.Thread(target=play_completion_sound,
                                               daemon=True).start(),
                      color=COLORS["text_dim"]).pack(side="left", padx=(8, 0))

    # ── SEZIONE INPUT ────────────────────────────────────────
    def _build_input_section(self, root):
        sec = self._section(root, "Inserisci il Testo")
        self.input_text = scrolledtext.ScrolledText(
            sec, height=10, bg=COLORS["surface2"], fg=COLORS["text"],
            insertbackground=COLORS["accent"], relief="flat", bd=0,
            font=FONT_MONO, wrap="word",
            highlightthickness=1, highlightbackground=COLORS["border"])
        self.input_text.pack(fill="x", pady=(0, 10))
        self.input_text.insert("1.0", "Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.input_text.bind("<FocusIn>", self._clear_placeholder)

        self.var_char_count = tk.StringVar(value="0 / 10000 caratteri")
        tk.Label(sec, textvariable=self.var_char_count,
                 font=FONT_SMALL, fg=COLORS["text_dim"],
                 bg=COLORS["surface"], anchor="e").pack(fill="x")
        self.input_text.bind("<KeyRelease>", self._update_char_count)

    def _update_char_count(self, e=None):
        txt = self.input_text.get("1.0", "end-1c")
        n = len(txt)
        self.var_char_count.set("{} / 10000 caratteri".format(n))

    # ── SEZIONE CONTROLLI ────────────────────────────────────
    def _build_controls_section(self, root):
        sec = self._section(root, "Parametri")

        row1 = styled_frame(sec); row1.pack(fill="x", pady=(0, 10))
        self.var_min_words = self._lentry(row1, "Parole min/chunk", "20")
        self.var_max_words = self._lentry(row1, "Parole max/chunk", "40")
        self.var_max_chars = self._lentry(row1, "Caratteri max",    "240")

        row2 = styled_frame(sec); row2.pack(fill="x", pady=(0, 10))
        self.var_voice1 = self._lentry(row2, "Voce 1 (2.Voci/)", "3l14n.wav", wide=True)
        self.var_voice2 = self._lentry(row2, "Voce 2 (opzionale)", "",         wide=True)
        grp_v = styled_frame(row2); grp_v.pack(side="left", padx=(8, 0), anchor="s")
        styled_button(grp_v, "✓ Verifica file voce",
                      self._verify_voice_files,
                      color=COLORS["text_dim"]).pack(pady=(18, 0))

        row3 = styled_frame(sec); row3.pack(fill="x", pady=(0, 10))
        self.var_exag = self._lentry(row3, "Exaggeration (default)", "0.62")
        self.var_cfg  = self._lentry(row3, "CFG Weight (default)",   "0.70")
        self.var_temp = self._lentry(row3, "Temperature (default)",  "0.58")
        grp = styled_frame(row3); grp.pack(side="left", padx=(16, 0))
        tk.Label(grp, text="Preset emotivi", font=FONT_LABEL,
                 fg=COLORS["accent"], bg=COLORS["surface"]).pack(anchor="w")
        styled_button(grp, "Modifica Preset",
                      self._open_presets, color="#8e44ad").pack(anchor="w", pady=(4, 0))

        row4 = styled_frame(sec); row4.pack(fill="x", pady=(0, 14))
        tk.Label(row4, text="Cartella Chatterbox (root):", font=FONT_LABEL,
                 fg=COLORS["accent"], bg=COLORS["surface"]).pack(side="left", padx=(0, 8))
        self.var_chatterbox_dir = tk.StringVar(value=str(pathlib.Path(__file__).parent))
        styled_entry(row4, width=55, textvariable=self.var_chatterbox_dir).pack(side="left", padx=(0, 8))
        styled_button(row4, "Sfoglia", self._browse_dir,
                      color=COLORS["text_dim"]).pack(side="left")

        btn_row = styled_frame(sec); btn_row.pack(fill="x", pady=(6, 0))
        styled_button(btn_row, "Analizza e Processa",
                      self.process_text, color=COLORS["accent2"]).pack(side="left", padx=(0, 10))
        styled_button(btn_row, "Cancella Tutto",
                      self.clear_all, color=COLORS["danger"]).pack(side="left")

    def _verify_voice_files(self):
        base = pathlib.Path(self.var_chatterbox_dir.get())
        voices_dir = base / "2.Voci"
        results = []
        for var, label in [(self.var_voice1, "Voce 1"), (self.var_voice2, "Voce 2")]:
            fname = var.get().strip()
            if not fname:
                results.append("  {} — non specificata (opzionale)".format(label))
                continue
            path = voices_dir / fname
            if path.exists():
                size_kb = path.stat().st_size // 1024
                results.append("  ✓ {} — {} ({} KB)".format(label, fname, size_kb))
            else:
                results.append("  ✗ {} — NON TROVATO: {}".format(label, path))
        messagebox.showinfo("Verifica File Voce", "\n".join(results))

    # ── STATS ────────────────────────────────────────────────
    def _build_stats_section(self, root):
        self.stats_frame = self._section(root, "Statistiche")
        self.stats_frame.pack_forget()

        cards = styled_frame(self.stats_frame)
        cards.pack(fill="x")
        for col in range(4):
            cards.columnconfigure(col, weight=1)
        for col, (var, lbl) in enumerate([
            (self.var_total_words,  "Parole Totali"),
            (self.var_total_chars,  "Caratteri"),
            (self.var_total_chunks, "Chunk Generati"),
            (self.var_errors,       "Problemi"),
        ]):
            stat_card(cards, var, lbl).grid(row=0, column=col, sticky="ew", padx=6, pady=4)

        self.tag_info_label = tk.Label(self.stats_frame, text="",
                                       font=FONT_BODY, fg=COLORS["warning"],
                                       bg=COLORS["surface"], pady=6)
        self.tag_info_label.pack()

        self.error_box = tk.Text(self.stats_frame, height=4,
                                 bg=COLORS["surface2"], fg=COLORS["warning"],
                                 font=FONT_SMALL, relief="flat", bd=0,
                                 highlightthickness=1, highlightbackground=COLORS["border"],
                                 state="disabled", wrap="word")
        self.error_box.pack(fill="x", pady=(8, 0))

    # ── LOG ──────────────────────────────────────────────────
    def _build_log_section(self, root):
        self.log_section = self._section(root, "Output Esecuzione")
        self.log_section.pack_forget()

        prog_frame = styled_frame(self.log_section)
        prog_frame.pack(fill="x", pady=(0, 8))

        self.progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Green.Horizontal.TProgressbar",
                        troughcolor=COLORS["surface2"],
                        background=COLORS["success"],
                        darkcolor=COLORS["success"],
                        lightcolor=COLORS["success"],
                        bordercolor=COLORS["border"])
        self.progress_bar = ttk.Progressbar(
            prog_frame, variable=self.progress_var,
            maximum=100, style="Green.Horizontal.TProgressbar",
            length=400)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.var_progress_label = tk.StringVar(value="In attesa...")
        tk.Label(prog_frame, textvariable=self.var_progress_label,
                 font=FONT_SMALL, fg=COLORS["text_dim"],
                 bg=COLORS["surface"]).pack(side="left")

        eta_row = styled_frame(self.log_section)
        eta_row.pack(fill="x", pady=(0, 6))
        self.var_eta = tk.StringVar(value="")
        tk.Label(eta_row, textvariable=self.var_eta,
                 font=FONT_SMALL, fg=COLORS["warning"],
                 bg=COLORS["surface"]).pack(side="left")
        self.var_device_live = tk.StringVar(value="")
        self.device_live_label = tk.Label(eta_row, textvariable=self.var_device_live,
                                          font=FONT_SMALL, fg=COLORS["gpu"],
                                          bg=COLORS["surface"])
        self.device_live_label.pack(side="right")

        self.log_text = scrolledtext.ScrolledText(
            self.log_section, height=14,
            bg="#050505", fg=COLORS["success"],
            font=("Courier New", 9), relief="flat", bd=0,
            state="disabled",
            highlightthickness=1, highlightbackground=COLORS["border"])
        self.log_text.pack(fill="x")

        stop_row = styled_frame(self.log_section)
        stop_row.pack(fill="x", pady=(8, 0))
        self.stop_btn = styled_button(stop_row, "⏹ Stop Processo",
                                      self._stop_process, color=COLORS["danger"])
        self.stop_btn.pack(side="left")
        self.stop_btn.config(state="disabled")

    # ── CHUNKS ──────────────────────────────────────────────
    def _build_chunks_section(self, root):
        self.chunks_section = self._section(root, "Chunk Generati")
        self.chunks_section.pack_forget()

        btn_row = styled_frame(self.chunks_section)
        btn_row.pack(fill="x", pady=(0, 14))
        styled_button(btn_row, "Salva Script .py",
                      self.save_script, color=COLORS["accent2"]).pack(side="left", padx=(0, 10))
        styled_button(btn_row, "Genera e Lancia su Chatterbox",
                      self.run_chatterbox, color=COLORS["success"]).pack(side="left", padx=(0, 10))
        styled_button(btn_row, "Copia Tutti i Chunk",
                      self.copy_all_chunks, color=COLORS["text_dim"]).pack(side="left")

        self.chunks_container = styled_frame(self.chunks_section)
        self.chunks_container.pack(fill="x")

    # ── GUIDA TAG (nel footer) ───────────────────────────────
    def _build_tag_reference(self, root):
        outer = tk.Frame(root, bg=COLORS["bg"], padx=18, pady=10)
        outer.pack(fill="x")

        # Intestazione con titolo e pulsante copia prompt
        hdr_row = tk.Frame(outer, bg=COLORS["bg"])
        hdr_row.pack(fill="x", pady=(0, 8))
        tk.Label(hdr_row, text="Guida Tag — Sistema Prosodico", font=FONT_H2,
                 fg=COLORS["accent"], bg=COLORS["bg"]).pack(side="left")

        btn_frame = tk.Frame(hdr_row, bg=COLORS["bg"])
        btn_frame.pack(side="right")
        styled_button(btn_frame, "📋 Copia Prompt Guida per AI",
                      self._copy_guide_prompt,
                      color=COLORS["success"]).pack(side="left", padx=(0, 8))
        styled_button(btn_frame, "💾 Scarica Prompt Guida",
                      self._save_guide_prompt,
                      color=COLORS["accent2"]).pack(side="left")

        inner = tk.Frame(outer, bg=COLORS["surface"], bd=0,
                         highlightthickness=1, highlightbackground=COLORS["border"],
                         padx=20, pady=16)
        inner.pack(fill="x")

        # Avviso chunk corti
        warn_frame = tk.Frame(inner, bg="#1a0a00",
                              highlightthickness=1, highlightbackground=COLORS["danger"],
                              padx=14, pady=10)
        warn_frame.pack(fill="x", pady=(0, 16))
        tk.Label(warn_frame,
                 text="⚠  REGOLA ANTI-RIPETIZIONE: ogni chunk deve avere almeno 5 parole pulite (esclusi i tag).\n"
                      "   Chunk troppo corti causano allucinazioni nel modello TTS (parole ripetute, artefatti).\n"
                      "   Se hai battute brevi (\"Bene.\", \"Sì.\", \"O maestro...\") uniscile alla riga successiva.",
                 font=FONT_SMALL, fg=COLORS["warning"], bg="#1a0a00",
                 justify="left", anchor="w").pack(fill="x")

        # Layout a due colonne
        cols = tk.Frame(inner, bg=COLORS["surface"])
        cols.pack(fill="x")
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        left_col = tk.Frame(cols, bg=COLORS["surface"])
        left_col.grid(row=0, column=0, sticky="nw", padx=(0, 16))
        right_col = tk.Frame(cols, bg=COLORS["surface"])
        right_col.grid(row=0, column=1, sticky="nw")

        def section_label(parent, txt):
            tk.Label(parent, text=txt, font=FONT_LABEL,
                     fg=COLORS["accent"], bg=COLORS["surface"],
                     pady=(6)).pack(anchor="w")

        def tag_grid(parent, data_list):
            """data_list: [(tag, color, desc), ...]"""
            f = tk.Frame(parent, bg=COLORS["surface"])
            f.pack(fill="x", pady=(0, 10))
            for col_i, (tag, color, desc) in enumerate(data_list):
                cell = tk.Frame(f, bg=COLORS["surface2"],
                                highlightthickness=1, highlightbackground=color)
                cell.grid(row=0, column=col_i, padx=3, pady=2, sticky="ew")
                f.columnconfigure(col_i, weight=1)
                tk.Label(cell, text=tag, font=("Courier New", 9, "bold"),
                         fg=color, bg=COLORS["surface2"], pady=4, padx=6).pack()
                tk.Label(cell, text=desc, font=FONT_SMALL, fg=COLORS["text_dim"],
                         bg=COLORS["surface2"], padx=6, pady=2, justify="center").pack()

        # ── COLONNA SINISTRA ─────────────────────────────────

        section_label(left_col, "TAG VOCE")
        tag_grid(left_col, [
            ("[v1]...[/v1]",        COLORS["v1"],  "Voce 1"),
            ("[v2]...[/v2]",        COLORS["v2"],  "Voce 2"),
            ("[V1_emo]...",         COLORS["v1"],  "V1 + emozione"),
            ("[V2_emo]...",         COLORS["v2"],  "V2 + emozione"),
            ("[emo]...[/emo]",      "#27ae60",     "Emo. su V1"),
        ])

        section_label(left_col, "STATI EMOTIVI")
        badge_row = tk.Frame(left_col, bg=COLORS["surface"])
        badge_row.pack(fill="x", pady=(0, 12))
        for emo in ALL_EMOTIONS:
            color = EMOTION_COLORS.get(emo, COLORS["text_dim"])
            tk.Label(badge_row, text=" {} ".format(emo), font=FONT_SMALL,
                     fg="#fff", bg=color, padx=4, pady=2).pack(side="left", padx=2, pady=2)

        section_label(left_col, "TAG PAUSE")
        tag_grid(left_col, [
            ("[p1] 0.20s", "#4a9080", "Pausa breve\nVirgola"),
            ("[p2] 0.40s", "#2980b9", "Pausa media\nDue punti"),
            ("[p3] 0.70s", "#8e44ad", "Pausa lunga\nPunto / ? / !"),
            ("[b]  0.90s", "#27ae60", "Breath\nRespiro reale"),
        ])

        section_label(left_col, "TAG ENFASI")
        tag_grid(left_col, [
            ("[e1]", "#e67e22", "Leggera\n+0.10 exag"),
            ("[e2]", "#e84357", "Forte\n+0.25 exag"),
        ])

        # ── COLONNA DESTRA ───────────────────────────────────

        section_label(right_col, "TAG DI GIUNZIONE (prima di [fine])")
        tag_grid(right_col, [
            ("[join]",   "#00cec9", "Stessa frase\noverlap 80ms"),
            ("[cont]",   "#74b9ff", "Stessa battuta\n0.12s smooth"),
            ("[cambio]", "#a29bfe", "Cambio voce\n0.50s + crossfade"),
            ("[para]",   "#fdcb6e", "Nuovo paragrafo\n0.90s"),
            ("[scena]",  "#e17055", "Cambio scena\n2.00s stacco"),
        ])

        section_label(right_col, "STRUTTURA BASE")
        tk.Text(right_col, height=8, bg="#060e1a", fg=COLORS["text_dim"],
                font=("Courier New", 9), relief="flat", bd=0,
                highlightthickness=1, highlightbackground=COLORS["border"],
                wrap="none", state="normal", cursor="arrow"
                ).pack(fill="x", pady=(0, 10))
        struct_box = right_col.winfo_children()[-1]
        struct_box.insert("1.0",
            "[inizio][V1_emozione]\n"
            "Testo da leggere con min 5 parole.[p3][para]\n"
            "[/V1_emozione][fine]\n\n"
            "ORDINE TAG:\n"
            "  1. [V1_emo]   apertura voce\n"
            "  2. Testo  [p1/p2/p3/b]  pause\n"
            "  3. [e1/e2]   enfasi (opzionale)\n"
            "  4. [join/cont/cambio/para/scena]  giunzione\n"
            "  5. [/V1_emo]  chiusura voce"
        )
        struct_box.config(state="disabled")

        section_label(right_col, "LEGACY (retrocompatibilità)")
        tag_grid(right_col, [
            ("[pausa] 0.50s",       "#7f8c8d", "Pausa"),
            ("[pausa_lunga] 1.20s", "#7f8c8d", "Pausa lunga"),
            ("[silenzio] 2.00s",    "#7f8c8d", "Silenzio"),
        ])

        # ── NOTA FINALE ──────────────────────────────────────
        note = tk.Label(inner,
                        text="💡 Usa il pulsante 'Copia Prompt Guida per AI' per ottenere il prompt completo da dare a Claude/GPT "
                             "per riscrivere automaticamente i tuoi capitoli con tutti i tag.",
                        font=FONT_SMALL, fg=COLORS["success"],
                        bg=COLORS["surface"], pady=10, justify="left", anchor="w")
        note.pack(fill="x", pady=(12, 0))

    def _copy_guide_prompt(self):
        self.clipboard_clear()
        self.clipboard_append(GUIDE_PROMPT)
        messagebox.showinfo("Copiato!",
                            "Prompt guida copiato negli appunti!\n\n"
                            "Incollalo in Claude, GPT o qualsiasi altra AI,\n"
                            "poi aggiungi il testo del capitolo da riscrivere.")

    def _save_guide_prompt(self):
        dest = pathlib.Path(self.var_chatterbox_dir.get() or str(pathlib.Path.cwd()))
        path = dest / "PROMPT_GUIDA_CHATTERTEXT.txt"
        path.write_text(GUIDE_PROMPT, encoding="utf-8")
        messagebox.showinfo("Salvato!",
                            "Prompt guida salvato in:\n{}\n\n"
                            "Aprilo con qualsiasi editor di testo.".format(path))

    # ── FOOTER ──────────────────────────────────────────────
    def _build_footer(self, root):
        ft = tk.Frame(root, bg=COLORS["bg"], pady=20)
        ft.pack(fill="x")
        tk.Label(ft, text="2026 (c) ChatterText v2.1 by Gerardo D'Orrico  —  GPU Ready Edition",
                 font=FONT_SMALL, fg=COLORS["text_dim"], bg=COLORS["bg"]).pack()

    # ── HELPERS ─────────────────────────────────────────────
    def _section(self, parent, title):
        outer = tk.Frame(parent, bg=COLORS["bg"], padx=18, pady=10)
        outer.pack(fill="x")
        tk.Label(outer, text=title, font=FONT_H2,
                 fg=COLORS["accent"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 8))
        inner = tk.Frame(outer, bg=COLORS["surface"], bd=0,
                         highlightthickness=1, highlightbackground=COLORS["border"],
                         padx=20, pady=16)
        inner.pack(fill="x")
        return inner

    def _lentry(self, parent, label, default, wide=False):
        grp = styled_frame(parent); grp.pack(side="left", padx=(0, 16))
        tk.Label(grp, text=label, font=FONT_LABEL,
                 fg=COLORS["accent"], bg=COLORS["surface"]).pack(anchor="w")
        var = tk.StringVar(value=default)
        styled_entry(grp, width=30 if wide else 10, textvariable=var).pack(anchor="w", pady=(2, 0))
        return var

    def _clear_placeholder(self, e):
        if "Incolla qui" in self.input_text.get("1.0", "end-1c"):
            self.input_text.delete("1.0", "end")

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Seleziona cartella Chatterbox")
        if d:
            self.var_chatterbox_dir.set(d)

    def _open_presets(self):
        EmotionPresetsWindow(self, self.emotion_presets,
                             on_save=lambda p: self.emotion_presets.update(p))

    def _update_device_badge(self):
        def _detect():
            device, info = get_device_info_string()
            color = COLORS["gpu"] if device == "cuda" else COLORS["cpu"]
            icon  = "🟢 " if device == "cuda" else "🔵 "
            self.after(0, lambda: self._set_device_badge(icon + info, color))
        threading.Thread(target=_detect, daemon=True).start()

    def _set_device_badge(self, text, color):
        self.device_badge_var.set(text)
        self.device_badge.config(bg=color)

    # ── LOGICA PRINCIPALE ────────────────────────────────────
    def process_text(self):
        raw = self.input_text.get("1.0", "end-1c").strip()
        if not raw or "Incolla qui" in raw:
            messagebox.showwarning("Attenzione", "Inserisci del testo prima di processare!")
            return

        has_tags = bool(re.search(r"\[inizio\]", raw, re.IGNORECASE))
        normalized = (
            re.sub(r"\[inizio\]([\s\S]*?)\[fine\]",
                   lambda m: "[inizio]" + normalize_text(m.group(1)) + "[fine]",
                   raw, flags=re.IGNORECASE)
            if has_tags else normalize_text(raw)
        )

        errors = analyze_text(normalized)
        words  = [w for w in normalized.split() if w]
        self.var_total_words.set(str(len(words)))
        self.var_total_chars.set(str(len(normalized)))
        self.var_errors.set(str(len(errors)))
        self.stats_frame.pack(fill="x")

        # Conta tag
        tag_count   = len(re.findall(r"\[inizio\]", normalized, re.IGNORECASE))
        emo_pat     = r"\[(?:(?:v1|v2)_)?(?:" + "|".join(ALL_EMOTIONS) + r")\]"
        emo_count   = len(re.findall(emo_pat, normalized, re.IGNORECASE))
        pause_pat   = r"\[(?:p[123]|b|pausa(?:_lunga)?|silenzio)\]"
        pause_count = len(re.findall(pause_pat, normalized, re.IGNORECASE))
        emph_count  = len(re.findall(r"\[e[12]\]", normalized, re.IGNORECASE))
        join_count  = len(re.findall(r"\[(?:join|cont|cambio|para|scena)\]", normalized, re.IGNORECASE))
        info_parts  = []
        if tag_count:  info_parts.append("{} blocchi".format(tag_count))
        if emo_count:  info_parts.append("{} emozioni".format(emo_count))
        if pause_count: info_parts.append("{} pause".format(pause_count))
        if emph_count: info_parts.append("{} enfasi".format(emph_count))
        if join_count: info_parts.append("{} giunzioni".format(join_count))
        if info_parts:
            self.tag_info_label.config(text="  ".join(info_parts), fg=COLORS["success"])
        else:
            self.tag_info_label.config(text="Modalità automatica (nessun tag trovato)",
                                       fg=COLORS["warning"])

        self.error_box.config(state="normal")
        self.error_box.delete("1.0", "end")
        if errors:
            for etype, msg in errors:
                self.error_box.insert("end", "{} {}\n".format(
                    "ATTENZIONE:" if etype == "warning" else "INFO:", msg))
        else:
            self.error_box.insert("end", "Nessun problema trovato!")
            self.error_box.config(fg=COLORS["success"])
        self.error_box.config(state="disabled")

        try:
            min_w = int(self.var_min_words.get())
            max_w = int(self.var_max_words.get())
            max_c = int(self.var_max_chars.get())
        except ValueError:
            min_w, max_w, max_c = 20, 40, 240

        chunks = chunk_text(normalized, min_w, max_w, max_c)
        self.processed_chunks = chunks
        self.var_total_chunks.set(str(len(chunks)))

        # Avvisa se ci sono chunk troppo corti
        short_chunks = []
        for i, c in enumerate(chunks):
            clean = _protected_pattern().sub("", c).strip()
            if len(clean.split()) < CHUNK_MIN_WORDS:
                short_chunks.append(i+1)
        if short_chunks:
            messagebox.showwarning(
                "Chunk troppo corti!",
                "I seguenti chunk hanno meno di {} parole e potrebbero\n"
                "causare ripetizioni nel modello TTS:\n\n"
                "Chunk: {}\n\n"
                "Consiglio: uniscili manualmente o usa il Prompt Guida per\n"
                "riscrivere il testo con blocchi di dimensione corretta.".format(
                    CHUNK_MIN_WORDS, ", ".join(str(n) for n in short_chunks[:10])))

        self._render_chunks()
        self.chunks_section.pack(fill="x")

    def _render_chunks(self):
        for w in self.chunks_container.winfo_children():
            w.destroy()
        self.chunk_vars = []

        for i, chunk in enumerate(self.processed_chunks):
            chunk_clean = _protected_pattern().sub("", chunk).strip()
            words  = len(chunk_clean.split())
            chars  = len(chunk_clean)
            status, status_text = chunk_status(words, chars)
            status_color = {"success": COLORS["success"],
                            "warning": COLORS["warning"],
                            "danger":  COLORS["danger"]}[status]

            voice, emotion = detect_chunk_tags(chunk)
            emph_list  = detect_emphasis_tags(chunk)
            pause_list = detect_pause_tags(chunk)
            join_tag   = detect_join_tag(chunk)

            if voice == "v2":
                v_label, v_color = "V2", COLORS["v2"]
            elif voice == "v1":
                v_label, v_color = "V1", COLORS["v1"]
            else:
                v_label, v_color = "Auto", COLORS["text_dim"]

            card = tk.Frame(self.chunks_container, bg=COLORS["chunk_bg"],
                            bd=0, highlightthickness=1,
                            highlightbackground=COLORS["border"])
            card.pack(fill="x", pady=(0, 10))

            hdr = tk.Frame(card, bg=COLORS["header_bg"], pady=8, padx=12)
            hdr.pack(fill="x")

            tk.Label(hdr, text="Chunk {}".format(i+1),
                     font=FONT_LABEL, fg=COLORS["accent"],
                     bg=COLORS["header_bg"]).pack(side="left")
            tk.Label(hdr, text=" {} ".format(v_label), font=FONT_SMALL,
                     fg="#fff", bg=v_color, padx=6, pady=2).pack(side="left", padx=4)

            if emotion:
                emo_color = EMOTION_COLORS.get(emotion, COLORS["text_dim"])
                tk.Label(hdr, text=" {} ".format(emotion), font=FONT_SMALL,
                         fg="#fff", bg=emo_color, padx=6, pady=2).pack(side="left", padx=2)

            for etag in emph_list:
                ec = "#e84357" if etag == "e2" else "#e67e22"
                tk.Label(hdr, text=" {} ".format(etag), font=FONT_SMALL,
                         fg="#fff", bg=ec, padx=5, pady=2).pack(side="left", padx=2)

            shown_pauses = []
            for ptag, _ in pause_list:
                if ptag not in shown_pauses:
                    shown_pauses.append(ptag)
                if len(shown_pauses) >= 3:
                    break
            for ptag in shown_pauses:
                pname = ptag.strip("[]")
                pc = {"p1": "#4a9080", "p2": "#2980b9", "p3": "#8e44ad",
                      "b": "#27ae60"}.get(pname, "#7f8c8d")
                tk.Label(hdr, text=" {} ".format(ptag), font=FONT_SMALL,
                         fg="#fff", bg=pc, padx=5, pady=2).pack(side="left", padx=1)

            if join_tag:
                jname = join_tag.strip("[]")
                jc = {"join": "#00cec9", "cont": "#74b9ff", "cambio": "#a29bfe",
                      "para": "#fdcb6e", "scena": "#e17055"}.get(jname, COLORS["text_dim"])
                jfg = "#000" if jname in ("para",) else "#fff"
                tk.Label(hdr, text=" {} ".format(join_tag), font=FONT_SMALL,
                         fg=jfg, bg=jc, padx=5, pady=2).pack(side="left", padx=1)

            info = tk.Frame(hdr, bg=COLORS["header_bg"])
            info.pack(side="right")
            tk.Label(info, text="{} par.  {} car.".format(words, chars),
                     font=FONT_SMALL, fg=COLORS["text_dim"],
                     bg=COLORS["header_bg"]).pack(side="left", padx=8)
            tk.Label(info, text=status_text, font=FONT_SMALL,
                     fg=status_color, bg=COLORS["header_bg"]).pack(side="left")

            self.chunk_vars.append(tk.StringVar(value=chunk))
            idx = i
            ta_frame = tk.Frame(card, bg=COLORS["chunk_bg"], padx=8, pady=6)
            ta_frame.pack(fill="x")
            ta = tk.Text(ta_frame, height=4, bg=COLORS["surface2"],
                         fg=COLORS["text"], font=FONT_MONO, relief="flat", bd=0,
                         wrap="word", insertbackground=COLORS["accent"],
                         highlightthickness=1, highlightbackground=COLORS["border"])
            ta.insert("1.0", chunk)
            ta.pack(fill="x")
            ta.bind("<KeyRelease>", lambda e, t=ta, ix=idx: self._on_chunk_edit(t, ix))

            act = tk.Frame(card, bg=COLORS["chunk_bg"], padx=8, pady=6)
            act.pack(fill="x")
            styled_button(act, "Copia",
                          lambda ix=idx: self._copy_chunk(ix)).pack(side="left", padx=(0, 6))
            styled_button(act, "Dividi",
                          lambda ix=idx: self._split_chunk(ix),
                          color=COLORS["warning"]).pack(side="left", padx=(0, 6))
            if i < len(self.processed_chunks) - 1:
                styled_button(act, "Unisci al successivo",
                              lambda ix=idx: self._merge_chunk(ix),
                              color="#17a2b8").pack(side="left")

    def _on_chunk_edit(self, ta, idx):
        self.processed_chunks[idx] = ta.get("1.0", "end-1c")

    def _copy_chunk(self, idx):
        self.clipboard_clear()
        self.clipboard_append(self.processed_chunks[idx])
        messagebox.showinfo("Copiato", "Chunk {} copiato!".format(idx+1))

    def copy_all_chunks(self):
        self.clipboard_clear()
        self.clipboard_append("\n\n---\n\n".join(self.processed_chunks))
        messagebox.showinfo("Copiato", "Tutti i chunk copiati!")

    def _split_chunk(self, idx):
        text = self.processed_chunks[idx]
        mid  = len(text) // 2
        win  = text[max(0, mid-100): min(len(text), mid+100)]
        m    = re.search(r"[.!?;:]\s", win)
        sp   = max(0, mid-100) + m.start() + 2 if m else mid
        self.processed_chunks[idx:idx+1] = [text[:sp].strip(), text[sp:].strip()]
        self._render_chunks()
        self.var_total_chunks.set(str(len(self.processed_chunks)))

    def _merge_chunk(self, idx):
        if idx >= len(self.processed_chunks) - 1:
            return
        merged = self.processed_chunks[idx] + " " + self.processed_chunks[idx+1]
        self.processed_chunks[idx:idx+2] = [merged]
        self._render_chunks()
        self.var_total_chunks.set(str(len(self.processed_chunks)))

    # ── SCRIPT & ESECUZIONE ─────────────────────────────────
    def _build_script(self):
        if not self.processed_chunks:
            messagebox.showwarning("Attenzione", "Processa prima il testo!")
            return None
        try:
            exag = float(self.var_exag.get())
            cfg  = float(self.var_cfg.get())
            temp = float(self.var_temp.get())
        except ValueError:
            exag, cfg, temp = 0.62, 0.70, 0.58
        return build_python_script(
            self.processed_chunks, exag, cfg, temp,
            self.var_voice1.get().strip() or "3l14n.wav",
            self.var_voice2.get().strip(),
            self.emotion_presets,
            self.var_device_mode.get()
        )

    def save_script(self):
        script = self._build_script()
        if not script:
            return
        dest = pathlib.Path(self.var_chatterbox_dir.get() or str(pathlib.Path.cwd()))
        path = dest / "chatterbox_auto.py"
        path.write_text(script, encoding="utf-8")
        self.script_path = str(path)
        messagebox.showinfo("Salvato", "Script salvato in:\n{}".format(path))

    def run_chatterbox(self):
        if self._running_proc and self._running_proc.poll() is None:
            messagebox.showwarning("In esecuzione",
                                   "Una generazione è già in corso!\nPremi Stop per interromperla.")
            return
        script = self._build_script()
        if not script:
            return
        dest = pathlib.Path(self.var_chatterbox_dir.get() or str(pathlib.Path.cwd()))
        sf = dest / "chatterbox_auto.py"
        sf.write_text(script, encoding="utf-8")
        self.script_path = str(sf)

        total_chunks = len(self.processed_chunks)

        self.log_section.pack(fill="x")
        self.progress_var.set(0)
        self.var_progress_label.set("0 / {} chunk".format(total_chunks))
        self.var_eta.set("Avvio in corso...")

        dm = self.var_device_mode.get()
        if dm == "cuda":
            self.var_device_live.set("⚡ GPU CUDA")
        elif dm == "cpu":
            self.var_device_live.set("🔵 CPU")
        else:
            self.var_device_live.set("🔄 Auto-detect...")

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end",
            "Avvio: python {}\n  Cartella: {}\n  Dispositivo: {}\n{}\n".format(
                sf, dest, dm.upper(), "-"*60))
        self.log_text.config(state="disabled")

        self.stop_btn.config(state="normal")
        self._gen_start_time = time.time()

        def run():
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.Popen(
                    [sys.executable, str(sf)],
                    cwd=str(dest),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    env=env)
                self._running_proc = proc

                for line in proc.stdout:
                    self._append_log(line)
                    m = re.search(r"Chunk\s+(\d+)/(\d+)", line)
                    if m:
                        n, tot = int(m.group(1)), int(m.group(2))
                        pct = int((n / tot) * 100)
                        elapsed = time.time() - self._gen_start_time
                        avg = elapsed / n if n > 0 else 0
                        remaining = avg * (tot - n)
                        self.after(0, lambda p=pct, nn=n, t=tot, r=remaining:
                                   self._update_progress(p, nn, t, r))
                    if "GPU" in line and "CUDA" in line.upper():
                        self.after(0, lambda: self.var_device_live.set("⚡ GPU CUDA — attivo"))
                    elif "CPU" in line and "dispositivo" in line.lower():
                        self.after(0, lambda: self.var_device_live.set("🔵 CPU — attivo"))

                proc.wait()
                rc = proc.returncode
                self._append_log("\n{}\n".format("-"*60))

                if rc == 0:
                    elapsed = time.time() - self._gen_start_time
                    self._append_log("Completato in {:.1f}s ({:.1f} min)!\n".format(
                        elapsed, elapsed/60))
                    self.after(0, lambda: self.progress_var.set(100))
                    self.after(0, lambda: self.var_progress_label.set(
                        "{} / {} chunk — COMPLETATO".format(total_chunks, total_chunks)))
                    self.after(0, lambda: self.var_eta.set(
                        "Tempo totale: {:.1f}s".format(elapsed)))
                    if self.var_notify_sound.get():
                        threading.Thread(target=play_completion_sound, daemon=True).start()
                    self.after(0, lambda: messagebox.showinfo(
                        "Generazione Completata!",
                        "File audio creato con successo!\n\nChunk: {}/{}\nTempo: {:.1f}s ({:.1f} min)".format(
                            total_chunks, total_chunks, elapsed, elapsed/60)))
                else:
                    self._append_log("Errore (code {})\n".format(rc))
            except Exception as ex:
                self._append_log("\nErrore avvio: {}\n".format(ex))
            finally:
                self.after(0, lambda: self.stop_btn.config(state="disabled"))

        threading.Thread(target=run, daemon=True).start()

    def _update_progress(self, pct, n, tot, remaining):
        self.progress_var.set(pct)
        self.var_progress_label.set("{} / {} chunk".format(n, tot))
        if remaining > 0:
            self.var_eta.set("ETA: {:.0f}s (~{:.1f} min)".format(remaining, remaining/60))

    def _stop_process(self):
        if self._running_proc and self._running_proc.poll() is None:
            self._running_proc.terminate()
            self._append_log("\n⏹ Processo interrotto dall'utente.\n")
            self.stop_btn.config(state="disabled")
            self.var_progress_label.set("Interrotto")
            self.var_eta.set("")

    def _append_log(self, text):
        def _do():
            self.log_text.config(state="normal")
            self.log_text.insert("end", text)
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.after(0, _do)

    def clear_all(self):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", "Incolla qui il tuo testo (fino a 10000 caratteri)...")
        self.processed_chunks = []
        self.chunk_vars = []
        for v in (self.var_total_words, self.var_total_chars,
                  self.var_total_chunks, self.var_errors):
            v.set("0")
        self.var_char_count.set("0 / 10000 caratteri")
        self.stats_frame.pack_forget()
        self.chunks_section.pack_forget()
        self.log_section.pack_forget()
        for w in self.chunks_container.winfo_children():
            w.destroy()


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    app = ChatterTextApp()
    app.mainloop()