import os
import re
import datetime
import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
import pathlib

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

# === NORMALIZZAZIONE TESTO AVANZATA ===
def normalize_text(text):
    """Normalizza il testo e risolve problemi comuni che causano ripetizioni"""
    
    # 1. Corregge apostrofi strani e maiuscole dopo apostrofo
    text = re.sub(r"l'Om\b", "l'om", text)  # lOm -> l'om
    text = re.sub(r"nell'(\w)", lambda m: f"nell'{m.group(1).lower()}", text)
    text = re.sub(r"dell'(\w)", lambda m: f"dell'{m.group(1).lower()}", text)
    text = re.sub(r"[`´]", "'", text)  # Normalizza apostrofi
    
    # 2. Elimina tag pause se presenti
    text = re.sub(r'<pause_[a-zA-Z_]+>', '', text)
    
    # 3. Rimuovi caratteri problematici rari
    text = re.sub(r'[^\w\s.,;:!?À-ùÀ-Ü\'\"-]', '', text)
    
    # 4. Normalizza spazi multipli
    text = re.sub(r'\s+', ' ', text)
    
    # 5. Normalizza i ritorni a capo
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    
    # 6. Rimuovi punteggiatura ripetuta (es. "..." -> ".")
    text = re.sub(r'([.!?])\1+', r'\1', text)
    
    # 7. Aggiunge pause naturali dopo punteggiatura
    text = re.sub(r'([.!?])\s+', r'\1  ', text)
    
    return text.strip()

# === VARIAZIONE AUTOMATICA DI PAROLE RIPETUTE ===
def vary_repetitions(text):
    """Sostituisce parole troppo ripetute con sinonimi"""
    
    # Dizionario di sinonimi comuni
    synonyms = {
        'sapeva': ['conosceva', 'era consapevole', 'comprendeva'],
        'già': ['ormai', 'a quel punto', 'in quel momento'],
    }
    
    words = text.split()
    
    # Conta occorrenze di parole chiave
    for key_word, alternatives in synonyms.items():
        count = sum(1 for w in words if w.lower() == key_word)
        
        # Se ripetuta più di 2 volte, sostituisci alcune occorrenze
        if count > 2:
            replaced = 0
            for i, word in enumerate(words):
                if word.lower() == key_word and replaced < count - 2:
                    words[i] = alternatives[replaced % len(alternatives)]
                    replaced += 1
    
    return ' '.join(words)

# === SPEZZATURA OTTIMALE: 40-60 PAROLE (250-400 CARATTERI) ===
def chunk_text(text, min_words=30, max_words=60, max_chars=400):
    """
    Spezza il testo in chunk ottimali per Chatterbox
    Target: 40-60 parole, 250-400 caratteri
    """
    chunks = []
    current = ""
    current_word_count = 0
    
    # Split per frasi complete
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        sentence_words = len(sentence.split())
        
        # Controlla se aggiungere questa frase supera i limiti
        would_exceed_words = current_word_count + sentence_words > max_words
        would_exceed_chars = len(current) + len(sentence) > max_chars
        
        if (would_exceed_words or would_exceed_chars) and current_word_count >= min_words:
            # Salva il chunk corrente
            chunks.append(current.strip())
            current = sentence
            current_word_count = sentence_words
        else:
            # Aggiungi al chunk corrente
            if current:
                current += " " + sentence
            else:
                current = sentence
            current_word_count += sentence_words
    
    # Aggiungi l'ultimo chunk
    if current.strip():
        chunks.append(current.strip())
    
    return chunks

# === FUNZIONE PER LOGGING DETTAGLIATO ===
def log_problematic_text(text, chunk_idx, error_msg):
    """Salva i chunk che causano errori per analisi"""
    log_file = pathlib.Path("error_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n")
        f.write(f"Chunk #{chunk_idx}\n")
        f.write(f"Error: {error_msg}\n")
        f.write(f"Parole: {len(text.split())}\n")
        f.write(f"Caratteri: {len(text)}\n")
        f.write(f"Text: {text}\n")
        
        # Analisi parole ripetute
        from collections import Counter
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)
        repeated = [(w, c) for w, c in word_counts.items() if c > 2]
        if repeated:
            f.write(f"Parole ripetute (>2x): {repeated}\n")
        
        f.write(f"{'='*60}\n")

# === CARICA TESTO ===
input_file = "testo_da_leggere.txt"
if not os.path.exists(input_file):
    print(f"❌ File {input_file} non trovato!")
    exit(1)

with open(input_file, "r", encoding="utf-8") as f:
    raw_text = f.read()

# Normalizza e varia ripetizioni
text = normalize_text(raw_text)
text = vary_repetitions(text)

# Verifica lunghezza testo
word_count = len(text.split())
print(f"📝 Testo caricato: {word_count} parole")

# Chunk ottimali: 40-60 parole
chunks = chunk_text(text, min_words=30, max_words=60, max_chars=400)

print(f"📦 Numero segmenti generati: {len(chunks)}")
print(f"📏 Lunghezza segmenti (parole): {[len(c.split()) for c in chunks]}")
print(f"📏 Lunghezza segmenti (caratteri): {[len(c) for c in chunks]}")

# Verifica che nessun chunk superi i limiti
for i, chunk in enumerate(chunks):
    words = len(chunk.split())
    chars = len(chunk)
    if words > 70 or chars > 450:
        print(f"⚠️ WARNING: Chunk {i+1} supera i limiti consigliati!")
        print(f"   Parole: {words}/60, Caratteri: {chars}/400")

# === GENERA AUDIO PER OGNI CHUNK ===
audio_segments = []
failed_chunks = []

for idx, par in enumerate(chunks):
    words = len(par.split())
    chars = len(par)
    
    print(f"\n🎙️ Genero segmento {idx+1}/{len(chunks)}…")
    print(f"   📊 {words} parole, {chars} caratteri")
    
    # Mostra preview
    preview = par[:60] + "..." if len(par) > 60 else par
    print(f"   📄 Preview: {preview}")
    
    try:
        # Parametri ottimizzati
        wav = model.generate(
            par,
            language_id='it',
            audio_prompt_path="2.Voci/3l14n.wav",
            exaggeration=0.7,
            cfg_weight=0.6,
            temperature=0.65,
            min_p=0.03,
            top_p=0.95
        )
        
        audio_segments.append(wav)
        print(f"   ✅ Generato con successo")
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Errore: {error_msg}")
        
        log_problematic_text(par, idx, error_msg)
        failed_chunks.append(idx)
        
        # Retry con parametri conservativi
        print(f"   🔄 Retry con parametri conservativi...")
        try:
            wav = model.generate(
                par,
                language_id='it',
                audio_prompt_path="2.Voci/my_audio.wav",
                exaggeration=0.5,
                cfg_weight=0.75,
                temperature=0.55,
                min_p=0.04,
                top_p=0.92
            )
            audio_segments.append(wav)
            print(f"   ✅ Recuperato")
        except Exception as e2:
            print(f"   ❌ Fallito: {e2}")
            continue

# === VERIFICA E SALVATAGGIO ===
if not audio_segments:
    print("\n❌ Nessun segmento generato. Controlla error_log.txt")
    exit(1)

if failed_chunks:
    print(f"\n⚠️ {len(failed_chunks)} chunk falliti: {failed_chunks}")

# Salvataggio
out_dir = pathlib.Path("1.Output")
out_dir.mkdir(exist_ok=True)

existing = list(out_dir.glob("audiolibro_*.wav"))
num = len(existing) + 1
out_name = out_dir / f"audiolibro_{num:02d}.wav"

final_audio = torch.cat(audio_segments, dim=-1)
ta.save(out_name, final_audio, model.sr)

duration = final_audio.shape[-1] / model.sr

print(f"\n✅ File creato: {out_name}")
print(f"📊 Statistiche:")
print(f"   - Segmenti: {len(chunks)} totali, {len(audio_segments)} riusciti")
print(f"   - Durata: {duration:.1f} secondi ({duration/60:.1f} minuti)")
print(f"   - Parole/segmento: {[len(c.split()) for c in chunks]}")

# Suggerimenti finali
if failed_chunks:
    print(f"\n💡 SUGGERIMENTI:")
    print(f"   - Controlla error_log.txt per i dettagli")
    print(f"   - Prova a ridurre max_words a 50")
    print(f"   - Verifica parole ripetute nei chunk falliti")