import json
import streamlit as st
from openai import OpenAI
from pdf_utils import fill_application_pdf

# ----------------------------
# PDF Field Map (page numbers are 0-indexed)
# ----------------------------
PDF_FIELD_MAP = {
    "innovative_product": {"page": 6, "x": 40, "y": 460},
    "primary_issues": {"page": 6, "x": 40, "y": 400},
    "skills_expertise": {"page": 6, "x": 40, "y": 340},
    "expected_deliverables": {"page": 6, "x": 40, "y": 270},
    "company_benefit": {"page": 6, "x": 40, "y": 200},
}

PDF_TEMPLATE_PATH = "pdf/Innovation_Voucher_ApplicationForm.pdf"
OUTPUT_PDF_PATH = "Completed_Innovation_Voucher_Application.pdf"

# ----------------------------
# Setup
# ----------------------------
client = OpenAI()

st.set_page_config(
    page_title="AI Grant Application Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AI-Assisted Innovation Voucher Application")
st.caption("Drafting support only. Human review required. No guarantees of funding.")
st.info("Fill in the details below, then click **Generate Draft**.")

# ----------------------------
# AI Drafting Function
# ----------------------------
def generate_application_answers(inputs):
    prompt = f"""
prompt = f"""
You are drafting responses for an Enterprise Ireland Innovation Voucher application.

Write in the style of a strong, fundable Innovation Voucher application that aligns with Enterprise Ireland evaluation norms.

Audience:
- A non-technical but highly experienced Enterprise Ireland evaluator
- Reviewing many applications
- Focused on learning value, technical uncertainty, and appropriate use of public funding

Primary evaluation lens (internal to the evaluator):
- Is there a clearly defined knowledge or technical gap?
- Is there genuine uncertainty where outcomes are not known in advance?
- Is external academic or specialist expertise necessary to resolve this uncertainty?
- Is the scope appropriate to a €5k–€10k Innovation Voucher?
- Will the outputs inform future technical or commercial decisions regardless of outcome?

Instructions (strict):
- Write conservatively and precisely
- Do NOT use marketing or promotional language
- Do NOT claim uniqueness, competitiveness, or market leadership
- Do NOT imply implementation, development, or commercial rollout
- Frame all work as investigation, assessment, validation, or analysis
- Clearly distinguish between what is currently known and what is uncertain
- Explicitly reference limitations, unknowns, and risks where relevant
- Avoid jargon; explain technical concepts plainly

Tone:
- Analytical
- Neutral
- Evidence-oriented
- Learning-focused

Output requirements:
Return STRICT JSON ONLY with the following keys:
- innovative_product
- primary_issues
- skills_expertise
- expected_deliverables
- company_benefit

For each section:
- 3–6 sentences
- Focus on *what will be investigated and why*
- Avoid stating outcomes as guaranteed

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

# ----------------------------
# Inputs (defined BEFORE use)
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
# Generate Draft + PDF
# ----------------------------
if st.button("Generate Draft"):
    if not company_name or not problem or not solution:
        st.warning("Please complete the required fields.")
    else:
        with st.spinner("Generating draft and preparing application PDF..."):
            inputs = {
                "company_name": company_name,
                "sector": sector,
                "team_size": team_size,
                "problem": problem,
                "proposed_solution": solution,
                "technical_uncertainty": technical_uncertainty,
                "external_expertise_required": external_expertise,
                "expected_outcomes": expected_outcomes,
                "timeline": timeline
            }

            answers = generate_application_answers(inputs)

            fill_application_pdf(
                template_path=PDF_TEMPLATE_PATH,
                output_path=OUTPUT_PDF_PATH,
                answers=answers,
                field_map=PDF_FIELD_MAP
            )

        st.success("Draft generated and application PDF prepared.")

        with open(OUTPUT_PDF_PATH, "rb") as f:
            st.download_button(
                "Download completed Innovation Voucher application (PDF)",
                f,
                file_name="Innovation_Voucher_Application_Completed.pdf",
                mime="application/pdf"
            )
