"""Cópia verificável de arquivos estáveis. Não é snapshot de banco em execução.
Uso: python backup_validado.py DESTINO_NOVO RESTAURACAO_NOVA ARQUIVO [ARQUIVO ...]
Nenhum destino existente é sobrescrito. Não remove originais. Não envia dados à rede.
"""
import hashlib, json, shutil, sys
from pathlib import Path


def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()


def executar(destino,restauracao,arquivos):
 dest=Path(destino); restore=Path(restauracao)
 if dest.exists() or restore.exists():raise FileExistsError('Use destinos novos')
 files=[Path(p).absolute() for p in arquivos]
 if not files or len(set(files))!=len(files):raise ValueError('Lista vazia ou repetida')
 for p in files:
  if not p.is_file() or p.is_symlink():raise ValueError('Entrada precisa ser arquivo regular')
 dest.mkdir(parents=True,mode=0o700); items=[]
 for p in files:
  before=sha(p);rel=p.relative_to(p.anchor);out=dest/'arquivos'/rel;out.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(p,out)
  if before!=sha(out) or before!=sha(p):raise RuntimeError('Origem mudou ou cópia divergiu')
  items.append({'arquivo':str(rel),'sha256':before,'bytes':out.stat().st_size})
 (dest/'manifest.json').write_text(json.dumps({'arquivos':items},indent=2))
 restore.mkdir(parents=True,mode=0o700)
 for item in items:
  rel=Path(item['arquivo']);src=dest/'arquivos'/rel;out=restore/rel;out.parent.mkdir(parents=True,exist_ok=True)
  if sha(src)!=item['sha256']:raise RuntimeError('Backup divergiu antes da restauração')
  shutil.copy2(src,out)
  if sha(out)!=item['sha256']:raise RuntimeError('Restauração divergiu')
 receipt={'arquivos':len(items),'bytes':sum(x['bytes'] for x in items),'hashes_restaurados_conferidos':True,'escopo':'arquivos explicitamente selecionados; mesmo disco; não é backup externo nem restauração integral'}
 (dest/'resultado.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));return receipt
if __name__=='__main__':print(json.dumps(executar(sys.argv[1],sys.argv[2],sys.argv[3:]),ensure_ascii=False))
