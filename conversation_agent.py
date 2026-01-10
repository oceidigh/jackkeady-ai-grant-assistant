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
    
    def is_complete(self) -> bool:
        """Check if all fields are collected"""
        return self.current_field_index >= len(FIELD_ORDER)
    
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
    
    SYSTEM_PROMPT = """You are an expert Enterprise Ireland grant consultant conducting a structured but conversational application interview.

Your goals:
1. Collect all required Innovation Voucher application data
2. Ask one question at a time
3. Translate informal user input into clear, formal grant language
4. Never expose form field names or internal structure
5. Confirm understanding before moving on
6. If information is unclear, ask a follow-up
7. If the user says "skip", mark the field as skipped and continue

Rules:
- Be concise and professional
- Do not repeat completed questions
- Do not ask multiple questions at once
- Do not invent facts
- If the user rambles, summarise and confirm
- If confidence is low, flag the answer

Response format:
You MUST respond in valid JSON with these exact keys:
- acknowledgement: Brief acknowledgement of user input
- extracted_data: Dict mapping field paths to values (e.g., {"company.legal_name": "Acme Ltd"})
- summary_for_user: Clean summary of what you understood in grant language
- confidence: "high" | "medium" | "low"
- next_question: The next question to ask (or "COMPLETE" if done)

CRITICAL: Your response must be ONLY valid JSON. No markdown, no code fences, no explanations."""

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
        
        # Call LLM
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
            
            # Update schema with extracted data
            if result.get("extracted_data"):
                for field_path, value in result["extracted_data"].items():
                    self.schema.set_field(field_path, value)
            
            # Update state
            current_field = self.state.get_current_field()
            if current_field and result.get("confidence"):
                self.state.confidence_flags[current_field] = result["confidence"]
            
            # Advance if we got data
            if result.get("extracted_data"):
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
            
        except json.JSONDecodeError as e:
            st.error(f"AI response was not valid JSON: {e}")
            st.code(raw)
            # Return safe fallback
            return {
                "acknowledgement": "I'm having trouble processing that.",
                "extracted_data": {},
                "summary_for_user": "Could you rephrase that?",
                "confidence": "low",
                "next_question": self._get_field_question(self.state.get_current_field())
            }
        except Exception as e:
            st.error(f"Error processing input: {e}")
            return {
                "acknowledgement": "Something went wrong.",
                "extracted_data": {},
                "summary_for_user": "Let's try that again.",
                "confidence": "low",
                "next_question": self._get_field_question(self.state.get_current_field())
            }
    
    def start_conversation(self) -> str:
        """Get the first question"""
        first_field = FIELD_ORDER[0]
        return self._get_field_question(first_field)
    
    def get_progress(self) -> float:
        """Get completion percentage"""
        return (self.state.current_field_index / len(FIELD_ORDER)) * 100
    
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
