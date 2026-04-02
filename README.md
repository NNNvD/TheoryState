# TheoryState Streamlit Dashboard

This repository contains a starter Streamlit dashboard and a repeatable cleaning script for the annual theory survey.

## Files
- `scripts/clean_data.py` — filters respondents using the two QC checks and exports cleaned data
- `app.py` — starter Streamlit dashboard
- `data/raw/` — put the Microsoft Forms CSV here
- `data/derived/` — cleaned outputs written here

## First run
1. Copy the raw CSV export into `data/raw/`
2. Rename it to:
   `TheoryState (Responses) - Form Responses 1.csv`
3. Run:
   `python scripts/clean_data.py`
4. Start the app:
   `streamlit run app.py`

## What the cleaning script does
1. Keeps only rows where:
   - column AC / `6. For quality control, please check number 4.` = 4
   - column BO / `3. For quality control, please check number 2` = 2
2. Removes open-text comment columns
3. Exports:
   - `responses_dashboard_ready.csv` — keeps background variables for filtering
   - `responses_numeric_only.csv` — drops text fields and keeps only numeric responses

## Deploying from GitHub to Streamlit
Once the repo is on GitHub, Streamlit Community Cloud can deploy it by selecting your repository, branch, and entrypoint file (`app.py`). It also supports connecting directly to GitHub repositories and updating apps when the code changes. citeturn730827search0turn730827search6
