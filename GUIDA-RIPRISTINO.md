# Ripristino di ChatterText e Qwen VoiceDesign

Configurazione rilevata il 5 settembre 2026. Guida per Windows a 64 bit.

Questa guida descrive il ripristino dell'app attuale, compreso il box per creare voci da testo. Non è stata eseguita una reinstallazione: l'app funzionante è rimasta intatta. La procedura su ambiente pulito dovrà essere collaudata nelle prossime prove. I file delle dipendenze allegati fotografano ciò che è installato oggi, ma non contengono i pacchetti o i modelli: per reinstallare da questi elenchi occorre Internet e che le versioni siano ancora disponibili.

## 1. Le due parti del sistema

| Parte | Situazione attuale |
|---|---|
| App ChatterText | `D:\Siti GitHub\chattertext` |
| Avvio | `Avvia-Chattertext_3.bat`, che richiama `venv_chatterbox\Scripts\pythonw.exe` e `ChatterText_3.0.py` |
| Ambiente Chatterbox | `venv_chatterbox`, Python 3.12.0 |
| Libreria Chatterbox effettivamente usata | Sottocartella `chatterbox`, installazione modificabile locale, versione 0.1.7 |
| GPU verificata | NVIDIA GeForce RTX 3060, 12 GB; driver rilevato 595.79 |
| PyTorch Chatterbox | 2.5.1+cu121; torchaudio 2.5.1+cu121 |
| Modello Chatterbox | `ResembleAI/chatterbox`, Multilingual V3, file `t3_mtl23ls_v3.safetensors` |
| Ambiente Qwen | `.venv`, Python 3.12.14, PyTorch e torchaudio 2.11.0+cu128 |
| Qwen | qwen-tts 0.1.1, Transformers 4.57.3, Accelerate 1.12.0 |

Cartella Qwen attuale:

```text
C:\Users\gerar\Documents\Codex\2026-09-05\referenced-chatgpt-conversation-this-is-an-2\outputs\Qwen3-VoiceDesign
```

Il file `qwen_voice_config.json`, accanto a ChatterText, contiene questo percorso. Il box avvia Qwen come processo separato: non installare Qwen nel venv Chatterbox e non unire i due elenchi di dipendenze.

Il Python di base di Chatterbox è in `C:\Users\gerar\AppData\Local\Programs\Python\Python312`. Quello di Qwen proviene attualmente dal runtime locale di Codex. Se uno di questi Python viene rimosso, il relativo ambiente può smettere di avviarsi. Per una nuova postazione usare una propria installazione permanente di Python 3.12 a 64 bit, con Tcl/Tk incluso, e ricreare gli ambienti. La diversa revisione 3.12 dovrà essere verificata nel collaudo.

## 2. Cosa conservare prima delle prove

Chiudere ChatterText e attendere la fine delle generazioni. Copiare su un disco di backup:

1. Tutta la cartella `D:\Siti GitHub\chattertext`, compresi file nascosti e la sottocartella `chatterbox`. Sono essenziali `ChatterText_3.0.py`, `qwen_voice_box.py`, `qwen_voice_config.json`, il file di avvio, icone, `2.Voci`, `1.Output`, testi e altri dati personali. Conservare anche questa guida e la cartella `Ripristino-Sistema`.
2. Tutta la cartella Qwen indicata sopra: `repository`, `models`, `audio`, script Python, file delle versioni e configurazioni. Il modello comprende anche `speech_tokenizer`: non copiare solo il file dei pesi principale.
3. La cache Chatterbox `C:\Users\gerar\.cache\huggingface\hub\models--ResembleAI--chatterbox`, comprese `blobs`, `refs` e `snapshots`. Se ci sono collegamenti simbolici, usare una copia che conservi i collegamenti oppure i file a cui puntano. Conservare anche le altre cache effettivamente richieste da eventuali funzionalità aggiuntive.

Conservare i venv come copia di emergenza del PC attuale, ma **non considerarli trasferibili**. Su un'altra postazione, o cambiando percorso, si ricreano: contengono riferimenti al Python e alle cartelle originali. La [documentazione Python](https://docs.python.org/3.12/library/venv.html) conferma questo comportamento.

La presente attività salva una guida e un inventario, **non un backup completo**. Per un ripristino esatto del PC, compresi driver e Python, serve anche un'immagine del sistema/disco. Per un'installazione senza Internet servirà preparare e collaudare un archivio dei pacchetti binari; non è incluso ora.

## 3. Scegliere il tipo di ripristino

- **Solo un file dell'app danneggiato:** ripristinare i file dalla propria copia più recente, mantenendo gli ambienti funzionanti. Per conservare il box, ripristinare insieme app, modulo e configurazione Qwen.
- **Ambiente Python danneggiato:** mantenere codice, modelli, voci e output; ricreare soltanto l'ambiente interessato.
- **Nuovo PC o nuova cartella:** copiare codice e dati, installare Python e driver NVIDIA appropriati, ricreare entrambi i venv, aggiornare il percorso Qwen e il collegamento di avvio.

Il backup `backup_voicedesign_20260905_210307` presente nel progetto è precedente al box: ripristinarne `ChatterText_3.0.py` rimuove l'integrazione dall'interfaccia. Non è la copia da usare per ottenere l'app completa attuale.

## 4. Preparare i percorsi

I comandi seguenti vanno eseguiti in PowerShell **uno alla volta**, controllando l'esito. Se un comando restituisce un errore, fermarsi e conservarne il messaggio. Non eseguirli ora sull'app funzionante: sono il percorso per le prossime prove.

Installare Python 3.12 a 64 bit dalla [distribuzione ufficiale](https://www.python.org/downloads/windows/), includendo Tcl/Tk. Installare un driver NVIDIA compatibile con la GPU e con i runtime CUDA usati. I pacchetti PyTorch includono il proprio runtime CUDA: per questa procedura non si compila codice CUDA e non è previsto installare il toolkit completo.

Impostare le variabili con i percorsi reali della postazione di destinazione. L'esempio seguente usa cartelle brevi; non sono state create automaticamente:

```powershell
$AppPath = 'D:\Siti GitHub\chattertext'
$QwenPath = 'D:\AI\Qwen3-VoiceDesign'
$PythonBase = 'C:\Users\gerar\AppData\Local\Programs\Python\Python312\python.exe'
$RestorePath = Join-Path $AppPath 'Ripristino-Sistema'
& $PythonBase --version
nvidia-smi
```

Su un altro account cambiare anche il percorso del Python. Prima copiare le cartelle dal backup nelle destinazioni scelte. Non rinominare o cancellare voci, modelli e output.

Se nella destinazione esiste già un ambiente da sostituire, chiudere l'app, verificare in Esplora file il percorso esatto e rinominare **solo** `venv_chatterbox` o `.venv` in un nome di backup libero. Conservare il vecchio ambiente fino al collaudo. Non creare il nuovo ambiente sopra quello vecchio.

## 5. Ricreare Chatterbox

Il `pyproject.toml` nella radice del progetto descrive una versione diversa. Il pacchetto in uso proviene da **`chatterbox\pyproject.toml`**: si reinstalla da questa sottocartella preservata nel backup, non dalla radice e non da un generico aggiornamento su Internet.

È presente una discrepanza già esistente: il pacchetto dichiara PyTorch/torchaudio 2.6.0, mentre l'ambiente usato dall'utente contiene 2.5.1+cu121. Il file `chatterbox-pip-check.txt` registra i due avvisi. Per ricreare lo stato attuale usiamo le versioni rilevate senza risolvere automaticamente le dipendenze. Non è una dichiarazione di compatibilità ufficiale e richiede il test audio finale. Un eventuale aggiornamento a 2.6.0 sarà una prova separata.

```powershell
& $PythonBase -m venv (Join-Path $AppPath 'venv_chatterbox')
$CbPython = Join-Path $AppPath 'venv_chatterbox\Scripts\python.exe'
& $CbPython -m pip install 'setuptools==80.10.2' wheel
& $CbPython -m pip install 'torch==2.5.1' 'torchaudio==2.5.1' --index-url https://download.pytorch.org/whl/cu121
& $CbPython -m pip install --no-deps -r (Join-Path $RestorePath 'chatterbox-dipendenze.txt')
& $CbPython -m pip install --no-deps --no-build-isolation -e (Join-Path $AppPath 'chatterbox')
& $CbPython -m pip check
```

L'ultima verifica dovrebbe segnalare soltanto le due discrepanze PyTorch documentate. Ulteriori messaggi vanno esaminati prima di procedere. Non usare `pip install -U` per tentare di eliminarli. I [comandi CUDA per PyTorch 2.5.1](https://pytorch.org/get-started/previous-versions/) sono documentati dal progetto.

`chatterbox-dipendenze.txt` deriva dal freeze reale, escludendo PyTorch/torchaudio (installati dall'indice CUDA) e l'installazione locale Chatterbox (installata dal backup). `--no-deps` evita che il resolver sostituisca le versioni rilevate; tutte le dipendenze devono quindi essere presenti nell'inventario. Il significato dell'opzione è descritto nella [documentazione pip](https://pip.pypa.io/en/stable/cli/pip_install/).

## 6. Ricreare Qwen VoiceDesign

```powershell
& $PythonBase -m venv (Join-Path $QwenPath '.venv')
$QwPython = Join-Path $QwenPath '.venv\Scripts\python.exe'
& $QwPython -m pip install 'setuptools==78.1.0' wheel
& $QwPython -m pip install 'torch==2.11.0' 'torchaudio==2.11.0' --index-url https://download.pytorch.org/whl/cu128
& $QwPython -m pip install --no-deps -r (Join-Path $RestorePath 'qwen-dipendenze.txt')
& $QwPython -m pip install --no-deps --no-build-isolation -e (Join-Path $QwenPath 'repository')
& $QwPython -m pip check
```

Per Qwen il controllo delle dipendenze attuale non segnala conflitti. Usare il codice del backup, commit `022e286b98fbec7e1e916cb940cdf532cd9f488e`, dal [repository ufficiale Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS).

Se il modello è stato copiato integralmente, non scaricarlo di nuovo. Se manca, questo comando recupera **la revisione attualmente usata**:

```powershell
$env:HF_HOME = Join-Path $QwenPath 'cache'
& $QwPython -c "from huggingface_hub import snapshot_download; import sys; snapshot_download('Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign', revision='5ecdb67327fd37bb2e042aab12ff7391903235d3', local_dir=sys.argv[1])" (Join-Path $QwenPath 'models\Qwen3-TTS-12Hz-1.7B-VoiceDesign')
Remove-Item Env:HF_HOME
```

Eseguire questo blocco in una nuova finestra PowerShell senza personalizzazioni HF_HOME. `download_model.py` originale, invece, interroga la revisione corrente online: non è il comando da preferire per ripristinare esattamente i pesi di oggi.

Nel test effettuato Qwen usa GPU, bfloat16 e SDPA. FlashAttention non è installato. L'eseguibile SoX non è presente, ma la generazione VoiceDesign verificata funziona ugualmente. Non installare componenti aggiuntivi solo per nascondere questi avvisi.

## 7. Ricollegare Qwen e recuperare i modelli Chatterbox

Aggiornare la configurazione Qwen dopo aver scelto il nuovo percorso:

```powershell
@{root=$QwenPath} | ConvertTo-Json | Set-Content -Encoding ascii (Join-Path $AppPath 'qwen_voice_config.json')
```

Questo comando è adatto ai percorsi ASCII mostrati. Per percorsi con caratteri accentati usare il pulsante **Cartella installazione Qwen** nel box, che salva correttamente in UTF-8.

Per Chatterbox, copiare la cache salvata nella cache Hugging Face del nuovo account (normalmente `%USERPROFILE%\.cache\huggingface\hub`). Il riferimento `main` nella cache rilevata punta a `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`. Se la cache manca, il caricamento di Chatterbox tenta il download online. Poiché il codice attuale non fissa una revisione del modello, un nuovo download potrebbe recuperare pesi diversi: per una riproduzione fedele preferire il backup della cache e il test offline.

Il JSON Qwen è una configurazione del percorso, non contiene il modello e non deve puntare alla sola sottocartella `models`.

## 8. Controlli prima dell'uso

Controllare separatamente i due ambienti:

```powershell
& $CbPython -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA non disponibile')"
& $QwPython -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA non disponibile')"
& $CbPython -c "import inspect; from chatterbox.mtl_tts import ChatterboxMultilingualTTS; print(inspect.signature(ChatterboxMultilingualTTS.from_pretrained))"
```

L'ultima firma deve includere `t3_model`, necessario per V3. Provare poi la generazione Qwen con un nome nuovo:

```powershell
& $QwPython (Join-Path $QwenPath 'generate.py') --output (Join-Path $QwenPath 'audio\test_ripristino.wav')
```

Avviare temporaneamente l'app dalla console, così eventuali errori restano leggibili:

```powershell
Set-Location $AppPath
& $CbPython (Join-Path $AppPath 'ChatterText_3.0.py')
```

Checklist di collaudo:

- Il box VoiceDesign si apre; genera almeno due varianti, riproduce e interrompe l'audio, salva e ricarica un JSON.
- Una variante viene assegnata a uno slot Chatterbox e compare in `2.Voci`.
- Chatterbox produce correttamente un breve testo italiano con quel sample, salvando in `1.Output`.
- L'interruzione di Qwen funziona e il successivo avvio riesce.
- Chiusura e riapertura con `Avvia-Chattertext_3.bat` funzionano senza console visibile. Se si usa un collegamento Windows, correggere i percorsi a `venv_chatterbox\Scripts\pythonw.exe` e `ChatterText_3.0.py`.

Per verificare la completezza della cache Chatterbox, dopo un primo test riuscito si può aprire una nuova PowerShell, impostare `$env:HF_HUB_OFFLINE='1'` e avviare da lì l'app. Un test audio riuscito in quella finestra conferma che i file richiesti da quel flusso sono disponibili localmente. Chiudere poi la finestra per eliminare l'impostazione di sessione. Qwen è già configurato offline nei suoi script di generazione.

Non eliminare il backup finché entrambe le generazioni non superano queste prove.

## 9. Problemi più comuni

| Sintomo | Controllo |
|---|---|
| L'app non parte | Avviarla con python.exe dalla console; verificare il Python di base e il venv. |
| Manca `qwen_voice_box` | Ripristinare il modulo accanto a `ChatterText_3.0.py`. |
| Cartella Qwen non valida | Selezionare la radice contenente `.venv`, `voice_worker.py`, `voice_request.py` e `models`. |
| CUDA non disponibile | Verificare driver, GPU e versione CUDA di torch nell'ambiente specifico, senza modificare l'altro ambiente. |
| Memoria GPU insufficiente | Chiudere altre generazioni/istanze; usare un testo breve e un solo processo. I 12 GB della RTX 3060 sono la configurazione collaudata, non una garanzia per ogni GPU. |
| Errore V3 o manca `t3_model` | Verificare che il pacchetto installato provenga dalla sottocartella `chatterbox` salvata, non da una versione differente. |
| Modello Qwen mancante offline | Ripristinare tutta la cartella modello, compreso `speech_tokenizer`, o eseguire il download con revisione fissata. |
| Frase Qwen troncata | Accorciare il testo o aumentare il limite token nel box. |
| Dipendenze non più scaricabili | Conservare l'errore; non sostituire versioni a caso. Occorrerà preparare un archivio pacchetti o collaudare una nuova combinazione. |

## 10. File di riferimento inclusi

Nella cartella `Ripristino-Sistema`: freeze originali di entrambi gli ambienti, elenchi ripuliti per la reinstallazione, risultato `pip check` Chatterbox e manifest SHA-256 dei principali file applicativi. Il manifest aiuta a riconoscere modifiche successive; non sostituisce il backup. Se l'app verrà modificata, aggiornare anche backup, guida e inventario.

Stato attuale: l'utente ha confermato il funzionamento del box. Nei test precedenti sono riuscite generazione GPU Qwen, due varianti, assegnazione voce in cartella di prova e interruzione. **Ripristino completo e trasferimento su altro PC ancora da provare.**
