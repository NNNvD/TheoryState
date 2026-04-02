# AGENTS.md

## Purpose
Build and maintain an interactive Streamlit dashboard for the annual TheoryState survey.

The dashboard should:
- read Microsoft Forms CSV exports from `data/raw/`
- run a repeatable cleaning pipeline
- write cleaned files to `data/derived/`
- visualize aggregate results interactively
- be deployable from GitHub to Streamlit Community Cloud
- be easy to update each year with minimal manual work

## Repository scope
This file is intended for the entire repository.

## Current repository structure
- `app.py` — Streamlit entrypoint
- `scripts/clean_data.py` — cleaning pipeline
- `data/raw/` — raw Microsoft Forms CSV export(s); never modify raw files in place
- `data/derived/` — cleaned and derived files created by scripts
- `requirements.txt` — Python dependencies
- `README.md` — setup and deployment instructions

## Project goal
This dashboard is for a survey on perspectives about theory development in psychological science.
The first working version should prioritize:
1. reliability
2. transparency
3. easy yearly updates
4. useful exploratory filtering
5. clear public-facing presentation

Do not over-engineer the first version.

## High-level product requirements
Build a dashboard with the following pages or sections:

### 1. Overview
Show:
- total raw rows
- rows after QC filtering
- included responses shown in current view
- breakdowns for background variables that are retained
- clear note on inclusion criteria

### 2. Table 1 page
For Table 1 items, show at least:
- commonness in respondent's subfield
- commonness in psychological science in general
- harmfulness if present

Provide:
- item selector
- summary table with means, medians, standard deviations, and N
- at least one interactive plot
- filters by subfield and respondent background where available

### 3. Table 2 page
For Table 2 items, show at least:
- prevalence/commonness where available
- agreement that limited theory development contributes causally
- magnitude of the causal contribution

Provide:
- item selector
- summary table with means, medians, standard deviations, and N
- at least one interactive plot
- same filters as Table 1 where possible

### 4. Methods / data quality page
Document:
- the two QC filters
- how rows are excluded
- which columns are dropped
- which background variables are retained
- current limitations and assumptions

## Cleaning rules
These rules are mandatory unless the user explicitly changes them.

### Step 1: QC filtering
Keep only rows where:
- column AC (`6. For quality control, please check number 4.`) equals `4`
- column BO (`3. For quality control, please check number 2`) equals `2`

Use both the preferred column names and positional fallbacks.
Do not assume headers will always remain perfectly stable.

### Step 2: comment removal
Remove open-ended comment columns from the public dashboard dataset.
Typical comment columns contain phrases such as:
- `Optional comment`
- `Final comments`

### Step 3: preserve structured background variables
Do **not** drop useful structured background variables that support filtering, including when they are text-valued.
Retain, if present:
- timestamp
- work in psychological science
- highest education in psychology / psychological science
- current subfield
- other structured respondent background variables added later

### Step 4: create multiple outputs
The cleaning pipeline should produce at least:
- a **dashboard-ready** file that retains structured background fields and numeric response columns
- a **numeric-only** file for analysis scripts
- a **cleaning summary** file with row counts and output dimensions

### Step 5: keep raw data untouched
Never overwrite or mutate files in `data/raw/`.
All transformations must be written to `data/derived/`.

## Data model requirements
Refactor toward a cleaner data model if needed.
Preferred outputs:
- `responses_dashboard_ready.csv` — wide file for quick loading
- `responses_numeric_only.csv` — numeric-only wide file
- `responses_long.csv` — long-form item-response file for plotting
- `cleaning_summary.csv` — cleaning metadata
- `item_dictionary.csv` — stable mapping from raw column names to item IDs and response dimensions

If you add `responses_long.csv`, structure it with columns like:
- `respondent_id`
- `year`
- `item_id`
- `item_label`
- `table`
- `dimension`
- `response`
- retained background variables

## Item dictionary
Create and use an item dictionary instead of relying on raw Microsoft Forms question text throughout the app.

The item dictionary should provide, at minimum:
- stable `item_id`
- short item label
- full core claim
- table number (`1` or `2`)
- dimension label
- raw source column name

This is important because:
- survey wording may change slightly in future years
- raw Microsoft Forms headers are long and fragile
- yearly comparisons require stable item identities

## UX requirements
The public dashboard should be readable by non-technical users.

### Design principles
- clear page titles
- concise explanatory text
- default views that work without any filter changes
- avoid overwhelming the user with raw column names
- avoid exposing internal cleaning artifacts unless useful

### Filters
Use a left sidebar for filters such as:
- subfield
- work status / eligibility variables if retained
- education level if retained
- year, once multiple waves exist

### Metrics and summaries
For each item or item set, prefer:
- mean
- median
- standard deviation
- N
- response distribution

### Comments
Do not display raw free-text comments in the first public dashboard unless the user explicitly asks for that and comment review/redaction has been addressed.

## Recommended technical choices
- Use `pandas` for cleaning and reshaping.
- Use `plotly` for interactive plots unless there is a strong reason to use another library.
- Keep the app as a single `app.py` only if it remains manageable; otherwise split into small modules under an `app/` package.
- Prefer explicit helper functions over long monolithic scripts.

## Code quality expectations
- Write readable, well-named functions.
- Add docstrings to non-trivial functions.
- Avoid hard-coding fragile assumptions when a small abstraction will do.
- Handle missing columns gracefully.
- Fail with informative error messages.
- Keep dependencies light.

## Backward compatibility
When improving the pipeline:
- do not break the current starter workflow
- keep `python scripts/clean_data.py` working
- keep `streamlit run app.py` working
- preserve existing output filenames unless there is a good reason to change them

If you add new outputs, document them in `README.md`.

## Deployment requirements
The app must remain deployable from GitHub to Streamlit Community Cloud.
Assume the entrypoint remains `app.py` unless the user requests a different structure.
Update `requirements.txt` if you add dependencies.

## Validation and checks
Before finishing:
1. run the cleaning script
2. run the Streamlit app entrypoint or otherwise verify it imports correctly
3. ensure required derived files are created
4. ensure there are no obvious tracebacks from basic execution
5. update `README.md` if setup or outputs changed

If you add automated checks or tests, run them as well.

## Suggested build order
When asked to extend the dashboard, proceed roughly in this order unless the user asks otherwise:
1. stabilize the cleaning pipeline
2. add an item dictionary
3. create a long-format dataset
4. improve the dashboard overview
5. build Table 1 page
6. build Table 2 page
7. add methods/data-quality page
8. add year-over-year support

## What to avoid
- Do not delete raw data.
- Do not remove structured background variables just because they are text-valued.
- Do not expose raw comments publicly by default.
- Do not hard-code logic so tightly to one year's exact column wording that next year's import breaks.
- Do not optimize for visual polish at the expense of data transparency.

## Preferred first deliverable
A solid first deliverable includes:
- improved cleaning script
- item dictionary
- long-format output
- sidebar filters
- overview metrics
- usable Table 1 and Table 2 views
- updated README with run/deploy instructions

## When uncertain
If something in the raw export is ambiguous:
- prefer explicit assumptions
- document those assumptions in code comments and the README
- do not silently discard potentially useful structured variables
