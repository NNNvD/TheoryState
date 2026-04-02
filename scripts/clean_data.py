from pathlib import Path
import pandas as pd

RAW_FILE = Path("data/raw/TheoryState (Responses) - Form Responses 1.csv")
DERIVED_DIR = Path("data/derived")

QC_COL_1_NAME = "6. For quality control, please check number 4. "
QC_COL_2_NAME = "3. For quality control, please check number 2"

# Fallback to spreadsheet positions if headers ever change:
# AC = 29th column -> zero-based index 28
# BO = 67th column -> zero-based index 66
QC_COL_1_INDEX = 28
QC_COL_2_INDEX = 66

STRUCTURED_TEXT_COLS = [
    "Timestamp",
    "Do you currently work as a psychological scientist (i.e., conduct psychological research or teach psychology/psychological science at a university or research institute)? ",
    "What is your highest completed university-level education in psychology/psychological science? ",
    "Which option best describes the subfield you currently work in most of the time?",
]

def get_qc_column(df: pd.DataFrame, preferred_name: str, fallback_index: int) -> str:
    if preferred_name in df.columns:
        return preferred_name
    return df.columns[fallback_index]

def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_FILE, low_memory=False)

    qc1 = get_qc_column(df, QC_COL_1_NAME, QC_COL_1_INDEX)
    qc2 = get_qc_column(df, QC_COL_2_NAME, QC_COL_2_INDEX)

    filtered = df[
        (pd.to_numeric(df[qc1], errors="coerce") == 4) &
        (pd.to_numeric(df[qc2], errors="coerce") == 2)
    ].copy()

    comment_cols = [
        c for c in filtered.columns
        if "Optional comment" in c or "Final comments" in c
    ]

    # Dashboard-ready file:
    # keep structured background variables for filtering, drop open-text comments and QC checks
    dashboard = filtered.drop(columns=comment_cols + [qc1, qc2], errors="ignore").copy()
    dashboard.to_csv(DERIVED_DIR / "responses_dashboard_ready.csv", index=False)

    # Numeric-only file:
    # drop all text fields and comments, then coerce the rest to numeric
    numeric = filtered.drop(columns=comment_cols + STRUCTURED_TEXT_COLS, errors="ignore").copy()
    for col in numeric.columns:
        numeric[col] = pd.to_numeric(numeric[col], errors="coerce")
    numeric = numeric.dropna(axis=1, how="all")
    numeric.to_csv(DERIVED_DIR / "responses_numeric_only.csv", index=False)

    summary = pd.DataFrame({
        "metric": ["raw_rows", "rows_after_qc", "dashboard_columns", "numeric_columns"],
        "value": [len(df), len(filtered), dashboard.shape[1], numeric.shape[1]],
    })
    summary.to_csv(DERIVED_DIR / "cleaning_summary.csv", index=False)

    print(f"Raw rows: {len(df)}")
    print(f"Rows after QC filter: {len(filtered)}")
    print(f"Dashboard-ready file: {DERIVED_DIR / 'responses_dashboard_ready.csv'}")
    print(f"Numeric-only file: {DERIVED_DIR / 'responses_numeric_only.csv'}")

if __name__ == "__main__":
    main()
