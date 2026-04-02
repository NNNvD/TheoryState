from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="TheoryState Dashboard", layout="wide")

DERIVED_DIR = Path("data/derived")
DASHBOARD_FILE = DERIVED_DIR / "responses_dashboard_ready.csv"
LONG_FILE = DERIVED_DIR / "responses_long.csv"
ITEM_DICTIONARY_FILE = DERIVED_DIR / "item_dictionary.csv"
SUMMARY_FILE = DERIVED_DIR / "cleaning_summary.csv"

BACKGROUND_ORDER_HINTS = [
    "Timestamp",
    "Do you currently work as a psychological scientist",
    "What is your highest completed university-level education",
    "Which option best describes the subfield",
]


def infer_background_columns(df: pd.DataFrame) -> list[str]:
    """Return likely structured background columns used for filtering."""
    lowered = {c: c.lower() for c in df.columns}
    background = []
    for col in df.columns:
        if any(h.lower() in lowered[col] for h in BACKGROUND_ORDER_HINTS):
            background.append(col)
    return background


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None, pd.DataFrame]:
    """Load dashboard datasets from derived outputs."""
    dashboard = pd.read_csv(DASHBOARD_FILE)
    long_df = pd.read_csv(LONG_FILE)
    item_dictionary = pd.read_csv(ITEM_DICTIONARY_FILE)
    summary = pd.read_csv(SUMMARY_FILE) if SUMMARY_FILE.exists() else None
    return dashboard, long_df, summary, item_dictionary


def describe_stats(values: pd.Series) -> dict[str, float]:
    """Compute summary metrics for one response series."""
    values = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "mean": values.mean(),
        "median": values.median(),
        "std": values.std(ddof=1),
        "N": int(values.notna().sum()),
    }


def apply_filters(df: pd.DataFrame, filters: dict[str, list[str]]) -> pd.DataFrame:
    """Apply sidebar filters if provided."""
    filtered = df.copy()
    for col, selected in filters.items():
        if selected:
            filtered = filtered[filtered[col].astype(str).isin(selected)]
    return filtered


st.title("TheoryState Survey Dashboard")
st.caption("Interactive public summary of perspectives on theory development in psychological science.")

required = [DASHBOARD_FILE, LONG_FILE, ITEM_DICTIONARY_FILE]
missing = [str(p) for p in required if not p.exists()]
if missing:
    st.error("Missing cleaned data files:\n- " + "\n- ".join(missing))
    st.info("Run `python scripts/clean_data.py` first.")
    st.stop()

dashboard_df, long_df, summary_df, item_dictionary = load_data()
background_cols = [c for c in infer_background_columns(dashboard_df) if c in dashboard_df.columns]

st.sidebar.header("Filters")
filters: dict[str, list[str]] = {}
for col in background_cols:
    options = sorted(dashboard_df[col].dropna().astype(str).unique().tolist())
    if options:
        filters[col] = st.sidebar.multiselect(col, options)

filtered_dashboard = apply_filters(dashboard_df, filters)
filtered_long = apply_filters(long_df, {k: v for k, v in filters.items() if k in long_df.columns})

page = st.sidebar.radio("Section", ["Overview", "Table 1", "Table 2", "Methods / Data Quality"])

if page == "Overview":
    st.header("Overview")
    raw_rows = None
    rows_after_qc = None
    if summary_df is not None and not summary_df.empty:
        summary_map = dict(zip(summary_df["metric"], summary_df["value"]))
        raw_rows = summary_map.get("raw_rows")
        rows_after_qc = summary_map.get("rows_after_qc")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total raw rows", raw_rows if raw_rows is not None else "N/A")
    c2.metric("Rows after QC filtering", rows_after_qc if rows_after_qc is not None else len(dashboard_df))
    c3.metric("Included in current view", len(filtered_dashboard))

    st.markdown(
        "**Inclusion criteria:** keep responses where both QC checks are passed "
        "(check number 4 = 4 and check number 2 = 2)."
    )

    st.subheader("Background variable breakdowns")
    for col in background_cols:
        counts = filtered_dashboard[col].astype(str).value_counts(dropna=False).reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(counts, x=col, y="count", title=col)
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

elif page in {"Table 1", "Table 2"}:
    table_num = 1 if page == "Table 1" else 2
    st.header(page)

    table_items = (
        item_dictionary[item_dictionary["table"] == table_num][["item_id", "item_label"]]
        .drop_duplicates()
        .sort_values("item_id")
    )
    if table_items.empty:
        st.warning(f"No items available for {page}.")
        st.stop()

    selected_item = st.selectbox("Select item", table_items["item_id"].tolist(), format_func=lambda x: f"{x} — {table_items.set_index('item_id').loc[x, 'item_label']}")
    item_df = filtered_long[(filtered_long["table"] == table_num) & (filtered_long["item_id"] == selected_item)].copy()

    if item_df.empty:
        st.warning("No rows available after filtering for this item.")
        st.stop()

    summary_rows = []
    for dimension, dim_df in item_df.groupby("dimension_label"):
        stats = describe_stats(dim_df["response"])
        summary_rows.append({"dimension": dimension, **stats})
    summary_table = pd.DataFrame(summary_rows).sort_values("dimension")

    st.subheader("Summary statistics")
    st.dataframe(summary_table, use_container_width=True)

    st.subheader("Response distribution")
    dim_options = sorted(item_df["dimension_label"].dropna().unique().tolist())
    selected_dimension = st.selectbox("Dimension", dim_options)
    plot_df = item_df[item_df["dimension_label"] == selected_dimension].copy()
    plot_df["response"] = pd.to_numeric(plot_df["response"], errors="coerce")
    plot_df = plot_df.dropna(subset=["response"])
    dist = plot_df["response"].value_counts().sort_index().rename_axis("response").reset_index(name="count")
    fig = px.bar(dist, x="response", y="count", title=f"{selected_item}: {selected_dimension}")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.header("Methods / Data Quality")
    st.markdown(
        """
### QC filters
- Keep rows where `6. For quality control, please check number 4.` equals `4`.
- Keep rows where `3. For quality control, please check number 2` equals `2`.

### Row exclusion and column handling
- Rows that fail either QC check are excluded.
- Free-text comment fields (e.g., `Optional comment`, `Final comments`) are removed from public outputs.
- Structured background variables (timestamp, work status, education, subfield) are retained when present.

### Output files
- `responses_dashboard_ready.csv`
- `responses_numeric_only.csv`
- `responses_long.csv`
- `item_dictionary.csv`
- `cleaning_summary.csv`

### Current limitations and assumptions
- Item labels are inferred from question numbering in source columns.
- If raw exports are missing, the cleaning script can rebuild derivative artifacts from an existing dashboard-ready file.
        """
    )

    if summary_df is not None:
        st.subheader("Cleaning summary")
        st.dataframe(summary_df, use_container_width=True)
