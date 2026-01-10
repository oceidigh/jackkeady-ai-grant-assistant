"""
Eligibility checker for Enterprise Ireland Innovation Voucher
Based on official criteria from enterprise-ireland.com
"""

import streamlit as st

# ============================================================
# Eligibility Criteria (from official sources)
# ============================================================

ELIGIBILITY_QUESTIONS = [
    {
        "key": "company_type",
        "question": "Is your company a limited company registered in Ireland?",
        "help_text": "Innovation Vouchers are only available to limited companies registered in Ireland.",
        "type": "yes_no",
        "qualifying_answer": True,
        "rejection_message": "Unfortunately, only limited companies registered in Ireland are eligible for Innovation Vouchers."
    },
    {
        "key": "company_size",
        "question": "Does your company have fewer than 250 employees?",
        "help_text": "This is the SME definition used by Enterprise Ireland.",
        "type": "yes_no",
        "qualifying_answer": True,
        "rejection_message": "Unfortunately, only SMEs with fewer than 250 employees are eligible."
    },
    {
        "key": "annual_turnover",
        "question": "Is your annual turnover less than €50 million?",
        "help_text": "This is part of the SME definition.",
        "type": "yes_no",
        "qualifying_answer": True,
        "rejection_message": "Unfortunately, companies with annual turnover of €50 million or more are not eligible."
    },
    {
        "key": "excluded_type",
        "question": "Is your company any of the following: charitable organization, commercial semi-state, not-for-profit, trade association, holding company, chamber of commerce, sports body, or agricultural sector?",
        "help_text": "These organization types are excluded from the Innovation Voucher scheme.",
        "type": "yes_no",
        "qualifying_answer": False,
        "rejection_message": "Unfortunately, the following are not eligible: charitable organizations, commercial semi-state companies, not-for-profit organizations, trade associations, holding companies, chambers of commerce, sports bodies, and agricultural sector businesses."
    },
    {
        "key": "voucher_count",
        "question": "How many Innovation Vouchers have you already used?",
        "help_text": "Companies can use a maximum of 4 vouchers total (3 standard + 1 co-funded).",
        "type": "number",
        "min_value": 0,
        "max_value": 10,
        "qualifying_answer": lambda x: x < 4,
        "rejection_message": "Unfortunately, companies can only use a maximum of 4 Innovation Vouchers total."
    },
    {
        "key": "active_voucher",
        "question": "Do you currently have an active (unredeemed) Innovation Voucher?",
        "help_text": "You can only have one active voucher at a time.",
        "type": "yes_no",
        "qualifying_answer": False,
        "rejection_message": "Unfortunately, you can only have one active voucher at a time. Please complete your current voucher before applying for another."
    },
    {
        "key": "prior_ei_funding",
        "question": "Have you received more than €300,000 in Enterprise Ireland funding in the past 5 years?",
        "help_text": "Companies with >€300k in prior EI funding are not eligible for fully funded standard €5k vouchers, but can apply for co-funded vouchers.",
        "type": "yes_no",
        "qualifying_answer": False,
        "warning_message": "You're not eligible for a standard €5k voucher, but you can apply for a co-funded voucher (50-50 cost share).",
        "continue_anyway": True
    }
]


def check_eligibility():
    """
    Run the eligibility check one question at a time.
    Returns True if eligible, False if not eligible.
    """
    
    # Initialize session state for tracking
    if "eligibility_step" not in st.session_state:
        st.session_state.eligibility_step = 0
        st.session_state.eligibility_answers = {}
        st.session_state.eligible = None
    
    # If we've already completed eligibility, return the result
    if st.session_state.eligible is not None:
        return st.session_state.eligible
    
    # Get current question
    current_step = st.session_state.eligibility_step
    
    # Check if we've completed all questions
    if current_step >= len(ELIGIBILITY_QUESTIONS):
        st.session_state.eligible = True
        return True
    
    question = ELIGIBILITY_QUESTIONS[current_step]
    
    # Display progress
    st.progress((current_step + 1) / len(ELIGIBILITY_QUESTIONS))
    st.caption(f"Question {current_step + 1} of {len(ELIGIBILITY_QUESTIONS)}")
    
    # Display the question
    st.subheader(question["question"])
    if question.get("help_text"):
        st.info(question["help_text"])
    
    # Get user input based on question type
    answer = None
    
    if question["type"] == "yes_no":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes", use_container_width=True, key=f"yes_{question['key']}"):
                answer = True
        with col2:
            if st.button("❌ No", use_container_width=True, key=f"no_{question['key']}"):
                answer = False
    
    elif question["type"] == "number":
        answer = st.number_input(
            "Enter number:",
            min_value=question.get("min_value", 0),
            max_value=question.get("max_value", 100),
            step=1,
            key=f"num_{question['key']}"
        )
        if st.button("Continue", key=f"continue_{question['key']}"):
            # Button clicked, we'll process the answer
            pass
        else:
            answer = None  # Don't process until button clicked
    
    # Process the answer
    if answer is not None:
        st.session_state.eligibility_answers[question["key"]] = answer
        
        # Check if answer is qualifying
        qualifying = question["qualifying_answer"]
        if callable(qualifying):
            is_qualified = qualifying(answer)
        else:
            is_qualified = (answer == qualifying)
        
        if not is_qualified:
            # Check if there's a warning message (continue anyway)
            if question.get("continue_anyway"):
                st.warning(question.get("warning_message", "Please note this limitation."))
                st.session_state.eligibility_step += 1
                st.rerun()
            else:
                # Hard rejection
                st.error(question.get("rejection_message", "Unfortunately, you are not eligible."))
                st.session_state.eligible = False
                return False
        else:
            # Move to next question
            st.session_state.eligibility_step += 1
            st.rerun()
    
    return None  # Still in progress


def reset_eligibility():
    """Reset the eligibility check to start over"""
    st.session_state.eligibility_step = 0
    st.session_state.eligibility_answers = {}
    st.session_state.eligible = None


def show_eligibility_summary():
    """Show a summary of eligibility answers"""
    if not st.session_state.get("eligibility_answers"):
        return
    
    st.subheader("✅ Eligibility Confirmed")
    
    with st.expander("View your answers"):
        for question in ELIGIBILITY_QUESTIONS:
            key = question["key"]
            if key in st.session_state.eligibility_answers:
                answer = st.session_state.eligibility_answers[key]
                st.write(f"**{question['question']}**")
                st.write(f"Your answer: {answer}")
                st.divider()
    
    if st.button("Start Over", key="reset_eligibility"):
        reset_eligibility()
        st.rerun()
