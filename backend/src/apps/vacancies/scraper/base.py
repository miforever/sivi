"""Shared data types for the vacancy scraper pipeline."""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime

# ---- Shared skill extraction (used by both channel and platform parsers) ----

KNOWN_SKILLS = [
    # Programming & IT
    "Python",
    "Django",
    "FastAPI",
    "DRF",
    "Flask",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Angular",
    "Next.js",
    "Node.js",
    "Nest.js",
    "Java",
    "Spring",
    "Kotlin",
    "Go",
    "Golang",
    "Rust",
    "C++",
    "C#",
    ".NET",
    "PHP",
    "Laravel",
    "Swift",
    "Flutter",
    "React Native",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "CI/CD",
    "Git",
    "Linux",
    "Nginx",
    "HTML",
    "CSS",
    "Tailwind",
    "Bootstrap",
    "Figma",
    "Photoshop",
    "Illustrator",
    "Power BI",
    "Tableau",
    "Excel",
    "Telegram Bot",
    "REST API",
    "GraphQL",
    "WebSocket",
    "Microservices",
    "DevOps",
    "QA",
    "SQL",
    "NoSQL",
    "ORM",
    "Celery",
    "RabbitMQ",
    "Kafka",
    "Pandas",
    "NumPy",
    "TensorFlow",
    "PyTorch",
    "Jira",
    "Trello",
    "Scrum",
    "Agile",
    # Design & Creative
    "CorelDRAW",
    "InDesign",
    "After Effects",
    "Premiere Pro",
    "Canva",
    "Sketch",
    "Blender",
    "AutoCAD",
    "3ds Max",
    "Revit",
    "SketchUp",
    "ArchiCAD",
    # Business & Office
    "1C",
    "SAP",
    "CRM",
    "ERP",
    "Word",
    "PowerPoint",
    "Google Sheets",
    "Outlook",
    # Marketing & Sales
    "SEO",
    "SMM",
    "Google Ads",
    "Facebook Ads",
    "Google Analytics",
    "Yandex Direct",
    "Bitrix24",
    "AmoCRM",
    "Tilda",
    "WordPress",
    # Finance & Accounting
    "IFRS",
    "GAAP",
    "QuickBooks",
    # Languages
    "IELTS",
    "TOEFL",
    # Logistics & Engineering
    "SolidWorks",
    "MATLAB",
    "MikroTik",
]

_SKILL_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in KNOWN_SKILLS) + r")\b",
    re.IGNORECASE,
)


def extract_skills_from_text(text: str) -> list[str]:
    """Extract recognized skills from text. Shared across all parsers."""
    found = _SKILL_PATTERN.findall(text)
    seen: set[str] = set()
    result: list[str] = []
    for skill in found:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            canonical = next((s for s in KNOWN_SKILLS if s.lower() == key), skill)
            result.append(canonical)
    return result


# Labels that may leak into location values from parsers
_LOCATION_LABEL_PREFIXES = re.compile(
    r"^(?:Location|Адрес[^:]*|Локация|Manzil|Манзил|Joylashuv|Hudud|Регион|Region|Город|📍)\s*:?\s*",
    re.IGNORECASE,
)


def _clean_location(raw: str) -> str:
    """Strip field labels, hashtags, emojis, and redundant whitespace from location."""
    if not raw:
        return raw
    loc = raw.strip()
    # Strip leading emojis / non-word chars
    loc = re.sub(r"^[^\w#]+", "", loc)
    # Strip known label prefixes (e.g. "Location:", "Адрес города и офиса:")
    loc = _LOCATION_LABEL_PREFIXES.sub("", loc).strip()
    # Strip hashtags (e.g. "#remote")
    loc = re.sub(r"#(\w+)", r"\1", loc).strip()
    # Collapse whitespace
    loc = re.sub(r"\s+", " ", loc)
    return loc


@dataclass
class ParsedVacancy:
    """Unified output format all parsers must produce — regardless of source."""

    title: str
    description: str
    company: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = ""
    employment_type: str = ""
    work_format: str = ""
    location: str = ""
    experience_years: int | None = None
    skills: list[str] = field(default_factory=list)
    contact_info: str = ""
    language: str = ""
    posted_at: datetime | None = None
    source_url: str = ""
    region: str = ""  # canonical region slug — set by scraper or resolved from location

    def __post_init__(self):
        self.location = _clean_location(self.location)

    @property
    def content_hash(self) -> str:
        raw = (
            f"{self.source_url.strip()}"
            f"|{self.title.lower().strip()}"
            f"|{self.company.lower().strip()}"
            f"|{self.description[:500].lower().strip()}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    @property
    def is_valid(self) -> bool:
        return bool(self.title.strip() and self.description.strip())
