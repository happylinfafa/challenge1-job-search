# Explainable Job Match v5


## Run
Python 3.12:
```
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -v
python evaluate.py
```


Upload PDF (selectable text), DOCX or UTF-8 TXT up to 5 MB, or paste resume text. Review the extracted profile and enter preferences, then Search Jobs. Results include up to five jobs, component scores, original evidence, gaps and downloadable feedback. No API key, LLM, RAG or BM25 is used. Education/experience are not scored; 100% is not a qualification or hiring guarantee.


## v4 rules
The only business hard filter is estimated minimum annual salary >= USD 60,000 (inclusive). Unknown/invalid salary ranges or unconfirmed annual USD basis are excluded. Both annual and annual_assumed periods are accepted with the estimate/assumption disclosed. No US, on-site, remote or hybrid filter is applied. Unknown skill evidence is separately excluded from recommendations, as in v2.


Default weights: Skills 40%, Salary 30%, Company Size 20%, Location 10%. Weights are editable and must sum to 100. Skills score = matched extracted skill count / extracted skill count * 100. Salary score = 100 when the lower bound meets the USER expectation, 50 when only upper bound meets it, otherwise 0. City and size score = 100 for exact normalized match, otherwise 0. The fixed USD 60,000 floor does not change with the user's expectation. Earned points = sum(weight * score / 100). Unknown components are excluded from the denominator; normalized score = earned / available weights * 100. Sort descending by unrounded percentage, then available weight, then ascending job ID.


## Data and limitations
Source: https://www.kaggle.com/datasets/andrewmvd/data-analyst-jobs . 2,252 cleaned historical jobs, from 2,253 original rows after user removal of damaged title DA-01758. Descriptions, skill mentions, salary bounds, locations, employee bands and source IDs are included. Salary is Glassdoor estimated annual USD, not employer-guaranteed pay; annual period is an explicit assumption. Names/text were normalized, K salary ranges parsed, unknown markers preserved as missing, and skills extracted with a limited dictionary. No duplicate core rows found. No current vacancy status or application links are available. Resume skills can include PyTorch/TensorFlow but these are not added to the original job dictionary. Original descriptions and evidence excerpts allow review. No model or external AI service receives resumes; uploaded files reach the app server and are processed in memory/session without intentional disk persistence.


## Actual v4 evaluation
2,252 input records: 679 pass salary screening; 1,572 are below the floor; 1 have missing/unparseable salary. Further skill-evidence screening can reduce eligible recommendations. Three synthetic profiles and actual Top-5 outputs are included in this `job-search-app/` directory alongside `app.py`. See [profile_results.csv](profile_results.csv), [evaluation.json](evaluation.json), [filter_audit.csv](filter_audit.csv), [tests.txt](tests.txt) and [VERIFICATION.md](VERIFICATION.md). These are program results, not human relevance judgments. Matching-only timings exclude browser/network latency. Running `python evaluate.py` creates a `results/` subdirectory and writes new `filter_audit.csv`, `profile_results.csv` and `evaluation.json` files there. These generated files are separate from the saved results currently committed alongside `app.py`.


## Update deployment
Repository: https://github.com/happylinfafa/challenge1-job-search
Online app: https://happylinfafa-job-search.streamlit.app/
Upload this directory's CONTENTS into existing job-search-app, replacing prior files, including matching.py, eligibility.py, app.py, requirements.txt, README and tests/results. Do not nest job-search-v4 inside it. Entry point stays job-search-app/app.py. This package has not been pushed or deployed by the assistant. Old online versions may remain until updated. Previous v3 US/on-site rules and result counts no longer apply. The original CSV's information_coverage_pct was derived with old weights; app computes current coverage from scoring fields and does not use that column.


## Interface refresh (v5)
Removed the two prominent data/filter banners. Data limitations and salary screening remain available in “About the data & salary filter”. Added a compact shortlist, expandable scoring table, teal/navy styling and a clearer empty state. Scoring and filtering are unchanged.

