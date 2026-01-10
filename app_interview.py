import os
import streamlit as st
from pdf_utils import fill_application_pdf
import eligibility_checker
from conversation_agent import init_agent
from application_schema import FIELD_ORDER

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

# ============================================================
# PDF Field Map
# ============================================================
PDF_FIELD_MAP = {
    "innovative_product":   {"page": 3, "x": 40, "y": 520},
    "primary_issues":       {"page": 3, "x": 40, "y": 420},
    "skills_expertise":     {"page": 3, "x": 40, "y": 320},
    "expected_deliverables":{"page": 3, "x": 40, "y": 220},
    "company_benefit":      {"page": 3, "x": 40, "y": 120},
}

# ============================================================
# Page Config - Clean, Professional
# ============================================================
st.set_page_config(
    page_title="Innovation Voucher Application",
    layout="centered",  # Changed from wide to centered for interview feel
    initial_sidebar_state="collapsed",  # Hide sidebar by default
)

# Custom CSS for professional interview UI
st.markdown("""
<style>
    /* Remove chat-like elements */
    .stChatMessage {
        display: none !important;
    }
    
    /* Clean, professional typography */
    .main {
        background-color: #FAFAFA;
    }
    
    h1 {
        font-weight: 600;
        font-size: 2rem;
        margin-bottom: 0.5rem;
        color: #1A1A1A;
    }
    
    h2 {
        font-weight: 500;
        font-size: 1.5rem;
        color: #2C2C2C;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Progress indicator */
    .stProgress > div > div {
        background-color: #0066CC;
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid #D0D0D0;
        border-radius: 6px;
        padding: 12px;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0066CC;
        box-shadow: 0 0 0 1px #0066CC;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        border: none;
    }
    
    .stButton > button[kind="primary"] {
        background-color: #0066CC;
    }
    
    /* Remove excessive padding */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 800px;
    }
    
    /* Info box styling */
    .stAlert {
        background-color: #F0F7FF;
        border-left: 4px solid #0066CC;
        padding: 1rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Safety Check
# ============================================================
if not os.path.exists(PDF_TEMPLATE_PATH):
    st.error(
        "Innovation Voucher PDF template not found.\n\n"
        f"Expected path: `{PDF_TEMPLATE_PATH}`"
    )
    st.stop()

# ============================================================
# PHASE 1: ELIGIBILITY CHECK
# ============================================================
st.title("Innovation Voucher Application")
st.caption("Enterprise Ireland")

st.markdown("---")

st.subheader("Step 1: Eligibility")

eligibility_result = eligibility_checker.check_eligibility()

# Stop if not eligible
if eligibility_result is False:
    st.stop()

# Still checking eligibility
if eligibility_result is None:
    st.stop()

# ============================================================
# PHASE 2: INTERVIEW INTERFACE (CLEAN, NO CHAT METAPHORS)
# ============================================================
st.success("✓ Eligible")
eligibility_checker.show_eligibility_summary()

st.markdown("---")

# Initialize agent
agent = init_agent()

# Check if conversation is complete
if agent.state.is_complete():
    
    # Rule 5 enforcement: MUST enter review mode before completion
    if not agent.state.in_review_mode:
        agent.enter_review_mode()
    
    st.subheader("Step 3: Review Application")
    
    # Professional summary
    review_summary = agent.get_review_summary()
    
    with st.expander("Overall Assessment", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Completion", review_summary["completion_rate"])
        with col2:
            st.metric("High Confidence", review_summary["high_confidence_rate"])
        with col3:
            quality_emoji = "✓" if review_summary["project_quality"] == "strong" else "!"
            st.metric("Project Quality", f"{quality_emoji} {review_summary['project_quality']}")
        
        if review_summary["strengths"]:
            st.markdown("**Strengths:**")
            for strength in review_summary["strengths"]:
                st.write(f"• {strength}")
        
        if review_summary["gaps"]:
            st.markdown("**Areas for attention:**")
            for gap in review_summary["gaps"]:
                st.write(gap)
        
        if review_summary["recommendations"]:
            st.markdown("**Recommendations:**")
            for rec in review_summary["recommendations"]:
                st.write(f"→ {rec}")
    
    # Get review sections
    review_sections = agent.get_review_sections()
    
    # Company section
    with st.expander("Company Information"):
        for field in review_sections["company"]:
            risk_emoji = {"critical": "!", "high": "!", "medium": "!", "low": "i", "none": ""}.get(field.get("risk_level", "none"), "")
            flag = f"{risk_emoji} " if field["flagged"] else ""
            st.markdown(f"**{flag}{field['label']}**")
            
            if field.get("risk_reason"):
                st.caption(field['risk_reason'])
            
            if field["skipped"]:
                st.caption("_Skipped_")
            elif field["value"]:
                st.write(field["value"])
            else:
                st.caption("_Not provided_")
            
            st.markdown("")
    
    # Contacts section
    with st.expander("Contact Information"):
        for field in review_sections["contacts"]:
            risk_emoji = {"critical": "!", "high": "!", "medium": "!", "low": "i", "none": ""}.get(field.get("risk_level", "none"), "")
            flag = f"{risk_emoji} " if field["flagged"] else ""
            st.markdown(f"**{flag}{field['label']}**")
            
            if field.get("risk_reason"):
                st.caption(field['risk_reason'])
            
            if field["skipped"]:
                st.caption("_Skipped_")
            elif field["value"]:
                st.write(field["value"])
            else:
                st.caption("_Not provided_")
            
            st.markdown("")
    
    # Project section
    with st.expander("Project Details"):
        for field in review_sections["project"]:
            risk_emoji = {"critical": "!", "high": "!", "medium": "!", "low": "i", "none": ""}.get(field.get("risk_level", "none"), "")
            flag = f"{risk_emoji} " if field["flagged"] else ""
            st.markdown(f"**{flag}{field['label']}**")
            
            if field.get("risk_reason"):
                st.caption(field['risk_reason'])
            
            if field["skipped"]:
                st.caption("_Skipped_")
            elif field["value"]:
                if isinstance(field["value"], list):
                    st.write(", ".join(field["value"]))
                else:
                    st.write(field["value"])
            else:
                st.caption("_Not provided_")
            
            st.markdown("")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Over", use_container_width=True):
            del st.session_state.agent
            st.rerun()
    
    with col2:
        if st.button("Generate PDF", type="primary", use_container_width=True):
            with st.spinner("Generating application..."):
                pdf_data = agent.export_for_pdf()
                
                fill_application_pdf(
                    template_path=PDF_TEMPLATE_PATH,
                    output_path=OUTPUT_PDF_PATH,
                    answers=pdf_data,
                    field_map=PDF_FIELD_MAP,
                )
            
            st.success("Application ready")
            
            with open(OUTPUT_PDF_PATH, "rb") as f:
                st.download_button(
                    label="Download Application",
                    data=f,
                    file_name="Innovation_Voucher_Application.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

else:
    # ============================================================
    # INTERVIEW INTERFACE - NO CHAT METAPHORS
    # ============================================================
    
    st.subheader("Step 2: Application Interview")
    
    # Section and progress
    section = agent.state.get_section()
    section_names = {
        "company": "Company Information",
        "contacts": "Contact Details",
        "project": "Project Details"
    }
    
    # Header with section and progress
    st.markdown(f"### {section_names.get(section, 'Application')}")
    
    progress = agent.get_progress()
    st.progress(progress / 100)
    st.caption(f"{len(agent.state.completed_fields)} of {len(FIELD_ORDER)} questions answered")
    
    st.markdown("")
    
    # Get current question
    current_field = agent.state.get_current_field()
    
    if current_field:
        # Show the question prominently
        if not agent.state.conversation_history:
            question = agent.start_conversation()
        else:
            # Get last agent response for question
            last_exchange = agent.state.conversation_history[-1]
            # Question should be stored separately or extracted
            # For now, we'll just show interface
            question = "Continue with your answer below"
        
        # Show last summary if present (confirmation of previous answer)
        if agent.state.conversation_history:
            last_exchange = agent.state.conversation_history[-1]
            if last_exchange.get("agent"):
                st.info(last_exchange["agent"])
        
        # Main question display
        st.markdown(f"**{question}**")
        
        # Input area
        user_input = st.text_area(
            "Your answer",
            label_visibility="collapsed",
            height=100,
            key="answer_input"
        )
        
        st.markdown("")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            submit = st.button("Continue", type="primary", use_container_width=True, disabled=not user_input)
        
        with col2:
            # Skip button (only for optional fields)
            if current_field not in eligibility_checker.REQUIRED_FIELDS:
                if st.button("Skip for now", use_container_width=True):
                    agent.state.skip_current()
                    st.rerun()
        
        with col3:
            # Go back button
            if agent.state.current_field_index > 0:
                if st.button("← Previous", use_container_width=True):
                    agent.state.go_back()
                    st.rerun()
        
        # Process submission
        if submit and user_input:
            try:
                with st.spinner("Processing..."):
                    result = agent.process_input(user_input)
                
                # Rerun to show next question
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.caption("Please try rephrasing your answer or contact support if the issue persists.")
    
    # Sidebar progress (collapsed by default)
    with st.sidebar:
        st.caption("Progress")
        st.caption(f"Section: {section_names.get(section, 'Unknown')}")
        st.caption(f"Completed: {len(agent.state.completed_fields)}/{len(FIELD_ORDER)}")
        st.caption(f"Skipped: {len(agent.state.skipped_fields)}")
