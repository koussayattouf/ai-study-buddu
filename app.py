import os
import tempfile
from contextlib import suppress

import streamlit as st

from study_buddy import (
    load_document,
    generate_summary,
    summary_to_pdf_bytes,
    generate_quiz,
)

st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="wide")

st.title("📚 AI Study Buddy")
st.caption("Upload a PDF or text file, then generate study material.")

# ============================================================
# Upload + Extraction (always visible above the tabs)
# ============================================================

uploaded = st.file_uploader("Choose a file", type=["pdf", "txt"])

if uploaded is None:
    st.info("Upload a file to get started.")
    st.stop()

# Save to temp file
suffix = os.path.splitext(uploaded.name)[1]
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(uploaded.read())
    tmp_path = tmp.name

# Extract text
with st.spinner("Reading document..."):
    try:
        text = load_document(tmp_path)
    finally:
        with suppress(OSError):
            os.unlink(tmp_path)

# Show file stats
st.success(f"Loaded **{uploaded.name}**")
col1, col2 = st.columns(2)
col1.metric("Characters", f"{len(text):,}")
col2.metric("Words", f"{len(text.split()):,}")

with st.expander("Preview first 500 characters"):
    st.text(text[:500])

st.divider()

# ============================================================
# Tabs: Summary and Quiz
# ============================================================

tab_summary, tab_quiz = st.tabs(["📝 Summary", "❓ Quiz"])

# ---- Summary Tab ----
with tab_summary:
    if st.button("📝 Generate Summary", type="primary"):
        with st.spinner("Summarizing... this may take 20–60 seconds"):
            st.session_state.summary = generate_summary(text)

    if "summary" in st.session_state:
        st.subheader("Summary")
        st.markdown(st.session_state.summary)

        stem = os.path.splitext(uploaded.name)[0]
        col_md, col_pdf = st.columns(2)

        with col_md:
            st.download_button(
                label="⬇️ Download as Markdown",
                data=st.session_state.summary,
                file_name=f"{stem}_summary.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col_pdf:
            with st.spinner("Preparing PDF..."):
                pdf_bytes = summary_to_pdf_bytes(st.session_state.summary)

            st.download_button(
                label="⬇️ Download as PDF",
                data=pdf_bytes,
                file_name=f"{stem}_summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---- Quiz Tab ----
with tab_quiz:
    num_q = st.slider("Number of questions", min_value=3, max_value=15, value=5)

    if st.button("🎯 Generate Quiz", type="primary"):
        with st.spinner(f"Creating {num_q} questions..."):
            st.session_state.quiz = generate_quiz(text, num_q)

    if "quiz" in st.session_state:
        st.subheader(f"Quiz ({len(st.session_state.quiz)} questions)")

        for i, q in enumerate(st.session_state.quiz, 1):
            st.markdown(f"**Q{i}. {q['question']}**")

            choice = st.radio(
                "Choose an answer:",
                q["options"],
                key=f"q{i}_{uploaded.name}",
                index=None,
                label_visibility="collapsed",
            )

            if choice is not None:
                if choice.startswith(q["answer"]):
                    st.success(f"✅ Correct! {q.get('explanation', '')}")
                else:
                    st.error(
                        f"❌ Correct answer: **{q['answer']}**. "
                        f"{q.get('explanation', '')}"
                    )

            st.divider()