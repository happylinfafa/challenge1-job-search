# Explainable Job Match — Resume edition

Run with Python 3.12:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Upload a selectable-text PDF, DOCX, UTF-8 TXT, or paste resume text. Click Extract profile, review suggested education/location/skills, manually supply preferences, then Search Jobs. Select one of the Top 5 to inspect the job/candidate comparison, earned/possible points, source excerpts, gaps and human decision controls. Feedback is kept in the current session and can be exported as JSON; it does not train a model or submit an application.

This layout follows the teacher's provided Explainable Job Match example. The student's original weights remain Skills 50%, Salary 20%, Location 20%, Company Size 10%; editable weights must total 100. Education is not scored. Skills are matched by the existing keyword rules; salary scores are 100/50/0 for lower-bound/upper-bound/no satisfaction. Location and size are exact-match preferences. Unknown components are excluded from the denominator. Unlike version 1, jobs with unknown skill evidence are excluded from main recommendations to prevent unsupported high scores. This exclusion is stated in the UI. There are no hard location or salary filters in this version.

Resume parsing is deterministic and conservative, not an LLM, full RAG, OCR or semantic search. It extracts candidate education and city suggestions, not verified qualifications; the user must review them. Names are optional manual input. Experience duration is not inferred. Resume skills use the dataset vocabulary plus PyTorch/TensorFlow; the job dataset itself is unchanged, so skills absent from job extraction cannot earn points. Source excerpts are actual resume/page or job-description snippets; manual additions are labeled as reviewed profile information. No external sources are fabricated.

Files are parsed in server memory/session without intentional resume persistence, caching or third-party model calls. In a cloud deployment uploads reach that server. Resume snippets appear in the current user's results. Do not include unnecessary sensitive information. Session reset discards state; exported decisions may contain the user's notes.

Data: 2,252 user-selected historical records from https://www.kaggle.com/datasets/andrewmvd/data-analyst-jobs . The original data had 2,253 rows; DA-01758 was removed by the user after spreadsheet title corruption. Salary is an estimated annual-USD interpretation, not guaranteed compensation. Vacancy dates, apply URLs, remote/hybrid eligibility, sponsorship and experience qualification are unverified. Existing cleaned data includes unknown values and a limited mentioned-skill dictionary. A displayed gap means a skill is absent from the reviewed profile, not proof the person lacks it.

## Update existing GitHub deployment

Replace app.py and requirements.txt in the existing job-search-app directory; add resume.py. matching.py and data/jobs.csv retain the original method/data. Keep Community Cloud entrypoint job-search-app/app.py and Python 3.12. Commit the files; the host should rebuild from the connected branch. This delivery does not itself modify GitHub or the hosted application.
