import streamlit as st

st.set_page_config(page_title="AI Study Buddy", page_icon="📚")

st.title("📚 AI Study Buddy")
st.write("If you can see this in your browser, Streamlit is working.")

name = st.text_input("What's your name?")
if name:
    st.success(f"Hello, {name}! 👋")