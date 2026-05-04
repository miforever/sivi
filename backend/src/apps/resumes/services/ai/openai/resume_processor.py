"""Resume processing functionality with date handling."""

import logging
from typing import Any

from .data_structures import validate_extracted_data
from .date_processor import DateProcessor

logger = logging.getLogger(__name__)


class ResumeProcessor:
    """Handles resume data processing and validation."""

    def __init__(self):
        self.date_processor = DateProcessor()

    def process_resume_data(self, resume_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process and validate resume data, including date processing.

        Args:
            resume_data: Raw resume data to process.

        Returns:
            Processed and validated resume data.
        """
        # Validate the basic structure
        validated_data = validate_extracted_data(resume_data)

        # Ensure required fields are filled
        validated_data = self._ensure_required_fields(validated_data)

        # Process dates for experiences
        for experience in validated_data.get("experiences", []):
            self.date_processor.process_dates_and_duration(experience)

        # Process dates for education
        for education in validated_data.get("education", []):
            self.date_processor.process_dates_and_duration(education)

        # Process dates for projects
        for project in validated_data.get("projects", []):
            self.date_processor.process_dates_and_duration(project)

        # Process dates for volunteer experience
        for volunteer in validated_data.get("volunteer_experience", []):
            self.date_processor.process_dates_and_duration(volunteer)

        return validated_data

    def _ensure_required_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Ensure all required fields are filled with reasonable defaults.

        Args:
            data: Resume data to validate.

        Returns:
            Data with required fields filled.
        """
        # Ensure education items have degree field
        for edu in data.get("education", []):
            if not edu.get("degree"):
                # Try to infer from context
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

        # Ensure skills have level field
        for skill in data.get("skills", []):
            if not skill.get("level"):
                skill["level"] = "Intermediate"  # Default level

        # Ensure social links are complete
        data["social_links"] = [
            link for link in data.get("social_links", []) if link.get("name") and link.get("url")
        ]

        return data

    def merge_resume_data(
        self, existing_data: dict[str, Any], new_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge new resume data with existing data, prioritizing new data.

        Args:
            existing_data: Existing resume data.
            new_data: New resume data to merge.

        Returns:
            Merged resume data.
        """
        merged = existing_data.copy()

        # Update basic fields
        for key in ["full_name", "email", "phone", "location", "professional_summary"]:
            if new_data.get(key):
                merged[key] = new_data[key]

        # Update social links
        if new_data.get("social_links"):
            merged["social_links"] = self._merge_social_links(
                existing_data.get("social_links", []), new_data.get("social_links", [])
            )

        # Merge experiences (avoid duplicates)
        merged["experiences"] = self._merge_experiences(
            existing_data.get("experiences", []), new_data.get("experiences", [])
        )

        # Merge education (avoid duplicates)
        merged["education"] = self._merge_education(
            existing_data.get("education", []), new_data.get("education", [])
        )

        # Merge projects (avoid duplicates)
        merged["projects"] = self._merge_projects(
            existing_data.get("projects", []), new_data.get("projects", [])
        )

        # Merge volunteer experience (avoid duplicates)
        merged["volunteer_experience"] = self._merge_volunteer_experience(
            existing_data.get("volunteer_experience", []), new_data.get("volunteer_experience", [])
        )

        # Merge skills (avoid duplicates)
        merged["skills"] = self._merge_skills(
            existing_data.get("skills", []), new_data.get("skills", [])
        )

        return self.process_resume_data(merged)

    def _merge_social_links(
        self, existing: list[dict[str, Any]], new: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge social links lists, avoiding duplicates."""
        merged = existing.copy()

        # Get existing names for comparison
        existing_names = [link.get("name", "").lower() for link in existing if link.get("name")]

        for new_link in new:
            # Only add if it has both name and url
            if (
                new_link.get("name")
                and new_link.get("url")
                and new_link.get("name", "").lower() not in existing_names
            ):
                merged.append(new_link)

        return merged

    def _merge_experiences(
        self, existing: list[dict[str, Any]], new: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge experience lists, avoiding duplicates."""
        merged = existing.copy()

        for new_exp in new:
            # Check if this experience already exists
            exists = any(
                exp.get("company", "").lower() == new_exp.get("company", "").lower()
                and exp.get("position", "").lower() == new_exp.get("position", "").lower()
                for exp in merged
            )

            if not exists:
                merged.append(new_exp)

        # Sort by start date (most recent first)
        return sorted(merged, key=lambda x: x.get("start_date", ""), reverse=True)

    def _merge_education(
        self, existing: list[dict[str, Any]], new: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge education lists, avoiding duplicates."""
        merged = existing.copy()

        for new_edu in new:
            # Check if this education already exists
            exists = any(
                edu.get("institution", "").lower() == new_edu.get("institution", "").lower()
                and edu.get("degree", "").lower() == new_edu.get("degree", "").lower()
                for edu in merged
            )

            if not exists:
                merged.append(new_edu)

        # Sort by start date (most recent first)
        return sorted(merged, key=lambda x: x.get("start_date", ""), reverse=True)

    def _merge_projects(
        self, existing: list[dict[str, Any]], new: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge project lists, avoiding duplicates."""
        merged = existing.copy()

        for new_project in new:
            # Check if this project already exists
            exists = any(
                proj.get("name", "").lower() == new_project.get("name", "").lower()
                for proj in merged
            )

            if not exists:
                merged.append(new_project)

        # Sort by start date (most recent first)
        return sorted(merged, key=lambda x: x.get("start_date", ""), reverse=True)

    def _merge_volunteer_experience(
        self, existing: list[dict[str, Any]], new: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge volunteer experience lists, avoiding duplicates."""
        merged = existing.copy()

        for new_volunteer in new:
            # Check if this volunteer experience already exists
            exists = any(
                vol.get("organization", "").lower() == new_volunteer.get("organization", "").lower()
                and vol.get("position", "").lower() == new_volunteer.get("position", "").lower()
                for vol in merged
            )

            if not exists:
                merged.append(new_volunteer)

        # Sort by start date (most recent first)
        return sorted(merged, key=lambda x: x.get("start_date", ""), reverse=True)

    def _merge_skills(
        self, existing: list[dict[str, Any]], new: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge skill lists, avoiding duplicates."""
        merged = existing.copy()
        existing_names = {skill.get("name", "").lower() for skill in existing}

        for new_skill in new:
            if new_skill.get("name", "").lower() not in existing_names:
                merged.append(new_skill)

        return merged
