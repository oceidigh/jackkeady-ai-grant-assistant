import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ----------------------------
# Setup
# ----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(
    page_title="AI Grant Application Assistant",
    layout="wide"
)

st.title("AI-Assisted Grant Application Drafting")
st.caption("Drafting support only. Human review required. No guarantees of funding.")

# ----------------------------
# Fake scheme (v1: hardcoded)
# ----------------------------
SCHEME = {
    "name": "Enterprise Ireland Innovation Voucher",
    "questions": [
        {
            "id": "Q1",
            "text": "Describe the innovation challenge your company wishes to address.",
            "max_words": 300,
            "criteria": [
                "Clear problem statement",
                "Innovation or technical uncertainty",
                "Relevance to company strategy"
            ]
        }
    ]
}

# ----------------------------
# Input Forms
# ----------------------------
with st.sidebar:
    st.header("Company Profile")
    company_name = st.text_input("Company name")
    sector = st.text_input("Sector")
    team_size = st.number_input("Team size", min_value=1, step=1)

    st.header("Project Overview")
    problem = st.text_area("Problem you are solving")
    solution = st.text_area("Proposed solution / innovation")
    timeline = st.text_input("Estimated timeline (e.g. 3 months)")

# ----------------------------
# Drafting Function
# ----------------------------
def generate_draft(question, inputs):
    prompt = f"""
You are assisting with drafting a government grant application.

Rules:
- Max {question['max_words']} words
- No marketing language
- No assumptions or fabricated data
- If information is missing, state that clearly

Question:
{question['text']}

Evaluation criteria:
{", ".join(question['criteria'])}

Company information:
{json.dumps(inputs, indent=2)}

Write a clear, factual response.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a careful, compliance-focused assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

# ----------------------------
# Generate Draft
# ----------------------------
if st.button("Generate Draft"):
    if not company_name or not problem:
        st.warning("Please complete the required fields.")
    else:
        inputs = {
            "company_name": company_name,
            "sector": sector,
            "team_size": team_size,
            "problem": problem,
            "solution": solution,
            "timeline": timeline
        }

        st.subheader("Drafted Application Responses")

        for q in SCHEME["questions"]:
            with st.expander(q["text"], expanded=True):
                draft = generate_draft(q, inputs)
                word_count = len(draft.split())

                st.markdown(draft)
                st.caption(f"Word count: {word_count} / {q['max_words']}")

                if word_count > q["max_words"]:
                    st.error("Exceeds word limit. Requires editing.")
                else:
                    st.success("Within word limit.")
