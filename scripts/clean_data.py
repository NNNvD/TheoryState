"""Data cleaning pipeline for TheoryState survey exports.

This script prefers raw Microsoft Forms exports from ``data/raw/`` and writes
cleaned outputs to ``data/derived/``.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import pandas as pd

DERIVED_DIR = Path("data/derived")
RAW_DIR = Path("data/raw")
DEFAULT_RAW_FILE = RAW_DIR / "TheoryState (Responses) - Form Responses 1.csv"

QC_COL_1_NAME = "6. For quality control, please check number 4. "
QC_COL_2_NAME = "3. For quality control, please check number 2"

# Fallback to spreadsheet positions if headers ever change:
# AC = 29th column -> zero-based index 28
# BO = 67th column -> zero-based index 66
QC_COL_1_INDEX = 28
QC_COL_2_INDEX = 66

BACKGROUND_HINTS = (
    "timestamp",
    "work as a psychological scientist",
    "highest completed university-level education",
    "subfield you currently work",
)
COMMENT_HINTS = ("Optional comment", "Final comments")
WORK_STATUS_HINT = "do you currently work as a psychological scientist"
ALLOWED_WORK_STATUS_VALUES = {"Yes, primarily", "Yes, partly", "No"}
SUBFIELD_HINT = "which option best describes the subfield you currently work in most of the time?"
SUBFIELD_CANONICAL_MAP = {
    "defelopmental psychology": "Developmental psychology",
    "developmental psychology": "Developmental psychology",
    "evolutionary psychology": "Evolutionary Psychology",
}

RESPONSE_DIMENSION_PATTERNS = {
    "common_subfield": "How common is this phenomenon in your subfield today?",
    "common_general": "How common is this phenomenon in psychological science in general today?",
    "harmfulness": "If this occurs, how harmful is this phenomenon for psychological science?",
    "causal_agreement": "To what extent do you agree that insufficient theory development contributes to this phenomenon?",
    "causal_magnitude": "Assuming this phenomenon occurs, how large is the causal contribution of insufficient theory development?",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def find_raw_file() -> Path | None:
    """Return the preferred raw export path if present, otherwise first CSV in data/raw."""
    if DEFAULT_RAW_FILE.exists():
        return DEFAULT_RAW_FILE
    if RAW_DIR.exists():
        candidates = sorted(RAW_DIR.glob("*.csv"))
        if candidates:
            return candidates[0]
    return None


def get_qc_column(df: pd.DataFrame, preferred_name: str, fallback_index: int) -> str:
    """Get QC column by name, then by positional fallback."""
    if preferred_name in df.columns:
        return preferred_name
    if fallback_index < len(df.columns):
        return df.columns[fallback_index]
    raise KeyError(
        f"Could not locate QC column '{preferred_name}' and fallback index {fallback_index} is out of range."
    )


def infer_background_columns(columns: Iterable[str]) -> list[str]:
    """Infer structured background columns for filtering support."""
    inferred: list[str] = []
    for col in columns:
        n = _normalize(col)
        if any(hint in n for hint in BACKGROUND_HINTS):
            inferred.append(col)
    return inferred


def infer_comment_columns(columns: Iterable[str]) -> list[str]:
    """Identify free-text comments to remove from public dashboard outputs."""
    return [c for c in columns if any(h in c for h in COMMENT_HINTS)]


def recode_work_status_column(df: pd.DataFrame) -> pd.DataFrame:
    """Constrain work-status values to allowed categories, recoding others to 'No'."""
    work_col = next(
        (col for col in df.columns if WORK_STATUS_HINT in _normalize(col)),
        None,
    )
    if work_col is None:
        return df

    recoded = df.copy()
    cleaned_values = recoded[work_col].astype(str).str.strip()
    recoded[work_col] = cleaned_values.where(cleaned_values.isin(ALLOWED_WORK_STATUS_VALUES), "No")
    return recoded


def recode_subfield_column(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse known subfield duplicates/typos to canonical labels."""
    subfield_col = next(
        (col for col in df.columns if SUBFIELD_HINT in _normalize(col)),
        None,
    )
    if subfield_col is None:
        return df

    recoded = df.copy()
    cleaned_values = recoded[subfield_col].astype(str).str.strip()
    canonicalized = cleaned_values.map(lambda v: SUBFIELD_CANONICAL_MAP.get(_normalize(v), v))
    recoded[subfield_col] = canonicalized
    return recoded


def build_item_dictionary(df: pd.DataFrame, background_cols: list[str]) -> pd.DataFrame:
    """Create a stable item dictionary from survey response columns."""
    rows: list[dict] = []
    response_cols = [c for c in df.columns if c not in background_cols]

    for col in response_cols:
        item_match = re.match(r"\s*(\d+)\.\s*(.*)", str(col))
        if not item_match:
            continue

        item_num = int(item_match.group(1))
        core = item_match.group(2).strip()
        normalized_core = _normalize(core)

        dimension = "unknown"
        dimension_label = "Unknown"
        for dim_key, phrase in RESPONSE_DIMENSION_PATTERNS.items():
            if _normalize(phrase) in normalized_core:
                dimension = dim_key
                dimension_label = phrase
                break

        table = 1 if dimension in {"common_subfield", "common_general", "harmfulness"} else 2

        rows.append(
            {
                "item_id": f"item_{item_num:02d}",
                "item_number": item_num,
                "item_label": f"Item {item_num}",
                "core_claim": f"Phenomenon {item_num}",
                "table": table,
                "dimension": dimension,
                "dimension_label": dimension_label,
                "raw_source_column": col,
            }
        )

    item_dictionary = pd.DataFrame(rows).drop_duplicates(subset=["raw_source_column"])
    item_dictionary = item_dictionary.sort_values(["item_number", "dimension"]).reset_index(drop=True)
    return item_dictionary


def build_long_responses(
    dashboard_df: pd.DataFrame,
    item_dictionary: pd.DataFrame,
    background_cols: list[str],
) -> pd.DataFrame:
    """Build long-form response table suitable for filtering and plotting."""
    long_df = dashboard_df.copy().reset_index(drop=True)
    long_df.insert(0, "respondent_id", long_df.index + 1)

    id_vars = ["respondent_id", *background_cols]
    response_cols = item_dictionary["raw_source_column"].tolist()

    long_df = long_df.melt(
        id_vars=id_vars,
        value_vars=[c for c in response_cols if c in long_df.columns],
        var_name="raw_source_column",
        value_name="response",
    )

    long_df["response"] = pd.to_numeric(long_df["response"], errors="coerce")
    long_df = long_df.merge(item_dictionary, on="raw_source_column", how="left")
    long_df["year"] = pd.to_datetime(long_df.get("Timestamp"), errors="coerce").dt.year

    ordered_cols = [
        "respondent_id",
        "year",
        "item_id",
        "item_label",
        "table",
        "dimension",
        "dimension_label",
        "response",
        *background_cols,
        "raw_source_column",
    ]
    keep_cols = [c for c in ordered_cols if c in long_df.columns]
    return long_df[keep_cols]


def main() -> None:
    """Run the TheoryState cleaning pipeline and write all derived outputs."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    raw_file = find_raw_file()
    source = "raw"
    if raw_file is not None:
        df = pd.read_csv(raw_file, low_memory=False)
        qc1 = get_qc_column(df, QC_COL_1_NAME, QC_COL_1_INDEX)
        qc2 = get_qc_column(df, QC_COL_2_NAME, QC_COL_2_INDEX)
        filtered = df[(pd.to_numeric(df[qc1], errors="coerce") == 4) & (pd.to_numeric(df[qc2], errors="coerce") == 2)].copy()
        filtered = filtered.drop(columns=[qc1, qc2], errors="ignore")
        raw_rows = len(df)
    else:
        fallback_dashboard = DERIVED_DIR / "responses_dashboard_ready.csv"
        if not fallback_dashboard.exists():
            raise FileNotFoundError(
                "No raw CSV found in data/raw and no fallback dashboard file in data/derived. "
                "Place a raw export in data/raw or create data/derived/responses_dashboard_ready.csv first."
            )
        filtered = pd.read_csv(fallback_dashboard, low_memory=False)
        source = "derived_fallback"
        raw_rows = pd.NA

    comment_cols = infer_comment_columns(filtered.columns)
    filtered = recode_work_status_column(filtered)
    filtered = recode_subfield_column(filtered)
    background_cols = infer_background_columns(filtered.columns)

    # Dashboard-ready: keep structured background + numeric response columns, remove comments.
    dashboard = filtered.drop(columns=comment_cols, errors="ignore").copy()
    dashboard.to_csv(DERIVED_DIR / "responses_dashboard_ready.csv", index=False)

    # Numeric-only output for analysis scripts.
    numeric = dashboard.drop(columns=background_cols, errors="ignore").copy()
    for col in numeric.columns:
        numeric[col] = pd.to_numeric(numeric[col], errors="coerce")
    numeric = numeric.dropna(axis=1, how="all")
    numeric.to_csv(DERIVED_DIR / "responses_numeric_only.csv", index=False)

    item_dictionary = build_item_dictionary(dashboard, background_cols=background_cols)
    item_dictionary.to_csv(DERIVED_DIR / "item_dictionary.csv", index=False)

    responses_long = build_long_responses(dashboard, item_dictionary, background_cols)
    responses_long.to_csv(DERIVED_DIR / "responses_long.csv", index=False)

    summary = pd.DataFrame(
        {
            "metric": [
                "data_source",
                "raw_rows",
                "rows_after_qc",
                "dashboard_columns",
                "numeric_columns",
                "long_rows",
                "unique_items",
            ],
            "value": [
                source,
                raw_rows,
                len(dashboard),
                dashboard.shape[1],
                numeric.shape[1],
                len(responses_long),
                item_dictionary["item_id"].nunique(),
            ],
        }
    )
    summary.to_csv(DERIVED_DIR / "cleaning_summary.csv", index=False)

    print(f"Data source: {source}")
    print(f"Rows after QC filter: {len(dashboard)}")
    print(f"Dashboard-ready file: {DERIVED_DIR / 'responses_dashboard_ready.csv'}")
    print(f"Numeric-only file: {DERIVED_DIR / 'responses_numeric_only.csv'}")
    print(f"Long-format file: {DERIVED_DIR / 'responses_long.csv'}")
    print(f"Item dictionary file: {DERIVED_DIR / 'item_dictionary.csv'}")


if __name__ == "__main__":
    main()
