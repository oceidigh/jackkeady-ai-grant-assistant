"""
Canonical schema for Innovation Voucher application.
Single source of truth for all application data.
Maps 1:1 to Enterprise Ireland Innovation Voucher form fields.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Address:
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    eircode: Optional[str] = None
    country: str = "Ireland"


@dataclass
class Employees:
    full_time: Optional[int] = None
    part_time: Optional[int] = None


@dataclass
class Company:
    legal_name: Optional[str] = None
    trading_name: Optional[str] = None
    cro_number: Optional[str] = None
    incorporation_date: Optional[str] = None
    registered_address: Address = field(default_factory=Address)
    website: Optional[str] = None
    primary_activity: Optional[str] = None
    description: Optional[str] = None
    employees: Employees = field(default_factory=Employees)


@dataclass
class Contact:
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class Contacts:
    primary: Contact = field(default_factory=Contact)


@dataclass
class Project:
    title: Optional[str] = None
    challenge: Optional[str] = None  # What problem are you solving?
    description: Optional[str] = None  # Proposed innovation
    objectives: List[str] = field(default_factory=list)
    skills_required: Optional[str] = None  # External expertise needed
    deliverables: List[str] = field(default_factory=list)
    commercial_impact: Optional[str] = None  # How will company benefit?
    technical_uncertainty: Optional[str] = None  # Knowledge gaps
    timeline: Optional[str] = None


@dataclass
class ApplicationSchema:
    company: Company = field(default_factory=Company)
    contacts: Contacts = field(default_factory=Contacts)
    project: Project = field(default_factory=Project)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary"""
        return asdict(self)

    def get_field(self, path: str) -> Any:
        """Get field value by dot-notation path (e.g., 'company.legal_name')"""
        parts = path.split('.')
        obj = self
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return None
        return obj

    def set_field(self, path: str, value: Any) -> bool:
        """Set field value by dot-notation path"""
        parts = path.split('.')
        obj = self
        
        # Navigate to parent object
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return False
        
        # Set final field
        final_field = parts[-1]
        if hasattr(obj, final_field):
            setattr(obj, final_field, value)
            return True
        return False

    def get_completion_percentage(self) -> float:
        """Calculate how much of the schema is filled"""
        total_fields = 0
        filled_fields = 0
        
        def count_fields(obj):
            nonlocal total_fields, filled_fields
            if hasattr(obj, '__dataclass_fields__'):
                for field_name, field_def in obj.__dataclass_fields__.items():
                    value = getattr(obj, field_name)
                    if isinstance(value, list):
                        total_fields += 1
                        if len(value) > 0:
                            filled_fields += 1
                    elif hasattr(value, '__dataclass_fields__'):
                        count_fields(value)
                    else:
                        total_fields += 1
                        if value is not None and value != "":
                            filled_fields += 1
        
        count_fields(self)
        return (filled_fields / total_fields * 100) if total_fields > 0 else 0


# Field navigation for agent
FIELD_ORDER = [
    # Company section
    "company.legal_name",
    "company.trading_name",
    "company.cro_number",
    "company.incorporation_date",
    "company.registered_address.line1",
    "company.registered_address.line2",
    "company.registered_address.city",
    "company.registered_address.county",
    "company.registered_address.eircode",
    "company.website",
    "company.primary_activity",
    "company.description",
    "company.employees.full_time",
    "company.employees.part_time",
    
    # Contacts section
    "contacts.primary.name",
    "contacts.primary.title",
    "contacts.primary.email",
    "contacts.primary.phone",
    
    # Project section
    "project.title",
    "project.challenge",
    "project.description",
    "project.technical_uncertainty",
    "project.skills_required",
    "project.objectives",
    "project.deliverables",
    "project.commercial_impact",
    "project.timeline",
]

# Required fields (cannot be skipped)
REQUIRED_FIELDS = [
    "company.legal_name",
    "company.cro_number",
    "contacts.primary.name",
    "contacts.primary.email",
    "project.title",
    "project.challenge",
    "project.description",
    "project.skills_required",
]
