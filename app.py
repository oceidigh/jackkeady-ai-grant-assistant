import json
import streamlit as st
from openai import OpenAI
from pdf_utils import fill_application_pdf


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
def generate_application_answers(inputs):
    prompt = f"""
You are drafting responses for an Enterprise Ireland Innovation Voucher application.

Write concise, factual answers suitable for a government evaluator.
No marketing language. No invented facts.

Return STRICT JSON with the following keys:
- innovative_product
- primary_issues
- skills_expertise
- expected_deliverables
- company_benefit

Business context:
{json.dumps(inputs, indent=2)}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an Enterprise Ireland funding assessor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return json.loads(response.choices[0].message.content)


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
    if not company_name or not problem or not innovation:
        st.warning("Please complete the required fields.")
    else:
        with st.spinner("Generating draft and preparing application PDF..."):
            inputs = {
                "company_name": company_name,
                "sector": sector,
                "team_size": team_size,
                "problem": problem,
                "innovation": innovation,
                "timeline": timeline
            }

            answers = generate_application_answers(inputs)

            # Fill the official PDF
            fill_application_pdf(
                template_path="pdf/Innovation_Voucher_ApplicationForm.pdf",
                output_path="Completed_Innovation_Voucher_Application.pdf",
                answers=answers,
                field_map=PDF_FIELD_MAP
            )

        st.success("Draft generated and application PDF prepared.")
