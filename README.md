# Theory-in-Psychology Sentiment Survey (SurveyJS + GitHub Pages + Google Sheets)

This repo is a static SurveyJS survey (GitHub Pages) that writes responses to a Google Sheet via a Google Apps Script Web App.

## 1) Create the Google Sheet
1. Create a new Google Sheet (any name).
2. Copy the Sheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/<THIS_PART_IS_THE_ID>/edit`

(Optional) Create a tab named `responses` (the script will create it if missing).

## 2) Deploy the Apps Script Web App
1. In your Sheet: **Extensions → Apps Script**
2. Paste `apps_script/Code.gs` into the editor (or copy/paste its contents).
3. Set:
   - `SPREADSHEET_ID`
   - `SHEET_NAME` (default: `responses`)
4. Click **Deploy → New deployment**
   - Select type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Copy the Web app URL (it will look like `https://script.google.com/macros/s/.../exec`)

## 3) Configure the survey frontend
1. Open `app.js`
2. Set:
   - `APPS_SCRIPT_WEBAPP_URL` to the Web app URL you copied
   - `SURVEY_YEAR` and `INSTRUMENT_VERSION` (optional)

## 4) Publish on GitHub Pages
1. Create a new GitHub repo and upload these files.
2. In repo settings: **Pages**
   - Source: `Deploy from a branch`
   - Branch: `main` (or `master`)
   - Folder: `/ (root)`
3. Your survey will be available at the GitHub Pages URL.

## 5) Annual rollover (minimal)
- Update `SURVEY_YEAR` and `INSTRUMENT_VERSION` in `app.js`, commit, and redeploy (GitHub Pages updates automatically).
- If you edit the item wording, update `items.json`. Try to keep the `slug` stable for longitudinal comparability.

## Files
- `index.html`: static page shell
- `app.js`: loads `items.json`, builds the survey, submits to Apps Script
- `items.json`: item bank (Table 1 + Table 2)
- `apps_script/Code.gs`: Apps Script backend (paste into Apps Script editor)
