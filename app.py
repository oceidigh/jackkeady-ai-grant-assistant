import streamlit as st

st.title("Debug Test")
st.write("If you see this, imports work!")

try:
    from eligibility_checker import check_eligibility
    st.success("✓ eligibility_checker imported")
except Exception as e:
    st.error(f"✗ eligibility_checker error: {e}")

try:
    from pdf_utils import fill_application_pdf
    st.success("✓ pdf_utils imported")
except Exception as e:
    st.error(f"✗ pdf_utils error: {e}")

try:
    from openai import OpenAI
    st.success("✓ openai imported")
except Exception as e:
    st.error(f"✗ openai error: {e}")

st.write("All checks complete!")
