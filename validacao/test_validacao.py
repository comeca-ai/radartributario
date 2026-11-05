import hashlib, importlib.util, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'candidato/dagster_radar'))
from integridade import verificar_manifesto,sha256
import definitions
from dagster import Definitions, asset, AssetSelection, define_asset_job
spec=importlib.util.spec_from_file_location('baixar',ROOT/'candidato/vigia/baixar.py'); baixar=importlib.util.module_from_spec(spec);spec.loader.exec_module(baixar)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self): self.tmp.cleanup()
 def manifest(self,p):
  (self.root/'manifest.json').write_text(json.dumps({'arquivos':[{'arquivo':p.name,'sha256':sha256(p),'bytes':p.stat().st_size}]}))
 def test_large_file_corruption(self):
  p=self.root/'large.bin'
  with p.open('wb') as f:f.truncate(151_000_000)
  self.manifest(p);self.assertTrue(verificar_manifesto(self.root)['ok'])
  with p.open('r+b') as f:f.seek(150_999_999);f.write(b'X')
  self.assertFalse(verificar_manifesto(self.root)['ok'])
 def test_missing_manifested_file(self):
  p=self.root/'sample.bin';p.write_bytes(b'abc');self.manifest(p);p.unlink()
  self.assertFalse(verificar_manifesto(self.root)['ok'])
 def test_extra_data(self):
  p=self.root/'sample.bin';p.write_bytes(b'abc');self.manifest(p);(self.root/'extra.csv').write_text('extra')
  self.assertFalse(verificar_manifesto(self.root)['ok'])
 def test_preserves_previous_attempt(self):
  with patch.object(baixar,'BRUTOS',str(self.root)):
   a=Path(baixar.novo_tmp('teste'));(a/'raw/original').write_text('preservado')
   b=Path(baixar.novo_tmp('teste'));self.assertNotEqual(a,b);self.assertEqual((a/'raw/original').read_text(),'preservado')
 def test_ingestion_accept_and_no_overwrite(self):
  with patch.object(baixar,'BRUTOS',str(self.root)):
   a=Path(baixar.novo_tmp('teste'));(a/'raw/entrada.csv').write_text('id\n1\n')
   m={'fonte':'fixture','referencia':'2026-10','fonte_url':'https://example.invalid','baixado_em':'2026-11-05'}
   dest=baixar.aceitar(str(a),'teste',m,False);self.assertTrue(verificar_manifesto(dest)['ok'])
   b=baixar.novo_tmp('teste')
   with self.assertRaises(FileExistsError):baixar.aceitar(b,'teste',m,False)
   self.assertTrue(Path(b).exists())
 def test_actual_check_blocks_downstream(self):
  pasta=self.root/'brutos/rfb-cnpj-2026-10';pasta.mkdir(parents=True)
  (pasta/'manifest.json').write_text(json.dumps({'arquivos':[{'arquivo':'ausente.zip','sha256':'0'*64}]}))
  calls=[]
  @asset(partitions_def=definitions.REFS)
  def consumidor(rfb_cnpj_bruto):calls.append(True)
  job=define_asset_job('teste_bloqueio',selection=AssetSelection.all(),partitions_def=definitions.REFS)
  defs=Definitions(assets=[definitions.rfb_cnpj_bruto,consumidor],asset_checks=[definitions.bruto_hash_confere],jobs=[job])
  with patch.object(definitions,'DADOS',str(self.root)):
   result=defs.get_job_def('teste_bloqueio').execute_in_process(partition_key='2026-10',raise_on_error=False)
  self.assertFalse(result.success);self.assertEqual(calls,[])
 def test_definitions_load(self):
  Definitions.validate_loadable(definitions.defs)
if __name__=='__main__':unittest.main(verbosity=2)
