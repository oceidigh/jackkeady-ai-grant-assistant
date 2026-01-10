import os
import streamlit as st
from pdf_utils import fill_application_pdf
import eligibility_checker
from conversation_agent import init_agent

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
# Page Config
# ============================================================
st.set_page_config(
    page_title="Innovation Voucher Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
st.title("🇮🇪 Innovation Voucher Assistant")
st.caption("AI-powered application assistant · Enterprise Ireland")

st.header("Step 1: Eligibility Check")
st.info("First, let's verify you're eligible for an Innovation Voucher.")

eligibility_result = eligibility_checker.check_eligibility()

# Stop if not eligible
if eligibility_result is False:
    st.stop()

# Still checking eligibility
if eligibility_result is None:
    st.stop()

# ============================================================
# PHASE 2: CONVERSATIONAL DATA COLLECTION
# ============================================================
st.success("✅ You're eligible to apply!")
eligibility_checker.show_eligibility_summary()

st.divider()
st.header("Step 2: Application Interview")
st.info(
    "I'll ask you some questions about your company and project. "
    "Just answer naturally - I'll convert everything into proper grant language. "
    "You can say 'skip' to skip optional fields."
)

# Initialize agent
agent = init_agent()

# Show progress
progress = agent.get_progress()
st.progress(progress / 100)
st.caption(f"Progress: {progress:.0f}% complete")

# Check if conversation is complete
if agent.state.is_complete():
    st.success("🎉 Interview complete!")
    
    st.subheader("Review Your Application")
    
    with st.expander("Company Information", expanded=True):
        st.write(f"**Legal Name:** {agent.schema.company.legal_name or 'Not provided'}")
        st.write(f"**Trading Name:** {agent.schema.company.trading_name or 'Same as legal name'}")
        st.write(f"**CRO Number:** {agent.schema.company.cro_number or 'Not provided'}")
        st.write(f"**Employees:** {agent.schema.company.employees.full_time or 0} FT, {agent.schema.company.employees.part_time or 0} PT")
    
    with st.expander("Contact Information", expanded=True):
        st.write(f"**Name:** {agent.schema.contacts.primary.name or 'Not provided'}")
        st.write(f"**Email:** {agent.schema.contacts.primary.email or 'Not provided'}")
        st.write(f"**Phone:** {agent.schema.contacts.primary.phone or 'Not provided'}")
    
    with st.expander("Project Details", expanded=True):
        st.write(f"**Title:** {agent.schema.project.title or 'Not provided'}")
        st.write(f"**Challenge:** {agent.schema.project.challenge or 'Not provided'}")
        st.write(f"**Description:** {agent.schema.project.description or 'Not provided'}")
        st.write(f"**Timeline:** {agent.schema.project.timeline or 'Not provided'}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Start Over", use_container_width=True):
            # Clear agent from session state
            del st.session_state.agent
            st.rerun()
    
    with col2:
        if st.button("📄 Generate PDF Application", type="primary", use_container_width=True):
            with st.spinner("Generating your application PDF..."):
                # Export data for PDF
                pdf_data = agent.export_for_pdf()
                
                # Generate PDF
                fill_application_pdf(
                    template_path=PDF_TEMPLATE_PATH,
                    output_path=OUTPUT_PDF_PATH,
                    answers=pdf_data,
                    field_map=PDF_FIELD_MAP,
                )
            
            st.success("✅ PDF generated!")
            
            with open(OUTPUT_PDF_PATH, "rb") as f:
                st.download_button(
                    label="⬇️ Download Innovation Voucher Application",
                    data=f,
                    file_name="Innovation_Voucher_Application.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

else:
    # ============================================================
    # CONVERSATION INTERFACE
    # ============================================================
    
    # Display conversation history
    if agent.state.conversation_history:
        with st.container():
            for exchange in agent.state.conversation_history[-3:]:  # Show last 3 exchanges
                with st.chat_message("user"):
                    st.write(exchange["user"])
                with st.chat_message("assistant"):
                    st.write(exchange["agent"])
    
    # Show current question
    current_field = agent.state.get_current_field()
    if current_field:
        # Get the question for current field
        if not agent.state.conversation_history:
            # First question
            question = agent.start_conversation()
            with st.chat_message("assistant"):
                st.write(question)
        else:
            # Show last assistant message if it contains a question
            last_exchange = agent.state.conversation_history[-1]
            # The next question should already be in the last response
    
    # User input
    user_input = st.chat_input("Type your answer here...")
    
    if user_input:
        # Show user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process input
        with st.spinner("Processing..."):
            result = agent.process_input(user_input)
        
        # Show agent response
        with st.chat_message("assistant"):
            if result.get("summary_for_user"):
                st.write(result["summary_for_user"])
            
            # Show confidence flag if low
            if result.get("confidence") == "low":
                st.warning("⚠️ I'm not completely sure I understood that correctly.")
            
            # Show next question if not complete
            if result.get("next_question") and result["next_question"] != "COMPLETE":
                st.write("")
                st.write(result["next_question"])
        
        # Rerun to update UI
        st.rerun()
    
    # Show section info
    section = agent.state.get_section()
    section_names = {
        "company": "Company Information",
        "contacts": "Contact Details",
        "project": "Project Details"
    }
    st.sidebar.info(f"**Current Section:** {section_names.get(section, 'Unknown')}")
    
    # Show field completion
    st.sidebar.caption(f"**Fields completed:** {len(agent.state.completed_fields)}/{len(eligibility_checker.ELIGIBILITY_QUESTIONS)}")
    st.sidebar.caption(f"**Fields skipped:** {len(agent.state.skipped_fields)}")
