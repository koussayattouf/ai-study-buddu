import os
import tempfile
import streamlit as st
from study_buddy import load_document

st.set_page_config(page_title="AI Study Buddy", page_icon="📚")

st.title("📚 AI Study Buddy")
st.caption("Upload a PDF or text file to get started.")

# ---- File Upload ----
uploaded = st.file_uploader("Choose a file", type=["pdf", "txt"])

if uploaded is not None:
    # 1. Save the uploaded file to a temporary location
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    # 2. Extract text using the backend
    with st.spinner("Reading document..."):
        text = load_document(tmp_path)

    # 3. Show some feedback
    st.success(f"Loaded **{uploaded.name}**")

    col1, col2 = st.columns(2)
    col1.metric("Characters", f"{len(text):,}")
    col2.metric("Words", f"{len(text.split()):,}")

    # 4. Preview the first 500 characters
    with st.expander("Preview first 500 characters"):
        st.text(text[:500])

    # We'll clean up the temp file at the end
    os.unlink(tmp_path)