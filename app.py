import json
import streamlit as st
from openai import OpenAI
from pdf_utils import fill_application_pdf

import os

st.write("PDF exists:", os.path.exists(PDF_TEMPLATE_PATH))
st.write("PDF directory:", os.listdir("pdf"))


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

import os

st.write("PDF exists:", os.path.exists(PDF_TEMPLATE_PATH))
st.write("PDF directory contents:", os.listdir("pdf"))

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
    prompt = (
        "You must respond with VALID JSON ONLY.\n"
        "Do not include explanations, comments, markdown, or formatting.\n"
        "Do not wrap the output in code fences.\n\n"
        "Return a JSON object with EXACTLY these keys:\n"
        "- innovative_product\n"
        "- primary_issues\n"
        "- skills_expertise\n"
        "- expected_deliverables\n"
        "- company_benefit\n\n"
        "Each value should be a concise paragraph of factual text.\n\n"
        "Context:\n"
        f"{json.dumps(inputs, indent=2)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an Enterprise Ireland funding assessor. "
                    "You ONLY output valid JSON. "
                    "Any text outside JSON is forbidden."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("AI response was not valid JSON. Please click Generate Draft again.")
        st.code(raw)
        raise


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
