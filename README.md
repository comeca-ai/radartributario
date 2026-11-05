# Radar Tributário

Código e documentação da plataforma Radar Tributário. As bases de dados ficam fora deste repositório.

## Organização observada

- Núcleo: Python, DuckDB, Parquet e Dagster; busca, empresas, estabelecimentos, carteiras e dossiês.
- Licitações: coleta PNCP, tratamento, verificações e publicação por releases.
- Veículos: domínio de dados com instância Dagster própria.
- Integrações: ferramentas fiscais e consultas empresariais.

## Trabalho autorizado em 05/11/2026

1. Validar e corrigir os bloqueios de qualidade.
2. Validar backup, restauração e ingestão para atualização.
3. Documentar procedimentos, evidências, limitações e mudanças.

Todos os dados existentes devem ser preservados. A orientação do proprietário é não adotar quarentena como classificação de negócio. Os caminhos legados permanecem até uma migração planejada; uma validação reprovada deve preservar os arquivos e impedir promoção automática de uma versão defeituosa.

## Estado inicial da validação

A inspeção encontrou checks do núcleo sem bloqueio explícito, verificação de hash que ignora arquivos acima de 150 MB, exclusão de temporários de tentativas anteriores no baixador e referências fixas de algumas fontes no índice. A existência de backup externo e a restauração integral ainda não foram comprovadas.

As correções estão sendo preparadas e testadas em cópia de trabalho. Não foram implantadas em produção. A sessão atual tem leitura do diretório operacional e escrita apenas na área de trabalho.

## Conteúdo permitido

Código revisado, documentação, contratos e testes com exemplos sintéticos. Não incluir bases, respostas de APIs com registros reais, arquivos de usuários, credenciais, configurações privadas, logs operacionais nem ambientes virtuais.
