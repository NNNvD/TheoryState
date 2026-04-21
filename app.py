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
    "common_subfield": "Problems common in own subfield",
    "common_general": "Problems common in psychology overall",
    "harmfulness": "Problems are harmful",
    "causal_agreement": "Limited theory contributes to consequences",
    "causal_magnitude": "Contribution is substantial",
}

OVERVIEW_DIMENSION_TOOLTIPS = {
    "common_subfield": "How common are these problems in respondents’ own subfield?",
    "common_general": "How common are these problems in psychology overall?",
    "harmfulness": "How harmful are these problems if they occur?",
    "causal_agreement": "Does limited theory development contribute to these consequences?",
    "causal_magnitude": "How large is that contribution?",
}

OVERVIEW_COLORS = {
    "common_subfield": "#1f77b4",
    "common_general": "#ff7f0e",
    "harmfulness": "#2ca02c",
    "causal_agreement": "#9467bd",
    "causal_magnitude": "#d62728",
}

OVERVIEW_QUESTION_BLOCKS = {
    "common_subfield": {
        "question": "How common are these problems in respondents’ own subfield?",
        "left_anchor": "1 = Not common at all",
        "right_anchor": "7 = Very common",
    },
    "common_general": {
        "question": "How common are these problems in psychology overall?",
        "left_anchor": "1 = Not common at all",
        "right_anchor": "7 = Very common",
    },
    "harmfulness": {
        "question": "If these problems occur, how harmful are they for psychological science?",
        "left_anchor": "1 = Not harmful at all",
        "right_anchor": "7 = Extremely harmful",
    },
    "causal_agreement": {
        "question": "To what extent do respondents agree that limited theory development contributes to these consequences?",
        "left_anchor": "1 = Strongly disagree",
        "right_anchor": "7 = Strongly agree",
    },
    "causal_magnitude": {
        "question": "How large do respondents judge that contribution to be?",
        "left_anchor": "1 = Negligible cause",
        "right_anchor": "7 = Major cause",
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

TABLE1_STATEMENT_ROWS = [
    ("Current quality of theories", "Theories are vague, verbal, and weakly predictive; they function more as rhetoric than precise explanatory systems."),
    ("Status of theory development", "Theory construction is rare and undervalued; description is often mistaken for theorizing."),
    ("Derivation of testable hypotheses", "Hypotheses are rarely deduced from (formal) theory."),
    ("How results inform theory", "Findings rarely falsify or refine theory."),
    ("Lack of disambiguation", "Constructs are undefined and boundary conditions are unclear."),
    ("Role of math, logic, and simulations", "Formal modeling remains peripheral despite its value for explicating mechanisms and deriving testable predictions."),
    ("Division of labor", "Lack of specializations for theoretical work vs. empirical research."),
    ("Overemphasis on methods", "Methodological sophistication eclipses conceptual integration; flexible analyses are rewarded."),
    ("Measurement vs. substantive theory", "Data models (factor, network) are mistaken for mechanisms."),
    ("Fragmentation across subfields", "Incompatible constructs and vocabularies impede integration."),
    ("Lack of cumulative record-keeping", "Few organized comparisons, versioning, and updating of theories."),
    ("Incentives favor discovery over understanding", "Journals and funders reward empirical novelty and volume over theory development and conceptual integration."),
    ("Educational neglect", "Curricula underweight theory formation, logic, and modeling."),
]

TABLE2_STATEMENT_ROWS = [
    ("Low replication rates", "Vague theories can fit any data, false positives included, and there are too few good theories from which to derive hypotheses."),
    ("Lack of cumulative progress", "Disconnected findings pile up without synthesis. Theories are not updated, and many overlapping theories survive or “fade away” too slowly."),
    ("Uninterpretable results", "Ambiguous constructs and auxiliaries undermine inference."),
    ("Overproduction of isolated effects", "A lack of integration and explanatory connections between effects under unifying theories."),
    ("Weak guidance for application & credibility", "Imprecise theories offer limited leverage, do not allow the derivation of predictions, and undermine trust."),
]

TABLE1_QUESTION_BLOCKS = [
    {
        "dimension": "common_subfield",
        "question": "How common is this problem in respondents’ own subfield?",
        "left_anchor": "1 = Not common at all",
        "right_anchor": "7 = Very common",
        "color": "#1f77b4",
    },
    {
        "dimension": "common_general",
        "question": "How common is this problem in psychology overall?",
        "left_anchor": "1 = Not common at all",
        "right_anchor": "7 = Very common",
        "color": "#ff7f0e",
    },
    {
        "dimension": "harmfulness",
        "question": "If this problem occurs, how harmful is it for psychological science?",
        "left_anchor": "1 = Not harmful at all",
        "right_anchor": "7 = Extremely harmful",
        "color": "#2ca02c",
    },
]

TABLE2_QUESTION_BLOCKS = [
    {
        "dimension": "causal_agreement",
        "question": "To what extent do respondents agree that limited theory development contributes to this consequence?",
        "left_anchor": "1 = Strongly disagree",
        "right_anchor": "7 = Strongly agree",
        "color": "#9467bd",
    },
    {
        "dimension": "causal_magnitude",
        "question": "How large do respondents judge that contribution to be?",
        "left_anchor": "1 = Negligible cause",
        "right_anchor": "7 = Major cause",
        "color": "#d62728",
    },
]

ITEM_BLOCK_BAR_HEIGHT = 150
WITHIN_GROUP_GAP_REM = 0.35
BETWEEN_GROUP_GAP_REM = 1.8
APP_TITLE = "The state and status of theory in psychological science"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def add_vertical_gap(rem: float) -> None:
    st.markdown(f"<div style='height: {rem}rem;'></div>", unsafe_allow_html=True)


def render_response_scale_bar(
    question: str,
    mean_response: float,
    left_anchor: str,
    right_anchor: str,
    color: str,
    metadata_text: str,
) -> None:
    """Render a compact custom 1-7 response-scale bar without a visible chart axis."""
    score = max(1.0, min(7.0, float(mean_response)))
    width_pct = ((score - 1) / 6) * 100
    min_width_pct = 18
    filled_width = max(width_pct, min_width_pct if score > 1 else 0)

    st.markdown(
        f"""
        <div style="margin: 0 0 0.2rem 0;">
            <p style="margin: 0 0 0.1rem 0;"><strong>{question}</strong></p>
            <p style="margin: 0 0 0.25rem 0; color: #9ca3af; font-size: 0.78rem;">{metadata_text}</p>
            <div style="
                width: 100%;
                background: #eef2f7;
                border-radius: 999px;
                height: 1.8rem;
                position: relative;
                overflow: hidden;
                border: 1px solid #e5e7eb;
            ">
                <div style="
                    width: {filled_width:.2f}%;
                    background: {color};
                    height: 100%;
                    border-radius: 999px;
                    display: flex;
                    align-items: center;
                    justify-content: flex-end;
                    padding-right: 0.55rem;
                    box-sizing: border-box;
                    transition: width 0.2s ease;
                ">
                    <span style="
                        color: white;
                        font-size: 1.0rem;
                        font-weight: 700;
                        line-height: 1;
                        white-space: nowrap;
                    ">{score:.1f} / 7</span>
                </div>
            </div>
            <div style="
                margin-top: 0.2rem;
                display: flex;
                justify-content: space-between;
                font-size: 0.8rem;
                color: #4b5563;
            ">
                <span>{left_anchor}</span>
                <span>{right_anchor}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_top_bar_title() -> None:
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 0.65rem;
        }}
        [data-testid="stHeader"] {{
            position: sticky;
            height: 4.2rem;
            background: white;
        }}
        [data-testid="stHeader"]::after {{
            content: "{APP_TITLE}";
            position: absolute;
            left: 3.5rem;
            top: 0.8rem;
            font-size: 2.1rem;
            font-weight: 600;
            color: rgb(49, 51, 63);
            white-space: nowrap;
            pointer-events: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def render_overview_question_blocks(summary: pd.DataFrame, dimensions: list[str], respondent_n: int) -> None:
    if summary.empty:
        st.info("No responses available under current filters.")
        return

    ordered = summary.set_index("dimension").reindex(dimensions).dropna(subset=["mean_response"])
    for idx, (dimension, row) in enumerate(ordered.iterrows()):
        meta = OVERVIEW_QUESTION_BLOCKS[dimension]
        render_response_scale_bar(
            question=meta["question"],
            mean_response=float(row["mean_response"]),
            left_anchor=meta["left_anchor"],
            right_anchor=meta["right_anchor"],
            color=OVERVIEW_COLORS[dimension],
            metadata_text=f"Participants: {respondent_n} · Responses: {int(row['N'])}",
        )
        if idx < len(ordered) - 1:
            add_vertical_gap(0.0)


def render_item_question_bar(
    question: str,
    mean_response: float,
    left_anchor: str,
    right_anchor: str,
    color: str,
    respondent_n: int,
    n_responses: int,
) -> None:
    render_response_scale_bar(
        question=question,
        mean_response=mean_response,
        left_anchor=left_anchor,
        right_anchor=right_anchor,
        color=color,
        metadata_text=f"Participants: {respondent_n} · Responses: {n_responses}",
    )


def render_item_blocks(
    summary: pd.DataFrame,
    ordered_item_names: list[str],
    question_blocks: list[dict[str, str]],
    respondent_n: int,
) -> None:
    if summary.empty:
        st.info("No responses available under current filters.")
        return

    for item_name in ordered_item_names:
        item_df = summary[summary["item_name"] == item_name].copy()
        if item_df.empty:
            continue
        st.markdown(f"### {item_name}")
        for q_idx, q in enumerate(question_blocks):
            row = item_df[item_df["dimension"] == q["dimension"]]
            if row.empty:
                continue
            mean_response = float(row.iloc[0]["mean_response"])
            n_responses = int(row.iloc[0]["N"])
            render_item_question_bar(
                question=q["question"],
                mean_response=mean_response,
                left_anchor=q["left_anchor"],
                right_anchor=q["right_anchor"],
                color=q["color"],
                respondent_n=respondent_n,
                n_responses=n_responses,
            )
            if q_idx < len(question_blocks) - 1:
                add_vertical_gap(WITHIN_GROUP_GAP_REM)
        add_vertical_gap(0.45)
        st.markdown("<hr style='margin: 0.2rem 0 0 0; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.12);'>", unsafe_allow_html=True)
        add_vertical_gap(BETWEEN_GROUP_GAP_REM)


def render_item_description_expander(expander_title: str, description_rows: list[tuple[str, str]]) -> None:
    with st.expander(expander_title, expanded=False):
        rows_html = "".join(
            f"<tr><td style='padding:0.45rem 0.6rem; vertical-align:top; font-weight:600; width:24%;'>{item}</td>"
            f"<td style='padding:0.45rem 0.6rem; vertical-align:top;'>{description}</td></tr>"
            for item, description in description_rows
        )
        st.markdown(
            f"""
            <table style="width:100%; border-collapse:collapse; table-layout:fixed; font-size:0.93rem;">
                <thead>
                    <tr>
                        <th style="text-align:left; padding:0.5rem 0.6rem; border-bottom:1px solid #e5e7eb;">Item</th>
                        <th style="text-align:left; padding:0.5rem 0.6rem; border-bottom:1px solid #e5e7eb;">Description</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )


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
    tooltip_labels = [OVERVIEW_DIMENSION_TOOLTIPS[d] for d in available_dims]
    corr_matrix.index = pretty_labels
    corr_matrix.columns = pretty_labels

    n_dims = len(pretty_labels)
    lower_mask = [[i >= j for j in range(n_dims)] for i in range(n_dims)]
    heatmap_values = corr_matrix.where(lower_mask)

    text_labels = heatmap_values.copy().astype(object)
    for i in range(n_dims):
        for j in range(n_dims):
            if i == j:
                text_labels.iat[i, j] = ""
            elif lower_mask[i][j] and pd.notna(text_labels.iat[i, j]):
                text_labels.iat[i, j] = f"{float(text_labels.iat[i, j]):.2f}"
            else:
                text_labels.iat[i, j] = ""

    strongest_pair = None
    weakest_pair = None
    pair_values: list[tuple[str, str, float]] = []
    for i in range(n_dims):
        for j in range(i):
            value = corr_matrix.iat[i, j]
            if pd.notna(value):
                pair_values.append((pretty_labels[i], pretty_labels[j], float(value)))
    if pair_values:
        strongest_pair = max(pair_values, key=lambda row: row[2])
        weakest_pair = min(pair_values, key=lambda row: row[2])

    fig = px.imshow(
        heatmap_values,
        text_auto=False,
        zmin=0,
        zmax=1,
        color_continuous_scale="Reds",
        aspect="auto",
        labels={"x": "", "y": "", "color": "Correlation (r)"},
    )
    fig.update_traces(
        text=text_labels.values,
        texttemplate="%{text}",
        hovertemplate=(
            "<b>%{customdata[0]}</b> and <b>%{customdata[1]}</b><br>"
            "Correlation (r): %{z:.2f}<extra></extra>"
        ),
        customdata=[[[tooltip_labels[i], tooltip_labels[j]] for j in range(n_dims)] for i in range(n_dims)],
    )
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Values range from -1 to +1.")
    if strongest_pair and weakest_pair:
        st.markdown(
            (
                f"**Strongest relationship:** {strongest_pair[0]} ↔ {strongest_pair[1]} "
                f"(r = {strongest_pair[2]:.2f})  \n"
                f"**Weakest relationship:** {weakest_pair[0]} ↔ {weakest_pair[1]} "
                f"(r = {weakest_pair[2]:.2f})"
            )
        )


def render_overview(filtered_long: pd.DataFrame, filtered_n: int) -> None:
    st.markdown(
        "<p style='margin:0.05rem 0 0.2rem 0;'>"
        "This dashboard presents results from the survey accompanying the statement "
        "<a href='https://doi.org/10.31234/osf.io/2fjx4_v2'><em>The state and status of theory in psychological science</em></a>."
        "</p>",
        unsafe_allow_html=True,
    )
    with st.expander("About this dashboard and survey", expanded=False):
        st.write(
            "The statement argues that theory development in psychology is often weaker than it should be for cumulative science. "
            "Many theories remain mostly verbal, underspecified, and weakly predictive; hypotheses are often not directly derived from theory; "
            "and new findings often do not strongly constrain, falsify, or refine existing theories."
        )
        st.write(
            "As a result, the field can accumulate many effects and findings without strong integrative explanations that connect results "
            "across studies and subfields. The statement further argues that this contributes to downstream problems such as low replication "
            "rates, limited cumulative progress, difficulty interpreting results, and weaker guidance for practical application."
        )
        st.markdown(
            "**You can also complete the survey here:**  \n"
            "[https://forms.gle/etCpCZ9UvSdPFQzb7](https://forms.gle/etCpCZ9UvSdPFQzb7)"
        )

    if filtered_n == 0:
        st.warning("No responses match the current filters.")
        return

    st.markdown("### Overall view of possible problems in theory development")
    st.write(
        "This section summarizes responses across the 13 Table 1 items, which concern possible problems in the current "
        "state of theory development in psychology."
    )
    render_item_description_expander(
        "View all Table 1 items and descriptions",
        TABLE1_STATEMENT_ROWS,
    )
    t1 = summarize_by_dimension(filtered_long, 1, ["common_subfield", "common_general", "harmfulness"])
    render_overview_question_blocks(
        t1,
        dimensions=["common_subfield", "common_general", "harmfulness"],
        respondent_n=filtered_n,
    )
    add_vertical_gap(0.75)

    st.markdown("### Overall view of possible consequences of limited theory development")
    st.write(
        "This section summarizes responses across the 5 Table 2 items, which concern possible consequences of limited "
        "theory development."
    )
    render_item_description_expander(
        "View all Table 2 items and descriptions",
        TABLE2_STATEMENT_ROWS,
    )
    t2 = summarize_by_dimension(filtered_long, 2, ["causal_agreement", "causal_magnitude"])
    render_overview_question_blocks(
        t2,
        dimensions=["causal_agreement", "causal_magnitude"],
        respondent_n=filtered_n,
    )

    with st.expander("Relationships among the main survey dimensions", expanded=False):
        st.markdown("### How perceptions of theory problems and consequences are related")
        st.write(
            "This figure shows how strongly the five broad survey dimensions tend to go together across respondents. "
            "Darker cells indicate stronger positive relationships."
        )
        render_correlation_heatmap(filtered_long)


def render_table1(filtered_long: pd.DataFrame, filtered_n: int, item_names: dict[str, str]) -> None:
    st.markdown(
        "<p style='margin:0.05rem 0 0.2rem 0;'>"
        "This dashboard presents results from the survey accompanying the statement "
        "<a href='https://doi.org/10.31234/osf.io/2fjx4_v2'><em>The state and status of theory in psychological science</em></a>."
        "</p>",
        unsafe_allow_html=True,
    )
    with st.expander("About this dashboard and survey", expanded=False):
        st.write(
            "The statement argues that theory development in psychology is often weaker than it should be for cumulative science. "
            "Many theories remain mostly verbal, underspecified, and weakly predictive; hypotheses are often not directly derived from theory; "
            "and new findings often do not strongly constrain, falsify, or refine existing theories."
        )
        st.write(
            "As a result, the field can accumulate many effects and findings without strong integrative explanations that connect results "
            "across studies and subfields. The statement further argues that this contributes to downstream problems such as low replication "
            "rates, limited cumulative progress, difficulty interpreting results, and weaker guidance for practical application."
        )
        st.markdown(
            "**You can also complete the survey here:**  \n"
            "[https://forms.gle/etCpCZ9UvSdPFQzb7](https://forms.gle/etCpCZ9UvSdPFQzb7)"
        )

    st.subheader("Table 1: Diagnoses")
        st.write(
        "This page presents item-level results for Table 1, which concern possible problems in the current "
        "state of theory development in psychology."
    )
    render_item_description_expander(
        "View all Table 1 items and descriptions",
        TABLE1_STATEMENT_ROWS,
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

    render_item_blocks(
        summary=summary,
        ordered_item_names=ordered_item_names,
        question_blocks=TABLE1_QUESTION_BLOCKS,
        respondent_n=filtered_n,
    )


def render_table2(filtered_long: pd.DataFrame, filtered_n: int, item_names: dict[str, str]) -> None:
    st.markdown(
        "<p style='margin:0.05rem 0 0.2rem 0;'>"
        "This dashboard presents results from the survey accompanying the statement "
        "<a href='https://doi.org/10.31234/osf.io/2fjx4_v2'><em>The state and status of theory in psychological science</em></a>."
        "</p>",
        unsafe_allow_html=True,
        )
    with st.expander("About this dashboard and survey", expanded=False):
        st.write(
            "The statement argues that theory development in psychology is often weaker than it should be for cumulative science. "
            "Many theories remain mostly verbal, underspecified, and weakly predictive; hypotheses are often not directly derived from theory; "
            "and new findings often do not strongly constrain, falsify, or refine existing theories."
        )
        st.write(
            "As a result, the field can accumulate many effects and findings without strong integrative explanations that connect results "
            "across studies and subfields. The statement further argues that this contributes to downstream problems such as low replication "
            "rates, limited cumulative progress, difficulty interpreting results, and weaker guidance for practical application."
        )
        st.markdown(
            "**You can also complete the survey here:**  \n"
            "[https://forms.gle/etCpCZ9UvSdPFQzb7](https://forms.gle/etCpCZ9UvSdPFQzb7)"
        )

    st.subheader("Table 2: Consequences")
    st.write(
        "This page presents item-level results for Table 2, which concern possible consequences of limited "
        "theory development."
    )
    render_item_description_expander(
        "View all Table 2 items and descriptions",
        TABLE2_STATEMENT_ROWS,
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

    render_item_blocks(
        summary=summary,
        ordered_item_names=ordered_item_names,
        question_blocks=TABLE2_QUESTION_BLOCKS,
        respondent_n=filtered_n,
    )


def main() -> None:
    render_top_bar_title()

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
