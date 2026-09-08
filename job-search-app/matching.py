import re
import pandas as pd

WEIGHTS = {'Skills': .5, 'Salary': .2, 'Location': .2, 'Size': .1}
ALIASES = {'powerbi':'power bi', 'microsoft excel':'excel', 'ms excel':'excel',
           'postgresql':'sql', 'mysql':'sql', 't-sql':'sql', 'pl/sql':'sql',
           'statistical':'statistics', 'github':'git', 'sklearn':'scikit-learn'}

def canonical(value):
    value = re.sub(r'\s+', ' ', str(value)).strip().casefold()
    return ALIASES.get(value, value)

def parse_skills(value):
    return {canonical(x) for x in re.split(r'[,;\n]', value or '') if x.strip()}

def available(value):
    return pd.notna(value) and str(value).strip() not in ('', '-1', 'Unknown')

def location_key(value):
    return re.sub(r'\s*,\s*', ',', canonical(value))

def rank_jobs(jobs, user_skills, location, minimum_salary, size):
    seeker = parse_skills(user_skills)
    ranked = []
    for _, row in jobs.iterrows():
        labels = [s.strip() for s in str(row.skills).split(';') if s.strip()] if available(row.skills) else []
        required = {canonical(s) for s in labels}
        matched = [s for s in labels if canonical(s) in seeker]
        missing = [s for s in labels if canonical(s) not in seeker]
        salary_score = None
        if available(row.salary_min) and available(row.salary_max):
            salary_score = 100 if row.salary_min >= minimum_salary else (50 if row.salary_max >= minimum_salary else 0)
        scores = {'Skills':100*len(required & seeker)/len(required) if required else None,
                  'Salary':salary_score,
                  'Location':100 if location_key(row.location)==location_key(location) else 0 if available(row.location) else None,
                  'Size':100 if row.company_size==size else 0 if available(row.company_size) else None}
        coverage = sum(WEIGHTS[k] for k,v in scores.items() if v is not None)
        total = sum(WEIGHTS[k]*v for k,v in scores.items() if v is not None)/coverage if coverage else 0
        ranked.append({'job':row.to_dict(), 'scores':scores, 'score':total,
                       'coverage':coverage, 'matched':matched, 'missing':missing})
    return sorted(ranked,key=lambda r:(-r['score'],-r['coverage'],str(r['job']['job_id'])))
