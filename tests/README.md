# Contract Enforcement Test Suite

## Purpose

This test suite enforces the architectural contracts defined in `AGENT_CONTRACT.md`.

**These tests are NOT optional.**  
**These tests are NOT flexible.**  
**These tests are NOT developer conveniences.**

They are **architectural safeguards** that prevent regression.

## Running Tests

```bash
pytest tests/
```

## Test Categories

### Contract Enforcement Tests (`test_agent_contract.py`)

These tests validate that contract violations cause **hard errors**:

- **test_missing_json_key_throws_error**: Validates Rule 1 (JSON contract)
- **test_multiple_questions_throws_error**: Validates Rule 3 (single question)
- **test_data_without_confirmation_throws_error**: Validates Rule 4 (confirmation)
- **test_invalid_json_throws_error_after_retry**: Validates Rule 7 (fail loudly)
- **test_review_mode_required_before_completion**: Validates Rule 5 (review mode)
- **test_edit_outside_review_mode_throws_error**: Validates Rule 5 (review enforcement)
- **test_invalid_field_path_rejected**: Validates Rule 2 (schema lock)
- **test_state_independent_of_history**: Validates Rule 6 (explicit state)

**If any of these tests are removed or weakened, the architecture is considered broken.**

### Golden Path Test

- **test_golden_path_exists**: Ensures regression baseline exists

The golden path transcript (`golden_path_transcript.json`) documents a complete successful interaction. It is used to:
- Detect architectural drift
- Validate refactors
- Serve as integration baseline for voice layer
- Document expected agent behavior

## Critical Rules

1. **Do NOT mock away contract enforcement**
   - Tests must exercise real validation logic
   - Mocks should only stub external dependencies (OpenAI API)

2. **Do NOT weaken assertions**
   - Tests must verify exceptions are raised
   - Tests must check exact error messages
   - Tests must not allow silent failures

3. **Do NOT skip tests**
   - Every test must pass on every commit
   - Skipped tests indicate architectural debt

4. **Do NOT remove tests**
   - Removing a test removes enforcement
   - Architecture becomes unprotected

## Failure Interpretation

### If a contract test fails:
1. **Stop all development**
2. Determine if:
   - Code violated contract (fix code)
   - Contract needs revision (update AGENT_CONTRACT.md first)
3. Never weaken test to make it pass

### If golden path test fails:
1. Check if changes are intentional
2. If yes: Update golden path with new baseline
3. If no: Revert changes causing drift

## Adding New Contracts

To add a new contract:
1. Update `AGENT_CONTRACT.md` with new rule
2. Add enforcement code to relevant module
3. Add test validating enforcement
4. Update this README

## Test Maintenance

These tests should be updated only when:
- New contracts are added
- Contract definitions change (rare)
- Enforcement mechanisms relocate

**These tests should NEVER be updated to accommodate code that violates contracts.**

---

**Remember: Passing tests mean contracts are enforced. Failing tests mean architecture is protected.**
