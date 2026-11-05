# Leads Reembolso — priorização comercial v1

Objetivo autorizado: priorizar empresas com possíveis equipes de funcionários ou prestadores em campo, para venda de sistema de reembolso. Classificação heurística, sem estimativa de número de trabalhadores ou probabilidade de compra.

## Execução comprovada em 05/11/2026

Referência das entradas: outubro/2026. Base original preservada com 1.274.502 CNPJs distintos. Fila consolidada: 986.378 raízes empresariais.

| Faixa | Empresas |
|---|---:|
| A — priorizar enriquecimento | 7.891 |
| B — segunda rodada | 125.885 |
| C — menor evidência | 852.602 |

Primeiros 1.000: construção/terraplenagem 388; energia/água/telecom 370; atacado 227; resíduos 7; transporte de cargas 6; fretamento 2.

## Critério reproduzível

Pontos por atividade: energia/água/telecom e construção 40; atacado 35; resíduos 30; transporte de cargas e fretamento 25; guincho e transporte de valores 20; ambulância e mineração 15; agropecuária 10.

Unidades ativas da raiz: 20 ou mais = 30 pontos; 5 a 19 = 22; 3 a 4 = 15; 2 = 8; demais = 0.
UFs ativas: 5 ou mais = 20 pontos; 3 a 4 = 15; 2 = 10; demais = 0.
Porte EPP (03): 5 pontos. Porte 05 significa demais e não foi interpretado como grande empresa. Capital social não pontua.

A: pelo menos 60 pontos e três unidades ou duas UFs.
B: pelo menos 40 pontos, fora de A.
C: demais elegíveis.

Elegibilidade: situação 02, índice encontrado e MEI diferente de S. MEI ausente permanece explícito e não é convertido em confirmação de N. Todos os registros permanecem no arquivo completo.

A fila seleciona uma entrada por raiz, maior pontuação, preferência por matriz entre empates, depois CNPJ. Ordenação final: pontuação, unidades ativas, UFs e identificadores para desempate. Pode selecionar uma filial quando a matriz não está na base; não inventa um CNPJ de matriz.

## Limites

- Sinais são indiretos: confirmar quantidade de equipes, uso de prestadores e despesas reembolsáveis na qualificação comercial.
- Algumas empresas com muitas unidades compram tudo centralmente; a pontuação não comprova reembolso.
- Trabalha somente com os setores já presentes. Representação comercial, manutenção e outros setores fora do recorte não foram adicionados.
- Regime tributário e tese de crédito não definem a prioridade.
- Não exclui consultas anteriores da API: conciliar fila com o cache antes de enriquecer.
- Esta versão não altera o enriquecimento em andamento, não chama APIs e não foi integrada ao Dagster.
- Validações executadas: quantidade e unicidade dos CNPJs preservadas, uma raiz por entrada na fila, elegibilidade conferida e hashes de entrada/saídas registrados.
- Os pesos são hipótese inicial comercial; ajustar com conversões observadas.

## Reproduzir

Python com DuckDB instalado:

```bash
python priorizar.py --dados /caminho/dados --referencia 2026-10 --saida /caminho/versao-nova
```

O destino precisa ser novo. Entradas relativas à pasta dados:
- prontos/leads_reembolso/leads_reembolso.parquet
- prontos/indice_empresas/ref=2026-10/indice.parquet

Saídas: leads_priorizados.parquet, fila_por_empresa.parquet, primeiros_1000.csv e manifest.json.
A primeira tentativa local parou antes de gerar dados por incompatibilidade de parâmetro em CREATE VIEW; o código foi corrigido e a execução seguinte concluída.

Na máquina, resultados em /home/ubuntu/leads-reembolso-priorizacao/resultado-v1-validado/. Arquivos de leads e respostas de APIs não devem ser enviados ao repositório.
