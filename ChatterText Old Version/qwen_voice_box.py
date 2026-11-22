"""VoiceDesign panel for ChatterText; only standard-library dependencies in the host."""
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

PRESETS = {
    'Narratore caldo': 'Uomo italiano di circa cinquant’anni, voce calda e leggermente grave. Narratore letterario, dizione naturale, ritmo tranquillo, tono intimo e riflessivo, espressivo senza teatralità.',
    'Narratrice naturale': 'Donna italiana adulta, voce morbida e limpida, dizione naturale. Narrazione letteraria pacata, espressiva, con pause fluide e tono accogliente.',
    'Documentario': 'Voce italiana adulta, timbro pieno e chiaro, tono autorevole e misurato. Dizione nitida, ritmo regolare, espressione sobria.',
    'Dialogo vivace': 'Voce italiana giovane adulta, naturale e brillante. Tono colloquiale, energico e spontaneo, con intonazione varia e senza enfasi eccessiva.',
}
DEFAULTS = dict(language='Italian', seed=42, variants=1, do_sample=True,
                temperature=0.9, top_p=1.0, top_k=50, repetition_penalty=1.05,
                subtalker_dosample=True, subtalker_temperature=0.9,
                subtalker_top_p=1.0, subtalker_top_k=50, max_new_tokens=2048)


class VoiceBox:
    def __init__(self, app, parent, colors):
        self.app, self.c = app, colors
        self.busy = False
        self.proc = None
        self.cancel = threading.Event()
        self.events = queue.Queue()
        self.results = []
        self.vars = {}
        self.config = Path(__file__).with_name('qwen_voice_config.json')
        try:
            root = json.loads(self.config.read_text(encoding='utf-8'))['root']
        except (OSError, ValueError, KeyError):
            root = ''
        self.root = tk.StringVar(value=root)
        sec = app._sec(parent, 'Crea una voce da testo — Qwen VoiceDesign')
        self.sec = sec
        self.button(sec, 'Apri / chiudi impostazioni VoiceDesign', self.toggle).pack(anchor='w')
        self.body = self.frame(sec)
        self.label(sec, 'Voce originale da descrizione · GPU locale · ambiente separato').pack(anchor='w', pady=(6, 0))
        self.build()
        app.after(100, self.poll)

    def frame(self, parent):
        return tk.Frame(parent, bg=self.c['surface'])

    def label(self, parent, text):
        return tk.Label(parent, text=text, bg=self.c['surface'], fg=self.c['text'],
                        font=('Segoe UI', 10), anchor='w', justify='left', wraplength=930)

    def button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=self.c['surface2'], fg=self.c['accent'],
                         activebackground=self.c['border'], activeforeground=self.c['text'],
                         relief='flat', padx=10, pady=7, cursor='hand2')

    def row(self, parent):
        row = self.frame(parent)
        row.pack(fill='x', pady=4)
        return row

    def field(self, parent, label, key, value, choices=None, width=15):
        cell = self.frame(parent)
        cell.pack(side='left', padx=(0, 14), fill='x', expand=True)
        self.label(cell, label).pack(anchor='w')
        var = tk.StringVar(value=str(value))
        self.vars[key] = var
        if choices:
            widget = ttk.Combobox(cell, textvariable=var, values=choices, state='readonly', width=width)
        else:
            widget = tk.Entry(cell, textvariable=var, width=width, bg=self.c['surface2'],
                              fg=self.c['text'], insertbackground=self.c['text'], relief='flat')
        widget.pack(fill='x', pady=3)
        return var

    def text_area(self, parent, label, text, height):
        self.label(parent, label).pack(anchor='w', pady=(8, 3))
        area = scrolledtext.ScrolledText(parent, height=height, wrap='word', bg=self.c['surface2'],
                                        fg=self.c['text'], insertbackground=self.c['text'], font=('Segoe UI', 10))
        area.insert('1.0', text)
        area.pack(fill='x')
        return area

    def build(self):
        b = self.body
        self.text = self.text_area(b, 'Testo da pronunciare (senza tag Chatterbox, massimo 1500 caratteri)',
                                  "Era una sera d'autunno, e dalla finestra entrava appena la luce della strada.", 3)
        r = self.row(b)
        self.button(r, 'Incolla testo', self.paste).pack(side='left')
        self.button(r, 'Importa TXT', self.import_text).pack(side='left', padx=6)
        self.field(r, 'Lingua', 'language', 'Italian', ['Italian', 'English', 'French', 'German', 'Spanish', 'Portuguese', 'Russian', 'Chinese', 'Japanese', 'Korean'])
        self.prompt = self.text_area(b, 'Descrizione della voce — questo è il prompt effettivo inviato al modello', PRESETS['Narratore caldo'], 4)
        r = self.row(b)
        self.preset = tk.StringVar(value='Narratore caldo')
        ttk.Combobox(r, textvariable=self.preset, values=list(PRESETS), state='readonly', width=24).pack(side='left')
        self.button(r, 'Applica preset', self.apply_preset).pack(side='left', padx=6)
        self.label(b, 'Assistente descrizione: scegli le caratteristiche e premi “Componi prompt”. Poi puoi modificare il testo liberamente.').pack(anchor='w', pady=(8, 0))
        r = self.row(b)
        self.field(r, 'Voce', 'gender', 'Maschile', ['Maschile', 'Femminile', 'Androgina'])
        self.field(r, 'Età apparente', 'age', '50 anni')
        self.field(r, 'Timbro', 'timbre', 'Caldo e profondo', ['Caldo e profondo', 'Morbido e limpido', 'Grave e ruvido', 'Leggero e brillante', 'Pieno e autorevole'])
        r = self.row(b)
        self.field(r, 'Ritmo', 'pace', 'Tranquillo', ['Tranquillo', 'Naturale', 'Lento', 'Vivace'])
        self.field(r, 'Interpretazione', 'style', 'Narrativa intima', ['Narrativa intima', 'Colloquiale', 'Documentaristica', 'Teatrale', 'Fiabesca'])
        self.field(r, 'Accento / dizione', 'accent', 'Italiano standard, dizione naturale', width=30)
        self.button(b, 'Componi prompt dalle caratteristiche', self.compose).pack(anchor='w', pady=5)
        self.label(b, 'Ritmo, età e timbro sono indicazioni interpretative, non regolazioni numeriche garantite.').pack(anchor='w')
        r = self.row(b)
        self.field(r, 'Seed (-1 = casuale)', 'seed', 42)
        self.field(r, 'Varianti da confrontare', 'variants', 1, ['1', '2', '3', '4'])
        self.button(r, 'Parametri avanzati', self.toggle_advanced).pack(side='left')
        self.advanced = self.frame(b)
        for entries in [
            [('Temperatura', 'temperature', .9), ('Top P', 'top_p', 1), ('Top K', 'top_k', 50)],
            [('Penalità ripetizioni', 'repetition_penalty', 1.05), ('Limite token audio', 'max_new_tokens', 2048)],
            [('Temperatura acustica', 'subtalker_temperature', .9), ('Top P acustico', 'subtalker_top_p', 1), ('Top K acustico', 'subtalker_top_k', 50)]]:
            r = self.row(self.advanced)
            for label, key, value in entries:
                self.field(r, label, key, value)
        r = self.row(self.advanced)
        for key, label in [('do_sample', 'Campionamento voce'), ('subtalker_dosample', 'Campionamento acustico')]:
            var = tk.BooleanVar(value=True)
            self.vars[key] = var
            tk.Checkbutton(r, text=label, variable=var, bg=self.c['surface'], fg=self.c['text'],
                           selectcolor=self.c['surface2']).pack(side='left', padx=8)
        self.label(self.advanced, 'Temperatura: più alta = più variabilità. Top P / K limitano le alternative (K=0 disattiva il filtro).\nI parametri di campionamento valgono solo se il relativo campionamento è attivo. Il limite token può troncare testi lunghi.\nIl seed aiuta a ripetere una prova nello stesso ambiente; non garantisce la stessa identità su testi diversi.').pack(anchor='w')
        self.button(self.advanced, 'Ripristina parametri di generazione', self.reset).pack(anchor='w')
        r = self.row(b)
        self.advanced_anchor = r
        self.button(r, 'Salva impostazioni JSON', self.save).pack(side='left')
        self.button(r, 'Carica impostazioni JSON', self.load).pack(side='left', padx=6)
        self.button(r, 'Cartella installazione Qwen', self.choose_root).pack(side='left')
        self.status = tk.StringVar(value='Pronto. Per creare un sample prova un testo di 10–20 secondi.')
        self.label(b, 'Le varianti vengono conservate in Qwen/audio con testo, prompt e impostazioni.').pack(anchor='w', pady=5)
        r = self.row(b)
        self.generate = self.button(r, 'Genera voce', self.start)
        self.generate.pack(side='left')
        self.stop_button = self.button(r, 'Interrompi', self.stop)
        self.stop_button.pack(side='left', padx=6)
        self.stop_button.config(state='disabled')
        self.progress = ttk.Progressbar(r, mode='indeterminate')
        self.progress.pack(side='left', fill='x', expand=True)
        tk.Label(b, textvariable=self.status, bg=self.c['surface'], fg=self.c['accent'], wraplength=900, justify='left').pack(anchor='w', pady=6)
        self.listbox = tk.Listbox(b, height=4, bg=self.c['surface2'], fg=self.c['text'], exportselection=False)
        self.listbox.pack(fill='x')
        r = self.row(b)
        self.button(r, 'Ascolta', self.play).pack(side='left')
        self.button(r, 'Ferma ascolto', self.stop_audio).pack(side='left', padx=4)
        self.button(r, 'Esporta WAV + JSON', self.export).pack(side='left')
        self.slot = tk.StringVar(value='1')
        ttk.Combobox(r, textvariable=self.slot, values=[str(i) for i in range(1, 8)], state='readonly', width=3).pack(side='left', padx=(14, 4))
        self.button(r, 'Usa come voce Chatterbox', self.assign).pack(side='left')
        self.log = self.text_area(b, 'Dettagli esecuzione', '', 4)
        self.log.config(state='disabled')

    def toggle(self):
        if self.body.winfo_manager(): self.body.pack_forget()
        else: self.body.pack(fill='x', pady=(10, 0))

    def toggle_advanced(self):
        if self.advanced.winfo_manager(): self.advanced.pack_forget()
        else: self.advanced.pack(fill='x', before=self.advanced_anchor)

    def set_text(self, widget, value):
        widget.delete('1.0', 'end'); widget.insert('1.0', value)

    def paste(self):
        try: self.set_text(self.text, self.app.clipboard_get())
        except tk.TclError: self.status.set('Appunti senza testo.')

    def import_text(self):
        path = filedialog.askopenfilename(filetypes=[('Testo UTF-8', '*.txt')])
        if path:
            try: self.set_text(self.text, Path(path).read_text(encoding='utf-8-sig'))
            except (OSError, UnicodeError) as e: messagebox.showerror('Importazione', str(e))

    def apply_preset(self): self.set_text(self.prompt, PRESETS[self.preset.get()])

    def compose(self):
        v = lambda key: self.vars[key].get().strip()
        self.set_text(self.prompt, f"Voce {v('gender').lower()}, età apparente {v('age')}, timbro {v('timbre').lower()}. Ritmo {v('pace').lower()}, interpretazione {v('style').lower()}. {v('accent')}. Lettura naturale, espressiva e senza enfasi eccessiva.")

    def reset(self):
        for key, value in DEFAULTS.items():
            if key not in ('language', 'seed', 'variants'): self.vars[key].set(value)

    def collect(self):
        data = {k: self.vars[k].get() for k in DEFAULTS}
        data.update(text=self.text.get('1.0', 'end-1c'), prompt=self.prompt.get('1.0', 'end-1c'))
        # Import only the dependency-free validator from the configured installation.
        import importlib.util
        path = Path(self.root.get()) / 'voice_request.py'
        spec = importlib.util.spec_from_file_location('qwen_request_validation', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.validate(data)

    def save(self):
        try:
            data = self.collect()
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Impostazioni', '*.json')])
            if path: Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e: messagebox.showerror('Impostazioni', str(e))

    def load(self):
        path = filedialog.askopenfilename(filetypes=[('Impostazioni', '*.json')])
        if not path: return
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            if not isinstance(data, dict): raise ValueError('File impostazioni non valido.')
            for key in DEFAULTS:
                if key in data: self.vars[key].set(data[key])
            for key, widget in [('text', self.text), ('prompt', self.prompt)]:
                if key in data: self.set_text(widget, str(data[key]))
            self.collect()
            self.status.set('Impostazioni caricate; il prompt visibile sarà usato nella prossima prova.')
        except Exception as e: messagebox.showerror('Impostazioni', str(e))

    def choose_root(self):
        path = filedialog.askdirectory(title='Cartella Qwen contenente .venv e voice_worker.py')
        if path:
            root = Path(path)
            if not (root / 'voice_worker.py').is_file() or not (root / '.venv/Scripts/python.exe').is_file():
                messagebox.showerror('Cartella', 'Questa cartella non contiene installazione e modulo VoiceDesign.'); return
            try:
                self.config.write_text(json.dumps({'root': str(root)}, indent=2), encoding='utf-8')
                self.root.set(str(root))
            except OSError as e: messagebox.showerror('Configurazione', str(e))

    def start(self):
        if self.busy: return
        if getattr(self.app, '_chatter_starting', False) or (self.app._proc and self.app._proc.poll() is None):
            messagebox.showwarning('GPU occupata', 'Attendi o interrompi la generazione Chatterbox.'); return
        try:
            data = self.collect()
            root = Path(self.root.get()).resolve()
            python = root / '.venv/Scripts/python.exe'
            if not python.is_file(): raise ValueError('Seleziona la cartella di installazione Qwen.')
            out = root / 'audio' / (time.strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6])
            out.mkdir(parents=True)
            request = out / 'richiesta.json'
            request.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            messagebox.showerror('Controlla le impostazioni', str(e)); return
        self.busy = True; self.cancel.clear()
        self.generate.config(state='disabled'); self.stop_button.config(state='normal')
        self.progress.start(12); self.status.set('Avvio ambiente Qwen...')
        threading.Thread(target=self.worker, args=(python, root, request, out), daemon=True).start()

    def worker(self, python, root, request, out):
        try:
            env = os.environ.copy(); env['PYTHONIOENCODING'] = 'utf-8'
            with (out / 'esecuzione.log').open('w', encoding='utf-8') as log:
                proc = subprocess.Popen([str(python), '-u', str(root / 'voice_worker.py'), '--request', str(request), '--output-dir', str(out)],
                    cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    encoding='utf-8', errors='replace', env=env,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                self.proc = proc
                if self.cancel.is_set(): proc.terminate()
                for line in proc.stdout:
                    log.write(line); log.flush()
                    if line.startswith('VOICE_EVENT '):
                        self.events.put(json.loads(line[len('VOICE_EVENT '):]))
                    else: self.events.put(dict(kind='log', message=line))
                code = proc.wait()
                self.events.put(dict(kind='exit', code=code, cancelled=self.cancel.is_set()))
        except Exception as e: self.events.put(dict(kind='exit', code=-1, error=str(e)))
        finally: self.proc = None

    def poll(self):
        try:
            while True:
                e = self.events.get_nowait()
                if e['kind'] == 'status': self.status.set(e['message'])
                elif e['kind'] == 'result':
                    self.results.append(e)
                    note = ' — verificare fine frase: possibile taglio' if e['possibly_truncated'] else ''
                    self.listbox.insert('end', f"Seed {e['seed']} · {e['duration_seconds']:.1f} s · {e['generation_seconds']:.1f} s di generazione{note}")
                    self.listbox.selection_clear(0, 'end'); self.listbox.selection_set('end')
                    self.listbox.see('end')
                elif e['kind'] == 'log':
                    self.log.config(state='normal'); self.log.insert('end', e['message']); self.log.see('end'); self.log.config(state='disabled')
                elif e['kind'] == 'exit':
                    self.busy = False; self.progress.stop()
                    self.generate.config(state='normal'); self.stop_button.config(state='disabled')
                    self.status.set('Interrotto. Le varianti già completate sono conservate.' if e.get('cancelled') else
                                    ('Completato. Seleziona una variante per ascoltarla o usarla in Chatterbox.' if e['code'] == 0 else 'Errore: ' + e.get('error', 'consulta i dettagli esecuzione.')))
        except queue.Empty: pass
        self.app.after(100, self.poll)

    def stop(self):
        self.cancel.set()
        proc = self.proc
        if proc and proc.poll() is None:
            try: proc.terminate()
            except OSError: pass
        if self.busy: self.status.set('Interruzione in corso...')

    def selected(self):
        selection = self.listbox.curselection()
        if not selection:
            self.status.set('Seleziona prima una variante.'); return None
        return Path(self.results[selection[0]]['output'])

    def play(self):
        path = self.selected()
        if path:
            try:
                import winsound
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except (OSError, RuntimeError) as e: self.status.set(str(e))

    def stop_audio(self):
        import winsound
        winsound.PlaySound(None, 0)

    def export(self):
        path = self.selected()
        if not path: return
        dest = filedialog.asksaveasfilename(defaultextension='.wav', initialfile=path.name, filetypes=[('Audio WAV', '*.wav')])
        if dest:
            try:
                target = Path(dest)
                if target.resolve() == path.resolve(): return
                shutil.copy2(path, target)
                shutil.copy2(path.with_suffix('.json'), target.with_suffix('.json'))
                self.status.set('Esportati WAV e impostazioni JSON.')
            except OSError as e: messagebox.showerror('Esportazione', str(e))

    def assign(self):
        path = self.selected()
        if not path: return
        try:
            dest = Path(self.app.vdir.get()) / '2.Voci'
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / ('qwen_' + path.parent.name + '_' + path.name)
            if not target.exists():
                shutil.copy2(path, target)
                shutil.copy2(path.with_suffix('.json'), target.with_suffix('.json'))
            getattr(self.app, 'vv' + self.slot.get()).set(target.name)
            self.status.set('Assegnata a Voce ' + self.slot.get() + ': ' + target.name)
        except OSError as e: messagebox.showerror('Assegnazione', str(e))


def mount(app, parent, colors):
    box = VoiceBox(app, parent, colors)
    app._qwen_box = box
    def close():
        box.stop(); box.stop_audio(); app.destroy()
    app.protocol('WM_DELETE_WINDOW', close)
    return box
