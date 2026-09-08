from pathlib import Path
import pandas as pd
import streamlit as st
from matching import rank_jobs, parse_skills, WEIGHTS

st.set_page_config(page_title='Career Match | Job Search',page_icon='🔎',layout='wide')

@st.cache_data
def load_jobs():
    return pd.read_csv(Path(__file__).parent/'data'/'jobs.csv')

jobs=load_jobs()
st.title('Find your next data analyst role')
st.caption('Career Match · Explainable recommendations based on your skills and preferences')
st.info(f'{len(jobs):,} historical job records. Salaries are Glassdoor estimates, interpreted as annual USD. These are not verified current vacancies.')
with st.sidebar:
    st.header('Your preferences')
    with st.form('search'):
        skills=st.text_input('Skills',value='Python, Pandas, SQL, PyTorch',help='Separate skills with commas. Unknown skills remain valid inputs but may not occur in this dataset.')
        sizes=sorted(jobs.company_size.dropna().unique(),key=lambda s:int(s.split()[0].replace('+','')))
        size=st.selectbox('Company Size',sizes)
        location=st.text_input('Location',value='Chicago, IL',placeholder='Kansas City, MO or Remote')
        salary=st.number_input('Minimum Expected Salary (USD / year)',min_value=0,value=80000,step=5000)
        submitted=st.form_submit_button('Search Jobs',type='primary',use_container_width=True)
    st.caption('Skills 50% · Salary 20% · Location 20% · Company Size 10%')
    st.caption('Preferences affect scores; they are not hard filters. Location uses exact city/state matching, ignoring case and comma spacing. Remote matches only an explicitly remote location.')

if submitted:
    if not parse_skills(skills) or not location.strip():
        st.error('Enter at least one skill and a preferred location.')
    else:
        st.session_state['results']=rank_jobs(jobs,skills,location,salary,size)[:5]
        st.session_state['query']=f'{skills} · {location} · ${salary:,.0f}+ · {size}'

with st.expander('How scoring works'):
    st.markdown('**Skills:** matched listed skills / listed skills × 100. **Salary:** 100 if the lower estimate meets your minimum, 50 if only the upper estimate does, otherwise 0. **Location and Size:** 100 for a match, otherwise 0.')
    st.markdown('Total = weighted sum of known component scores / sum of their weights. Missing fields are unknown, not zero. Coverage shows available scoring evidence; scores with lower coverage are less complete. Ties use higher coverage, then job ID. Scores are not hiring probabilities.')
    st.caption('Skill extraction uses a limited dictionary of mentioned skills, not verified mandatory qualifications. PyTorch and other unextracted skills may not earn credit even when mentioned in the original description. Review the source description.')

if 'results' not in st.session_state:
    st.subheader('Start with your preferences')
    st.write('Choose your preferences and select Search Jobs to compare the top five recommendations.')
else:
    st.subheader('Your Top 5 matches')
    st.caption('Results for: '+st.session_state['query'])
    export=[]
    for i,result in enumerate(st.session_state['results'],1):
        j=result['job']
        with st.container(border=True):
            st.subheader(f"{i}. {j['title']}")
            company=j['company'] if pd.notna(j['company']) else 'Company unknown'
            st.write(f"{company} · {j['location']}")
            st.caption(str(j['company_size']) if pd.notna(j['company_size']) else 'Company size unknown')
            salary_label=f"${j['salary_min']:,.0f}–${j['salary_max']:,.0f} estimated / year" if pd.notna(j['salary_min']) else 'Salary unknown'
            st.write(salary_label)
            cols=st.columns(5)
            cols[0].metric('Total match',f"{result['score']:.1f}/100")
            for col,(key,value) in zip(cols[1:],result['scores'].items()):
                col.metric(key,'Unknown' if value is None else f'{value:.1f}/100')
            st.caption(f"Information coverage: {result['coverage']:.0%} · Job ID: {j['job_id']}")
            if result['coverage']<1:
                st.warning('Incomplete scoring evidence: known factors have been reweighted. Review the missing information before comparing.')
            st.write('**Matched skills:** '+(', '.join(result['matched']) or 'None identified'))
            st.write('**Missing listed skills:** '+(', '.join(result['missing']) or ('None' if result['scores']['Skills'] is not None else 'Unknown — no dictionary skills identified')))
            with st.expander('Read job description'):
                st.text(j['description'])
        export.append({'job_id':j['job_id'],'title':j['title'],'company':company,'location':j['location'],'salary':salary_label,'total_score':round(result['score'],2),'coverage':result['coverage'],**result['scores'],'matched_skills':'; '.join(result['matched']),'missing_skills':'; '.join(result['missing'])})
    st.download_button('Download Top 5 CSV',pd.DataFrame(export).to_csv(index=False).encode('utf-8-sig'),'top_5_jobs.csv','text/csv')
