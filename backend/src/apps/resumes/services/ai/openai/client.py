"""Main OpenAI service client."""

import json
import logging
import os
import time
from typing import Any

from openai import OpenAI

from .api_client import OpenAIApiClient
from .constants import FAST_MODEL
from .data_structures import validate_extracted_data
from .date_processor import DateProcessor
from .exceptions import OpenAIServiceError
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for handling all OpenAI related operations for resume processing.
    Combines functionality from the original OpenAIService and OpenAIResumeExtractor.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the OpenAI client with optional API key.

        Args:
            api_key: Optional OpenAI API key. If not provided,
                    will use OPENAI_API_KEY from environment variables.

        Raises:
            OpenAIServiceError: If API key is not provided or found in environment.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIServiceError(
                "OpenAI API key not provided and not found in environment variables"
            )

        self.client = OpenAI(api_key=self.api_key)
        self.api_client = OpenAIApiClient(self.client)
        self.prompt_builder = PromptBuilder()
        self.date_processor = DateProcessor()

    def _post_process_resume_data(self, resume_data: dict[str, Any]) -> dict[str, Any]:
        """
        Post-process resume data to ensure consistent formatting and field completeness.

        Args:
            resume_data: Raw resume data from OpenAI.

        Returns:
            Processed and validated resume data.
        """
        # Validate basic structure first
        validated_data = validate_extracted_data(resume_data)

        # Additional validation for required fields
        validated_data = self._ensure_required_fields(validated_data)

        # Process dates for all sections
        for experience in validated_data.get("experiences", []):
            self.date_processor.process_dates_and_duration(experience)

        for education in validated_data.get("education", []):
            self.date_processor.process_dates_and_duration(education)

        for project in validated_data.get("projects", []):
            self.date_processor.process_dates_and_duration(project)

        for volunteer in validated_data.get("volunteer_experience", []):
            self.date_processor.process_dates_and_duration(volunteer)

        # Validate date consistency
        validation_report = self.date_processor.validate_date_consistency(validated_data)
        if not validation_report["is_valid"]:
            logger.warning(f"Date validation issues found: {validation_report['issues']}")

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

    def generate_resume_from_qa(
        self,
        questions_answers: list[dict[str, str]],
        user_info: dict[str, str] | None = None,
        language: str = "en",
        position: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a structured resume from Q&A data using OpenAI's GPT model.

        Args:
            questions_answers: List of dicts with 'question' and 'answer' keys, or a single dict.
            user_info: Optional dict with user info like name, email, etc.
            language: Language code for the output resume (default: 'en')
            position: Optional job position for the resume

        Returns:
            Dict containing structured resume information.

        Raises:
            OpenAIServiceError: If there's an error processing the request.
        """
        if not questions_answers:
            raise OpenAIServiceError("No questions and answers provided")

        # Handle both single QA pair (dict) and multiple QAs (list)
        if isinstance(questions_answers, dict):
            questions_answers = [questions_answers]

        try:
            # Format the Q&A data
            qa_text = "\n".join(
                [
                    f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}"
                    for qa in questions_answers
                    if qa and isinstance(qa, dict) and qa.get("question") and qa.get("answer")
                ]
            )

            if not qa_text:
                raise OpenAIServiceError("No valid question-answer pairs provided")

            # Add user info if provided
            if user_info:
                user_info_text = "\n".join([f"{k}: {v}" for k, v in user_info.items() if v])
                qa_text = f"User Information:\n{user_info_text}\n\nQ&A Session:\n{qa_text}"

            # Add position if provided
            if position:
                qa_text = f"Target Position: {position}\n\n{qa_text}"

            # Create the structured prompt
            prompt = self.prompt_builder.create_qa_generation_prompt(qa_text, language)

            # Make API request
            content = self.api_client.make_request(
                [
                    {"role": "system", "content": self.prompt_builder.get_base_prompt()},
                    {"role": "user", "content": prompt},
                ]
            )

            # Parse and validate response
            resume_data = self.api_client.parse_json_response(content)

            # For single QA pair, we might want to merge with existing data
            if len(questions_answers) == 1 and user_info:
                # Preserve any existing user info that wasn't updated
                for field in ["full_name", "email", "phone", "location"]:
                    if field in user_info and field not in resume_data:
                        resume_data[field] = user_info[field]

            return self._post_process_resume_data(resume_data)

        except Exception as e:
            logger.error(f"Error generating resume from Q&A: {e}")
            raise OpenAIServiceError(f"Error processing resume: {e!s}")

    def enhance_resume(
        self,
        resume_data: dict[str, Any],
        target_position: str | None = None,
        job_description: str | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Enhance an existing resume with better formatting, content, and ATS optimization.

        Args:
            resume_data: Existing resume data to enhance.
            target_position: The target job position (optional).
            job_description: The job description to optimize for (optional).
            language: Language code for the output resume (default: 'en')

        Returns:
            Enhanced resume data.

        Raises:
            OpenAIServiceError: If there's an error processing the enhancement.
        """
        if not resume_data:
            raise OpenAIServiceError("No resume data provided for enhancement")

        try:
            resume_text = json.dumps(resume_data, indent=2, ensure_ascii=False)
            prompt = self.prompt_builder.create_enhancement_prompt(
                resume_text, target_position, job_description, language
            )

            # Make API request
            content = self.api_client.make_request(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert resume writer specializing in creating ATS-optimized resumes. "
                            "Enhance the provided resume data to be more professional, achievement-focused, "
                            "and optimized for applicant tracking systems. Maintain exact field structure and "
                            "date formats. For current positions, ensure end_date is null and current is true. "
                            "Return ONLY the enhanced JSON object."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            enhanced_data = self.api_client.parse_json_response(content)
            return self._post_process_resume_data(enhanced_data)

        except Exception as e:
            logger.error(f"Error enhancing resume: {e}")
            raise OpenAIServiceError(f"Error enhancing resume: {e!s}")

    def analyze_resume_strengths(
        self, resume_data: dict[str, Any], job_description: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze the strengths and areas for improvement in a resume.

        Args:
            resume_data: The resume data to analyze.
            job_description: Optional job description to compare against.

        Returns:
            Dict containing analysis results.

        Raises:
            OpenAIServiceError: If there's an error processing the analysis.
        """
        if not resume_data:
            raise OpenAIServiceError("No resume data provided for analysis")

        try:
            # First, validate the resume data structure and dates
            validation_report = self.date_processor.validate_date_consistency(resume_data)

            resume_text = json.dumps(resume_data, indent=2, ensure_ascii=False)
            prompt = self.prompt_builder.create_analysis_prompt(resume_text, job_description)

            content = self.api_client.make_request(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert resume reviewer with deep knowledge of ATS systems "
                            "and hiring practices. Provide detailed, constructive feedback on the "
                            "following resume. Be specific and provide actionable suggestions. "
                            "Pay special attention to date consistency, field completeness, and "
                            "current position handling."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=3000,
            )

            analysis_result = self.api_client.parse_json_response(content)

            # Add validation report to analysis
            analysis_result["date_validation"] = validation_report

            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            raise OpenAIServiceError(f"Error analyzing resume: {e!s}")

    def generate_cover_letter(
        self,
        resume_data: dict[str, Any],
        job_description: str,
        company_name: str,
        hiring_manager: str = "Hiring Manager",
    ) -> str:
        """
        Generate a personalized cover letter based on resume data and job description.

        Args:
            resume_data: The resume data to use for personalization.
            job_description: The job description to target.
            company_name: Name of the company applying to.
            hiring_manager: Name of the hiring manager (optional).

        Returns:
            Generated cover letter as a string.

        Raises:
            OpenAIServiceError: If there's an error generating the cover letter.
        """
        if not all([resume_data, job_description, company_name]):
            raise OpenAIServiceError("Missing required parameters for cover letter generation")

        try:
            target_position = job_description.split("\n")[0].strip()
            prompt = self.prompt_builder.create_cover_letter_prompt(
                resume_data, job_description, target_position, company_name, hiring_manager
            )

            content = self.api_client.make_request(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional career coach specializing in creating compelling, "
                            "personalized cover letters. Write a professional cover letter that "
                            "highlights the candidate's relevant experience and skills in relation "
                            "to the job description. Use a professional but engaging tone."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=None,
                temperature=0.7,
                max_tokens=2000,
            )

            return content

        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            raise OpenAIServiceError(f"Error generating cover letter: {e!s}")

    def extract_resume_info(
        self, text: str, language: str = "en", skip_post_processing: bool = False
    ) -> dict[str, Any] | None:
        """
        Extract structured resume information using OpenAI API.

        Args:
            text: Resume text to extract information from.
            language: Language code for the output resume (default: 'en')
            skip_post_processing: If True, skip heavy post-processing for faster extraction

        Returns:
            Extracted resume data or None if extraction fails.
        """
        start_time = time.time()
        logger.info(
            f"Starting resume info extraction, text length: {len(text)} characters, skip_post_processing: {skip_post_processing}"
        )

        if not text or not text.strip():
            logger.warning("Empty text provided for resume extraction")
            return None

        try:
            # Time prompt building
            prompt_start = time.time()
            logger.info("Building extraction prompt...")
            prompt = self.prompt_builder.create_extraction_prompt(text, language)
            prompt_time = time.time() - prompt_start
            logger.info(
                f"Prompt building completed in {prompt_time:.2f} seconds, prompt length: {len(prompt)} characters"
            )

            # Time API request
            api_start = time.time()
            logger.info(
                f"Making OpenAI API request to model: {FAST_MODEL} (faster model for extraction)"
            )
            content = self.api_client.make_request(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that extracts structured information from resumes. "
                            "Always use the exact field structure specified and maintain consistent date formats. "
                            "For current positions, set end_date to null and current to true."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                model=FAST_MODEL,
            )
            api_time = time.time() - api_start
            logger.info(f"OpenAI API request completed in {api_time:.2f} seconds")

            # Time response parsing
            parse_start = time.time()
            logger.info("Parsing API response...")
            extracted_data = self.api_client.parse_json_response(content)
            parse_time = time.time() - parse_start
            logger.info(f"Response parsing completed in {parse_time:.2f} seconds")

            # Time post-processing (optional)
            if skip_post_processing:
                logger.info("Skipping post-processing for faster extraction")
                processed_data = extracted_data
                post_time = 0
            else:
                post_start = time.time()
                logger.info("Post-processing extracted data...")
                processed_data = self._post_process_resume_data(extracted_data)
                post_time = time.time() - post_start
                logger.info(f"Post-processing completed in {post_time:.2f} seconds")

            total_time = time.time() - start_time
            logger.info(
                f"Total resume extraction completed in {total_time:.2f} seconds (prompt: {prompt_time:.2f}s, api: {api_time:.2f}s, parse: {parse_time:.2f}s, post: {post_time:.2f}s)"
            )

            return processed_data

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error in extract_resume_info after {total_time:.2f} seconds: {e}")
            return None

    def validate_resume_structure(self, resume_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate the structure and completeness of resume data.

        Args:
            resume_data: Resume data to validate.

        Returns:
            Validation report with detailed findings.
        """
        validation_report = {
            "is_valid": True,
            "missing_fields": [],
            "invalid_fields": [],
            "recommendations": [],
            "date_validation": {},
        }

        try:
            # Check date consistency
            date_validation = self.date_processor.validate_date_consistency(resume_data)
            validation_report["date_validation"] = date_validation

            if not date_validation["is_valid"]:
                validation_report["is_valid"] = False

            # Check required fields
            required_sections = ["experiences", "education", "skills"]
            for section in required_sections:
                if not resume_data.get(section):
                    validation_report["missing_fields"].append(
                        f"Missing or empty {section} section"
                    )
                    validation_report["is_valid"] = False

            # Check contact information
            contact_fields = ["full_name", "email", "phone"]
            for field in contact_fields:
                if not resume_data.get(field):
                    validation_report["missing_fields"].append(f"Missing {field}")

            # Validate experience fields
            for i, exp in enumerate(resume_data.get("experiences", [])):
                required_exp_fields = ["company", "position", "start_date"]
                for field in required_exp_fields:
                    if not exp.get(field):
                        validation_report["invalid_fields"].append(
                            f"Experience {i + 1}: Missing {field}"
                        )
                        validation_report["is_valid"] = False

            # Generate recommendations
            if validation_report["missing_fields"]:
                validation_report["recommendations"].append(
                    "Complete missing contact information fields"
                )

            if validation_report["date_validation"].get("issues"):
                validation_report["recommendations"].append("Fix date format inconsistencies")

            if not resume_data.get("professional_summary"):
                validation_report["recommendations"].append(
                    "Add a professional summary to strengthen your resume"
                )

        except Exception as e:
            logger.error(f"Error validating resume structure: {e}")
            validation_report["is_valid"] = False
            validation_report["invalid_fields"].append(f"Validation error: {e!s}")

        return validation_report
