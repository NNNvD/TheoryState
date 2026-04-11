from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="The state and status of theory in psychological science",
    layout="wide",
)

DERIVED_DIR = Path("data/derived")
DASHBOARD_FILE = DERIVED_DIR / "responses_dashboard_ready.csv"
LONG_FILE = DERIVED_DIR / "responses_long.csv"
ITEM_DICTIONARY_FILE = DERIVED_DIR / "item_dictionary.csv"

FILTERS = {
    "work_status": {
        "label": "Work in psychological science",
        "source_prompt": "Do you currently work as a psychological scientist (i.e., conduct psychological research or teach psychology/psychological science at a university or research institute)?",
        "allowed_values": ["No", "Yes, partly", "Yes, primarily"],
    },
    "education": {
        "label": "Education in psychology",
        "source_prompt": "What is your highest completed university-level education in psychology/psychological science?",
    },
    "subfield": {
        "label": "Subfield",
        "source_prompt": "Which option best describes the subfield you currently work in most of the time?",
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

OVERVIEW_DIMENSION_LABELS = {
    "common_subfield": "Lack of theory in respondents’ subfield",
    "common_general": "Lack of theory in psychology overall",
    "harmfulness": "Lack of theory is harmful",
    "causal_agreement": "Lack of theory contributes to problems",
    "causal_magnitude": "Magnitude of this contribution",
}

OVERVIEW_COLORS = {
    "common_subfield": "#1f77b4",
    "common_general": "#ff7f0e",
    "harmfulness": "#2ca02c",
    "causal_agreement": "#9467bd",
    "causal_magnitude": "#d62728",
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

TABLE1_STATEMENT_ROWS = [
    ("Current quality of theories", "Many theories are underspecified, weakly integrated, or insufficiently formalized."),
    ("Status of theory development", "Theory development is often underprioritized relative to data collection and method-focused work."),
    ("Derivation of testable hypotheses", "Theories frequently do not generate precise, risky, and discriminative predictions."),
    ("How results inform theory", "Empirical findings often do not feed back clearly into revising or refining theory."),
    ("Lack of disambiguation", "Competing explanations are not consistently adjudicated through strong tests."),
    ("Role of math, logic, and simulations", "Formal tools are underused for clarifying assumptions and implications."),
    ("Division of labor", "Theory-building and empirical testing are not always coordinated effectively."),
    ("Overemphasis on methods", "Methodological innovation can outpace substantive theoretical development."),
    ("Measurement vs. substantive theory", "Measurement and psychometrics can be emphasized without matching progress in substantive theory."),
    ("Fragmentation across subfields", "Theoretical frameworks are often fragmented across subfields and research traditions."),
    ("Lack of cumulative record-keeping", "The field lacks strong cumulative structures for tracking theory performance over time."),
    ("Incentives favor discovery over understanding", "Incentives can reward novel findings more than explanatory integration and understanding."),
    ("Educational neglect", "Training in formal and cumulative theory development is often limited."),
]

TABLE2_STATEMENT_ROWS = [
    ("Low replication rates", "Insufficient theory development may contribute to lower reproducibility and replication success."),
    ("Lack of cumulative progress", "Weak theory development can slow accumulation of coherent, integrative knowledge."),
    ("Uninterpretable results", "Findings may be difficult to interpret when theoretical commitments are vague or underspecified."),
    ("Overproduction of isolated effects", "Limited theory can yield many disconnected effects without broader explanatory structure."),
    ("Weak guidance for application & credibility", "Applied translation and public credibility can suffer when theory is underdeveloped."),
]

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
        if not col or col not in out.columns or not values:
            continue
        out = out[out[col].astype(str).isin(values)]
    return out


def render_sidebar_controls(dashboard_df: pd.DataFrame, filter_cols: dict[str, str]) -> tuple[str, dict[str, list[str]]]:
    st.sidebar.markdown("### Page")
    page_options = ["Overview", "Table 1", "Table 2"]
    page = st.sidebar.radio(
        "Choose dashboard page",
        page_options,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("### Filters")

    options_by_key: dict[str, list[str]] = {}
    for key in FILTERS:
        col = filter_cols.get(key)
        if col and col in dashboard_df.columns:
            options = sorted(dashboard_df[col].dropna().astype(str).unique().tolist())
            allowed_values = FILTERS[key].get("allowed_values")
            if allowed_values:
                allowed_order = {normalize_text(value): idx for idx, value in enumerate(allowed_values)}
                options = [value for value in options if normalize_text(value) in allowed_order]
                options = sorted(options, key=lambda value: allowed_order[normalize_text(value)])
            options_by_key[key] = options
        else:
            options_by_key[key] = []

    if st.sidebar.button("Reset filters", use_container_width=True):
        for key, options in options_by_key.items():
            for option in options:
                st.session_state[f"filter_{key}_{option}"] = False

    selections: dict[str, list[str]] = {}
    for key, cfg in FILTERS.items():
        selected_values: list[str] = []
        with st.sidebar.expander(cfg["label"], expanded=False):
            for option in options_by_key[key]:
                checked = st.checkbox(option, key=f"filter_{key}_{option}")
                if checked:
                    selected_values.append(option)
        selections[key] = selected_values

    return page, selections


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
    ordered_item_names: list[str],
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

    out["item_name"] = pd.Categorical(out["item_name"], categories=ordered_item_names, ordered=True)
    out["dimension"] = pd.Categorical(out["dimension"], categories=dimensions, ordered=True)
    return out.sort_values(["item_name", "dimension"])


def render_statement_table(rows: list[tuple[str, str]]) -> None:
    table_df = pd.DataFrame(rows, columns=["Item", "Description from the statement context"])
    st.dataframe(table_df, use_container_width=True, hide_index=True)


def render_kpi_cards(summary: pd.DataFrame, respondent_n: int) -> None:
    if summary.empty:
        return
    columns = st.columns(len(summary))
    for col, (_, row) in zip(columns, summary.iterrows()):
        with col:
            st.markdown(f"**{row['label']}**")
            st.metric("Average score", f"{row['score']:.1f}")
            st.progress(float(row["score"] / 100), text=f"{row['score']:.1f} / 100")
            st.caption(f"N respondents = {respondent_n} · n responses = {int(row['N'])}")


def render_overview_aggregate_chart(summary: pd.DataFrame, title: str) -> None:
    if summary.empty:
        st.info("No responses available under current filters.")
        return

    fig = px.bar(
        summary,
        x="score",
        y="label",
        orientation="h",
        color="label",
        color_discrete_map={label: color for label, color in zip(summary["label"], summary["color"])},
        text=summary["score"].round(1).map(lambda x: f"{x:.1f}"),
        labels={"score": "Average score (0–100)", "label": ""},
        template="plotly_white",
        custom_data=["full_label", "N"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Score: %{x:.1f}<br>"
            "Average across all filtered items<br>"
            "n responses: %{customdata[1]}<extra></extra>"
        ),
    )
    fig.update_layout(
        title=title,
        showlegend=True,
        legend_title_text="",
        height=360,
        xaxis_range=[0, 100],
        margin=dict(l=10, r=10, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_correlation_heatmap(filtered_long: pd.DataFrame) -> None:
    all_dimensions = ["common_subfield", "common_general", "harmfulness", "causal_agreement", "causal_magnitude"]
    base = filtered_long[filtered_long["dimension"].isin(all_dimensions)].copy()
    if base.empty:
        return
    base["response"] = pd.to_numeric(base["response"], errors="coerce")
    base = base.dropna(subset=["response"])
    dimension_means = (
        base.groupby(["respondent_id", "dimension"], as_index=False)
        .agg(mean_response=("response", "mean"))
        .pivot(index="respondent_id", columns="dimension", values="mean_response")
        .reset_index()
    )
    available_dims = [d for d in all_dimensions if d in dimension_means.columns]
    if len(available_dims) < 2:
        st.info("Correlation view unavailable for the current filter selection.")
        return

    for dim in available_dims:
        dimension_means[dim] = mean_to_score_100(dimension_means[dim])

    corr_matrix = dimension_means[available_dims].corr()
    pretty_labels = [OVERVIEW_DIMENSION_LABELS[d] for d in available_dims]
    corr_matrix.index = pretty_labels
    corr_matrix.columns = pretty_labels

    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        zmin=-1,
        zmax=1,
        color_continuous_scale="RdBu_r",
        aspect="auto",
        labels={"x": "", "y": "", "color": "Correlation"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b> vs <b>%{x}</b><br>"
            "Correlation: %{z:.2f}<br>"
            "Average across filtered respondents<extra></extra>"
        )
    )
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Pairwise Pearson correlations across the five aggregate dimensions (using respondents in the current filter view).")


def render_overview(filtered_long: pd.DataFrame, filtered_n: int) -> None:
    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    st.markdown("### Aggregate Table 1. Diagnoses of the state and status of theory")
    st.write(
        "This chart summarizes responses across the 13 items of the diagnosis of the state and status of theory in "
        "psychological science (see [statement](https://doi.org/10.31234/osf.io/2fjx4_v2)). It shows how common "
        "respondents think these candidate problems are in their own subfield, how common they think they are in "
        "psychology overall, and how harmful they judge them to be if they occur. Responses to the 13 items have "
        "been averaged and then transformed to a 0-100 scale (0 = Not common/harmful at all; 100 = Very common/Extremely harmful)."
    )
    t1 = summarize_by_dimension(filtered_long, 1, ["common_subfield", "common_general", "harmfulness"])
    t1["label"] = t1["dimension"].map(OVERVIEW_DIMENSION_LABELS)
    t1["full_label"] = t1["label"]
    t1["color"] = t1["dimension"].map(OVERVIEW_COLORS)
    render_kpi_cards(t1, respondent_n=filtered_n)
    render_overview_aggregate_chart(t1, "Table 1 aggregate scores")

    st.markdown("### Aggregate Table 2. Consequences of the state and status of theory")
    st.write(
        "This chart summarizes responses across the 5 items of the consequences of the state and status of theory in "
        "psychological science (see [statement](https://doi.org/10.31234/osf.io/2fjx4_v2)). It shows the extent to "
        "which respondents think limited theory development contributes (a lot or a bit) to problems such as "
        "*low replication rates, lack of cumulative progress,* and *Overproduction of isolated effects*. Responses "
        "to the 5 items have been averaged and then transformed to a 0-100 scale (0 = Strongly disagree/Negligible cause; "
        "100 = Strongly agree/Major cause)."
    )
    t2 = summarize_by_dimension(filtered_long, 2, ["causal_agreement", "causal_magnitude"])
    t2["label"] = t2["dimension"].map(OVERVIEW_DIMENSION_LABELS)
    t2["full_label"] = t2["label"]
    t2["color"] = t2["dimension"].map(OVERVIEW_COLORS)
    render_kpi_cards(t2, respondent_n=filtered_n)
    render_overview_aggregate_chart(t2, "Table 2 aggregate scores")

    st.markdown("### How these broad perceptions relate to each other")
    st.write(
        "This heatmap shows pairwise correlations among the five aggregate dimensions. Values near +1 indicate that "
        "respondents who score high on one dimension also tend to score high on another, while values near 0 indicate "
        "little linear association."
    )
    render_correlation_heatmap(filtered_long)


def render_grouped_bars(summary: pd.DataFrame, height: int) -> None:
    if summary.empty:
        return

    fig = px.bar(
        summary,
        y="item_name",
        x="score",
        color="label",
        orientation="h",
        barmode="group",
        color_discrete_map=COLOR_MAP,
        text=summary["score"].round(1).map(lambda x: f"{x:.1f}"),
        labels={"item_name": "Item", "score": "Score (0–100)", "label": ""},
        template="plotly_white",
        hover_data={"item_name": True, "full_label": True, "score": ":.1f", "N": True},
    )
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        cliponaxis=False,
    )
    fig.update_layout(
        height=height,
        xaxis_range=[0, 100],
        yaxis={"categoryorder": "array", "categoryarray": list(summary["item_name"].drop_duplicates()[::-1])},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        margin=dict(l=20, r=20, t=20, b=20),
        bargap=0.22,
        bargroupgap=0.08,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_table1(filtered_long: pd.DataFrame, filtered_n: int, item_names: dict[str, str]) -> None:
    st.subheader("Table 1. Diagnoses of the state and status of theory in psychological science")
    st.write(
        "These items summarize possible diagnoses of the current state of theorizing and theory development in psychological science. "
        "The chart shows how common respondents think each phenomenon is, both in their own subfield and in psychology more generally, "
        "and how harmful they consider it if it occurs."
    )
    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    ordered_item_names = [TABLE1_ITEM_NAMES[i] for i in range(1, 14)]
    summary = summarize_items(
        filtered_long,
        table=1,
        dimensions=["common_subfield", "common_general", "harmfulness"],
        item_names=item_names,
        ordered_item_names=ordered_item_names,
    )
    if summary.empty:
        st.info("No Table 1 responses available under current filters.")
        return

    render_grouped_bars(summary, height=820)

    st.markdown("#### Statement table")
    render_statement_table(TABLE1_STATEMENT_ROWS)


def render_table2(filtered_long: pd.DataFrame, filtered_n: int, item_names: dict[str, str]) -> None:
    st.subheader("Table 2. Consequences of the state and status of theory in psychological science")
    st.write(
        "These items summarize possible consequences of limited theory development in psychological science. "
        "The chart shows the extent to which respondents think insufficient theory development contributes to each consequence "
        "and how important that contribution is."
    )
    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    ordered_item_names = [TABLE2_ITEM_NAMES[i] for i in range(1, 6)]
    summary = summarize_items(
        filtered_long,
        table=2,
        dimensions=["causal_agreement", "causal_magnitude"],
        item_names=item_names,
        ordered_item_names=ordered_item_names,
    )
    if summary.empty:
        st.info("No Table 2 responses available under current filters.")
        return

    render_grouped_bars(summary, height=560)

    st.markdown("#### Statement table")
    render_statement_table(TABLE2_STATEMENT_ROWS)


def main() -> None:
    st.title("The state and status of theory in psychological science")
    st.markdown(
        "This dashboard presents results from the survey accompanying the statement *The state and status of theory in psychological science*. "
        "The statement argues that theory development in psychology is often weakly developed, insufficiently formalized, and poorly "
        "integrated with empirical research, and that this has important consequences for cumulative progress in the field. "
        "The full statement is available here: https://doi.org/10.31234/osf.io/2fjx4_v2.\n\n"
        "The survey asks respondents to evaluate possible diagnoses of the current state of theory development in psychology, as well as "
        "possible downstream consequences. The objective of the survey is to map where psychological scientists agree or disagree, "
        "which issues are seen as most important, and how these perspectives may change over time. You can complete the survey here: "
        "https://forms.gle/etCpCZ9UvSdPFQzb7."
    )
    st.caption("Scores are shown on a 0–100 scale derived from 1–7 survey responses.")

    required = [DASHBOARD_FILE, LONG_FILE, ITEM_DICTIONARY_FILE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        st.error("Missing required data files:\n- " + "\n- ".join(missing))
        st.stop()

    dashboard_df, long_df, item_dict = load_data()
    filter_cols = find_filter_columns(dashboard_df)
    item_names = build_item_name_map(item_dict)

    page, selections = render_sidebar_controls(dashboard_df, filter_cols)
    filtered_dashboard = apply_filters(dashboard_df, filter_cols, selections)
    filtered_long = apply_filters(long_df, filter_cols, selections)
    filtered_n = int(filtered_dashboard.shape[0])
    st.sidebar.markdown(f"**Filtered N:** {filtered_n}")

    if page == "Overview":
        render_overview(filtered_long, filtered_n)
    elif page == "Table 1":
        render_table1(filtered_long, filtered_n, item_names)
    else:
        render_table2(filtered_long, filtered_n, item_names)


if __name__ == "__main__":
    main()
