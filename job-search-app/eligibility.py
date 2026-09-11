import pandas as pd
SALARY_FLOOR=60000

def classify(row):
    low=pd.to_numeric(row.get('salary_min'),errors='coerce')
    high=pd.to_numeric(row.get('salary_max'),errors='coerce')
    period=row.get('salary_period','')
    currency=row.get('salary_currency','')
    if pd.isna(low) or pd.isna(high): reason='Salary unknown or unparseable'
    elif low<0 or high<low: reason='Invalid salary range'
    elif currency!='USD' or period not in ('annual','annual_assumed'): reason='Annual USD basis not confirmed'
    elif low<SALARY_FLOOR: reason='Estimated minimum below USD 60,000'
    else: reason='Eligible: estimated minimum >= USD 60,000'
    return dict(job_id=row['job_id'],location=row.get('location',''),salary_min=low,salary_max=high,salary_period=period,evidence=f"Original salary: {row.get('salary_raw','Unknown')}; currency: {currency}; period: {period}",filter_reason=reason,eligible=reason.startswith('Eligible:'))

def screen(jobs):
    audit=pd.DataFrame([classify(r) for r in jobs.to_dict('records')],columns=['job_id','location','salary_min','salary_max','salary_period','evidence','filter_reason','eligible'])
    keep=set(audit.loc[audit.eligible==True,'job_id'])
    return jobs[jobs.job_id.isin(keep)].copy(),audit
