"""Prioridade comercial v1: hipóteses de despesas em campo, sem estimar empregados.
Preserva todos os CNPJs; produz uma fila por raiz empresarial para evitar consultas repetidas.
"""
import argparse,datetime,hashlib,json
from pathlib import Path
import duckdb

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dados',type=Path,required=True);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--referencia',default='2026-10');a=ap.parse_args()
 src=a.dados/'prontos/leads_reembolso/leads_reembolso.parquet';idx=a.dados/f'prontos/indice_empresas/ref={a.referencia}/indice.parquet'
 if a.saida.exists():raise SystemExit('Destino existente: use uma nova versão; nada foi sobrescrito.')
 a.saida.mkdir(parents=True,mode=0o700)
 c=duckdb.connect();c.execute("set threads=2;set memory_limit='1GB'")
 c.read_parquet(str(src)).create_view('leads')
 c.read_parquet(str(idx)).create_view('indice')
 # Uma raiz por linha no índice é condição para não multiplicar a base.
 assert c.execute('select count(*)=count(distinct cnpj_basico) from indice').fetchone()[0]
 c.execute('''create table sinais as select l.*,i.opcao_mei,
 i.n_ativos,i.n_ufs,i.cnae_predominante_descricao,
 i.cnpj_basico is not null as indice_encontrado,
 case l.subcategoria
 when 'energia_agua_telecom' then 40 when 'construcao_terraplenagem' then 40
 when 'atacado_com_frota' then 35 when 'coleta_residuos' then 30
 when 'transporte_carga_interestadual' then 25 when 'transporte_passageiros_fretamento' then 25
 when 'reboque_guincho' then 20 when 'transporte_valores' then 20
 when 'ambulancia_remocao' then 15 when 'mineracao' then 15
 when 'agropecuaria' then 10 else 0 end as pontos_atividade,
 case when i.n_ativos>=20 then 30 when i.n_ativos>=5 then 22 when i.n_ativos>=3 then 15 when i.n_ativos>=2 then 8 else 0 end as pontos_unidades,
 case when i.n_ufs>=5 then 20 when i.n_ufs>=3 then 15 when i.n_ufs>=2 then 10 else 0 end as pontos_geografia,
 case when l.porte='03' then 5 else 0 end as pontos_porte,
 case when l.subcategoria='atacado_com_frota' then 'Possivel equipe de vendas e distribuicao externa'
 when l.subcategoria in ('energia_agua_telecom','construcao_terraplenagem') then 'Possiveis equipes tecnicas ou prestadores em campo'
 when l.subcategoria in ('transporte_carga_interestadual','transporte_passageiros_fretamento') then 'Possiveis viagens com alimentacao e hospedagem'
 else 'Operacao externa possivel; confirmar se ha despesa paga por trabalhador ou prestador' end as hipotese_comercial
 from leads l left join indice i using(cnpj_basico)''')
 c.execute('''create table pontuado as select *,
 pontos_atividade+pontos_unidades+pontos_geografia+pontos_porte as pontuacao,
 situacao_cadastral='02' and coalesce(opcao_mei,'')<>'S' and indice_encontrado as elegivel,
 case when opcao_mei='N' then 'Nao MEI explicito' when opcao_mei='S' then 'MEI' else 'Sem indicacao MEI; campo ausente' end as estado_mei,
 'Atividade: '||pontos_atividade||'; unidades ativas: '||coalesce(n_ativos::varchar,'desconhecido')||' ('||pontos_unidades||' pontos); UFs: '||coalesce(n_ufs::varchar,'desconhecido')||' ('||pontos_geografia||' pontos); porte EPP: '||pontos_porte as justificativa
 from sinais''')
 c.execute('''create table priorizado as select *,case
 when not elegivel then 'Revisar elegibilidade'
 when pontuacao>=60 and (n_ativos>=3 or n_ufs>=2) then 'A - priorizar enriquecimento'
 when pontuacao>=40 then 'B - segunda rodada'
 else 'C - menor evidencia' end as prioridade
 from pontuado''')
 c.execute('''create table fila as select *,row_number() over(order by pontuacao desc,n_ativos desc nulls last,n_ufs desc nulls last,cnpj_basico,cnpj) as ordem_enriquecimento
 from (select * from priorizado where elegivel qualify row_number() over(partition by cnpj_basico order by pontuacao desc,case when matriz_filial='1' then 0 else 1 end,cnpj)=1)''')
 for table,name in [('priorizado','leads_priorizados.parquet'),('fila','fila_por_empresa.parquet')]:
  c.execute(f"copy {table} to ? (format parquet,compression zstd)",[str(a.saida/name)])
 c.execute('copy (select * from fila order by ordem_enriquecimento limit 1000) to ? (header, delimiter \',\')',[str(a.saida/'primeiros_1000.csv')])
 n=c.execute('select count(*),count(distinct cnpj) from priorizado').fetchone();orig=c.execute('select count(*) from leads').fetchone()[0]
 assert n==(orig,orig)
 assert c.execute('select count(*) from fila where not elegivel or opcao_mei=\'S\' or situacao_cadastral<>\'02\'').fetchone()[0]==0
 assert c.execute('select count(*)=count(distinct cnpj_basico) from fila').fetchone()[0]
 resumo={'versao':'v1','referencia':a.referencia,'gerado_em':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cnpjs_preservados':orig,'empresas_na_fila':c.execute('select count(*) from fila').fetchone()[0],
 'prioridades_empresas':c.execute('select prioridade,count(*) from fila group by 1 order by 1').fetchall(),
 'segmentos_primeiros_1000':c.execute('select subcategoria,count(*) from (select * from fila order by ordem_enriquecimento limit 1000) group by 1 order by 2 desc').fetchall(),
 'verificacoes':{'cnpjs_preservados_sem_duplicacao':True,'fila_uma_raiz_por_empresa':True,'fila_ativa_sem_mei_S':True},
 'limites':['Pontuacao heuristica, nao probabilidade nem numero de funcionarios.','Porte 05 significa demais; nao foi interpretado como grande empresa.','Atividade, filiais e UFs sao sinais indiretos. Reembolso, empregados e prestadores precisam ser confirmados.','Fila abrange somente setores existentes na base original.','Nao exclui automaticamente CNPJs ja consultados: reconciliar com cache de enriquecimento antes de comprar consultas.'],
 'entrada_sha256':sha(src),'saidas':[{ 'arquivo':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(a.saida.iterdir()) if p.is_file()]}
 (a.saida/'manifest.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2));print(json.dumps(resumo,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
