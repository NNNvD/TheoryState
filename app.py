from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="TheoryState Dashboard", layout="wide")

DERIVED_DIR = Path("data/derived")
DASHBOARD_FILE = DERIVED_DIR / "responses_dashboard_ready.csv"
LONG_FILE = DERIVED_DIR / "responses_long.csv"
ITEM_DICTIONARY_FILE = DERIVED_DIR / "item_dictionary.csv"

FILTER_PROMPTS = {
    "work_status": {
        "prompt": "Do you currently work as a psychological scientist (i.e., conduct psychological research or teach psychology/psychological science at a university or research institute)?",
        "label": "Work status",
    },
    "education": {
        "prompt": "What is your highest completed university-level education in psychology/psychological science?",
        "label": "Education",
    },
    "subfield": {
        "prompt": "Which option best describes the subfield you currently work in most of the time?",
        "label": "Subfield",
    },
}

DIMENSION_LABELS = {
    "common_subfield": "How common is this phenomenon in your subfield today?",
    "common_general": "How common is this phenomenon in psychological science in general today?",
    "harmfulness": "If this occurs, how harmful is this phenomenon for psychological science?",
    "causal_agreement": "To what extent do you agree that insufficient theory development contributes to this phenomenon?",
    "causal_magnitude": "How significant is the causal contribution to this phenomenon?",
}

DIMENSION_SHORT = {
    "common_subfield": "Common (subfield)",
    "common_general": "Common (psych science)",
    "harmfulness": "Harmfulness",
    "causal_agreement": "Theory contributes",
    "causal_magnitude": "Causal significance",
}

COLOR_MAP = {
    DIMENSION_SHORT["common_subfield"]: "#1f77b4",  # blue
    DIMENSION_SHORT["common_general"]: "#ff7f0e",  # orange
    DIMENSION_SHORT["harmfulness"]: "#2ca02c",  # green
    DIMENSION_SHORT["causal_agreement"]: "#9467bd",  # purple
    DIMENSION_SHORT["causal_magnitude"]: "#d62728",  # red
}


def normalize_text(text: str) -> str:
    """Normalize column text for resilient matching."""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def ci95_from_std(std: pd.Series, n: pd.Series) -> pd.Series:
    """Return 95% confidence-interval half-widths from sample std and N."""
    n = pd.to_numeric(n, errors="coerce")
    std = pd.to_numeric(std, errors="coerce")
    sem = std / np.sqrt(n)
    return 1.96 * sem


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load dashboard-ready, long, and item dictionary datasets."""
    dashboard_df = pd.read_csv(DASHBOARD_FILE)
    long_df = pd.read_csv(LONG_FILE)
    item_dict = pd.read_csv(ITEM_DICTIONARY_FILE)
    return dashboard_df, long_df, item_dict


def find_filter_columns(df: pd.DataFrame) -> dict[str, str]:
    """Match required global filter prompts to source columns."""
    norm_to_col = {normalize_text(c): c for c in df.columns}
    matched: dict[str, str] = {}
    for key, prompt_meta in FILTER_PROMPTS.items():
        target = normalize_text(prompt_meta["prompt"])
        direct = norm_to_col.get(target)
        if direct:
            matched[key] = direct
            continue
        for norm_col, original_col in norm_to_col.items():
            if target in norm_col or norm_col in target:
                matched[key] = original_col
                break
    return matched


def build_display_labels(item_dict: pd.DataFrame) -> dict[str, str]:
    """Create human-readable labels keyed by item_id."""
    dedup = item_dict[["item_id", "item_label", "core_claim", "item_number"]].drop_duplicates("item_id")

    def choose_label(row: pd.Series) -> str:
        core_claim = str(row.get("core_claim", "")).strip()
        item_label = str(row.get("item_label", "")).strip()
        if core_claim:
            return core_claim
        if item_label:
            return item_label
        item_number = int(row.get("item_number", 0))
        return f"Item {item_number:02d}"

    dedup["display_label"] = dedup.apply(choose_label, axis=1)
    return dict(zip(dedup["item_id"], dedup["display_label"]))


def apply_global_filters(df: pd.DataFrame, filter_cols: dict[str, str], selected: dict[str, list[str]]) -> pd.DataFrame:
    """Apply global multiselect filters to any dataframe containing the filter columns."""
    filtered = df.copy()
    for key, values in selected.items():
        col = filter_cols.get(key)
        if col and col in filtered.columns and values:
            filtered = filtered[filtered[col].astype(str).isin(values)]
    return filtered


def summarize_by_dimension(filtered_long: pd.DataFrame, table: int, ordered_dimensions: list[str]) -> pd.DataFrame:
    """Aggregate mean scores and 95% CI by dimension across all items in a table."""
    subset = filtered_long[(filtered_long["table"] == table) & (filtered_long["dimension"].isin(ordered_dimensions))].copy()
    if subset.empty:
        return pd.DataFrame(columns=["dimension", "dimension_label", "mean_score", "ci95", "N"])

    subset["response"] = pd.to_numeric(subset["response"], errors="coerce")
    summary = (
        subset.groupby("dimension", as_index=False)
        .agg(mean_score=("response", "mean"), std=("response", "std"), N=("response", "count"))
    )
    summary["ci95"] = ci95_from_std(summary["std"], summary["N"]).fillna(0)
    summary["dimension_label"] = summary["dimension"].map(DIMENSION_LABELS)
    summary["dimension_short"] = summary["dimension"].map(DIMENSION_SHORT)
    summary["dimension"] = pd.Categorical(summary["dimension"], categories=ordered_dimensions, ordered=True)
    return summary.sort_values("dimension")


def summarize_by_item_and_dimension(
    filtered_long: pd.DataFrame,
    table: int,
    ordered_dimensions: list[str],
    item_labels: dict[str, str],
) -> pd.DataFrame:
    """Aggregate mean scores and 95% CI by item and dimension for table pages."""
    subset = filtered_long[(filtered_long["table"] == table) & (filtered_long["dimension"].isin(ordered_dimensions))].copy()
    if subset.empty:
        return pd.DataFrame(columns=["item_id", "item_name", "dimension", "dimension_label", "mean_score", "ci95", "N"])

    subset["response"] = pd.to_numeric(subset["response"], errors="coerce")
    summary = (
        subset.groupby(["item_id", "dimension"], as_index=False)
        .agg(mean_score=("response", "mean"), std=("response", "std"), N=("response", "count"))
    )
    summary["ci95"] = ci95_from_std(summary["std"], summary["N"]).fillna(0)
    summary["dimension_label"] = summary["dimension"].map(DIMENSION_LABELS)
    summary["dimension_short"] = summary["dimension"].map(DIMENSION_SHORT)
    summary["item_name"] = summary["item_id"].map(item_labels).fillna(summary["item_id"])

    sort_basis = (
        summary[summary["dimension"] == "harmfulness"][["item_id", "mean_score"]]
        if table == 1
        else summary[summary["dimension"] == "causal_magnitude"][["item_id", "mean_score"]]
    )
    sort_basis = sort_basis.rename(columns={"mean_score": "sort_metric"})
    summary = summary.merge(sort_basis, on="item_id", how="left")
    summary = summary.sort_values(["sort_metric", "item_name"], ascending=[False, True])

    item_order = summary.drop_duplicates("item_id")["item_name"].tolist()
    summary["item_name"] = pd.Categorical(summary["item_name"], categories=item_order, ordered=True)
    summary["dimension"] = pd.Categorical(summary["dimension"], categories=ordered_dimensions, ordered=True)
    return summary.sort_values(["item_name", "dimension"], ascending=[True, True])


def render_global_filters(dashboard_df: pd.DataFrame, filter_cols: dict[str, str]) -> dict[str, list[str]]:
    """Render global sidebar filters with defaults set to all options."""
    st.sidebar.header("Global filters")
    selections: dict[str, list[str]] = {}
    for key, prompt_meta in FILTER_PROMPTS.items():
        col = filter_cols.get(key)
        if not col:
            continue
        options = sorted(dashboard_df[col].dropna().astype(str).unique().tolist())
        selections[key] = st.sidebar.multiselect(prompt_meta["label"], options=options, default=options)
    return selections


def render_overview(filtered_long: pd.DataFrame, filtered_n: int) -> None:
    """Render overview page with aggregate charts and respondent-level scatter."""
    st.header("Overview")
    st.metric("Filtered sample size (N)", filtered_n)

    if filtered_n == 0:
        st.warning("No data remain after filtering. Please broaden one or more filters.")
        return

    table1_dims = ["common_subfield", "common_general", "harmfulness"]
    table2_dims = ["causal_agreement", "causal_magnitude"]

    table1_summary = summarize_by_dimension(filtered_long, table=1, ordered_dimensions=table1_dims)
    table2_summary = summarize_by_dimension(filtered_long, table=2, ordered_dimensions=table2_dims)

    st.subheader("Table 1 aggregate means")
    fig_t1 = px.bar(
        table1_summary,
        x="dimension_short",
        y="mean_score",
        color="dimension_short",
        color_discrete_map=COLOR_MAP,
        text=table1_summary["mean_score"].round(2).map(lambda v: f"{v:.2f}"),
        labels={"dimension_short": "Question type", "mean_score": "Mean response (1–7)"},
        template="plotly_white",
    )
    fig_t1.update_traces(
        textposition="outside",
        error_y=dict(type="data", array=table1_summary["ci95"].to_numpy(), visible=True),
        hovertemplate="%{customdata[2]}<br>Mean=%{y:.2f}<br>95% CI ±%{customdata[1]:.2f}<br>N=%{customdata[0]}<extra></extra>",
        customdata=table1_summary[["N", "ci95", "dimension_label"]].to_numpy(),
    )
    fig_t1.update_layout(
        yaxis_range=[0.9, 7.1],
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        height=440,
    )
    st.plotly_chart(fig_t1, use_container_width=True)

    st.subheader("Table 2 aggregate means")
    fig_t2 = px.bar(
        table2_summary,
        x="dimension_short",
        y="mean_score",
        color="dimension_short",
        color_discrete_map=COLOR_MAP,
        text=table2_summary["mean_score"].round(2).map(lambda v: f"{v:.2f}"),
        labels={"dimension_short": "Question type", "mean_score": "Mean response (1–7)"},
        template="plotly_white",
    )
    fig_t2.update_traces(
        textposition="outside",
        error_y=dict(type="data", array=table2_summary["ci95"].to_numpy(), visible=True),
        hovertemplate="%{customdata[2]}<br>Mean=%{y:.2f}<br>95% CI ±%{customdata[1]:.2f}<br>N=%{customdata[0]}<extra></extra>",
        customdata=table2_summary[["N", "ci95", "dimension_label"]].to_numpy(),
    )
    fig_t2.update_layout(
        yaxis_range=[0.9, 7.1],
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        height=440,
    )
    st.plotly_chart(fig_t2, use_container_width=True)

    st.subheader("Respondent-level relationship between Table 1 and Table 2 aggregates")
    scatter_base = filtered_long[filtered_long["dimension"].isin(["common_general", "causal_agreement"])].copy()
    scatter_base["response"] = pd.to_numeric(scatter_base["response"], errors="coerce")
    respondent_scores = (
        scatter_base.groupby(["respondent_id", "dimension"], as_index=False)
        .agg(mean_score=("response", "mean"))
        .pivot(index="respondent_id", columns="dimension", values="mean_score")
        .reset_index()
        .dropna(subset=["common_general", "causal_agreement"])
    )

    if respondent_scores.empty:
        st.info("Not enough data for the respondent-level scatter plot under current filters.")
        return

    scatter_fig = px.scatter(
        respondent_scores,
        x="common_general",
        y="causal_agreement",
        opacity=0.7,
        labels={
            "common_general": "Respondent average: Table 1 commonness in psychology in general (1–7)",
            "causal_agreement": "Respondent average: Table 2 agreement that theory contributes (1–7)",
        },
        hover_data={"respondent_id": True, "common_general": ":.2f", "causal_agreement": ":.2f"},
        template="plotly_white",
    )

    if len(respondent_scores) >= 2:
        slope, intercept = np.polyfit(respondent_scores["common_general"], respondent_scores["causal_agreement"], deg=1)
        x_line = np.linspace(respondent_scores["common_general"].min(), respondent_scores["common_general"].max(), 100)
        y_line = slope * x_line + intercept
        scatter_fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name="Regression line",
                line=dict(color="#444", width=2),
                hoverinfo="skip",
            )
        )

    scatter_fig.update_layout(
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis_range=[1, 7],
        yaxis_range=[1, 7],
    )
    st.plotly_chart(scatter_fig, use_container_width=True)


def render_table_page(
    filtered_long: pd.DataFrame,
    filtered_n: int,
    table: int,
    title: str,
    ordered_dimensions: list[str],
    item_labels: dict[str, str],
) -> None:
    """Render table-specific grouped horizontal bar chart."""
    st.header(title)
    st.metric("Filtered sample size (N)", filtered_n)

    if filtered_n == 0:
        st.warning("No data remain after filtering. Please broaden one or more filters.")
        return

    summary = summarize_by_item_and_dimension(filtered_long, table, ordered_dimensions, item_labels)
    if summary.empty:
        st.info("No responses available for this page with current filters.")
        return

    fig = px.bar(
        summary,
        y="item_name",
        x="mean_score",
        color="dimension_short",
        barmode="group",
        orientation="h",
        color_discrete_map=COLOR_MAP,
        text=summary["mean_score"].round(2).map(lambda v: f"{v:.2f}"),
        labels={"item_name": "Item", "mean_score": "Mean response (1–7)", "dimension_short": "Question type"},
        hover_data={"item_name": True, "dimension_label": True, "N": True, "mean_score": ":.2f", "ci95": ":.2f"},
        template="plotly_white",
    )
    fig.update_traces(
        textposition="outside",
        error_x=dict(type="data", array=summary["ci95"].to_numpy(), visible=True),
    )
    fig.update_layout(
        xaxis_range=[1, 7],
        yaxis={"categoryorder": "array", "categoryarray": list(summary["item_name"].cat.categories[::-1])},
        height=620 if table == 1 else 480,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.title("TheoryState Survey Dashboard")
    st.caption("All charts show mean scores on the original 1–7 response scale with 95% confidence intervals.")

    required_files = [DASHBOARD_FILE, LONG_FILE, ITEM_DICTIONARY_FILE]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        st.error("Missing cleaned data files:\n- " + "\n- ".join(missing))
        st.info("Run `python scripts/clean_data.py` first.")
        return

    dashboard_df, long_df, item_dict = load_data()
    filter_cols = find_filter_columns(dashboard_df)
    item_labels = build_display_labels(item_dict)

    selections = render_global_filters(dashboard_df, filter_cols)
    filtered_dashboard = apply_global_filters(dashboard_df, filter_cols, selections)
    filtered_long = apply_global_filters(long_df, filter_cols, selections)
    filtered_n = int(filtered_dashboard.shape[0])

    page = st.sidebar.radio("Page", ["Overview", "Table 1 items", "Table 2 items"])

    if page == "Overview":
        render_overview(filtered_long, filtered_n)
    elif page == "Table 1 items":
        render_table_page(
            filtered_long,
            filtered_n,
            table=1,
            title="Table 1 items",
            ordered_dimensions=["common_subfield", "common_general", "harmfulness"],
            item_labels=item_labels,
        )
    else:
        render_table_page(
            filtered_long,
            filtered_n,
            table=2,
            title="Table 2 items",
            ordered_dimensions=["causal_agreement", "causal_magnitude"],
            item_labels=item_labels,
        )


if __name__ == "__main__":
    main()
