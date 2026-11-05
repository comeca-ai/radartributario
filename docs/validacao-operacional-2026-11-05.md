# Validação operacional — 05/11/2026

## Resultado e alcance

Trabalho autorizado: bloqueios de qualidade, backup, restauração e ingestão de atualizações. Todos os dados devem ser preservados. Nenhuma base foi enviada ao GitHub.

**Estado: correções candidatas testadas, ainda não implantadas.** A sessão tem leitura do diretório operacional, mas escrita somente na área de trabalho e temporários. O repositório estava vazio; os arquivos publicados aqui são ferramentas e patches de validação, não uma cópia completa da aplicação.

## Evidências obtidas

| Verificação | Resultado |
|---|---|
| Runtime local | Python 3.12; Dagster 1.9.13 |
| Testes novos | 7 passaram |
| Testes existentes de Licitações | 14 passaram |
| Check real do núcleo com entrada inválida | Execução falhou e consumidor dependente não executou |
| Arquivo de 151 MB adulterado | Corrupção detectada após o limite antigo de 150 MB |
| Arquivo manifestado ausente / dado extra | Reprovados |
| Nova tentativa de ingestão | Tentativa anterior preservada |
| Aceitação de coleta local e reexecução | Manifesto verificado; destino existente não sobrescrito |
| Definições completas candidatas | Carregadas e validadas pelo Dagster |
| Backup e restauração de amostra real | 6 arquivos, 217.591 bytes; hashes idênticos |

Logs integrais e amostra de backup permanecem na máquina, na área radar-validacao/evidencias. Os testes de ingestão usam fixtures sintéticas; não representam uma coleta online. Foram observados avisos de arquivos abertos sem fechamento explícito no código legado; não causaram falha dos testes.

## Correções preparadas

- Checks do núcleo, entidades e API PJ passam a declarar bloqueio. O check de casos-ouro permanece informativo, conforme seu contrato original.
- Integridade da Receita passa a verificar arquivos de todos os tamanhos em fluxo, arquivos ausentes, caminhos fora da pasta, entradas duplicadas, tamanhos e dados extras.
- JSON e Markdown não manifestados continuam tratados como metadados no contrato legado. Se manifestados, são verificados.
- Cada tentativa do baixador usa uma pasta temporária exclusiva; nenhuma tentativa anterior é apagada por novo_tmp.

O patch não remove nem muda classificação de dados. Os nomes de diretórios legados não foram migrados.

**Limite importante:** bloquear consumidores no Dagster não desfaz arquivos já gravados pelo asset que reprovou. O núcleo ainda escreve algumas saídas diretamente, e a publicação de dossiês valida depois de executar geradores. A publicação integral por release, como já existe em Licitações, continua pendente no núcleo. Não declarar o item 1 integralmente concluído.

## Reproduzir os testes em cópia isolada

Os comandos abaixo são para a máquina que contém a instalação existente, sem executar pipelines reais:

```bash
mkdir -p candidato/dagster_radar candidato/vigia
cp /srv/tributario/pipeline/dagster_radar/*.py candidato/dagster_radar/
cp /srv/tributario/pipeline/dagster_radar/casos_ouro.json candidato/dagster_radar/
cp /srv/tributario/pipeline/vigia/baixar.py candidato/vigia/
cp integridade.py candidato/dagster_radar/
```

O patch utiliza caminhos pipeline/. Aplicar inicialmente em uma segunda árvore com esse nome, usando git apply --check antes de git apply; depois copiar os quatro arquivos corrigidos para candidato/, mantendo o restante da cópia. Não aplicar sobre código divergente sem revisão.

```bash
PYTHONDONTWRITEBYTECODE=1 /srv/tributario/pipeline/.venv/bin/python test_validacao.py
```

O teste usa candidato/ ao lado de test_validacao.py. O resultado esperado é 7 testes aprovados. O caso de bloqueio gera logs de falha intencional do Dagster; isso é esperado.

Para os testes existentes de Licitações:

```bash
cd /srv/tributario/produtos/radar-licitacoes/pipeline
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

Resultado observado: 14 testes aprovados, sem executar coleta real.

## Backup e restauração

O ensaio incluiu catálogo, quatro arquivos de código originais e um Parquet agregado. A ferramenta backup_validado.py:

1. Exige destinos novos e arquivos regulares explicitamente selecionados.
2. Calcula SHA-256 na origem e na cópia.
3. Reconfere a origem para detectar mudanças durante a cópia.
4. Grava manifesto.
5. Restaura em outro diretório e confere todos os hashes.
6. Preserva originais e recusa destinos já existentes.

```bash
python3 backup_validado.py /destino/backup-novo /destino/restore-novo /origem/arquivo1 /origem/arquivo2
```

Esse procedimento foi executado no mesmo disco. Não é backup externo, snapshot transacional nem recuperação integral da plataforma. Bancos Dagster/SQLite/DuckDB em uso exigem mecanismo próprio de snapshot ou janela sem escritores; não copiar arquivos de banco abertos como se fossem consistentes.

Para concluir a recuperação integral falta:
- definir destino externo com capacidade, acesso e retenção;
- inventariar todos os dados, inclusive pastas históricas, veículos, licitações e arquivos mantidos em caminhos legados;
- incluir código, dependências fixadas, configurações e segredos em backup privado;
- executar backup consistente;
- restaurar em ambiente independente;
- validar bancos, contagens, serviços e leitura pelas aplicações;
- registrar duração, espaço consumido e ponto de recuperação.

Nenhum backup deve ser enviado para este repositório. Não apagar dados para liberar espaço no ensaio.

## Ingestão e atualização: achados

- Receita: sensor detecta referências ausentes e retorna aviso; não baixa automaticamente. A carga mensal pressupõe arquivos/conversões existentes.
- PNCP, CGU e PGFN: baixador existente cria arquivos e manifestos; os testes locais comprovaram aceitação e proteção contra sobrescrita.
- Índice de empresas: PGFN e CEIS têm referências fixas no código. Download de versão nova não garante atualização da busca.
- Receita: baixar_receita.py ainda contém remoção de arquivo com tamanho divergente e reaproveitamento por tamanho sem conferir hash. Não foi corrigido neste pacote; não usar para reingestão antes de tratar essas condições.
- Dossiês: impressão das entradas usa nomes de partições, não o conteúdo completo dos Parquets. Alterar conteúdo de uma partição existente pode não disparar atualização.
- Licitações: testes existentes cobrem paginação, modalidades, corrupção, duplicidade, período, bloqueio Dagster e preservação da release anterior.

Acesso Git ao GitHub pelo terminal falhou por resolução DNS; publicação foi feita pelo conector GitHub. Fontes externas de ingestão não foram consultadas neste ensaio. Portanto, atualidade das fontes e atualização online de ponta a ponta seguem pendentes.

## Procedimento de implantação e reversão

1. Obter sessão com escrita autorizada no diretório operacional.
2. Conferir que os arquivos originais ainda correspondem ao patch com git apply --check.
3. Pausar agendas e aguardar ausência de execuções ativas.
4. Copiar os arquivos atuais para backup com hashes.
5. Aplicar as quatro alterações e instalar integridade.py ao lado de definitions.py.
6. Reexecutar os testes isolados e validar o carregamento das definições.
7. Recarregar a localização de código na instância correta.
8. Validar uma atualização em destino separado antes de promover saídas.
9. Reativar agendas e observar a primeira execução.

Para reverter: pausar agendas, aguardar jobs, restaurar os arquivos de código do backup, recarregar definições e validar. Reversão de código não reverte dados já escritos; preservar e tratar as versões de dados separadamente.

## Pendências abertas

- Implantação das correções.
- Publicação atômica do núcleo e dossiês.
- Correção do baixador específico da Receita.
- Seleção explícita de novas referências no índice e teste de atualização.
- Backup externo e restauração integral.
- Teste online de ingestão e verificação de serviços.

A documentação registra somente resultados comprovados; não equivale a certificação da operação em produção.
