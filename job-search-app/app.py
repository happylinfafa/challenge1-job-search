from pathlib import Path
import json
import pandas as pd
import streamlit as st
from matching import rank_jobs, parse_skills
from resume import read_document, extract, evidence_for

st.set_page_config(page_title='Explainable Job Match',page_icon='🔎',layout='wide')
st.markdown('<style>.stApp{background:#f6f8fc}h1,h2,h3{color:#183653} [data-testid="stMetric"]{background:#eef5fa;padding:12px;border-radius:10px}</style>',unsafe_allow_html=True)
@st.cache_data
def load():
    return pd.read_csv(Path(__file__).parent/'data/jobs.csv')
jobs=load()
vocab=sorted({s.strip() for x in jobs.skills.dropna() for s in x.split(';')}|{'PyTorch','TensorFlow'})
st.title('Explainable Job Match')
st.caption('Resume → Review profile → Weighted matching → Evidence → Human decision')
st.info('2,252 historical jobs · Estimated annual USD salaries · Scores describe available evidence, not hiring probability.')
for key,value in {'skills':'','education':'','location':'','candidate':'Candidate','documents':[]}.items():
    st.session_state.setdefault(key,value)
with st.expander('1 · Upload resume and extract profile',expanded=True):
    st.caption('PDF with selectable text, DOCX, or UTF-8 TXT; maximum 5 MB. Processed in this session without an external AI API or intentional disk storage. Scanned PDFs require text/OCR first.')
    upload=st.file_uploader('Resume',type=['pdf','docx','txt'])
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
    st.header('2 · Review your profile')
    with st.form('profile_form'):
        name=st.text_input('Display name (optional)',key='candidate')
        education=st.text_input('Education (review extracted text)',key='education')
        skills=st.text_input('Skills, separated by commas',key='skills')
        location=st.text_input('Preferred city, state',key='location')
        salary=st.number_input('Minimum expected salary (USD/year)',min_value=0,value=80000,step=5000)
        sizes=sorted(jobs.company_size.dropna().unique(),key=lambda s:int(s.split()[0].replace('+','')))
        size=st.selectbox('Company size',sizes)
        st.caption('Education is contextual only. Weights retain your four original factors.')
        weights={k:st.number_input(f'{k} weight (%)',0,100,v,5) for k,v in [('Skills',50),('Salary',20),('Location',20),('Size',10)]}
        search=st.form_submit_button('Search Jobs',type='primary')
    st.caption('City and size are scoring preferences. Remote/hybrid eligibility, experience and sponsorship are not inferred.')
if search:
    if not parse_skills(skills) or not location.strip(): st.error('Provide skills and a preferred location.')
    elif sum(weights.values())!=100: st.error('Weights must total 100%.')
    else:
        results=rank_jobs(jobs,skills,location,salary,size)
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
    st.write('Upload a resume or enter a profile, review the fields, then select Search Jobs.')
else:
    results=st.session_state.results; p=st.session_state.profile
    st.subheader('3 · Top 5 recommendations')
    st.caption(f"{st.session_state.unknown_count} jobs without extracted skill evidence excluded from this recommendation list. This is evidence screening, not a finding that you are unqualified.")
    if not results: st.warning('No jobs with skill evidence available.')
    else:
        overview=pd.DataFrame([{'Job':r['job']['title'],'Company':r['job']['company'],'Score':round(r['score'],1),'Evidence weight':r['possible']} for r in results])
        st.dataframe(overview,hide_index=True,use_container_width=True)
        selected=st.selectbox('Inspect a recommendation',range(len(results)),format_func=lambda i:f"{i+1}. {results[i]['job']['title']}")
        r=results[selected]; j=r['job']
        left,right=st.columns([1,1.25])
        with left:
            with st.container(border=True):
                st.subheader('Job & Candidate')
                a,b=st.columns(2)
                with a:
                    st.write('**'+j['title']+'**'); st.write(j['company'] if pd.notna(j['company']) else 'Company unknown'); st.write(j['location']); st.write(j['company_size'] if pd.notna(j['company_size']) else 'Size unknown')
                with b:
                    st.write('**'+(p['name'] or 'Candidate')+'**'); st.write(p['education'] or 'Education not supplied'); st.write(p['skills']); st.write(p['location'])
                salary_text=f"${j['salary_min']:,.0f}–${j['salary_max']:,.0f}" if pd.notna(j['salary_min']) else 'Unknown'
                st.write('Estimated annual salary: '+salary_text)
                st.metric('Overall match · scored subtotal',f"{r['earned']:.1f} / {r['possible']}",f"{r['score']:.1f}% normalized",delta_color='off')
                for k,value in r['scores'].items():
                    w=p['weights'][k]
                    st.write(f"{k}: unknown" if value is None else f"{k}: {value*w/100:.1f} / {w} points ({value:.1f}/100)")
                    if value is not None: st.progress(value/100)
                st.caption('Unknown factors excluded from denominator. A high percentage with fewer scored points has less evidence.')
        with right:
            with st.container(border=True):
                st.subheader('Evidence retrieved')
                evidence=[]
                for skill in r['matched']:
                    e=evidence_for(skill,st.session_state.result_docs)
                    evidence.append({'Type':'Candidate skill','Evidence':e['Evidence'] if e else skill+' — user-confirmed profile; no resume excerpt found','Source':e['Source'] if e else 'Reviewed profile'})
                for skill in r['matched']+r['missing']:
                    e=evidence_for(skill,[('Job description '+j['job_id'],j['description'])])
                    evidence.append({'Type':'Job skill mention','Evidence':e['Evidence'] if e else skill+' — extracted dataset field; verify description','Source':e['Source'] if e else 'Dataset skills field'})
                evidence.extend([{'Type':'Salary','Evidence':f"Job: {salary_text}; preference: ${p['salary']:,.0f}",'Source':'Dataset salary estimate + reviewed profile'}, {'Type':'Location','Evidence':f"Job: {j['location']}; preference: {p['location']}",'Source':'Dataset location + reviewed profile'}, {'Type':'Company size','Evidence':f"Job: {j['company_size'] if pd.notna(j['company_size']) else 'Unknown'}; preference: {p['size']}",'Source':'Dataset size + reviewed profile'}])
                st.dataframe(pd.DataFrame(evidence),hide_index=True,use_container_width=True)
            with st.container(border=True):
                st.subheader('Gaps / unknowns')
                st.write('**Matched:** '+(', '.join(r['matched']) or 'None'))
                st.write('**Skills not in reviewed profile:** '+(', '.join(r['missing']) or 'None among extracted skills'))
                st.write('**Unknown scoring fields:** '+(', '.join(k for k,v in r['scores'].items() if v is None) or 'None'))
                st.caption('Experience, remote/hybrid arrangement, sponsorship and current vacancy status are unverified. Skill mentions are not necessarily mandatory. PyTorch/TensorFlow can be extracted from resumes, but are absent from the current job skill dictionary.')
            with st.container(border=True):
                st.subheader('Human decision')
                action=st.radio('Next step',['Save for later','Review missing information','Adjust weights'],key='decision_'+j['job_id'])
                note=st.text_area('Your feedback',key='note_'+j['job_id'])
                if st.button('Confirm decision',key='confirm_'+j['job_id']):
                    st.session_state.setdefault('feedback',{})[j['job_id']]={'job_id':j['job_id'],'action':action,'note':note,'score':r['score'],'weights':p['weights']}
                    st.success('Recorded in this session. Adjust weights in the sidebar and search again if desired.')
                if st.session_state.get('feedback'):
                    st.download_button('Download decisions',json.dumps(list(st.session_state.feedback.values()),indent=2),'decisions.json','application/json')
        with st.expander('Original job description'): st.text(j['description'])
        st.download_button('Download Top 5',overview.to_csv(index=False).encode('utf-8-sig'),'recommendations.csv','text/csv')
