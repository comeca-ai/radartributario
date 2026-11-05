"""Verificação em fluxo de todos os arquivos manifestados, sem limite de tamanho."""
import hashlib
import json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def verificar_manifesto(pasta):
    root = Path(pasta).resolve()
    m = json.loads((root / 'manifest.json').read_text())
    erros, vistos, conferidos = [], set(), 0
    itens = m.get('arquivos', [])
    if not itens:
        erros.append('manifesto vazio')
    for item in itens:
        rel = item.get('arquivo', '')
        p = root / rel
        if not rel or Path(rel).is_absolute() or not p.resolve().is_relative_to(root):
            erros.append('caminho fora da pasta'); continue
        if rel in vistos:
            erros.append('entrada duplicada: ' + rel); continue
        vistos.add(rel)
        if not p.is_file():
            erros.append('ausente: ' + rel); continue
        if not item.get('sha256'):
            erros.append('sem hash: ' + rel); continue
        if sha256(p) != item['sha256']:
            erros.append('hash divergente: ' + rel); continue
        if item.get('bytes') is not None and p.stat().st_size != item['bytes']:
            erros.append('tamanho divergente: ' + rel); continue
        conferidos += 1
    # JSON/Markdown não manifestados são metadados no contrato legado.
    for p in root.rglob('*'):
        if p.is_file() and p.suffix not in ('.json', '.md') and p.relative_to(root).as_posix() not in vistos:
            erros.append('não manifestado: ' + p.relative_to(root).as_posix())
    return {'ok': not erros, 'conferidos': conferidos, 'total_erros': len(erros), 'erros': erros[:50]}
