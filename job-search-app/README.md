# Career Match — Job Search Application

Streamlit application for 2,252 historical data analyst jobs. Enter skills, company size, location and expected minimum annual salary. Select Search Jobs to see the Top 5, component scores and skill gaps.

## Run locally

Use Python 3.10 or newer. Open a terminal in this folder:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501). The bundled CSV is loaded automatically. No API key required.

## Matching method

Skills 50%, Salary 20%, Location 20%, Company Size 10%. Each component is 0–100.

- Skills: proportion of listed skills found in the user's comma-separated list, with case and selected aliases normalized. Additional user skills do not reduce the score.
- Salary: 100 if the lower estimate meets the expectation; 50 if only the upper estimate does; otherwise 0.
- Location: exact location after case, whitespace and comma normalization. Remote is not inferred from job descriptions. All location preferences are soft preferences.
- Size: 100 if the selected employee band matches, otherwise 0.
- Unknown components are excluded and weights renormalized. Information coverage shows the sum of known weights. Low-coverage jobs can score highly, so the interface warns about incomplete evidence.
- Sort by unrounded total descending, coverage descending, then job ID ascending. Display scores rounded to one decimal. Scores are not hiring probabilities.

The sidebar uses a form: edited inputs take effect only after Search Jobs. A result caption identifies the submitted query. Blank skills/location produce a validation error. Results can be downloaded as CSV.

## Data provenance and limits

Source: [Kaggle Data Analyst Jobs](https://www.kaggle.com/datasets/andrewmvd/data-analyst-jobs), user-supplied cleaned snapshot. Original 2,253 records; the user removed DA-01758 after its title became a spreadsheet error, leaving 2,252. IDs are preserved. Data contains source row IDs, original descriptions, derived skill mentions, estimated salary bounds, locations and company employee bands. No current vacancy status or application URLs are available.

Salary is Glassdoor estimated compensation, interpreted as annual USD (the period is marked annual_assumed). Skills come from a limited dictionary, not an exhaustive mandatory-requirements model. In particular PyTorch is not in the existing extraction dictionary and will not earn skill credit. Unknown fields remain unknown. This version does not use embeddings, an LLM, RAG or live job APIs. Personal inputs are used in the current Streamlit session; there is no application database storing user profiles.

## Tests

```sh
python -m unittest discover -v
```

Tests cover a manually calculated 77.5 score, missing-field renormalization, missing skills, location matching, salary boundaries and stable ordering. Data and matching code can be used for later retrieval-method comparisons; no relevance improvements are claimed without evaluation.

## Files

- app.py: UI
- matching.py: scoring
- test_matching.py: automated checks
- data/jobs.csv: selected dataset
- requirements.txt: runtime dependencies

Streamlit runs as a web server; a Colab notebook alone does not expose its port as a public website. Local execution is the documented route for this version. Hosting/GitHub publication has not been performed.
