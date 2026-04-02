# TheoryState Streamlit Dashboard

This repository contains a Streamlit dashboard and a repeatable cleaning pipeline for the annual TheoryState survey on theory development in psychological science.

## Project structure
- `app.py` — Streamlit dashboard entrypoint
- `scripts/clean_data.py` — cleaning pipeline and derived data generation
- `data/raw/` — raw Microsoft Forms exports (never modify in place)
- `data/derived/` — generated outputs for dashboard + analysis
- `requirements.txt` — Python dependencies

## First run
1. Place a Microsoft Forms CSV export in `data/raw/`.
2. (Recommended) use the default filename:
   `TheoryState (Responses) - Form Responses 1.csv`
3. Run the cleaning pipeline:
   ```bash
   python scripts/clean_data.py
   ```
4. Start the dashboard:
   ```bash
   streamlit run app.py
   ```

## Cleaning rules implemented
1. **QC filtering**
   - Keep rows where AC / `6. For quality control, please check number 4.` equals `4`
   - Keep rows where BO / `3. For quality control, please check number 2` equals `2`
   - Uses preferred header names with positional fallbacks.
2. **Comment removal**
   - Drops open-ended columns matching patterns like `Optional comment` and `Final comments`.
3. **Structured background retention**
   - Keeps timestamp, work status, education, subfield, and similar structured fields for filtering.
4. **Multiple outputs**
   - Writes dashboard-ready, numeric-only, long-form, item dictionary, and summary outputs.
5. **Raw data safety**
   - Never writes to or mutates files in `data/raw/`.

## Derived outputs
Running `python scripts/clean_data.py` generates:

- `data/derived/responses_dashboard_ready.csv` — wide dataset for app loading
- `data/derived/responses_numeric_only.csv` — numeric-only wide dataset
- `data/derived/responses_long.csv` — long item-response dataset for plotting/filtering
- `data/derived/item_dictionary.csv` — stable item mapping from raw columns to item metadata
- `data/derived/cleaning_summary.csv` — row counts and output dimensions

## Dashboard sections
The dashboard includes:
- **Overview**: raw rows, rows after QC, rows in current filtered view, and background breakdowns
- **Table 1**: item selector, mean/median/SD/N table, and interactive distribution plot
- **Table 2**: item selector, mean/median/SD/N table, and interactive distribution plot
- **Methods / Data Quality**: QC logic, exclusions, retained variables, outputs, assumptions

## Deployment
Deploy on Streamlit Community Cloud with:
- repository: this GitHub repo
- branch: your target branch
- entrypoint: `app.py`
