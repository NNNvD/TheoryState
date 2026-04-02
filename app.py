from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="TheoryState Dashboard", layout="wide")

DATA_FILE = Path("data/derived/responses_dashboard_ready.csv")

st.title("TheoryState Dashboard")
st.caption("Starter dashboard for the annual theory survey.")

if not DATA_FILE.exists():
    st.warning("Cleaned data not found. Run `python scripts/clean_data.py` first.")
    st.stop()

df = pd.read_csv(DATA_FILE)

st.subheader("Overview")
c1, c2, c3 = st.columns(3)
c1.metric("Included responses", len(df))
c2.metric("Columns", df.shape[1])
c3.metric("Item-response columns", max(df.shape[1] - 4, 0))

background_cols = df.columns[:4].tolist()
question_cols = df.columns[4:].tolist()

with st.expander("Background variables"):
    st.write(df[background_cols].head())

st.subheader("Question means")
numeric = df[question_cols].apply(pd.to_numeric, errors="coerce")
summary = pd.DataFrame({
    "question": numeric.columns,
    "mean": numeric.mean(),
    "n": numeric.notna().sum(),
}).sort_values("question")
st.dataframe(summary, use_container_width=True)

st.subheader("Distribution for one question")
selected = st.selectbox("Select a question", question_cols)
plot_df = numeric[selected].dropna().value_counts().sort_index().rename_axis("response").reset_index(name="count")
st.bar_chart(plot_df.set_index("response")["count"])

st.info("Next step: replace raw question text with an item dictionary and add filters by subfield, work status, and year.")
