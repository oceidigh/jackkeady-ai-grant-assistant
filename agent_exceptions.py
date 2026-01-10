"""
Custom exceptions for conversation agent
Allows agent logic to be pure Python without Streamlit dependency
"""


class AgentContractError(Exception):
    """Raised when agent violates JSON response contract"""
    pass


class AgentValidationError(Exception):
    """Raised when agent response fails validation"""
    pass


class AgentProcessingError(Exception):
    """Raised when agent encounters processing errors"""
    pass
