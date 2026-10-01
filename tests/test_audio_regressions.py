"""Regression tests without loading the GPU model or the desktop window."""
import ast
import json
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
APP = ast.parse((ROOT / 'ChatterText_3.0.py').read_text(encoding='utf-8'))
WORKER = (ROOT / 'chatterbox_auto.py').read_text(encoding='utf-8')

def functions(source, names, scope):
    tree = ast.parse(source) if isinstance(source, str) else source
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<test>', 'exec'), scope)

class Tensor(np.ndarray):
    def dim(self): return self.ndim
    def detach(self): return self
    def cpu(self): return self
    def numel(self): return self.size
    def amax(self, dim): return np.max(self, axis=dim).view(Tensor)
    def unsqueeze(self, axis): return np.expand_dims(self, axis).view(Tensor)
    def abs(self): return np.abs(self).view(Tensor)

def tensor(data): return np.asarray(data, dtype=float).view(Tensor)

class RegressionTests(unittest.TestCase):
    def test_complete_generated_script(self):
        scope = dict(json=json, ALL_EMO=['calmo'])
        functions(APP, ['build_python_script'], scope)
        script = scope['build_python_script'](['Prima frase. Seconda frase.'], .5,.5,.7,
                    'voice.wav','','','','','','',{})
        compile(script, '<generated>', 'exec')
        generated = ast.parse(script)
        current = ast.parse(WORKER)
        for name in ['generate_recoverable','speech_units','rms_normalize','full_process','asmb']:
            get = lambda tree: next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(ast.dump(get(generated)), ast.dump(get(current)), name)

    def test_sentence_split_preserves_all_words(self):
        scope=dict(re=re)
        functions(WORKER,['speech_units'],scope)
        for text in ['Prima frase. Seconda frase! Ultima senza punto',
                     ' '.join('parola'+str(i) for i in range(120)),
                     'Il sig. Rossi aspetta. Costa 3.14 euro.\nPoi riparte.']:
            units=scope['speech_units'](text)
            self.assertEqual(' '.join(units).split(),text.split())
            self.assertTrue(all(len(u.split())<=24 for u in units))

    def test_text_between_voice_blocks_not_dropped(self):
        scope=dict(re=re,ALL_EMO=['calmo'],_rebalance_leading_pauses=lambda c:c)
        functions(APP,['chunk_text'],scope)
        text='[inizio]Prima. [V1_calmo]Dentro.[/V1_calmo] In mezzo. [V2]Altra.[/V2] Dopo.[fine]'
        chunks=scope['chunk_text'](text,5,24,180)
        self.assertEqual(chunks,['Prima.','[V1_calmo]Dentro.[/V1_calmo]','In mezzo.','[V2]Altra.[/V2]','Dopo.'])

    def test_separators_never_reach_voice_model(self):
        calls=[]
        def generate(text, **kwargs):
            calls.append(text)
            raise AssertionError('A separator must not be synthesized')
        scope=dict(re=re, PAUSE_SCALE=1, model=SimpleNamespace(sr=100,generate=generate),
                   torch=SimpleNamespace(zeros=lambda shape:tensor(np.zeros(shape)),
                       cat=lambda ws,dim:np.concatenate(ws,axis=dim).view(Tensor)))
        functions(WORKER,['speech_units','generate_recoverable'],scope)
        for separator in ['.', '...', '\u2026', '---', '* * *', '.\n.\n.']:
            wav=scope['generate_recoverable'](separator,'voice.wav',[])
            self.assertEqual(wav.shape,(1,40))
            self.assertFalse(wav.any())
        self.assertEqual(calls,[])

    def test_pause_position_and_voice(self):
        scope=dict(re=re,chunks=['placeholder'],PR=re.compile(r'\[p[12]\]'))
        scope['pc']=lambda c:('Prima[p1][p2]Seconda[p1]Fine','v2','calmo',
                             [('[p1]',.2),('[p2]',.4),('[p1]',.2)],.8,None,'[para]')
        block=WORKER[WORKER.index('tc=[]'):WORKER.index('def noise_gate')]
        exec(block,scope)
        tc=scope['tc']
        self.assertEqual([r[0] for r in tc],['Prima','Seconda','Fine'])
        self.assertAlmostEqual(tc[0][4],.6)
        self.assertEqual([r[4] for r in tc[1:]],[.2,0])
        self.assertTrue(all(r[1:3]==['v2','calmo'] for r in tc))
        self.assertEqual([r[6] for r in tc],[None,None,'[para]'])

    def test_normalization_is_linear_and_independent_of_silence(self):
        scope=dict(torch=SimpleNamespace(sqrt=np.sqrt,mean=np.mean),RMS_TARGET_DB=-18)
        functions(WORKER,['rms_normalize'],scope)
        f=scope['rms_normalize']
        voice=tensor([[.01,.1,-.2,.8,-.4]])
        with_pause=tensor(np.concatenate([voice,np.zeros((1,10000))],axis=1))
        normalized=f(voice)
        np.testing.assert_allclose(normalized,f(with_pause)[:,:5])
        np.testing.assert_allclose(normalized/voice,np.full((1,5),normalized[0,0]/voice[0,0]))
        self.assertLessEqual(abs(normalized).max(),.95)
        np.testing.assert_array_equal(f(tensor([[0,0,0]])),[[0,0,0]])

    def test_recovery_keeps_every_sentence_and_rejects_silence(self):
        torch=SimpleNamespace(
            isfinite=np.isfinite,
            zeros=lambda shape:tensor(np.zeros(shape)),
            cat=lambda ws,dim: np.concatenate(ws,axis=dim).view(Tensor),
            nn=SimpleNamespace(functional=SimpleNamespace(
                pad=lambda w,p: np.pad(w,p).view(Tensor))))
        calls=[]
        def generate(text, **kwargs):
            calls.append(text)
            if len(text.split())>6: raise RuntimeError('simulated model failure')
            return tensor(np.full((1,len(text.split())*30),.2))
        model=SimpleNamespace(sr=100,generate=generate)
        scope=dict(torch=torch,re=re,model=model,REPETITION_PENALTY=1.2,PAUSE_SCALE=1,
                   full_process=lambda w,sr:w,print=lambda *a,**k:None)
        functions(WORKER,['speech_units','generate_recoverable'],scope)
        params=[dict(exaggeration=.5,cfg_weight=.5,temperature=.7,min_p=.05,top_p=1)]*3
        text='uno due tre quattro cinque sei sette otto nove dieci undici dodici'
        wav=scope['generate_recoverable'](text,'voice.wav',params)
        self.assertEqual(wav.shape,(1,360))
        self.assertEqual(' '.join(calls[3:]),text)
        calls.clear()
        scope['generate_recoverable']('Prima frase. Seconda frase.','voice.wav',params)
        self.assertEqual(calls,['Prima frase.','Seconda frase.'])
        calls.clear()
        wav=scope['generate_recoverable']('Prima frase.\n.\nSeconda frase.','voice.wav',params)
        self.assertEqual(calls,['Prima frase.','Seconda frase.'])
        self.assertEqual(wav.shape,(1,160))
        self.assertFalse(wav[:,60:100].any())
        # Long silence must not make incomplete speech pass the duration check.
        model.generate=lambda *a,**k:tensor([[.2]*10+[0]*1000])
        with self.assertRaises(RuntimeError):
            scope['generate_recoverable']('Questa frase contiene sei parole distinte','voice.wav',params)

    def test_join_does_not_double_explicit_pause_or_remove_onset(self):
        scope=dict(PAUSE_SCALE=1,JM={'[para]':(.9,'silence')},
                   torch=SimpleNamespace(zeros=np.zeros,cat=lambda ws,dim:np.concatenate(ws,axis=dim)))
        functions(WORKER,['asmb'],scope)
        left=np.ones((1,100)); right=np.full((1,30),2.)
        joined=scope['asmb'](left,right,100,'[para]',existing_pause=.4)
        self.assertEqual(joined.shape,(1,180))
        np.testing.assert_array_equal(joined[:,-30:],right)
        self.assertEqual(scope['asmb'](left,right,100,'[para]',existing_pause=2).shape,(1,130))

if __name__=='__main__': unittest.main()
