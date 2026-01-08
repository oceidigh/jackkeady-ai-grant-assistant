import json
import streamlit as st
from openai import OpenAI

# ----------------------------
# Setup
# ----------------------------
client = OpenAI()

st.set_page_config(
    page_title="AI Grant Application Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AI-Assisted Grant Application Drafting")
st.caption("Drafting support only. Human review required. No guarantees of funding.")

st.info("Fill in the details below, then click **Generate Draft**.")

# ----------------------------
# Scheme (v1: hardcoded)
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
# Functions
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


def compliance_check(question, draft):
    prompt = f"""
You are reviewing a draft answer to a government grant application.

Rules:
- Be strict and conservative
- Do not rewrite the answer
- Identify risks and gaps only

Question:
{question['text']}

Evaluation criteria:
{", ".join(question['criteria'])}

Draft answer:
{draft}

Output a bullet list under these headings:
- Criteria not fully addressed
- Missing evidence or numbers
- Vague or risky statements
- Information requiring human confirmation
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a compliance-focused reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    return response.choices[0].message.content.strip()

# ----------------------------
# Inputs (MAIN PAGE – no sidebar)
# ----------------------------
st.header("Company Profile")
company_name = st.text_input("Company name")
sector = st.text_input("Sector")
team_size = st.number_input("Team size", min_value=1, step=1)

st.header("Project Overview")
problem = st.text_area("Problem you are solving")
solution = st.text_area("Proposed solution / innovation")
timeline = st.text_input("Estimated timeline (e.g. 3 months)")

# ----------------------------
# Generate Draft
# ----------------------------
if st.button("Generate Draft"):
    if not company_name or not problem:
        st.warning("Please complete at least the company name and problem description.")
    else:
        inputs = {
            "company_name": company_name,
            "sector": sector,
            "team_size": team_size,
            "problem": problem,
            "solution": solution,
            "timeline": timeline
        }

        st.subheader("Drafted Application Response")

        for q in SCHEME["questions"]:
            draft = generate_draft(q, inputs)
            critique = compliance_check(q, draft)

            st.markdown("### Draft")
            st.markdown(draft)

            st.markdown("### Compliance Review")
            st.warning(critique)

            word_count = len(draft.split())
            st.caption(f"Word count: {word_count} / {q['max_words']}")
