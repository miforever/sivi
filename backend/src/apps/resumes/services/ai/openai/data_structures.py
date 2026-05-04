"""Data structure definitions and validation functions."""

from typing import Any


def get_default_resume_structure() -> dict[str, Any]:
    """Return the default resume structure with empty values."""
    return {
        "full_name": "",
        "title": "",
        "email": "",
        "phone": "",
        "location": "",
        "position": "",
        "professional_summary": "",
        "social_links": [],
        "experiences": [],
        "education": [],
        "projects": [],
        "volunteer_experience": [],
        "skills": [],
        "certifications": [],
    }


def get_default_social_links() -> list[dict[str, Any]]:
    """Return the default social links structure with empty values."""
    return [{"name": "", "url": ""}]


def validate_social_link_item(social_link: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure a social link item."""
    name = social_link.get("name", "").strip()
    url = social_link.get("url", "").strip()

    # Only return valid social links with both name and url
    if name and url:
        return {"name": name, "url": url}
    else:
        # Return None to indicate this should be filtered out
        return None


def validate_experience_item(exp: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure an experience item."""
    return {
        "company": exp.get("company", ""),
        "position": exp.get("position", ""),
        "start_date": exp.get("start_date", ""),
        "end_date": exp.get("end_date", ""),
        "current": exp.get("current", False),
        "duration": exp.get("duration", ""),
        "achievements": exp.get("achievements", []),
        "skills_used": exp.get("skills_used", []),
        "responsibilities": exp.get("responsibilities", []),
        "description": exp.get("description", ""),
    }


def validate_education_item(edu: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure an education item."""
    degree = edu.get("degree", "").strip()

    # If degree is missing, try to infer from context or use default
    if not degree:
        # Try to infer from field_of_study or institution
        field_of_study = edu.get("field_of_study", "").strip()
        institution = edu.get("institution", "").strip()

        if "university" in institution.lower() or "college" in institution.lower():
            degree = "Bachelor's Degree"
        elif "high school" in institution.lower() or "secondary" in institution.lower():
            degree = "High School Diploma"
        elif "master" in field_of_study.lower():
            degree = "Master's Degree"
        elif "phd" in field_of_study.lower() or "doctorate" in field_of_study.lower():
            degree = "Doctorate"
        else:
            degree = "Bachelor's Degree"  # Default fallback

    return {
        "institution": edu.get("institution", ""),
        "degree": degree,
        "field_of_study": edu.get("field_of_study", ""),
        "start_date": edu.get("start_date", ""),
        "end_date": edu.get("end_date", ""),
        "current": edu.get("current", False),
        "duration": edu.get("duration", ""),
        "description": edu.get("description", ""),
        "achievements": edu.get("achievements", []),
    }


def validate_project_item(project: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure a project item."""
    return {
        "name": project.get("name", ""),
        "description": project.get("description", ""),
        "start_date": project.get("start_date", ""),
        "end_date": project.get("end_date", ""),
        "current": project.get("current", False),
        "duration": project.get("duration", ""),
        "role": project.get("role", ""),
        "organization": project.get("organization", ""),
        "team_size": project.get("team_size", ""),
        "achievements": project.get("achievements", []),
        "responsibilities": project.get("responsibilities", []),
        "skills_used": project.get("skills_used", []),
        "url": project.get("url", ""),
        "category": project.get(
            "category", ""
        ),  # e.g., "research", "marketing", "construction", "event", etc.
        "status": project.get("status", ""),  # e.g., "completed", "ongoing", "cancelled"
    }


def validate_volunteer_experience_item(volunteer: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure a volunteer experience item."""
    return {
        "organization": volunteer.get("organization", ""),
        "position": volunteer.get("position", ""),
        "start_date": volunteer.get("start_date", ""),
        "end_date": volunteer.get("end_date", ""),
        "current": volunteer.get("current", False),
        "duration": volunteer.get("duration", ""),
        "location": volunteer.get("location", ""),
        "description": volunteer.get("description", ""),
        "achievements": volunteer.get("achievements", []),
        "responsibilities": volunteer.get("responsibilities", []),
        "skills_used": volunteer.get("skills_used", []),
        "hours_per_week": volunteer.get("hours_per_week", ""),
        "cause": volunteer.get(
            "cause", ""
        ),  # e.g., "education", "environment", "healthcare", "community"
        "url": volunteer.get("url", ""),
    }


def validate_skill_item(skill: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure a skill item."""
    return {"name": skill.get("name", "")}


def validate_certification_item(cert: dict[str, Any]) -> dict[str, Any]:
    """Validate and structure a certification item."""
    name = cert.get("name", "").strip()
    issuer = cert.get("issuer", "").strip()
    date = cert.get("date", "")
    url = cert.get("url", "").strip()
    description = cert.get("description", "")

    if not name:
        name = "Certification Name"

    return {"name": name, "issuer": issuer, "date": date, "url": url, "description": description}


def validate_resume_completeness(data: dict[str, Any]) -> dict[str, Any]:
    """
    Comprehensive validation to ensure all required fields are present and valid.

    Args:
        data: Resume data to validate.

    Returns:
        Validated and cleaned resume data.
    """
    validated = data.copy()

    # Validate social links - ensure both name and url are present
    validated["social_links"] = [
        link
        for link in data.get("social_links", [])
        if isinstance(link, dict)
        and link.get("name")
        and link.get("name").strip()
        and link.get("url")
        and link.get("url").strip()
    ]

    # Validate education - ensure degree field is present
    for edu in validated.get("education", []):
        if not edu.get("degree") or not edu.get("degree").strip():
            # Try to infer degree from context
            field_of_study = edu.get("field_of_study", "").lower()
            institution = edu.get("institution", "").lower()

            if "master" in field_of_study or "mba" in field_of_study:
                edu["degree"] = "Master's Degree"
            elif "phd" in field_of_study or "doctorate" in field_of_study:
                edu["degree"] = "Doctorate"
            elif "university" in institution or "college" in institution:
                edu["degree"] = "Bachelor's Degree"
            elif "high school" in institution or "secondary" in institution:
                edu["degree"] = "High School Diploma"
            else:
                edu["degree"] = "Bachelor's Degree"  # Default fallback

    # Validate experiences - ensure basic required fields and dates
    for exp in validated.get("experiences", []):
        if not exp.get("company") or not exp.get("company").strip():
            exp["company"] = "Company Name"  # Default fallback
        if not exp.get("position") or not exp.get("position").strip():
            exp["position"] = "Position Title"  # Default fallback
        # Ensure start_date is never empty
        if not exp.get("start_date") or not exp.get("start_date").strip():
            exp["start_date"] = "2020-01-01"  # Default fallback

    # Validate projects - ensure basic required fields and dates
    for project in validated.get("projects", []):
        if not project.get("name") or not project.get("name").strip():
            project["name"] = "Project Name"  # Default fallback
        # Ensure start_date is never empty
        if not project.get("start_date") or not project.get("start_date").strip():
            project["start_date"] = "2020-01-01"  # Default fallback

    # Validate certifications - ensure name and sensible date
    for cert in validated.get("certifications", []):
        if not cert.get("name") or not cert.get("name").strip():
            cert["name"] = "Certification Name"
        # Ensure date exists but don't force a specific value here
        if not cert.get("date"):
            cert["date"] = ""

    # Validate volunteer experience - ensure basic required fields and dates
    for volunteer in validated.get("volunteer_experience", []):
        if not volunteer.get("organization") or not volunteer.get("organization").strip():
            volunteer["organization"] = "Organization Name"  # Default fallback
        if not volunteer.get("position") or not volunteer.get("position").strip():
            volunteer["position"] = "Volunteer Position"  # Default fallback
        # Ensure start_date is never empty
        if not volunteer.get("start_date") or not volunteer.get("start_date").strip():
            volunteer["start_date"] = "2020-01-01"  # Default fallback

    # Validate dates - ensure all dates are in YYYY-MM-DD format
    validated = validate_and_fix_dates(validated)

    return validated


def validate_and_fix_dates(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and fix date formats to ensure they are always in YYYY-MM-DD format.

    Args:
        data: Resume data to validate.

    Returns:
        Data with validated and fixed dates.
    """
    import re
    from datetime import datetime

    def fix_date_format(date_str: str, is_start_date: bool = True) -> str:
        """Fix date format to YYYY-MM-DD."""
        if not date_str or not isinstance(date_str, str):
            # Use current year as fallback
            current_year = datetime.now().year
            return f"{current_year}-01-01"

        date_str = date_str.strip()

        # If already in correct format, return as is
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                pass

        # Try to extract year and month
        year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
        if year_match:
            year = year_match.group(0)
            # Look for month
            month_match = re.search(r"\b(0?[1-9]|1[0-2])\b", date_str)
            if month_match:
                month = month_match.group(0).zfill(2)
                day = "01" if is_start_date else "28"
                return f"{year}-{month}-{day}"
            else:
                # Only year found
                month = "01" if is_start_date else "12"
                day = "01" if is_start_date else "31"
                return f"{year}-{month}-{day}"

        # If no valid date found, use current year
        current_year = datetime.now().year
        return f"{current_year}-01-01"

    # Fix dates in experiences
    for exp in data.get("experiences", []):
        exp["start_date"] = fix_date_format(exp.get("start_date", ""), is_start_date=True)
        if exp.get("end_date"):
            exp["end_date"] = fix_date_format(exp.get("end_date", ""), is_start_date=False)

    # Fix dates in education
    for edu in data.get("education", []):
        edu["start_date"] = fix_date_format(edu.get("start_date", ""), is_start_date=True)
        if edu.get("end_date"):
            edu["end_date"] = fix_date_format(edu.get("end_date", ""), is_start_date=False)

    # Fix dates in projects
    for project in data.get("projects", []):
        project["start_date"] = fix_date_format(project.get("start_date", ""), is_start_date=True)
        if project.get("end_date"):
            project["end_date"] = fix_date_format(project.get("end_date", ""), is_start_date=False)

    # Fix dates in volunteer experience
    for volunteer in data.get("volunteer_experience", []):
        volunteer["start_date"] = fix_date_format(
            volunteer.get("start_date", ""), is_start_date=True
        )
        if volunteer.get("end_date"):
            volunteer["end_date"] = fix_date_format(
                volunteer.get("end_date", ""), is_start_date=False
            )

    # Fix dates in certifications (single date field)
    for cert in data.get("certifications", []):
        if cert.get("date"):
            cert["date"] = fix_date_format(cert.get("date", ""), is_start_date=False)

    return data


def validate_extracted_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and clean the extracted resume data.

    Args:
        data: Raw extracted resume data.

    Returns:
        Validated and cleaned resume data.
    """
    validated = get_default_resume_structure()

    # Update with provided data
    for key in validated:
        if key in data:
            validated[key] = data[key]

    # Process experiences
    validated["experiences"] = [
        validate_experience_item(exp) for exp in data.get("experiences", [])
    ]

    # Process education
    validated["education"] = [validate_education_item(edu) for edu in data.get("education", [])]

    # Process projects
    validated["projects"] = [validate_project_item(project) for project in data.get("projects", [])]

    # Process volunteer experience
    validated["volunteer_experience"] = [
        validate_volunteer_experience_item(volunteer)
        for volunteer in data.get("volunteer_experience", [])
    ]

    # Process skills
    validated["skills"] = [validate_skill_item(skill) for skill in data.get("skills", [])]

    # Process social links
    validated["social_links"] = [
        link
        for link in [validate_social_link_item(link) for link in data.get("social_links", [])]
        if link is not None  # Only include valid social links
    ]

    # Final comprehensive validation
    validated = validate_resume_completeness(validated)

    return validated
