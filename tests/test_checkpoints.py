"""Disk checkpoint/restart tests using small synthetic WAVs, without the TTS model."""
import ast
import inspect
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
import numpy as np
from test_audio_regressions import APP, WORKER, Tensor, functions

class Model:
    sr=1000

class Audio(Tensor):
    def numpy(self): return np.asarray(self)
    def clone(self): return self.copy().view(Audio)

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=os.getcwd(); os.chdir(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir,self.old)
        Path('script.py').write_text('test script')
        Path('voice.wav').write_bytes(b'reference voice')
        runtime=next(ast.literal_eval(n.value) for n in APP.body if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='CHECKPOINT_RUNTIME' for t in n.targets))
        self.ns=dict(os=os,re=re,sys=sys,pathlib=__import__('pathlib'),inspect=inspect,
                     model=Model(),__file__='script.py',tc=[['Prima','v1',None,[],.1,None,None],['Seconda','v1',None,[],.1,None,None]],
                     RMS_TARGET_DB=-18,PAUSE_SCALE=1,JM={},dyn_pause=lambda *a,**k:0,
                     torch=SimpleNamespace(from_numpy=lambda a:a.view(Audio),
                         zeros=lambda shape:np.zeros(shape,dtype='float32').view(Audio),
                         cat=lambda ws,dim:np.concatenate(ws,axis=dim).view(Audio)))
        for i in range(1,8): self.ns['AUDIO_V'+str(i)]='voice.wav'
        for i in range(2,8): self.ns['HAS'+str(i)]=False
        exec(runtime,self.ns)
        functions(WORKER,['asmb'],self.ns)
        self.ns['initialize_job']()
    def tearDown(self):
        if 'job_lock' in self.ns: self.ns['job_lock'].close()
    def save(self,i):
        data=np.full((1,600),.2,dtype='float32').view(Audio)
        return self.ns['save_chunk'](i,data)
    def test_resume_and_corruption(self):
        path=self.save(0)
        original_dir=self.ns['job_dir']
        self.ns['job_lock'].close()
        self.ns['tc'][0][4]=9
        self.ns['initialize_job']()
        self.assertEqual(self.ns['job_dir'],original_dir)
        self.assertEqual(self.ns['tc'][0][4],.1)
        self.assertEqual(self.ns['cached_chunk'](0),path)
        self.assertIsNone(self.ns['cached_chunk'](1))
        path.write_bytes(b'corrupted')
        self.assertIsNone(self.ns['cached_chunk'](0))
    def test_changed_voice_has_separate_session(self):
        self.save(0); original=self.ns['job_dir']
        self.ns['job_lock'].close()
        Path('voice.wav').write_bytes(b'different reference')
        self.ns['initialize_job']()
        self.assertNotEqual(original,self.ns['job_dir'])
        self.assertIsNone(self.ns['cached_chunk'](0))
    def test_streaming_assembly_and_atomic_output(self):
        paths=[self.save(i) for i in range(2)]
        output=Path('1.Output/result.wav')
        duration=self.ns['assemble_saved'](paths,output)
        self.assertAlmostEqual(duration,1.2)
        output=Path(self.ns['progress']['output'])
        self.assertEqual(output.name,'audiolibro_01.wav')
        data,sr=self.ns['sf'].read(output)
        self.assertEqual(len(data),1200)
        self.assertEqual(sr,1000)
        self.assertTrue(np.isfinite(data).all())
        self.assertLessEqual(np.abs(data).max(),.95)
        self.assertEqual(self.ns['progress']['status'],'completato')
        self.assertTrue(all(p.exists() for p in paths))
    def test_failed_assembly_preserves_blocks_and_existing_output(self):
        good=self.save(0); output=Path('1.Output/result.wav'); output.write_bytes(b'previous result')
        with self.assertRaises(Exception):
            self.ns['assemble_saved']([good,Path('missing.wav')],output)
        self.assertEqual(output.read_bytes(),b'previous result')
        self.assertTrue(good.exists())

    def test_537_blocks_with_one_missing_then_resume(self):
        self.ns['tc']=[['Testo','v1',None,[],.1,None,None] for _ in range(537)]
        self.ns['progress']['chunks']=self.ns['tc']
        self.ns['save_progress']()
        for i in range(537):
            if i!=10: self.save(i)
        self.ns['job_lock'].close()
        self.ns['initialize_job']()
        missing=[i for i in range(537) if self.ns['cached_chunk'](i) is None]
        self.assertEqual(missing,[10])
        self.save(10)
        paths=[self.ns['cached_chunk'](i) for i in range(537)]
        duration=self.ns['assemble_saved'](paths,Path('1.Output/complete.wav'))
        self.assertAlmostEqual(duration,537*.6)
        self.assertEqual(len(self.ns['progress']['completed']),537)

    def test_progressive_names_preserve_existing_files(self):
        folder=Path('1.Output')
        (folder/'audiolibro_192.wav').write_bytes(b'old')
        (folder/'audiolibro_123456789012345678901234.wav').write_bytes(b'legacy hash')
        source=folder/'new.tmp.wav'; source.write_bytes(b'new')
        result=self.ns['publish_numbered'](source,folder)
        self.assertEqual(result.name,'audiolibro_193.wav')
        self.assertEqual((folder/'audiolibro_192.wav').read_bytes(),b'old')
        source.write_bytes(b'next')
        self.assertEqual(self.ns['publish_numbered'](source,folder).name,'audiolibro_194.wav')

if __name__=='__main__': unittest.main()
