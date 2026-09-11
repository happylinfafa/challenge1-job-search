"""Run from project folder: python evaluate.py. Outputs real program results, not relevance labels."""
from pathlib import Path
import json,time
import pandas as pd
from eligibility import screen
from matching import rank_jobs

root=Path(__file__).parent
out=root/'results';out.mkdir(exist_ok=True)
jobs=pd.read_csv(root/'data/jobs.csv')
filtered,audit=screen(jobs)
audit.to_csv(out/'filter_audit.csv',index=False,encoding='utf-8-sig')
summary={'input_rows':len(jobs),'filter_counts':audit.filter_reason.value_counts().to_dict(),'profiles':[]}
all_rows=[]
for label,skills,location in [('SQL profile','SQL','Chicago, IL'),('Python profile','Python, SQL, Excel','New York, NY'),('BI profile','Tableau, Power BI, SQL','Plano, TX')]:
    start=time.perf_counter()
    ranked=[r for r in rank_jobs(filtered,skills,location,80000,'51 to 200 employees') if r['scores']['Skills'] is not None][:5]
    summary['profiles'].append({'label':label,'skills':skills,'location':location,'salary':80000,'size':'51 to 200 employees','returned':len(ranked),'matching_ms':round((time.perf_counter()-start)*1000,2)})
    for i,r in enumerate(ranked,1):
        all_rows.append({'profile':label,'rank':i,'job_id':r['job']['job_id'],'title':r['job']['title'],'score':round(r['score'],2),'coverage':r['coverage'],**r['scores'],'matched':'; '.join(r['matched']),'missing':'; '.join(r['missing'])})
pd.DataFrame(all_rows).to_csv(out/'profile_results.csv',index=False,encoding='utf-8-sig')
(out/'evaluation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
