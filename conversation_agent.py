"""
Stateful conversational agent for Innovation Voucher applications.
Implements the agent loop from the implementation brief.
"""

import json
import streamlit as st
from typing import Optional, Dict, Any, List
from openai import OpenAI
from application_schema import ApplicationSchema, FIELD_ORDER, REQUIRED_FIELDS


class AgentState:
    """Tracks conversation state"""
    def __init__(self):
        self.current_field_index: int = 0
        self.completed_fields: List[str] = []
        self.skipped_fields: List[str] = []
        self.confidence_flags: Dict[str, str] = {}  # field -> "high" | "medium" | "low"
        self.conversation_history: List[Dict[str, str]] = []
        self.in_review_mode: bool = False  # Rule 5 enforcement
        self.review_edits: Dict[str, Any] = {}  # Track edits during review
    
    def get_current_field(self) -> Optional[str]:
        """Get the field we're currently collecting"""
        if self.current_field_index < len(FIELD_ORDER):
            return FIELD_ORDER[self.current_field_index]
        return None
    
    def advance(self):
        """Move to next field"""
        current = self.get_current_field()
        if current:
            self.completed_fields.append(current)
        self.current_field_index += 1
    
    def skip_current(self):
        """Skip current field and advance"""
        current = self.get_current_field()
        if current and current not in REQUIRED_FIELDS:
            self.skipped_fields.append(current)
            self.current_field_index += 1
            return True
        return False
    
    def go_back(self) -> bool:
        """Go back to previous field for editing"""
        if self.current_field_index > 0:
            self.current_field_index -= 1
            # Remove from completed if present
            prev_field = self.get_current_field()
            if prev_field in self.completed_fields:
                self.completed_fields.remove(prev_field)
            return True
        return False
    
    def is_complete(self) -> bool:
        """Check if all fields are collected"""
        return self.current_field_index >= len(FIELD_ORDER)
    
    def enter_review_mode(self):
        """Rule 5: Enter formal review mode"""
        self.in_review_mode = True
    
    def exit_review_mode(self):
        """Exit review mode"""
        self.in_review_mode = False
    
    def get_section(self) -> str:
        """Get current section name"""
        current = self.get_current_field()
        if not current:
            return "complete"
        if current.startswith("company"):
            return "company"
        elif current.startswith("contacts"):
            return "contacts"
        elif current.startswith("project"):
            return "project"
        return "unknown"


class ConversationAgent:
    """Manages conversational data collection"""
    
    SYSTEM_PROMPT = """You are an expert Enterprise Ireland grant consultant conducting a structured interview.

CRITICAL INTERVIEW RULES:
1. You are an INTERVIEWER, not a summarizer
2. Every response MUST end with exactly ONE explicit question
3. NEVER make declarative statements about what the user said
4. NEVER assume confirmation from short replies like "yes"
5. ALWAYS restate your understanding and ask for explicit confirmation
6. Ask one question at a time

BANNED BEHAVIORS:
❌ "The company trades under a different name." (declarative - not allowed)
❌ "The company is focused on..." (assumption - not allowed)
❌ Advancing without asking next question
❌ Treating "yes" as complete confirmation

CORRECT BEHAVIORS:
✓ "Thanks. Just to be clear, does the company trade under a different name than its registered name?"
✓ "I understand you want to [restate]. Can you tell me more about [specific aspect]?"
✓ Always end with "?"

FIELD-SPECIFIC REWRITE GUIDANCE:
When collecting project fields (challenge, description, commercial_impact), transform informal input into evaluator-grade language:
- PROJECT CHALLENGE: Focus on the specific problem, its impact, and why current solutions are inadequate. Avoid vague terms.
- PROJECT DESCRIPTION: Describe the innovation in terms of what will be developed, validated, or achieved. Focus on tangible outputs.
- COMMERCIAL IMPACT: Explain concrete business outcomes (market access, certification, revenue potential, competitive advantage).
- TECHNICAL UNCERTAINTY: Identify specific knowledge gaps, unproven assumptions, or validation needs.
- SKILLS REQUIRED: Name actual expertise areas, facilities, or capabilities needed.

WEAK ANSWER DETECTION:
Mark confidence as LOW and ask a follow-up if the answer:
- Is fewer than 10 words for project fields
- Contains only buzzwords without specifics
- Lacks concrete detail
- Is vague about outcomes, methods, or impact

When this happens, ask ONE targeted question to strengthen the answer. Do NOT advance until specificity improves.

CONFIDENCE SCORING RULES:
- HIGH: Answer contains specific detail, concrete outcomes, clear context, and no ambiguity. Grant-ready.
- MEDIUM: Answer has some detail but lacks full specificity or contains minor ambiguities. Usable but could be stronger.
- LOW: Answer is vague, generic, very brief, or requires assumptions. Cannot write quality grant text without follow-up.

REWRITING PRINCIPLES:
- Keep all factual content from user input
- Do NOT invent numbers, dates, or details
- Transform casual language into formal grant language
- Remove filler words and conversational hedges
- Structure information clearly with specific outcomes

Response format (MUST be valid JSON):
{
  "acknowledgement": "Brief acknowledgement",
  "extracted_data": {"field.path": "value"},
  "summary_for_user": "Professional summary of what you understood",
  "confidence": "high" | "medium" | "low",
  "next_question": "ONE explicit question ending with ?"
}

CRITICAL: Your response must be ONLY valid JSON. No markdown, no code fences, no explanations.
CRITICAL: next_question MUST be a question ending with "?" - declarative statements are forbidden."""

    def __init__(self):
        self.client = OpenAI()
        self.schema = ApplicationSchema()
        self.state = AgentState()
    
    def _get_field_question(self, field_path: str) -> str:
        """Map field to natural question"""
        questions = {
            "company.legal_name": "What's your company's legal name?",
            "company.trading_name": "Do you trade under a different name, or is it the same as your legal name?",
            "company.cro_number": "What's your CRO number?",
            "company.incorporation_date": "When was the company incorporated?",
            "company.registered_address.line1": "What's the first line of your registered address?",
            "company.registered_address.line2": "Is there a second line for the address, or can we skip that?",
            "company.registered_address.city": "What city or town?",
            "company.registered_address.county": "What county?",
            "company.registered_address.eircode": "What's the Eircode?",
            "company.website": "Do you have a website?",
            "company.primary_activity": "What sector or industry does the company operate in?",
            "company.description": "Can you describe what the company does in a sentence or two?",
            "company.employees.full_time": "How many full-time employees do you have?",
            "company.employees.part_time": "How many part-time employees?",
            
            "contacts.primary.name": "Who should I put as the main contact for this application?",
            "contacts.primary.title": "What's their job title?",
            "contacts.primary.email": "What's their email address?",
            "contacts.primary.phone": "And their phone number?",
            
            "project.title": "Let's talk about the project. What would you call it?",
            "project.challenge": "What's the main problem or challenge you're trying to solve?",
            "project.description": "What's the innovation you're proposing? What are you aiming to develop or achieve?",
            "project.technical_uncertainty": "What are the technical or knowledge gaps? What don't you know how to do yet?",
            "project.skills_required": "What kind of external expertise or facilities do you need that you don't have in-house?",
            "project.objectives": "What are the main objectives or goals of this project? Tell me the key things you want to achieve.",
            "project.deliverables": "What will you actually deliver at the end? Think reports, prototypes, validated findings, etc.",
            "project.commercial_impact": "How will this benefit your company commercially? Why does this matter for your business?",
            "project.timeline": "How long do you think this project will take?",
        }
        return questions.get(field_path, "Can you provide more information?")
    
    def _build_context(self, user_input: str) -> Dict[str, Any]:
        """Build structured context for LLM"""
        current_field = self.state.get_current_field()
        
        return {
            "current_field": current_field,
            "field_question": self._get_field_question(current_field) if current_field else None,
            "is_required": current_field in REQUIRED_FIELDS if current_field else False,
            "known_data": self.schema.to_dict(),
            "completed_fields": self.state.completed_fields,
            "user_input": user_input,
            "instruction": "Extract data from user input and determine next question"
        }
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Main agent loop:
        User input → Interpret → Extract → Update schema → Update state → Respond
        """
        
        # Check for skip command
        if user_input.lower().strip() in ["skip", "skip this", "pass"]:
            if self.state.skip_current():
                next_field = self.state.get_current_field()
                return {
                    "acknowledgement": "Okay, skipping.",
                    "extracted_data": {},
                    "summary_for_user": "Field skipped.",
                    "confidence": "high",
                    "next_question": self._get_field_question(next_field) if next_field else "COMPLETE"
                }
            else:
                return {
                    "acknowledgement": "Sorry, this field is required.",
                    "extracted_data": {},
                    "summary_for_user": "This field cannot be skipped.",
                    "confidence": "high",
                    "next_question": self._get_field_question(self.state.get_current_field())
                }
        
        # Build context
        context = self._build_context(user_input)
        
        # Call LLM with retry logic
        max_retries = 1
        raw = None
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(context, indent=2)}
                    ],
                    temperature=0.3,
                )
                
                raw = response.choices[0].message.content.strip()
                
                # Remove markdown fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                
                result = json.loads(raw)
                
                # Validate required keys (Rule 1 enforcement)
                required_keys = ["acknowledgement", "extracted_data", "summary_for_user", "confidence", "next_question"]
                missing_keys = [k for k in required_keys if k not in result]
                
                if missing_keys:
                    if attempt < max_retries:
                        # Retry with correction prompt
                        context["instruction"] = f"CORRECTION: Your previous response was missing these required keys: {missing_keys}. Respond with valid JSON containing all required keys."
                        continue
                    else:
                        raise ValueError(f"Agent response missing required keys: {missing_keys}")
                
                # Valid response, break retry loop
                break
                
            except json.JSONDecodeError as e:
                if attempt < max_retries:
                    # Retry with correction prompt
                    context["instruction"] = "CORRECTION: Your previous response was not valid JSON. Respond ONLY with valid JSON, no markdown, no code fences."
                    continue
                else:
                    # Hard error after retry
                    st.error("**SYSTEM ERROR: Agent failed to return valid JSON after retry**")
                    st.code(raw if raw else "No response")
                    raise RuntimeError(f"Agent contract violation: Invalid JSON after {max_retries + 1} attempts") from e
        
        # Validate single-question rule (Rule 4 enforcement)
        next_q = result.get("next_question", "")
        if next_q != "COMPLETE":
            # CRITICAL: Agent must ask explicit question, not make declarative statements
            if not next_q or not next_q.strip():
                raise RuntimeError("Agent contract violation: next_question cannot be empty")
            
            # Must end with question mark (interview discipline)
            if not next_q.strip().endswith("?"):
                raise RuntimeError(f"Agent contract violation: Response must end with explicit question. Got: '{next_q}'")
            
            # Check for multiple questions
            question_indicators = next_q.count("?")
            if question_indicators > 1:
                raise RuntimeError(f"Agent contract violation: Multiple questions detected in next_question. Only one question allowed per turn.")
        
        # Rule 4 enforcement: Require confirmation before advancing
        # Check if we need confirmation (extracted data present but no explicit confirmation yet)
        if result.get("extracted_data") and not result.get("summary_for_user"):
            raise RuntimeError("Agent contract violation: Cannot advance without providing summary_for_user confirmation.")
        
        # STAGE 2: Weak answer detection - prevent advancement if confidence is low and this is a project field
        current_field = self.state.get_current_field()
        if (result.get("confidence") == "low" and 
            current_field and 
            current_field.startswith("project.") and
            result.get("extracted_data")):
            
            # Low confidence on project field with data = weak answer detected
            # Do NOT advance - the next_question should be a follow-up
            # Store in history but don't update schema or advance state
            self.state.conversation_history.append({
                "user": user_input,
                "agent": result.get("summary_for_user", "") + "\n\n[Quality check: Answer needs more detail]"
            })
            
            # Return result with follow-up question, no advancement
            return result
        
        # Update schema with extracted data ONLY after summary provided and quality check passed
        if result.get("extracted_data") and result.get("summary_for_user"):
            for field_path, value in result["extracted_data"].items():
                self.schema.set_field(field_path, value)
            
            # Update state
            if current_field and result.get("confidence"):
                self.state.confidence_flags[current_field] = result["confidence"]
            
            # Advance only after confirmation provided and quality validated
            self.state.advance()
            
            # Store in history
            self.state.conversation_history.append({
                "user": user_input,
                "agent": result.get("summary_for_user", "")
            })
            
            # Check if complete
            if self.state.is_complete():
                result["next_question"] = "COMPLETE"
            elif result.get("next_question") == "COMPLETE":
                # Override if not actually complete
                next_field = self.state.get_current_field()
                if next_field:
                    result["next_question"] = self._get_field_question(next_field)
            
            return result
            
        # All errors are hard errors - no soft fallbacks (Rule 7)
    
    def start_conversation(self) -> str:
        """Get the first question"""
        first_field = FIELD_ORDER[0]
        return self._get_field_question(first_field)
    
    def get_progress(self) -> float:
        """Get completion percentage"""
        return (self.state.current_field_index / len(FIELD_ORDER)) * 100
    
    def enter_review_mode(self):
        """Rule 5: Enter formal review mode (mandatory before completion)"""
        if not self.state.is_complete():
            raise RuntimeError("Cannot enter review mode: data collection not complete")
        self.state.enter_review_mode()
    
    def get_review_sections(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Rule 5: Generate review sections with flagged fields
        STAGE 2: Enhanced with quality assessment and risk highlighting
        Returns sections with field name, value, confidence, and skipped status
        """
        sections = {
            "company": [],
            "contacts": [],
            "project": []
        }
        
        for field_path in FIELD_ORDER:
            section = field_path.split(".")[0]
            value = self.schema.get_field(field_path)
            confidence = self.state.confidence_flags.get(field_path, "unknown")
            is_skipped = field_path in self.state.skipped_fields
            is_required = field_path in REQUIRED_FIELDS
            
            # STAGE 2: Enhanced risk assessment
            risk_level = "none"
            risk_reason = None
            
            if is_skipped and is_required:
                risk_level = "critical"
                risk_reason = "Required field skipped"
            elif is_skipped:
                risk_level = "medium"
                risk_reason = "Optional field skipped"
            elif confidence == "low":
                risk_level = "high"
                risk_reason = "Low confidence - may need strengthening"
            elif confidence == "medium" and field_path.startswith("project."):
                risk_level = "low"
                risk_reason = "Could be more specific for evaluators"
            
            field_data = {
                "path": field_path,
                "label": field_path.split(".")[-1].replace("_", " ").title(),
                "value": value,
                "confidence": confidence,
                "skipped": is_skipped,
                "required": is_required,
                "flagged": confidence == "low" or is_skipped,
                "risk_level": risk_level,  # STAGE 2: Added risk assessment
                "risk_reason": risk_reason  # STAGE 2: Added risk explanation
            }
            
            sections[section].append(field_data)
        
        return sections
    
    def get_review_summary(self) -> Dict[str, Any]:
        """
        STAGE 2: Generate professional review summary for consultant-style review
        Returns overall assessment with strengths, gaps, and recommendations
        """
        sections = self.get_review_sections()
        
        # Count quality metrics
        total_fields = len(FIELD_ORDER)
        completed_fields = len([f for f in FIELD_ORDER if f not in self.state.skipped_fields])
        high_confidence = sum(1 for f in self.state.confidence_flags.values() if f == "high")
        low_confidence = sum(1 for f in self.state.confidence_flags.values() if f == "low")
        skipped_required = len([f for f in self.state.skipped_fields if f in REQUIRED_FIELDS])
        skipped_optional = len(self.state.skipped_fields) - skipped_required
        
        # Assess project section quality (most critical for grant)
        project_fields = [f for f in sections["project"] if not f["skipped"]]
        project_quality = "strong"
        if any(f["confidence"] == "low" for f in project_fields):
            project_quality = "needs strengthening"
        elif any(f["confidence"] == "medium" for f in project_fields):
            project_quality = "adequate"
        
        # Generate strengths
        strengths = []
        if high_confidence > total_fields * 0.7:
            strengths.append("Strong level of detail across most fields")
        if completed_fields == total_fields:
            strengths.append("All information provided - no gaps")
        if project_quality == "strong":
            strengths.append("Project section is well-defined and specific")
        
        # Generate gaps and risks
        gaps = []
        if skipped_required > 0:
            gaps.append(f"⚠️ CRITICAL: {skipped_required} required field(s) skipped")
        if low_confidence > 0:
            gaps.append(f"⚠️ {low_confidence} field(s) marked low confidence - may need strengthening")
        if skipped_optional > 0:
            gaps.append(f"ℹ️ {skipped_optional} optional field(s) skipped")
        if project_quality == "needs strengthening":
            gaps.append("⚠️ Project section needs more specific detail for evaluators")
        
        # Generate recommendations
        recommendations = []
        if low_confidence > 0:
            recommendations.append("Review and strengthen low-confidence fields before submission")
        if skipped_required > 0:
            recommendations.append("Complete all required fields before submission")
        if project_quality != "strong":
            recommendations.append("Add more specific outcomes and metrics to project description")
        if not recommendations:
            recommendations.append("Application appears submission-ready")
        
        return {
            "completion_rate": f"{completed_fields}/{total_fields}",
            "high_confidence_rate": f"{high_confidence}/{completed_fields}",
            "project_quality": project_quality,
            "strengths": strengths,
            "gaps": gaps,
            "recommendations": recommendations,
            "overall_readiness": "ready" if not gaps else "needs_review"
        }
    
    def edit_field_in_review(self, field_path: str, new_value: Any):
        """Rule 5: Allow targeted edits during review"""
        if not self.state.in_review_mode:
            raise RuntimeError("Cannot edit: not in review mode")
        
        self.schema.set_field(field_path, new_value)
        self.state.review_edits[field_path] = new_value
        
        # Update confidence to high after manual edit
        self.state.confidence_flags[field_path] = "high"
    
    def export_for_pdf(self) -> Dict[str, str]:
        """Export collected data in format needed for PDF generation"""
        return {
            "innovative_product": self.schema.project.description or "",
            "primary_issues": self.schema.project.challenge or "",
            "skills_expertise": self.schema.project.skills_required or "",
            "expected_deliverables": ", ".join(self.schema.project.deliverables) if self.schema.project.deliverables else "",
            "company_benefit": self.schema.project.commercial_impact or "",
        }


def init_agent():
    """Initialize agent in session state"""
    if "agent" not in st.session_state:
        st.session_state.agent = ConversationAgent()
    return st.session_state.agent       
