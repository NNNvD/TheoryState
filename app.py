from __future__ import annotations

from pathlib import Path
import re
import textwrap

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

FILTERS = {
    "work_status": {
        "source_prompt": "Do you currently work as a psychological scientist (i.e., conduct psychological research or teach psychology/psychological science at a university or research institute)?",
        "label": "Work in psychological science",
    },
    "education": {
        "source_prompt": "What is your highest completed university-level education in psychology/psychological science?",
        "label": "Education in psychology",
    },
    "subfield": {
        "source_prompt": "Which option best describes the subfield you currently work in most of the time?",
        "label": "Subfield",
    },
}

DIMENSION_META = {
    "common_subfield": {
        "short": "Subfield commonness",
        "full": "How common is this phenomenon in your subfield today?",
    },
    "common_general": {
        "short": "General commonness",
        "full": "How common is this phenomenon in psychological science in general today?",
    },
    "harmfulness": {
        "short": "Harm if present",
        "full": "If this occurs, how harmful is this phenomenon for psychological science?",
    },
    "causal_agreement": {
        "short": "Theory contributes",
        "full": "To what extent do you agree that insufficient theory development contributes to this phenomenon?",
    },
    "causal_magnitude": {
        "short": "Causal importance",
        "full": "How significant is the causal contribution to this phenomenon?",
    },
}

TABLE1_ITEM_NAMES = {
    1: "Current quality of theories",
    2: "Status of theory development",
    3: "Derivation of testable hypotheses",
    4: "How results inform theory",
    5: "Lack of disambiguation",
    6: "Role of math, logic, and simulations",
    7: "Division of labor",
    8: "Overemphasis on methods",
    9: "Measurement vs. substantive theory",
    10: "Fragmentation across subfields",
    11: "Lack of cumulative record-keeping",
    12: "Incentives favor discovery over understanding",
    13: "Educational neglect",
}

TABLE2_ITEM_NAMES = {
    1: "Low replication rates",
    2: "Lack of cumulative progress",
    3: "Uninterpretable results",
    4: "Overproduction of isolated effects",
    5: "Weak guidance for application & credibility",
}

COLOR_MAP = {
    "Subfield commonness": "#1f77b4",
    "General commonness": "#ff7f0e",
    "Harm if present": "#2ca02c",
    "Theory contributes": "#9467bd",
    "Causal importance": "#d62728",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def mean_to_score_100(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return ((values - 1) / 6) * 100


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return pd.read_csv(DASHBOARD_FILE), pd.read_csv(LONG_FILE), pd.read_csv(ITEM_DICTIONARY_FILE)


def find_filter_columns(df: pd.DataFrame) -> dict[str, str]:
    normalized = {normalize_text(c): c for c in df.columns}
    matched: dict[str, str] = {}
    for key, cfg in FILTERS.items():
        target = normalize_text(cfg["source_prompt"])
        if target in normalized:
            matched[key] = normalized[target]
            continue
        for ncol, col in normalized.items():
            if target in ncol or ncol in target:
                matched[key] = col
                break
    return matched


def build_item_name_map(item_dict: pd.DataFrame) -> dict[str, str]:
    name_map: dict[str, str] = {}
    unique_items = item_dict[["item_id", "item_number", "table"]].drop_duplicates("item_id")
    for _, row in unique_items.iterrows():
        item_id = row["item_id"]
        number = int(row["item_number"])
        table = int(row["table"])
        if table == 1:
            name_map[item_id] = TABLE1_ITEM_NAMES.get(number, f"Table 1 item {number}")
        else:
            name_map[item_id] = TABLE2_ITEM_NAMES.get(number, f"Table 2 item {number}")
    return name_map


def apply_filters(df: pd.DataFrame, filter_cols: dict[str, str], selections: dict[str, list[str]]) -> pd.DataFrame:
    out = df.copy()
    for key, values in selections.items():
        col = filter_cols.get(key)
        if col and col in out.columns:
            out = out[out[col].astype(str).isin(values)]
    return out


def render_sidebar_filters(dashboard_df: pd.DataFrame, filter_cols: dict[str, str]) -> dict[str, list[str]]:
    st.sidebar.header("Filters")

    options_by_key: dict[str, list[str]] = {}
    for key in FILTERS:
        col = filter_cols.get(key)
        if col and col in dashboard_df.columns:
            options_by_key[key] = sorted(dashboard_df[col].dropna().astype(str).unique().tolist())
        else:
            options_by_key[key] = []

    if st.sidebar.button("Reset filters", use_container_width=True):
        for key, options in options_by_key.items():
            st.session_state[f"filter_{key}"] = options

    selections: dict[str, list[str]] = {}
    for key, cfg in FILTERS.items():
        selections[key] = st.sidebar.multiselect(
            cfg["label"],
            options=options_by_key[key],
            default=options_by_key[key],
            key=f"filter_{key}",
        )
    return selections


def summarize_by_dimension(filtered_long: pd.DataFrame, table: int, dimensions: list[str]) -> pd.DataFrame:
    subset = filtered_long[(filtered_long["table"] == table) & (filtered_long["dimension"].isin(dimensions))].copy()
    if subset.empty:
        return pd.DataFrame(columns=["dimension", "label", "score", "N"])
    subset["response"] = pd.to_numeric(subset["response"], errors="coerce")
    out = subset.groupby("dimension", as_index=False).agg(mean_response=("response", "mean"), N=("response", "count"))
    out["score"] = mean_to_score_100(out["mean_response"])
    out["label"] = out["dimension"].map(lambda d: DIMENSION_META[d]["short"])
    out["full_label"] = out["dimension"].map(lambda d: DIMENSION_META[d]["full"])
    out["dimension"] = pd.Categorical(out["dimension"], categories=dimensions, ordered=True)
    return out.sort_values("dimension")


def summarize_items(
    filtered_long: pd.DataFrame,
    table: int,
    dimensions: list[str],
    item_names: dict[str, str],
    sort_dimension: str,
) -> pd.DataFrame:
    subset = filtered_long[(filtered_long["table"] == table) & (filtered_long["dimension"].isin(dimensions))].copy()
    if subset.empty:
        return pd.DataFrame(columns=["item_name", "dimension", "label", "score", "N"])

    subset["response"] = pd.to_numeric(subset["response"], errors="coerce")
    out = subset.groupby(["item_id", "dimension"], as_index=False).agg(mean_response=("response", "mean"), N=("response", "count"))
    out["score"] = mean_to_score_100(out["mean_response"])
    out["label"] = out["dimension"].map(lambda d: DIMENSION_META[d]["short"])
    out["full_label"] = out["dimension"].map(lambda d: DIMENSION_META[d]["full"])
    out["item_name"] = out["item_id"].map(item_names).fillna(out["item_id"])

    sorter = out[out["dimension"] == sort_dimension][["item_id", "score"]].rename(columns={"score": "sort_score"})
    out = out.merge(sorter, on="item_id", how="left").sort_values(["sort_score", "item_name"], ascending=[False, True])
    order = out.drop_duplicates("item_id")["item_name"].tolist()
    out["item_name"] = pd.Categorical(out["item_name"], categories=order, ordered=True)
    return out.sort_values(["item_name", "dimension"])


def kpi_value(filtered_long: pd.DataFrame, dimension: str) -> float:
    vals = pd.to_numeric(filtered_long[filtered_long["dimension"] == dimension]["response"], errors="coerce")
    return float(mean_to_score_100(pd.Series([vals.mean()])).iloc[0]) if vals.notna().any() else float("nan")


def render_overview(filtered_long: pd.DataFrame, filtered_n: int) -> None:
    st.subheader("Aggregate results across all items")
    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filtered N", filtered_n)
    c2.metric("Mean Table 1 harmfulness", f"{kpi_value(filtered_long, 'harmfulness'):.1f}")
    c3.metric("Mean Table 1 general commonness", f"{kpi_value(filtered_long, 'common_general'):.1f}")
    c4.metric("Mean Table 2 causal contribution", f"{kpi_value(filtered_long, 'causal_agreement'):.1f}")

    t1 = summarize_by_dimension(filtered_long, 1, ["common_subfield", "common_general", "harmfulness"])
    t2 = summarize_by_dimension(filtered_long, 2, ["causal_agreement", "causal_magnitude"])

    st.markdown("#### Table 1 aggregate scores")
    fig1 = px.bar(
        t1,
        x="label",
        y="score",
        color="label",
        color_discrete_map=COLOR_MAP,
        text=t1["score"].round(1).map(lambda x: f"{x:.1f}"),
        labels={"label": "", "score": "Score (0–100)"},
        template="plotly_white",
    )
    fig1.update_traces(
        textposition="outside",
        hovertemplate="%{customdata[0]}<br>Score=%{y:.1f}<br>N=%{customdata[1]}<extra></extra>",
        customdata=t1[["full_label", "N"]].to_numpy(),
    )
    fig1.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""), yaxis_range=[0, 100], height=430)
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("#### Table 2 aggregate scores")
    fig2 = px.bar(
        t2,
        x="label",
        y="score",
        color="label",
        color_discrete_map=COLOR_MAP,
        text=t2["score"].round(1).map(lambda x: f"{x:.1f}"),
        labels={"label": "", "score": "Score (0–100)"},
        template="plotly_white",
    )
    fig2.update_traces(
        textposition="outside",
        hovertemplate="%{customdata[0]}<br>Score=%{y:.1f}<br>N=%{customdata[1]}<extra></extra>",
        customdata=t2[["full_label", "N"]].to_numpy(),
    )
    fig2.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""), yaxis_range=[0, 100], height=430)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Relation between Table 1 and Table 2 aggregate scores")
    pair = filtered_long[filtered_long["dimension"].isin(["common_general", "causal_agreement"])].copy()
    pair["response"] = pd.to_numeric(pair["response"], errors="coerce")
    agg = (
        pair.groupby(["respondent_id", "dimension"], as_index=False)
        .agg(mean_response=("response", "mean"))
        .pivot(index="respondent_id", columns="dimension", values="mean_response")
        .dropna()
        .reset_index()
    )
    if agg.empty:
        st.info("Not enough respondent-level data for this plot under current filters.")
        return
    agg["x"] = mean_to_score_100(agg["common_general"])
    agg["y"] = mean_to_score_100(agg["causal_agreement"])

    scatter = px.scatter(
        agg,
        x="x",
        y="y",
        labels={"x": "Table 1 general commonness", "y": "Table 2 theory contribution"},
        opacity=0.75,
        template="plotly_white",
        hover_data={"respondent_id": True, "x": ":.1f", "y": ":.1f"},
    )
    if len(agg) >= 2:
        slope, intercept = np.polyfit(agg["x"], agg["y"], 1)
        line_x = np.linspace(agg["x"].min(), agg["x"].max(), 80)
        scatter.add_trace(go.Scatter(x=line_x, y=slope * line_x + intercept, mode="lines", name="Trend", line=dict(color="#555")))
    scatter.update_layout(height=420, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""), xaxis_range=[0, 100], yaxis_range=[0, 100])
    st.plotly_chart(scatter, use_container_width=True)


def wrap_item_labels(series: pd.Series, width: int = 38) -> pd.Series:
    return series.astype(str).map(lambda s: "<br>".join(textwrap.wrap(s, width=width)))


def render_table1(filtered_long: pd.DataFrame, filtered_n: int, item_names: dict[str, str]) -> None:
    st.subheader("Commonness and harm of candidate features of the current research landscape")
    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    summary = summarize_items(
        filtered_long,
        table=1,
        dimensions=["common_subfield", "common_general", "harmfulness"],
        item_names=item_names,
        sort_dimension="harmfulness",
    )
    if summary.empty:
        st.info("No Table 1 responses available under current filters.")
        return

    summary["item_wrapped"] = wrap_item_labels(summary["item_name"])
    fig = px.bar(
        summary,
        y="item_wrapped",
        x="score",
        color="label",
        orientation="h",
        barmode="group",
        color_discrete_map=COLOR_MAP,
        text=summary["score"].round(1).map(lambda x: f"{x:.1f}"),
        labels={"item_wrapped": "Item", "score": "Score (0–100)", "label": ""},
        template="plotly_white",
        hover_data={"item_name": True, "full_label": True, "score": ":.1f", "N": True},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=760,
        xaxis_range=[0, 100],
        yaxis={"categoryorder": "array", "categoryarray": list(summary["item_wrapped"].drop_duplicates()[::-1])},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_table2(filtered_long: pd.DataFrame, filtered_n: int, item_names: dict[str, str]) -> None:
    st.subheader("Perceived contribution of limited theory development to downstream consequences")
    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    summary = summarize_items(
        filtered_long,
        table=2,
        dimensions=["causal_agreement", "causal_magnitude"],
        item_names=item_names,
        sort_dimension="causal_magnitude",
    )
    if summary.empty:
        st.info("No Table 2 responses available under current filters.")
        return

    summary["item_wrapped"] = wrap_item_labels(summary["item_name"], width=42)
    fig = px.bar(
        summary,
        y="item_wrapped",
        x="score",
        color="label",
        orientation="h",
        barmode="group",
        color_discrete_map=COLOR_MAP,
        text=summary["score"].round(1).map(lambda x: f"{x:.1f}"),
        labels={"item_wrapped": "Item", "score": "Score (0–100)", "label": ""},
        template="plotly_white",
        hover_data={"item_name": True, "full_label": True, "score": ":.1f", "N": True},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=530,
        xaxis_range=[0, 100],
        yaxis={"categoryorder": "array", "categoryarray": list(summary["item_wrapped"].drop_duplicates()[::-1])},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.title("TheoryState Dashboard")
    st.markdown(
        "This dashboard summarizes responses to the TheoryState survey on theory development in psychological science. "
        "Scores are shown on a 0–100 scale, where higher values indicate stronger endorsement, greater perceived commonness, "
        "greater harm, or stronger perceived causal contribution. Use the filters on the left to explore how responses differ "
        "across work roles, education backgrounds, and subfields."
    )
    st.caption("Scores are based on 1–7 responses transformed to a 0–100 scale.")

    required = [DASHBOARD_FILE, LONG_FILE, ITEM_DICTIONARY_FILE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        st.error("Missing required data files:\n- " + "\n- ".join(missing))
        st.stop()

    dashboard_df, long_df, item_dict = load_data()
    filter_cols = find_filter_columns(dashboard_df)
    item_names = build_item_name_map(item_dict)

    selections = render_sidebar_filters(dashboard_df, filter_cols)
    filtered_dashboard = apply_filters(dashboard_df, filter_cols, selections)
    filtered_long = apply_filters(long_df, filter_cols, selections)
    filtered_n = int(filtered_dashboard.shape[0])

    page = st.sidebar.radio("Page", ["Overview", "Table 1: Current research landscape", "Table 2: Consequences"])

    if page == "Overview":
        render_overview(filtered_long, filtered_n)
    elif page == "Table 1: Current research landscape":
        render_table1(filtered_long, filtered_n, item_names)
    else:
        render_table2(filtered_long, filtered_n, item_names)


if __name__ == "__main__":
    main()
