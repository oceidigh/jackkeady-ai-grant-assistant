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
You are an Enterprise Ireland Client Advisor drafting responses for an Innovation Voucher application.

Your task is to translate the company’s business context into clear, factual, conservative answers that align with Innovation Voucher evaluation priorities.

You are writing for an evaluator who is non-technical but highly experienced, commercially focused, and reviewing many applications. They are assessing learning value, technical uncertainty, and appropriate use of public funding.

What the evaluator is implicitly looking for (do not reference these explicitly in the output):
- A clear and specific knowledge or technical gap the company cannot reasonably resolve internally
- Genuine technical uncertainty where outcomes are unknown and require investigation or validation
- A project scope appropriate to a €5k–€10k Innovation Voucher
- A justified need for external academic or specialist research expertise (not routine consultancy)
- Evidence the company can understand and apply the findings (absorptive capacity)
- Non-commercial, learning-focused outputs (feasibility, validation, risk reduction)
- Reduction of downstream technical, financial, or development risk

Core objectives:
- Define the innovation relative to the company’s current capabilities, not the wider market
- Identify specific, bounded technical or knowledge gaps
- Explain why these gaps require external expertise
- Show how outcomes will inform future decisions regardless of success or failure

Rules (strict):
- No marketing or promotional language
- No invented facts or assumptions
- Be conservative, precise, and specific
- Explicitly reference unknowns, risks, and technical uncertainty
- Clearly distinguish what is currently known versus what must be validated externally
- Avoid jargon; explain technical concepts plainly

Output requirements:
Return STRICT JSON ONLY with the following keys:
- innovative_product
- primary_issues
- skills_expertise
- expected_deliverables
- company_benefit

Each value should be concise (3–6 sentences), factual, and framed as an investigation or validation rather than an execution or commercialisation.

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

problem = st.text_area(
    "What problem are you trying to solve?",
    help="Describe the core challenge or limitation that exists today."
)

solution = st.text_area(
    "What is your proposed innovation?",
    help="What new product, process, or capability are you aiming to develop?"
)

technical_uncertainty = st.text_area(
    "What technical or knowledge gaps exist?",
    help="What do you not yet know how to do, prove, or validate?"
)

external_expertise = st.text_area(
    "What type of external expertise is required?",
    help="What skills or facilities are needed that your company does not have in-house?"
)

expected_outcomes = st.text_area(
    "What would a successful outcome look like?",
    help="Describe tangible outputs such as reports, prototypes, or validated findings."
)

timeline = st.text_input("Estimated project duration (e.g. 3 months)")


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
