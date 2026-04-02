#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatterText - App Desktop Python
Analizza testo, genera chunk e lancia Chatterbox TTS direttamente.
Posizionare nella root di Chatterbox ed eseguire con: python chattertext_app.py

TAG SUPPORTATI:
  Voce:     [v1]...[/v1]   [v2]...[/v2]
  Blocchi:  [inizio]...[fine]
  Pause:    [pausa]  [pausa_lunga]  [silenzio]
  Emotivi (voce neutra):        [calmo]...[/calmo]
  Emotivi (voce specifica):     [V1_calmo]...[/V1_calmo]  [V2_calmo]...[/V2_calmo]
  Stati: calmo | appassionato | arrabbiato | triste | ironico
         sussurrato | riflessivo | deciso | preoccupato | gentile | serio
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import os
import subprocess
import threading
import sys
import re
import json
import pathlib

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
#  LOGICA TESTO
# ─────────────────────────────────────────
def _protected_pattern():
    emo = "|".join(ALL_EMOTIONS)
    return re.compile(
        r"\[/?(?:v1|v2|inizio|fine|pausa|pausa_lunga|silenzio"
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
    words = re.findall(r"\b\w+\b", text.lower())
    wcount = {}
    for w in words:
        wcount[w] = wcount.get(w, 0) + 1
    repeated = sorted([(w, c) for w, c in wcount.items() if c > 3 and len(w) > 3],
                      key=lambda x: -x[1])[:5]
    if repeated:
        errors.append(("info", "Parole ripetute: " +
                       ", ".join('"{}" ({}x)'.format(w, c) for w, c in repeated)))
    specials = re.findall(r"[^\w\s.,;:!?\u00C0-\u00F9'\"\\-]", text)
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
    if words > 60 or chars > 350:
        return "danger", "Troppo lungo"
    if words < 20 or chars < 100:
        return "warning", "Troppo corto"
    return "success", "Ottimale"


def detect_chunk_tags(chunk):
    """Restituisce (voice, emotion) dal chunk."""
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
#  GENERAZIONE SCRIPT PYTHON
# ─────────────────────────────────────────
def build_python_script(chunks, default_exag, default_cfg, default_temp,
                        voice1, voice2, emotion_presets):
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

    lines = [
        "# Script generato automaticamente da ChatterText Desktop",
        "# Versione con Tag Emotivi + CPU Safe + Trim + Crossfade",
        "import os, re, sys, torch, torchaudio as ta, pathlib, datetime",
        "from chatterbox.mtl_tts import ChatterboxMultilingualTTS",
        "",
        "# Fix encoding per Windows (cp1252 -> utf-8)",
        "if sys.platform == 'win32':",
        "    import io",
        "    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')",
        "    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')",
        "",
        "_orig_torch_load = torch.load",
        "def _cpu_safe_load(*args, **kwargs):",
        "    kwargs.setdefault('map_location', torch.device('cpu'))",
        "    return _orig_torch_load(*args, **kwargs)",
        "torch.load = _cpu_safe_load",
        "",
        "print('Caricamento modello Chatterbox...')",
        "model = ChatterboxMultilingualTTS.from_pretrained(device='cpu')",
        "print('Modello caricato!')",
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
        "# === PRESET EMOTIVI ===",
        "EMOTION_PRESETS = {}".format(presets_repr),
        "DEFAULT_PARAMS  = {{'exaggeration':{},'cfg_weight':{},'temperature':{},'top_p':0.75,'min_p':0.15}}".format(
            default_exag, default_cfg, default_temp),
        "",
        "PAUSE_MAP = {'[pausa]': 0.5, '[pausa_lunga]': 1.2, '[silenzio]': 2.0}",
        'EMO_NAMES = r"{}"'.format(emo_pipe),
        "",
        "def parse_chunk(chunk):",
        "    parts = re.split(r'(\\[pausa(?:_lunga)?\\]|\\[silenzio\\])', chunk)",
        "    pauses = [('pause', PAUSE_MAP[p]) for p in parts if p in PAUSE_MAP]",
        "    m = re.search(r'\\[(v1|v2)_(' + EMO_NAMES + r')\\]', chunk, re.IGNORECASE)",
        "    if m:",
        "        v, e = m.group(1).lower(), m.group(2).lower()",
        "        clean = re.sub(r'\\[/?(?:v1|v2)_(?:' + EMO_NAMES + r')\\]', '', chunk)",
        "        return re.sub(r'\\[pausa(?:_lunga)?\\]|\\[silenzio\\]', '', clean).strip(), v, e, pauses",
        "    m = re.search(r'\\[(v1|v2)\\]', chunk, re.IGNORECASE)",
        "    if m:",
        "        v = m.group(1).lower()",
        "        clean = re.sub(r'\\[/?(?:v1|v2)\\]', '', chunk)",
        "        return re.sub(r'\\[pausa(?:_lunga)?\\]|\\[silenzio\\]', '', clean).strip(), v, None, pauses",
        "    m = re.search(r'\\[(' + EMO_NAMES + r')\\]', chunk, re.IGNORECASE)",
        "    if m:",
        "        e = m.group(1).lower()",
        "        clean = re.sub(r'\\[/?(?:' + EMO_NAMES + r')\\]', '', chunk)",
        "        return re.sub(r'\\[pausa(?:_lunga)?\\]|\\[silenzio\\]', '', clean).strip(), 'v1', e, pauses",
        "    clean = re.sub(r'\\[pausa(?:_lunga)?\\]|\\[silenzio\\]', '', chunk).strip()",
        "    return clean, 'v1', None, pauses",
        "",
        "def prosody_params(emotion):",
        "    if emotion and emotion in EMOTION_PRESETS:",
        "        p = EMOTION_PRESETS[emotion].copy()",
        "        p.setdefault('top_p', 0.75); p.setdefault('min_p', 0.15)",
        "        return p",
        "    return DEFAULT_PARAMS.copy()",
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
        "print('\\n' + '='*60)",
        "print('INIZIO GENERAZIONE AUDIO')",
        "print('='*60)",
        "",
        "for idx, (text, voice, emotion, pauses) in enumerate(tagged_chunks):",
        "    emo_label = '[{}]'.format(emotion) if emotion else ''",
        "    print(f'\\n Chunk {idx+1}/{len(tagged_chunks)} [{voice.upper()}]{emo_label} - {len(text.split())} parole')",
        "    voice_prompt = AUDIO_PROMPT_V2 if (voice == 'v2' and HAS_TWO_VOICES) else AUDIO_PROMPT_V1",
        "    p = prosody_params(emotion)",
        "    try:",
        "        wav = model.generate(text, language_id='it', audio_prompt_path=voice_prompt,",
        "            exaggeration=p['exaggeration'], cfg_weight=p['cfg_weight'],",
        "            temperature=p['temperature'], min_p=p['min_p'], top_p=p['top_p'])",
        "        wav = wav / (torch.max(torch.abs(wav)) + 1e-8) * 0.95",
        "        if pauses:",
        "            extra = sum(d for _,d in pauses)",
        "            wav = torch.cat([wav, torch.zeros((wav.shape[0], int(model.sr*extra)))], dim=-1)",
        "        audio_segments.append(wav); print('   OK!')",
        "    except Exception as e:",
        "        print(f'   Errore: {e} - Retry...')",
        "        try:",
        "            wav = model.generate(text, language_id='it', audio_prompt_path=voice_prompt,",
        "                exaggeration=0.0, cfg_weight=0.25, temperature=0.22, min_p=0.20, top_p=0.65)",
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
        "def apply_fade(wav, sr, fade_ms=14):",
        "    f = int(sr * fade_ms / 1000)",
        "    wav = wav.clone()",
        "    wav[...,:f] *= torch.linspace(0,1,f); wav[...,-f:] *= torch.linspace(1,0,f)",
        "    return wav",
        "",
        "final_audio = None",
        "for i, seg in enumerate(audio_segments):",
        "    seg = reduce_noise(seg, model.sr)",
        "    seg = trim_edges(seg, model.sr)",
        "    seg = apply_fade(seg, model.sr)",
        "    if final_audio is None: final_audio = seg; continue",
        "    pause = dynamic_pause(chunks[i-1])",
        "    silence = torch.zeros((seg.shape[0], int(model.sr * pause)))",
        "    final_audio = crossfade_join(final_audio, torch.cat([silence, seg], dim=-1), model.sr)",
        "",
        "final_audio = final_audio / (torch.max(torch.abs(final_audio)) + 1e-8) * 0.95",
        "ta.save(out_name, final_audio, model.sr)",
        "duration = final_audio.shape[-1] / model.sr",
        "print(f'\\n FILE CREATO: {out_name}')",
        "print(f'   Durata: {duration:.1f}s ({duration/60:.1f} min)')",
        "print(f'   Chunk riusciti: {len(audio_segments)}/{len(chunks)}')",
        "if failed_chunks: print(f'   Chunk falliti: {failed_chunks}')",
        "print('\\nProcesso completato!')",
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
        self.title("ChatterText")
        self.geometry("1100x860")
        self.minsize(900, 700)
        self.configure(bg=COLORS["bg"])

        self.processed_chunks = []
        self.chunk_vars = []
        self.script_path = None
        self.emotion_presets = {k: v.copy() for k, v in EMOTION_PRESETS.items()}

        self.var_total_words  = tk.StringVar(value="0")
        self.var_total_chars  = tk.StringVar(value="0")
        self.var_total_chunks = tk.StringVar(value="0")
        self.var_errors       = tk.StringVar(value="0")

        self._build_ui()

    def _build_ui(self):
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=COLORS["bg"])
        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Contenitore centrato con larghezza massima
        self._canvas_window = canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw")

        # Centra e limita larghezza al resize della finestra
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
        self._build_input_section(root)
        self._build_controls_section(root)
        self._build_emotion_reference(root)
        self._build_stats_section(root)
        self._build_log_section(root)
        self._build_chunks_section(root)
        self._build_footer(root)

    def _build_header(self, root):
        hdr = tk.Frame(root, bg="#0a1628", pady=28)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ChatterText", font=FONT_H1,
                 fg="#ffffff", bg="#0a1628").pack()
        tk.Label(hdr, text="Analizza e prepara il testo per Chatterbox TTS",
                 font=FONT_BODY, fg=COLORS["text_dim"], bg="#0a1628").pack(pady=(4, 0))

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

    def _build_controls_section(self, root):
        sec = self._section(root, "Parametri")

        row1 = styled_frame(sec); row1.pack(fill="x", pady=(0, 10))
        self.var_min_words = self._lentry(row1, "Parole min/chunk", "20")
        self.var_max_words = self._lentry(row1, "Parole max/chunk", "40")
        self.var_max_chars = self._lentry(row1, "Caratteri max",    "240")

        row2 = styled_frame(sec); row2.pack(fill="x", pady=(0, 10))
        self.var_voice1 = self._lentry(row2, "Voce 1 (2.Voci/)", "3l14n.wav", wide=True)
        self.var_voice2 = self._lentry(row2, "Voce 2 (opzionale)", "",         wide=True)

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

    def _build_emotion_reference(self, root):
        sec = self._section(root, "Riferimento Tag Emotivi")

        tk.Label(sec, text="Formati supportati:",
                 font=FONT_LABEL, fg=COLORS["accent"], bg=COLORS["surface"]).pack(anchor="w")

        examples = tk.Frame(sec, bg=COLORS["surface"])
        examples.pack(fill="x", pady=(6, 10))

        ex_data = [
            ("[calmo]testo[/calmo]",              "Voce auto + emozione"),
            ("[v1]testo[/v1]",                    "Voce 1, default"),
            ("[v2]testo[/v2]",                    "Voce 2, default"),
            ("[V1_calmo]testo[/V1_calmo]",         "Voce 1 + emozione"),
            ("[V2_arrabbiato]testo[/V2_arrabbiato]", "Voce 2 + emozione"),
        ]
        for col, (tag, desc) in enumerate(ex_data):
            f = tk.Frame(examples, bg=COLORS["surface2"],
                         highlightthickness=1, highlightbackground=COLORS["border"])
            f.grid(row=0, column=col, padx=4, pady=2, sticky="ew")
            examples.columnconfigure(col, weight=1)
            tk.Label(f, text=tag, font=("Courier New", 8), fg=COLORS["accent"],
                     bg=COLORS["surface2"], pady=4, padx=6).pack()
            tk.Label(f, text=desc, font=FONT_SMALL, fg=COLORS["text_dim"],
                     bg=COLORS["surface2"], padx=6).pack()

        badge_row = tk.Frame(sec, bg=COLORS["surface"])
        badge_row.pack(fill="x", pady=(4, 0))
        tk.Label(badge_row, text="Stati: ", font=FONT_LABEL,
                 fg=COLORS["text_dim"], bg=COLORS["surface"]).pack(side="left")
        for emo in ALL_EMOTIONS:
            color = EMOTION_COLORS.get(emo, COLORS["text_dim"])
            tk.Label(badge_row, text=" {} ".format(emo), font=FONT_SMALL,
                     fg="#fff", bg=color, padx=4, pady=2).pack(side="left", padx=2, pady=2)

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

    def _build_log_section(self, root):
        self.log_section = self._section(root, "Output Esecuzione")
        self.log_section.pack_forget()
        self.log_text = scrolledtext.ScrolledText(
            self.log_section, height=12,
            bg="#050505", fg=COLORS["success"],
            font=("Courier New", 9), relief="flat", bd=0,
            state="disabled",
            highlightthickness=1, highlightbackground=COLORS["border"])
        self.log_text.pack(fill="x")

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

    def _build_footer(self, root):
        ft = tk.Frame(root, bg=COLORS["bg"], pady=20)
        ft.pack(fill="x")
        tk.Label(ft, text="2026 (c) ChatterText by Gerardo D'Orrico",
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

    # ── LOGICA ──────────────────────────────────────────────
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

        tag_count = len(re.findall(r"\[inizio\]", normalized, re.IGNORECASE))
        emo_pat   = r"\[(?:(?:v1|v2)_)?(?:" + "|".join(ALL_EMOTIONS) + r")\]"
        emo_count = len(re.findall(emo_pat, normalized, re.IGNORECASE))
        info_parts = []
        if tag_count:
            info_parts.append("{} blocchi [inizio]/[fine]".format(tag_count))
        if emo_count:
            info_parts.append("{} tag emotivi".format(emo_count))
        if info_parts:
            self.tag_info_label.config(text="  ".join(info_parts), fg=COLORS["success"])
        else:
            self.tag_info_label.config(text="Modalita automatica (nessun tag trovato)",
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

        self._render_chunks()
        self.chunks_section.pack(fill="x")

    def _render_chunks(self):
        for w in self.chunks_container.winfo_children():
            w.destroy()
        self.chunk_vars = []

        for i, chunk in enumerate(self.processed_chunks):
            words  = len(chunk.split())
            chars  = len(chunk)
            status, status_text = chunk_status(words, chars)
            status_color = {"success": COLORS["success"],
                            "warning": COLORS["warning"],
                            "danger":  COLORS["danger"]}[status]

            voice, emotion = detect_chunk_tags(chunk)
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

            info = tk.Frame(hdr, bg=COLORS["header_bg"])
            info.pack(side="right")
            tk.Label(info, text="{} parole  {} car.".format(words, chars),
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
                styled_button(act, "Unisci",
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
            self.emotion_presets
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
        script = self._build_script()
        if not script:
            return
        dest = pathlib.Path(self.var_chatterbox_dir.get() or str(pathlib.Path.cwd()))
        sf = dest / "chatterbox_auto.py"
        sf.write_text(script, encoding="utf-8")
        self.script_path = str(sf)

        self.log_section.pack(fill="x")
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end",
            "Avvio: python {}\n  Cartella: {}\n{}\n".format(sf, dest, "-"*60))
        self.log_text.config(state="disabled")

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
                for line in proc.stdout:
                    self._append_log(line)
                proc.wait()
                rc = proc.returncode
                self._append_log("\n{}\n".format("-"*60))
                self._append_log("Completato!\n" if rc == 0
                                 else "Errore (code {})\n".format(rc))
            except Exception as ex:
                self._append_log("\nErrore avvio: {}\n".format(ex))

        threading.Thread(target=run, daemon=True).start()

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