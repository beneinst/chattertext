import os
import re
import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# Imposta il device per Intel ARC
if hasattr(torch, "xpu") and torch.xpu.is_available():
    device = "xpu"
else:
    device = "cpu"

map_location = torch.device(device)

# Patch per torch.load
torch_load_original = torch.load
def patched_torch_load(*args, **kwargs):
    if 'map_location' not in kwargs:
        kwargs['map_location'] = map_location
    return torch_load_original(*args, **kwargs)

torch.load = patched_torch_load

# Carica il modello
model = ChatterboxMultilingualTTS.from_pretrained(device=device)

# === NORMALIZZAZIONE TESTO SENZA TAG PAUSA ===
def normalize_text(text):
    # Elimina tag pause se presenti
    text = re.sub(r'<pause_[a-zA-Z_]+>', '', text)

    # Normalizza i ritorni a capo
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Aggiunge pause naturali con due spazi dopo . ? !
    text = re.sub(r'([.!?])\s+', r'\1  ', text)

    return text.strip()

# === SPEZZATURA IN CHUNK DA 350–500 CARATTERI ===
def chunk_text(text, max_len=450):
    chunks = []
    current = ""

    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        if len(current) + len(sentence) > max_len:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks

# === CARICA TESTO ===
with open("testo_da_leggere.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

text = normalize_text(raw_text)

chunks = chunk_text(text, max_len=450)

print(f"Numero segmenti generati: {len(chunks)}")

# === GENERA AUDIO PER OGNI CHUNK ===
audio_segments = []

for idx, par in enumerate(chunks):
    print(f"Genero segmento {idx+1}/{len(chunks)}…")

    # Aggiunge pausa naturale tra segmenti
    par = par + "...  "

    wav = model.generate(
    par,
    language_id='it',
    audio_prompt_path="2.Voci/3l14n.wav",
    exaggeration=0.7,
    cfg_weight=0.5,
    temperature=0.6,
    min_p=0.02,
    top_p=0.98
    )

    audio_segments.append(wav)

# === CONCATENA ===
final_audio = torch.cat(audio_segments, dim=-1)

output_path = "1.Output/audiolibro_01.wav"
ta.save(output_path, final_audio, model.sr)

print(f"File audio generato: {output_path}")