"""
Enhanced application schema with page grouping for better UX
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
    challenge: Optional[str] = None
    description: Optional[str] = None
    objectives: List[str] = field(default_factory=list)
    skills_required: Optional[str] = None
    deliverables: List[str] = field(default_factory=list)
    commercial_impact: Optional[str] = None
    technical_uncertainty: Optional[str] = None
    timeline: Optional[str] = None


@dataclass
class ApplicationSchema:
    company: Company = field(default_factory=Company)
    contacts: Contacts = field(default_factory=Contacts)
    project: Project = field(default_factory=Project)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_field(self, path: str) -> Any:
        parts = path.split('.')
        obj = self
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return None
        return obj

    def set_field(self, path: str, value: Any) -> bool:
        parts = path.split('.')
        obj = self
        
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return False
        
        final_field = parts[-1]
        if hasattr(obj, final_field):
            setattr(obj, final_field, value)
            return True
        return False


# UX IMPROVEMENT: Page-based grouping for better flow
FIELD_PAGES = [
    {
        "id": "company_basics",
        "title": "Company Basics",
        "description": "Let's start with your company information",
        "type": "form",  # Multi-field page
        "fields": [
            {
                "path": "company.legal_name",
                "label": "Legal company name",
                "type": "text",
                "required": True,
                "help": "The official registered name"
            },
            {
                "path": "company.trading_name",
                "label": "Trading name (if different)",
                "type": "text",
                "required": False,
                "help": "Leave blank if same as legal name"
            },
            {
                "path": "company.cro_number",
                "label": "CRO number",
                "type": "text",
                "required": True,
                "help": "Companies Registration Office number"
            },
            {
                "path": "company.incorporation_date",
                "label": "Incorporation date",
                "type": "text",
                "required": False,
                "help": "Month and year (e.g., March 2020)"
            }
        ]
    },
    {
        "id": "company_address",
        "title": "Registered Address",
        "description": "Your company's registered address",
        "type": "form",
        "fields": [
            {
                "path": "company.registered_address.line1",
                "label": "Address line 1",
                "type": "text",
                "required": True
            },
            {
                "path": "company.registered_address.line2",
                "label": "Address line 2",
                "type": "text",
                "required": False
            },
            {
                "path": "company.registered_address.city",
                "label": "City/Town",
                "type": "text",
                "required": True
            },
            {
                "path": "company.registered_address.county",
                "label": "County",
                "type": "text",
                "required": True
            },
            {
                "path": "company.registered_address.eircode",
                "label": "Eircode",
                "type": "text",
                "required": False
            }
        ]
    },
    {
        "id": "company_details",
        "title": "Company Activity",
        "description": "Tell us about what your company does",
        "type": "form",
        "fields": [
            {
                "path": "company.website",
                "label": "Website",
                "type": "text",
                "required": False,
                "help": "Your company website URL"
            },
            {
                "path": "company.primary_activity",
                "label": "Primary sector/industry",
                "type": "text",
                "required": False,
                "help": "e.g., Software development, Medical devices"
            },
            {
                "path": "company.description",
                "label": "What does your company do?",
                "type": "textarea",
                "required": False,
                "help": "Brief description in 1-2 sentences"
            },
            {
                "path": "company.employees.full_time",
                "label": "Full-time employees",
                "type": "number",
                "required": False
            },
            {
                "path": "company.employees.part_time",
                "label": "Part-time employees",
                "type": "number",
                "required": False
            }
        ]
    },
    {
        "id": "contact_info",
        "title": "Main Contact",
        "description": "Who should we contact about this application?",
        "type": "form",
        "fields": [
            {
                "path": "contacts.primary.name",
                "label": "Contact name",
                "type": "text",
                "required": True
            },
            {
                "path": "contacts.primary.title",
                "label": "Job title",
                "type": "text",
                "required": False
            },
            {
                "path": "contacts.primary.email",
                "label": "Email address",
                "type": "text",
                "required": True
            },
            {
                "path": "contacts.primary.phone",
                "label": "Phone number",
                "type": "text",
                "required": False
            }
        ]
    },
    # Project fields use interview mode (AI-guided, single question)
    {
        "id": "project_title",
        "title": "Project Overview",
        "description": "Now let's talk about your innovation project",
        "type": "interview",  # Single-question AI mode
        "field": "project.title"
    },
    {
        "id": "project_challenge",
        "title": "Project Challenge",
        "description": "What problem are you solving?",
        "type": "interview",
        "field": "project.challenge"
    },
    {
        "id": "project_description",
        "title": "Innovation Description",
        "description": "What will you develop or achieve?",
        "type": "interview",
        "field": "project.description"
    },
    {
        "id": "project_uncertainty",
        "title": "Technical Uncertainty",
        "description": "What don't you know how to do yet?",
        "type": "interview",
        "field": "project.technical_uncertainty"
    },
    {
        "id": "project_skills",
        "title": "External Expertise",
        "description": "What expertise do you need?",
        "type": "interview",
        "field": "project.skills_required"
    },
    {
        "id": "project_objectives",
        "title": "Project Objectives",
        "description": "What are your main goals?",
        "type": "interview",
        "field": "project.objectives"
    },
    {
        "id": "project_deliverables",
        "title": "Expected Deliverables",
        "description": "What will you deliver at the end?",
        "type": "interview",
        "field": "project.deliverables"
    },
    {
        "id": "project_impact",
        "title": "Commercial Impact",
        "description": "How will this benefit your business?",
        "type": "interview",
        "field": "project.commercial_impact"
    },
    {
        "id": "project_timeline",
        "title": "Project Timeline",
        "description": "How long will this take?",
        "type": "interview",
        "field": "project.timeline"
    }
]

# Required fields for validation
REQUIRED_FIELDS = [
    "company.legal_name",
    "company.cro_number",
    "company.registered_address.line1",
    "company.registered_address.city",
    "company.registered_address.county",
    "contacts.primary.name",
    "contacts.primary.email",
    "project.title",
    "project.challenge",
    "project.description",
    "project.skills_required",
]

# Backwards compatibility: Extract flat field list from FIELD_PAGES
FIELD_ORDER = []
for page in FIELD_PAGES:
    if page["type"] == "form":
        for field_config in page["fields"]:
            FIELD_ORDER.append(field_config["path"])
    else:  # interview
        FIELD_ORDER.append(page["field"])
