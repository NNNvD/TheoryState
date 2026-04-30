# TheoryState Streamlit Dashboard

This repository contains a Streamlit dashboard and a repeatable cleaning pipeline for the annual TheoryState survey on theory development in psychological science.

## Project structure
- `app.py` — Streamlit dashboard entrypoint
- `scripts/clean_data.py` — cleaning pipeline and derived data generation
- `data/raw/` — raw Microsoft Forms exports (never modify in place)
- `data/derived/` — generated outputs for dashboard + analysis
- `.github/workflows/clean-data.yml` — GitHub Actions workflow to run cleaning automatically
- `.github/workflows/pages.yml` — GitHub Pages deployment workflow for `docs/`
- `docs/index.html` — GitHub Pages wrapper that embeds the deployed Streamlit app
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

## Automating data cleaning (GitHub Actions)
A workflow is included at `.github/workflows/clean-data.yml`.

It runs automatically when:
- files under `data/raw/` change, or
- `scripts/clean_data.py` changes.

You can also run it manually from the Actions tab (`workflow_dispatch`).

The job:
1. installs dependencies,
2. runs `python scripts/clean_data.py`,
3. uploads `data/derived/` as an Actions artifact (`derived-data`).

## Showing the dashboard on GitHub Pages
GitHub Pages cannot run Streamlit server code directly. Instead:

1. Deploy the dashboard to **Streamlit Community Cloud** (or another Streamlit host).
2. Set the hosted app URLs in `docs/index.html` (`DASHBOARD_URL` and `SHARE_URL_FALLBACK`).
3. Enable Pages in GitHub repo settings (source: GitHub Actions).
4. Push to `main` (or `work`) to trigger `.github/workflows/pages.yml`.

The root Pages URL now opens `docs/index.html` (dashboard launcher). The launcher opens the Streamlit app URL in a new tab to avoid iframe/redirect issues.

## Deployment
### Streamlit Community Cloud
Deploy with:
- repository: this GitHub repo
- branch: your target branch
- entrypoint: `app.py`

### GitHub Pages
After enabling Pages, the `pages.yml` workflow publishes `docs/` so the repo website redirects visitors to the dashboard launcher page.


### Streamlit access errors (`share.streamlit.io/errors/not_found`)
If you see “You do not have access to this app or it does not exist”, verify all of the following:
- The app is deployed on Streamlit Community Cloud and has a valid URL like `https://<app-name>.streamlit.app/`.
- In **App settings → Sharing**, set visibility to **Public** (or grant explicit access to your account).
- `DASHBOARD_URL` in `docs/index.html` matches the deployed app URL exactly.
- If the custom URL is still propagating, try the fallback share URL format: `https://share.streamlit.io/<github-user>/<repo>/<branch>/app.py`.
- If ownership changed, reconnect the correct GitHub account in Streamlit Cloud settings.

### If Pages still shows README instead of dashboard
- In repo **Settings → Pages**, either:
  - set source to **GitHub Actions** (recommended), or
  - set source to **Deploy from a branch** and folder **/(root)** (this repo now includes a root `index.html` redirect).
- Ensure the Pages URL opens `/index.html` and not a cached README view.

## Public launch checklist (recommended before announcement)
Before sharing broadly, verify:
- the Streamlit app URL is live and public
- `python scripts/clean_data.py` completes without errors
- `data/derived/` files are refreshed from the latest `data/raw/` export
- dashboard filters render with realistic defaults (no empty starting views)
- Methods / Data Quality section still matches the current cleaning script
- README links (repo, app URL, Pages URL) all work in an incognito window

## Sharing the dashboard
Use these links in announcements:
- **Primary app URL**: your deployed `https://<app-name>.streamlit.app/`
- **Project repository**: this GitHub repo (methods + reproducible pipeline)
- **Optional landing page**: GitHub Pages launcher URL from `docs/index.html`

Suggested one-line description:
> “TheoryState is an interactive dashboard summarizing survey responses about theory development in psychological science, with a transparent reproducible cleaning pipeline.”

## Updating for a new wave/year
1. Add the new Microsoft Forms CSV export to `data/raw/`.
2. Run:
   ```bash
   python scripts/clean_data.py
   ```
3. Confirm updated outputs in `data/derived/`:
   - `responses_dashboard_ready.csv`
   - `responses_numeric_only.csv`
   - `responses_long.csv`
   - `item_dictionary.csv`
   - `cleaning_summary.csv`
4. Launch locally:
   ```bash
   streamlit run app.py
   ```
5. Spot-check Overview, Table 1, Table 2, and Methods pages.
6. Commit the refreshed derived files plus any code/docs changes.

## Recommended repository additions (optional but high-value)
To make the project easier for outside users:
- `LICENSE` (clear reuse terms)
- `CONTRIBUTING.md` (how to propose fixes/updates)
- `CHANGELOG.md` (track data and app changes over time)
- `CITATION.cff` (how to cite the dashboard/pipeline)

These are not required for functionality, but they improve trust and maintainability for a public launch.

