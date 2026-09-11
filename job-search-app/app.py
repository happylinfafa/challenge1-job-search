from pathlib import Path
import json
import pandas as pd
import streamlit as st
from matching import rank_jobs, parse_skills
from resume import read_document, extract, evidence_for
from eligibility import screen

st.set_page_config(page_title='Explainable Job Match',page_icon='🔎',layout='wide')
st.markdown("""<style>
.stApp {background:#f4f7fb;color:#172b43}
[data-testid="stHeader"] {background:transparent}
[data-testid="stMainBlockContainer"] {max-width:1440px;padding-top:2rem}
[data-testid="stSidebar"] {background:#eaf0f6;border-right:1px solid #d5e0ea}
h1,h2,h3 {color:#122b46;letter-spacing:-.025em}
h1 {font-size:2.3rem!important}
h3 {font-size:1.25rem!important}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:16px}
[data-testid="stExpander"], [data-testid="stForm"] {background:#fff;border:1px solid #d5e0ea;border-radius:14px}
[data-testid="stMetric"] {background:#12334a;color:#fff;padding:20px 24px;border-radius:14px}
[data-testid="stMetric"] * {color:#fff!important}
[data-testid="stMetricValue"] {font-size:2.4rem}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {background:#087f79;border:1px solid #087f79;border-radius:9px;min-height:42px}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {background:#06645f;border-color:#06645f}
[data-testid="stProgress"] [role="progressbar"] {accent-color:#087f79}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden}
.brand-label {font-size:.8rem;font-weight:700;letter-spacing:.14em;color:#087f79;margin-bottom:.4rem}
.empty-panel {background:white;border:1px dashed #b6c9d8;border-radius:16px;padding:2rem;margin-top:1rem}
.empty-panel h3 {margin:0 0 .5rem}
.empty-panel p {color:#51657a;margin:0}
@media(max-width:760px) {[data-testid="stMainBlockContainer"]{padding:1rem}h1{font-size:1.8rem!important}}
</style>""",unsafe_allow_html=True)
@st.cache_data
def load():
    return pd.read_csv(Path(__file__).parent/'data/jobs.csv')
jobs=load()
@st.cache_data
def filter_jobs(frame):
    return screen(frame)
salary_jobs,filter_audit=filter_jobs(jobs)
vocab=sorted({s.strip() for x in jobs.skills.dropna() for s in x.split(';')}|{'PyTorch','TensorFlow'})
st.markdown('<div class="brand-label">CAREER MATCH</div>',unsafe_allow_html=True)
st.title('Find your next opportunity')
st.caption('Your skills. Your preferences. A clearer job shortlist.')
with st.expander('About the data & salary filter'):
    st.write(f'{len(jobs):,} historical job records with estimated annual USD salaries. Availability is not verified.')
    st.write('Jobs need an estimated annual salary minimum of USD 60,000 or more. Unknown or invalid salaries are excluded. Location and work arrangement are preferences, not hard filters.')
    st.dataframe(filter_audit.filter_reason.value_counts().rename_axis('Reason').reset_index(name='Jobs'),hide_index=True)
    st.dataframe(filter_audit[filter_audit.eligible],hide_index=True)
    st.download_button('Download filter audit',filter_audit.to_csv(index=False).encode('utf-8-sig'),'filter_audit.csv','text/csv')
for key,value in {'skills':'','education':'','location':'','candidate':'Candidate','documents':[]}.items():
    st.session_state.setdefault(key,value)
with st.expander('Upload your resume',expanded=True):
    st.caption('PDF with selectable text, DOCX, or UTF-8 TXT; maximum 5 MB. Processed in this session without an external AI API or intentional disk storage. Scanned PDFs require text/OCR first.')
    upload=st.file_uploader('Resume',type=['pdf','docx','txt'],max_upload_size=5)
    pasted=st.text_area('Or paste resume text',height=90)
    if st.button('Extract profile',type='primary'):
        try:
            docs=read_document(upload.name,upload.getvalue()) if upload else [('Pasted resume',pasted)]
            if not any(text.strip() for _,text in docs): raise ValueError('No readable text. Paste resume text or upload a text-based document.')
            profile=extract(docs,vocab)
            st.session_state.documents=docs
            for key in ('skills','education','location'): st.session_state[key]=profile[key]
            st.session_state.pop('results',None)
            st.success('Extracted suggested fields. Review and correct them below; salary and company preferences are not inferred.')
        except Exception as e:
            st.error(f'Unable to read resume: {e}')

with st.sidebar:
    st.header('Your profile')
    st.caption('Review your details, then search.')
    with st.form('profile_form'):
        name=st.text_input('Display name (optional)',key='candidate')
        education=st.text_input('Education (review extracted text)',key='education')
        skills=st.text_input('Skills, separated by commas',key='skills')
        location=st.text_input('Preferred city, state',key='location')
        salary=st.number_input('Minimum expected salary (USD/year)',min_value=0,value=80000,step=5000)
        sizes=sorted(jobs.company_size.dropna().unique(),key=lambda s:int(s.split()[0].replace('+','')))
        size=st.selectbox('Company size',sizes)
        st.markdown('#### Matching preferences')
        st.caption('Set weights to a total of 100%. Education is not scored.')
        weights={k:st.number_input(f'{k} weight (%)',0,100,v,5) for k,v in [('Skills',40),('Salary',30),('Location',10),('Size',20)]}
        search=st.form_submit_button('Search Jobs',type='primary',use_container_width=True)
    st.caption('The USD 60,000 estimated annual minimum is fixed. Your salary expectation affects scoring after filtering. City and size are preferences; experience is not scored.')
if search:
    st.session_state.pop('results',None)
    if not parse_skills(skills) or not location.strip(): st.error('Provide skills and a preferred location.')
    elif sum(weights.values())!=100: st.error('Weights must total 100%.')
    else:
        results=rank_jobs(salary_jobs,skills,location,salary,size)
        for r in results:
            active={k:v for k,v in r['scores'].items() if v is not None and weights[k]>0}
            r['possible']=sum(weights[k] for k in active)
            r['earned']=sum(weights[k]*v/100 for k,v in active.items())
            r['score']=100*r['earned']/r['possible'] if r['possible'] else 0
        # Insufficient skill evidence is kept outside main recommendations.
        eligible=[r for r in results if r['scores']['Skills'] is not None]
        st.session_state.unknown_count=len(results)-len(eligible)
        st.session_state.results=sorted(eligible,key=lambda r:(-r['score'],-r['possible'],r['job']['job_id']))[:5]
        st.session_state.profile=dict(name=name,education=education,skills=skills,location=location,salary=salary,size=size,weights=weights)
        st.session_state.result_docs=list(st.session_state.documents)
if 'results' not in st.session_state:
    st.markdown('<div class="empty-panel"><h3>Your shortlist starts here</h3><p>Upload a resume or enter your skills in the sidebar. Select Search Jobs to compare your best matches.</p></div>',unsafe_allow_html=True)
else:
    results=st.session_state.results; p=st.session_state.profile
    st.subheader(f'Your top matches · {len(results)} jobs')
    st.caption(f"{st.session_state.unknown_count} jobs without extracted skill evidence excluded from this recommendation list. This is evidence screening, not a finding that you are unqualified.")
    if not results: st.warning('No jobs meet the estimated salary-floor and skill-evidence requirements. No unverified jobs have been added to fill the list.')
    else:
        overview=pd.DataFrame([{'Job ID':r['job']['job_id'],'Job':r['job']['title'],'Company':r['job']['company'],'Score':round(r['score'],1),'Evidence weight':r['possible'],**r['scores'],'Matched skills':'; '.join(r['matched']),'Missing skills':'; '.join(r['missing'])} for r in results])
        summary=pd.DataFrame([{'Job':r['job']['title'],'Company':r['job']['company'],'Location':r['job']['location'],'Match (%)':round(r['score'],1),'Estimated annual salary':f"USD {r['job']['salary_min']:,.0f}–{r['job']['salary_max']:,.0f}"} for r in results])
        st.dataframe(summary,hide_index=True,use_container_width=True)
        with st.expander('Compare all scoring details'):
            st.dataframe(overview,hide_index=True,use_container_width=True)
        selected=st.selectbox('Inspect a recommendation',range(len(results)),format_func=lambda i:f"{i+1}. {results[i]['job']['title']}")
        r=results[selected]; j=r['job']
        left,right=st.columns([1,1.25])
        with left:
            with st.container(border=True):
                st.subheader('Match overview')
                a,b=st.columns(2)
                with a:
                    st.write('**'+j['title']+'**'); st.write(j['company'] if pd.notna(j['company']) else 'Company unknown'); st.write(j['location']); st.write(j['company_size'] if pd.notna(j['company_size']) else 'Size unknown')
                with b:
                    st.write('**'+(p['name'] or 'Candidate')+'**'); st.write(p['education'] or 'Education not supplied'); st.write(p['skills']); st.write(p['location'])
                salary_text=f"USD {j['salary_min']:,.0f}–{j['salary_max']:,.0f} / year (estimated)" if pd.notna(j['salary_min']) else 'Unknown'
                st.write('Estimated annual salary: '+salary_text)
                st.metric('Overall match · scored subtotal',f"{r['earned']:.1f} / {r['possible']}",f"{r['score']:.1f}% normalized",delta_color='off')
                for k,value in r['scores'].items():
                    w=p['weights'][k]
                    st.write(f"{k}: unknown" if value is None else f"{k}: {value*w/100:.1f} / {w} points ({value:.1f}/100)")
                    if value is not None: st.progress(value/100)
                st.caption('Unknown factors excluded from denominator. A high percentage with fewer scored points has less evidence.')
                st.caption('100% means the scored factors match; it is not a hiring probability. Education, seniority and experience are not scored.')
                st.caption('City scoring uses the dataset location field. No US or on-site requirement is enforced; review actual work arrangements in the description.')
        with right:
            with st.container(border=True):
                st.subheader('Why this job matches')
                evidence=[]
                audit_row=filter_audit[filter_audit.job_id==j['job_id']].iloc[0]
                evidence.append({'Type':'Mandatory estimated salary screen','Evidence':audit_row.evidence,'Source':'Dataset salary fields '+j['job_id']})
                for skill in r['matched']:
                    e=evidence_for(skill,st.session_state.result_docs)
                    evidence.append({'Type':'Candidate skill','Evidence':e['Evidence'] if e else skill+' — user-confirmed profile; no resume excerpt found','Source':e['Source'] if e else 'Reviewed profile'})
                for skill in r['matched']+r['missing']:
                    e=evidence_for(skill,[('Job description '+j['job_id'],j['description'])])
                    evidence.append({'Type':'Job skill mention','Evidence':e['Evidence'] if e else skill+' — extracted dataset field; verify description','Source':e['Source'] if e else 'Dataset skills field'})
                evidence.extend([{'Type':'Salary','Evidence':f"Job: {salary_text}; preference: ${p['salary']:,.0f}",'Source':'Dataset salary estimate + reviewed profile'}, {'Type':'Location','Evidence':f"Job: {j['location']}; preference: {p['location']}",'Source':'Dataset location + reviewed profile'}, {'Type':'Company size','Evidence':f"Job: {j['company_size'] if pd.notna(j['company_size']) else 'Unknown'}; preference: {p['size']}",'Source':'Dataset size + reviewed profile'}])
                st.dataframe(pd.DataFrame(evidence),hide_index=True,use_container_width=True)
            with st.container(border=True):
                st.subheader('Skills & gaps')
                st.write('**Matched:** '+(', '.join(r['matched']) or 'None'))
                st.write('**Skills not in reviewed profile:** '+(', '.join(r['missing']) or 'None among extracted skills'))
                st.write('**Unknown scoring fields:** '+(', '.join(k for k,v in r['scores'].items() if v is None) or 'None'))
                st.caption('Experience, remote/hybrid arrangement, sponsorship and current vacancy status are unverified. Skill mentions are not necessarily mandatory. PyTorch/TensorFlow can be extracted from resumes, but are absent from the current job skill dictionary.')
            with st.container(border=True):
                st.subheader('Your next step')
                action=st.radio('Next step',['Save for later','Review missing information','Adjust weights'],key='decision_'+j['job_id'])
                note=st.text_area('Your feedback',key='note_'+j['job_id'])
                if st.button('Confirm decision',key='confirm_'+j['job_id']):
                    st.session_state.setdefault('feedback',{})[j['job_id']]={'job_id':j['job_id'],'action':action,'note':note,'score':r['score'],'weights':p['weights']}
                    st.success('Recorded in this session. Adjust weights in the sidebar and search again if desired.')
                if st.session_state.get('feedback'):
                    st.download_button('Download decisions',json.dumps(list(st.session_state.feedback.values()),indent=2),'decisions.json','application/json')
        with st.expander('Original job description'): st.text(j['description'])
        st.download_button('Download Top 5',overview.to_csv(index=False).encode('utf-8-sig'),'recommendations.csv','text/csv')
