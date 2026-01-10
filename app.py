import os
import streamlit as st
from pdf_utils import fill_application_pdf
import eligibility_checker
from conversation_agent import init_agent
from application_schema_enhanced import FIELD_PAGES, REQUIRED_FIELDS, ApplicationSchema
import re

# ============================================================
# Paths
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdf")
PDF_TEMPLATE_PATH = os.path.join(
    PDF_DIR, "Innovation_Voucher_ApplicationForm.pdf"
)
OUTPUT_PDF_PATH = os.path.join(
    BASE_DIR, "Completed_Innovation_Voucher_Application.pdf"
)

PDF_FIELD_MAP = {
    "innovative_product":   {"page": 3, "x": 40, "y": 520},
    "primary_issues":       {"page": 3, "x": 40, "y": 420},
    "skills_expertise":     {"page": 3, "x": 40, "y": 320},
    "expected_deliverables":{"page": 3, "x": 40, "y": 220},
    "company_benefit":      {"page": 3, "x": 40, "y": 120},
}

# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="Innovation Voucher Application",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Enhanced CSS for modern, trustworthy UI
st.markdown("""
<style>
    .main {
        background-color: #F8F9FA;
    }
    
    h1 {
        font-weight: 600;
        font-size: 2rem;
        color: #1A1A1A;
        margin-bottom: 0.25rem;
    }
    
    h2 {
        font-weight: 500;
        font-size: 1.25rem;
        color: #2C2C2C;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
    
    h3 {
        font-weight: 500;
        font-size: 1.1rem;
        color: #4A4A4A;
        margin-bottom: 1rem;
    }
    
    /* Card styling */
    .stExpander {
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border: 1px solid #D0D0D0;
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 0.95rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #0066CC;
        box-shadow: 0 0 0 1px #0066CC;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton > button[kind="primary"] {
        background-color: #0066CC;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #0052A3;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #0066CC;
        height: 6px;
    }
    
    /* Remove padding */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
        max-width: 720px;
    }
    
    /* Quality indicator styling */
    .quality-indicator {
        padding: 12px;
        border-radius: 6px;
        margin: 12px 0;
        background-color: #FFF9E6;
        border-left: 4px solid #FFA500;
    }
    
    /* Confirmation box */
    .confirmation-box {
        padding: 16px;
        border-radius: 8px;
        background-color: #F0F7FF;
        border: 1px solid #B3D9FF;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Safety Check
# ============================================================
if not os.path.exists(PDF_TEMPLATE_PATH):
    st.error(f"PDF template not found: `{PDF_TEMPLATE_PATH}`")
    st.stop()

# ============================================================
# Initialize Session State
# ============================================================
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

if "form_data" not in st.session_state:
    st.session_state.form_data = {}

if "page_completed" not in st.session_state:
    st.session_state.page_completed = set()

# ============================================================
# Helper Functions
# ============================================================

def validate_field(field_config, value):
    """Validate field value"""
    if field_config["required"] and not value:
        return False, f"{field_config['label']} is required"
    
    # Email validation
    if field_config["path"] == "contacts.primary.email" and value:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return False, "Please enter a valid email address"
    
    # CRO number validation
    if field_config["path"] == "company.cro_number" and value:
        if not (value.isdigit() and len(value) >= 5):
            return False, "CRO number should be at least 5 digits"
    
    return True, None


def assess_answer_quality(text):
    """Real-time quality assessment"""
    if not text or len(text.strip()) < 10:
        return "brief", "This answer is quite brief. Consider adding more detail."
    
    if len(text.strip().split()) < 15:
        return "short", "This could be stronger with more specific information."
    
    # Check for buzzwords without substance
    buzzwords = ["synergy", "innovative", "disrupt", "revolutionize", "transform"]
    if any(word in text.lower() for word in buzzwords) and len(text.split()) < 30:
        return "vague", "Try to be more specific about outcomes and methods rather than using general terms."
    
    return "good", None


# ============================================================
# PHASE 1: ELIGIBILITY
# ============================================================
st.title("Innovation Voucher Application")
st.caption("Enterprise Ireland")
st.markdown("---")

st.subheader("Step 1: Eligibility Check")

eligibility_result = eligibility_checker.check_eligibility()

if eligibility_result is False:
    st.stop()

if eligibility_result is None:
    st.stop()

st.success("✓ You're eligible to apply")
eligibility_checker.show_eligibility_summary()

st.markdown("---")

# ============================================================
# PHASE 2: APPLICATION (PAGE-BASED)
# ============================================================

st.subheader("Step 2: Application")

# Progress indicator
total_pages = len(FIELD_PAGES)
current_page_index = st.session_state.current_page_index
progress = (current_page_index / total_pages) * 100

st.progress(progress / 100)
st.caption(f"Page {current_page_index + 1} of {total_pages} • ~{(total_pages - current_page_index) * 2} minutes remaining")

st.markdown("")

# Get current page
if current_page_index >= len(FIELD_PAGES):
    # REVIEW MODE
    st.markdown("### Step 3: Review Your Application")
    
    st.info("Review your application below. Click any section to edit.")
    
    # Group by section
    company_fields = [p for p in FIELD_PAGES if p["id"].startswith("company")]
    contact_fields = [p for p in FIELD_PAGES if p["id"].startswith("contact")]
    project_fields = [p for p in FIELD_PAGES if p["id"].startswith("project")]
    
    # Company card
    with st.expander("✓ Company Information", expanded=False):
        st.markdown("**Legal name:** " + st.session_state.form_data.get("company.legal_name", "_Not provided_"))
        st.markdown("**CRO number:** " + str(st.session_state.form_data.get("company.cro_number", "_Not provided_")))
        st.markdown("**Address:** " + st.session_state.form_data.get("company.registered_address.city", "_Not provided_"))
        st.markdown("**Employees:** " + str(st.session_state.form_data.get("company.employees.full_time", 0)) + " FT")
        
        if st.button("Edit company information", key="edit_company"):
            st.session_state.current_page_index = 0
            st.rerun()
    
    # Contact card
    with st.expander("✓ Contact Information", expanded=False):
        st.markdown("**Name:** " + st.session_state.form_data.get("contacts.primary.name", "_Not provided_"))
        st.markdown("**Email:** " + st.session_state.form_data.get("contacts.primary.email", "_Not provided_"))
        
        if st.button("Edit contact information", key="edit_contact"):
            st.session_state.current_page_index = 3
            st.rerun()
    
    # Project card with quality indicators
    with st.expander("Project Details", expanded=True):
        challenge = st.session_state.form_data.get("project.challenge", "")
        if challenge:
            st.markdown("**Challenge:**")
            st.write(challenge)
            quality, _ = assess_answer_quality(challenge)
            if quality != "good":
                st.warning("💡 Consider strengthening this answer with more specific details")
        
        description = st.session_state.form_data.get("project.description", "")
        if description:
            st.markdown("**Innovation:**")
            st.write(description)
        
        impact = st.session_state.form_data.get("project.commercial_impact", "")
        if impact:
            st.markdown("**Commercial impact:**")
            st.write(impact)
        
        if st.button("Edit project details", key="edit_project"):
            st.session_state.current_page_index = 4
            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("← Back to edit", use_container_width=True):
            st.session_state.current_page_index = len(FIELD_PAGES) - 1
            st.rerun()
    
    with col2:
        if st.button("Generate PDF Application", type="primary", use_container_width=True):
            with st.spinner("Generating..."):
                # Map form_data to PDF format
                pdf_data = {
                    "innovative_product": st.session_state.form_data.get("project.description", ""),
                    "primary_issues": st.session_state.form_data.get("project.challenge", ""),
                    "skills_expertise": st.session_state.form_data.get("project.skills_required", ""),
                    "expected_deliverables": st.session_state.form_data.get("project.deliverables", ""),
                    "company_benefit": st.session_state.form_data.get("project.commercial_impact", ""),
                }
                
                fill_application_pdf(
                    template_path=PDF_TEMPLATE_PATH,
                    output_path=OUTPUT_PDF_PATH,
                    answers=pdf_data,
                    field_map=PDF_FIELD_MAP,
                )
            
            st.success("✓ Application ready")
            
            with open(OUTPUT_PDF_PATH, "rb") as f:
                st.download_button(
                    label="Download Application PDF",
                    data=f,
                    file_name="Innovation_Voucher_Application.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
else:
    # CURRENT PAGE
    current_page = FIELD_PAGES[current_page_index]
    
    st.markdown(f"### {current_page['title']}")
    if current_page.get("description"):
        st.caption(current_page["description"])
    
    st.markdown("")
    
    if current_page["type"] == "form":
        # MULTI-FIELD FORM PAGE
        page_data = {}
        page_valid = True
        
        for field_config in current_page["fields"]:
            field_path = field_config["path"]
            
            # Get existing value
            existing_value = st.session_state.form_data.get(field_path, "")
            
            # Show input
            if field_config["type"] == "text":
                value = st.text_input(
                    field_config["label"],
                    value=existing_value,
                    help=field_config.get("help"),
                    key=f"input_{field_path}"
                )
            elif field_config["type"] == "textarea":
                value = st.text_area(
                    field_config["label"],
                    value=existing_value,
                    help=field_config.get("help"),
                    height=100,
                    key=f"input_{field_path}"
                )
            elif field_config["type"] == "number":
                value = st.number_input(
                    field_config["label"],
                    value=int(existing_value) if existing_value else 0,
                    min_value=0,
                    step=1,
                    key=f"input_{field_path}"
                )
            else:
                value = existing_value
            
            page_data[field_path] = value
            
            # Validate
            is_valid, error_msg = validate_field(field_config, value)
            if not is_valid:
                page_valid = False
                if value:  # Only show error if user has entered something
                    st.error(error_msg)
        
        st.markdown("")
        
        # Navigation
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if current_page_index > 0:
                if st.button("← Previous", use_container_width=True):
                    st.session_state.current_page_index -= 1
                    st.rerun()
        
        with col2:
            if st.button("Continue →", type="primary", use_container_width=True, disabled=not page_valid):
                # Save data
                st.session_state.form_data.update(page_data)
                st.session_state.page_completed.add(current_page["id"])
                st.session_state.current_page_index += 1
                st.rerun()
    
    else:
        # INTERVIEW MODE (AI-GUIDED SINGLE QUESTION)
        agent = init_agent()
        field_path = current_page["field"]
        
        # Check if we have pending confirmation
        if agent.state.pending_confirmation:
            # CONFIRMATION STEP
            pending = agent.state.pending_confirmation
            
            st.markdown('<div class="confirmation-box">', unsafe_allow_html=True)
            st.markdown("**What I understood:**")
            st.write(pending["summary"])
            
            if pending["confidence"] == "low":
                st.warning("⚠️ This answer could be more specific for grant evaluators")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("**Is this correct?**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✓ Yes, continue", type="primary", use_container_width=True):
                    # Apply data
                    for path, value in pending["data"].items():
                        st.session_state.form_data[path] = value
                    agent.state.confirm_pending()
                    st.session_state.current_page_index += 1
                    st.rerun()
            
            with col2:
                if st.button("Let me edit", use_container_width=True):
                    agent.state.reject_pending()
                    st.rerun()
        
        else:
            # QUESTION INPUT
            existing_answer = st.session_state.form_data.get(field_path, "")
            
            user_input = st.text_area(
                "Your answer",
                value=existing_answer,
                height=150,
                key=f"interview_{field_path}",
                help=current_page.get("description")
            )
            
            # Real-time quality indicator
            if user_input and len(user_input) > 5:
                quality, feedback = assess_answer_quality(user_input)
                if feedback:
                    st.markdown(f'<div class="quality-indicator">💡 {feedback}</div>', unsafe_allow_html=True)
            
            st.markdown("")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if current_page_index > 0:
                    if st.button("← Previous", use_container_width=True):
                        st.session_state.current_page_index -= 1
                        st.rerun()
            
            with col2:
                if st.button("Continue →", type="primary", use_container_width=True, disabled=not user_input):
                    try:
                        # Process with AI
                        with st.spinner("Processing..."):
                            result = agent.process_input(user_input)
                        
                        # Set pending confirmation
                        if result.get("extracted_data"):
                            agent.state.set_pending_confirmation(
                                result["extracted_data"],
                                result["summary_for_user"],
                                result["confidence"]
                            )
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
