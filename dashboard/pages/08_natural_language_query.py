import streamlit as st
from dashboard.utils.api_client import query_nlq

EXAMPLES = [
    "Which states have the highest average readmission rates?",
    "Show hospitals in Arizona with low readmission risk and high patient experience",
    "Which hospital types have the best quality scores?",
    "What community health factors correlate with high readmission risk?",
    "Show the top 10 hospitals by quality score in Texas",
    "Which hospitals improved the most between 2021 and 2023?",
]


def run():
    st.header("8. Natural Language Query")
    if "nlq_history" not in st.session_state: st.session_state.nlq_history = []
    with st.sidebar:
        st.subheader("Query history")
        for item in st.session_state.nlq_history[-5:][::-1]:
            st.caption(item.get("question"))
    selected = None
    cols = st.columns(2)
    for i, q in enumerate(EXAMPLES):
        if cols[i % 2].button(q): selected = q
    question = st.text_input("Ask a question about hospital quality data...", value=selected or "")
    if st.button("Submit") and question:
        response = query_nlq(question)
        if response:
            st.session_state.nlq_history.append(response)
            with st.expander("Generated SQL", expanded=True):
                st.code(response.get("generated_sql", ""), language="sql")
            st.dataframe(response.get("results", []), use_container_width=True)
            st.markdown(f'<div class="callout">{response.get("plain_english_summary", "")}</div>', unsafe_allow_html=True)
