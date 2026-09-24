import os
import tempfile
from contextlib import suppress

import streamlit as st

from study_buddy import load_document, generate_summary

st.set_page_config(page_title="AI Study Buddy", page_icon="📚")

st.title("📚 AI Study Buddy")
st.caption("Upload a PDF or text file, then generate a summary.")

# ---- File Upload ----
uploaded = st.file_uploader("Choose a file", type=["pdf", "txt"])

if uploaded is not None:
    # 1. Save uploaded bytes to a temp file
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    # 2. Extract text using the backend
    with st.spinner("Reading document..."):
        try:
            text = load_document(tmp_path)
        finally:
            with suppress(OSError):
                os.unlink(tmp_path)

    # 3. Show file stats
    st.success(f"Loaded **{uploaded.name}**")
    col1, col2 = st.columns(2)
    col1.metric("Characters", f"{len(text):,}")
    col2.metric("Words", f"{len(text.split()):,}")

    with st.expander("Preview first 500 characters"):
        st.text(text[:500])

    st.divider()

    # 4. Generate Summary button
    if st.button("📝 Generate Summary", type="primary"):
        with st.spinner("Summarizing... this may take 20–60 seconds"):
            st.session_state.summary = generate_summary(text)

    # 5. Display the summary if we have one
    if "summary" in st.session_state:
        st.subheader("Summary")
        st.markdown(st.session_state.summary)

        st.download_button(
            label="⬇️ Download as Markdown",
            data=st.session_state.summary,
            file_name=f"{os.path.splitext(uploaded.name)[0]}_summary.md",
            mime="text/markdown",
        )