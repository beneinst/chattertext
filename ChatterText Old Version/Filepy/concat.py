import subprocess, pathlib

dir_out   = pathlib.Path("1.Output")
wav_files = sorted(dir_out.glob("audiolibro_*.wav"))

if not wav_files:
    exit("❌  Nessun file audiolibro_*.wav trovato.")

list_file = dir_out / "__file_list.txt"
with list_file.open("w", encoding="utf-8") as f:
    for wav in wav_files:
        f.write(f"file '{wav.resolve()}'\n")

final = dir_out / "audiolibro_completo.wav"
cmd   = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(final), "-y"]
subprocess.run(cmd, check=True)

list_file.unlink()          # pulizia
print(f"✅  Libro completo creato: {final}")