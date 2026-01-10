# AGENT CONTRACT

**Status:** LOCKED  
**Last Updated:** 2026-01-10  
**Enforcement:** MANDATORY

This document defines the architectural contracts that govern the conversational agent system. These rules are **non-negotiable** and must be enforced at runtime.

---

## 1. Agent JSON Response Contract

Every LLM turn **MUST** return valid JSON with exactly these keys:

```json
{
  "acknowledgement": "<string>",
  "extracted_data": {<dict>},
  "summary_for_user": "<string>",
  "confidence": "high" | "medium" | "low",
  "next_question": "<string>" | "COMPLETE"
}
```

**Enforcement location:** `conversation_agent.py` lines 202-212  
**Violation behavior:** System throws `ValueError` after one retry and stops flow  
**No exceptions permitted**

---

## 2. Canonical Schema Lock

All collected data **MUST** map 1:1 to `ApplicationSchema` in `application_schema.py`.

**Rules:**
- No free-text blobs outside schema
- No invented field names
- No renaming of existing fields
- Schema changes are treated as database migrations

**Enforcement location:** `conversation_agent.py` lines 241-243  
**Violation behavior:** `set_field()` returns False; data is rejected  
**No exceptions permitted**

---

## 3. Single-Question-Per-Turn Rule

The agent **MUST** ask exactly one question per turn.

**Rules:**
- `next_question` contains one and only one question mark
- No bundled questions
- No compound questions
- No clarifications without advancing

**Enforcement location:** `conversation_agent.py` lines 228-233  
**Violation behavior:** System throws `RuntimeError` if multiple question marks detected  
**No exceptions permitted**

---

## 4. Confirmation Before Advancement

The agent **MUST NOT** advance to the next field without user confirmation.

**Rules:**
- If `extracted_data` is present, `summary_for_user` MUST also be present
- Summary must confirm understanding in grant language
- User sees confirmation before system advances

**Enforcement location:** `conversation_agent.py` lines 235-251  
**Violation behavior:** System throws `RuntimeError` if data extracted without summary  
**No exceptions permitted**

---

## 5. Mandatory Review Mode

The system **MUST** enter explicit review mode before completion.

**Rules:**
- Review mode iterates through all sections
- Each field is presented with confidence flag
- Skipped fields are marked
- Low-confidence fields are flagged
- User can edit any field before final submission
- Agent cannot proceed to PDF generation without review

**Enforcement location:** `conversation_agent.py` lines 293-339, `app_new.py` lines 77-79  
**Violation behavior:** System throws `RuntimeError` if review skipped  
**No exceptions permitted**

---

## 6. State Tracking (Never Inferred)

Agent state **MUST** be explicit and never inferred from chat history.

**Rules:**
- `AgentState` object maintains canonical state
- State includes: `current_field_index`, `completed_fields`, `skipped_fields`, `confidence_flags`, `in_review_mode`
- Chat history is for display only
- State is single source of truth

**Enforcement location:** `conversation_agent.py` lines 11-23  
**Violation behavior:** Any inference from history is architectural violation  
**No exceptions permitted**

---

## 7. Failure Over Degradation

The system **MUST** fail loudly rather than degrade silently.

**Rules:**
- No soft fallbacks
- No "make it work" logic
- No silent error recovery
- All violations throw exceptions
- No continuation after contract breach

**Enforcement location:** `conversation_agent.py` line 270  
**Violation behavior:** All errors propagate as `RuntimeError` or `ValueError`  
**No exceptions permitted**

---

## 8. Separation of Concerns

Agent logic **MUST** remain isolated from UI, storage, and voice layers.

**Rules:**
- `conversation_agent.py` contains only agent logic
- `app_new.py` contains only UI logic
- `application_schema.py` contains only data structure
- No mixing of responsibilities
- No tight coupling

**Enforcement:** Manual code review  
**Violation behavior:** Architectural debt; immediate refactor required  
**No exceptions permitted**

---

## Modification Policy

**To modify this contract:**
1. Document the proposed change in a separate proposal file
2. Explain why the change is necessary
3. Demonstrate that the change does not compromise rigor
4. Update enforcement code before updating contract
5. Update contract tests to match new enforcement

**Unauthorized modifications to this contract are considered architectural violations.**

---

## Test Requirements

Any system claiming compliance with this contract **MUST** have:
1. Automated test validating JSON contract enforcement
2. Automated test validating single-question rule
3. Golden-path transcript demonstrating full compliance
4. Review mode enforcement test

**Location:** `tests/test_agent_contract.py`

---

**End of Contract**
