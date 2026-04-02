#!/usr/bin/env python3
"""
Audio Time Stretcher con Librosa
Rallenta/velocizza file audio senza alterare il tono della voce.
Utile per rallentare la velocità di lettura di output TTS (Chatterbox, ecc.)

Uso:
    python audio_stretch.py input.wav output.wav --rate 0.85
    python audio_stretch.py input.wav output.wav --rate 0.85 --silence 150

Parametri:
    --rate     : velocità (0.85 = 15% più lento, 1.0 = originale, 1.2 = 20% più veloce)
    --silence  : millisecondi di silenzio da aggiungere tra i chunk (se dividi per frasi)
    --split    : divide per silenzi e aggiunge pause extra tra le parole
"""

import argparse
import sys
import os

def check_dependencies():
    missing = []
    try:
        import librosa
    except ImportError:
        missing.append("librosa")
    try:
        import soundfile
    except ImportError:
        missing.append("soundfile")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print(f"❌ Dipendenze mancanti: {', '.join(missing)}")
        print(f"   Installa con: pip install {' '.join(missing)}")
        sys.exit(1)

def time_stretch_audio(input_path, output_path, rate=0.85, add_silence_ms=0, split_words=False):
    import librosa
    import soundfile as sf
    import numpy as np

    print(f"📂 Caricamento: {input_path}")
    y, sr = librosa.load(input_path, sr=None)  # mantieni sample rate originale
    
    duration_original = len(y) / sr
    print(f"⏱  Durata originale: {duration_original:.2f}s")

    if split_words and add_silence_ms > 0:
        # Trova silenzi e inserisci pause extra
        print(f"🔍 Analisi silenzi nel file audio...")
        
        # Calcola energia per frame
        frame_length = 2048
        hop_length = 512
        energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Soglia silenzio (10% del massimo)
        threshold = np.max(energy) * 0.10
        is_silent = energy < threshold
        
        # Trova transizioni silenzio/voce
        silence_samples = librosa.frames_to_samples(np.where(is_silent)[0], hop_length=hop_length)
        
        # Applica time stretch a tutto il file
        print(f"🎚  Applicazione time stretch (rate={rate})...")
        y_stretched = librosa.effects.time_stretch(y, rate=rate)
        
        # Aggiungi silenzio extra nelle pause
        extra_silence = np.zeros(int(sr * add_silence_ms / 1000))
        
        # Ricostruzione con pause (semplificata: aggiungi silenzio dove c'erano già silenzi)
        chunks = []
        prev_i = 0
        silent_regions = librosa.effects.split(y, top_db=30)  # trova regioni non silenziose
        
        for start, end in silent_regions:
            # Stretch del chunk vocale
            chunk = y[start:end]
            chunk_stretched = librosa.effects.time_stretch(chunk, rate=rate)
            chunks.append(chunk_stretched)
            chunks.append(extra_silence)  # pausa extra dopo ogni parola/frase
        
        if chunks:
            y_final = np.concatenate(chunks)
        else:
            y_final = y_stretched
            
    else:
        # Semplice time stretch su tutto il file
        print(f"🎚  Applicazione time stretch (rate={rate})...")
        y_final = librosa.effects.time_stretch(y, rate=rate)

    duration_final = len(y_final) / sr
    print(f"⏱  Nuova durata: {duration_final:.2f}s ({((duration_final/duration_original)-1)*100:+.1f}%)")

    print(f"💾 Salvataggio: {output_path}")
    sf.write(output_path, y_final, sr)
    print(f"✅ Fatto!")


def batch_process(input_dir, output_dir, rate=0.85, add_silence_ms=0):
    """Processa tutti i .wav in una cartella"""
    import librosa
    import soundfile as sf
    import numpy as np
    
    os.makedirs(output_dir, exist_ok=True)
    wav_files = [f for f in os.listdir(input_dir) if f.endswith('.wav')]
    
    if not wav_files:
        print(f"❌ Nessun file .wav trovato in {input_dir}")
        return
    
    print(f"📁 Processamento di {len(wav_files)} file...")
    
    for filename in wav_files:
        in_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, filename)
        time_stretch_audio(in_path, out_path, rate=rate, add_silence_ms=add_silence_ms)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="🎙️ Audio Time Stretcher per TTS - rallenta senza cambiare tono",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Rallenta del 15%
  python audio_stretch.py input.wav output.wav --rate 0.85
  
  # Rallenta del 20% e aggiungi 200ms di pausa tra parole
  python audio_stretch.py input.wav output.wav --rate 0.80 --silence 200 --split

  # Processa una cartella intera
  python audio_stretch.py --batch ./input_dir ./output_dir --rate 0.85

Rate comuni:
  0.70 = 30% più lento
  0.80 = 20% più lento  
  0.85 = 15% più lento  ← consigliato per TTS
  0.90 = 10% più lento
  1.00 = originale
  1.20 = 20% più veloce
        """
    )
    
    parser.add_argument("input", nargs="?", help="File audio input (.wav)")
    parser.add_argument("output", nargs="?", help="File audio output (.wav)")
    parser.add_argument("--rate", type=float, default=0.85,
                        help="Velocità (0.85=15%% più lento, default: 0.85)")
    parser.add_argument("--silence", type=int, default=0,
                        help="Millisecondi di silenzio extra tra parole (default: 0)")
    parser.add_argument("--split", action="store_true",
                        help="Analizza e inserisce pause tra frasi/parole")
    parser.add_argument("--batch", nargs=2, metavar=("INPUT_DIR", "OUTPUT_DIR"),
                        help="Modalità batch: processa tutti i .wav in una cartella")
    
    args = parser.parse_args()
    
    check_dependencies()
    
    print("🎙️  Audio Time Stretcher - Chatterbox TTS Helper")
    print("=" * 50)
    
    if args.batch:
        input_dir, output_dir = args.batch
        batch_process(input_dir, output_dir, rate=args.rate, add_silence_ms=args.silence)
    elif args.input and args.output:
        if not os.path.exists(args.input):
            print(f"❌ File non trovato: {args.input}")
            sys.exit(1)
        time_stretch_audio(
            args.input, 
            args.output, 
            rate=args.rate,
            add_silence_ms=args.silence,
            split_words=args.split
        )
    else:
        parser.print_help()
        print("\n⚠️  Specifica input e output, o usa --batch per la cartella.")


if __name__ == "__main__":
    main()