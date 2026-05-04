"""Prompt building functionality for different OpenAI operations."""

import json
from typing import Any

from .data_structures import get_default_resume_structure


class PromptBuilder:
    """Builds prompts for various OpenAI operations."""

    @staticmethod
    def get_base_prompt() -> str:
        """Return the base system prompt for resume generation."""
        return (
            "You are an expert resume writer and career coach. Your task is to help create a professional, "
            "ATS-friendly resume based on the provided information. Follow these guidelines:\n"
            "1. Use clear, concise, and action-oriented language\n"
            "2. Focus on achievements and quantifiable results\n"
            "3. Use industry-standard section headers and formatting\n"
            "4. Ensure all dates are in YYYY-MM-DD format consistently\n"
            "5. For current positions/education: set end_date to null and current to true\n"
            "6. Include relevant keywords from the job description if provided\n"
            "7. Structure the information in reverse chronological order\n"
            "8. For social links: ALWAYS include both name and url fields. Never create incomplete social links\n"
            "9. Filter content to include only what's relevant to the target position"
        )

    @staticmethod
    def _get_language_instruction(language: str) -> str:
        """Get language-specific instruction for resume generation."""
        if language == "en":
            return ""

        # Map common language codes to full names
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "uk": "Ukrainian",
            "ru": "Russian",
            "uz": "Uzbek",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "pl": "Polish",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "tr": "Turkish",
            "cs": "Czech",
            "hu": "Hungarian",
            "ro": "Romanian",
            "bg": "Bulgarian",
            "hr": "Croatian",
            "sk": "Slovak",
            "sl": "Slovenian",
            "et": "Estonian",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "el": "Greek",
            "he": "Hebrew",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "tl": "Filipino",
        }

        language_name = language_names.get(language.lower(), language.title())
        return f"\n\nLANGUAGE REQUIREMENT: Generate ALL resume content (names, job titles, companies, descriptions, achievements, etc.) in {language_name}. Maintain the JSON structure with English field names, but all VALUES should be in {language_name}."

    @staticmethod
    def _get_translation_instruction(target_language: str) -> str:
        """Get instruction for translating input content to target language."""
        # Map common language codes to full names
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "uk": "Ukrainian",
            "ru": "Russian",
            "uz": "Uzbek",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "pl": "Polish",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "tr": "Turkish",
            "cs": "Czech",
            "hu": "Hungarian",
            "ro": "Romanian",
            "bg": "Bulgarian",
            "hr": "Croatian",
            "sk": "Slovak",
            "sl": "Slovenian",
            "et": "Estonian",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "el": "Greek",
            "he": "Hebrew",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "tl": "Filipino",
        }

        language_name = language_names.get(target_language.lower(), target_language.title())

        return f"""
TRANSLATION REQUIREMENT:
The input text may be in ANY language (English, Russian, Spanish, Chinese, etc.), but you MUST output the final resume content in {language_name}.

CRITICAL TRANSLATION RULES:
1. READ and UNDERSTAND the input in whatever language it's provided
2. TRANSLATE all content (names, job titles, company names, descriptions, achievements, skills, etc.) to {language_name}
3. Use native {language_name} terminology for job titles and industry terms
4. Maintain professional tone and meaning during translation
5. Do NOT keep the original language - everything must be in {language_name}
6. For proper nouns (people's names, specific company names), keep them as-is unless they have standard {language_name} equivalents
7. JSON field names remain in English (e.g., "full_name", "position"), but all VALUES must be in {language_name}
8. For the person's NAME (full_name field): Extract ONLY the first name and last name (surname). Remove any patronymics, middle names, or extra name parts. Write the name in {language_name} script (e.g., Cyrillic for Russian, Latin for English).
9. For LOCATION: Simplify to country and city ONLY. Remove districts, regions, neighborhoods, or internal subdivisions. Example: "Узбекистан, Ташкент" not "Узбекистан, Ташкентская область, Чиланзарский район".
10. For JOB TITLES and POSITIONS: Translate ALL words fully into {language_name}. Do NOT mix languages or scripts. Every word must be a proper {language_name} word. If the input uses a different language (e.g., Uzbek "Dasturchi", "Sotuvchi", "Buxgalter"), translate it to the correct {language_name} equivalent. Examples for Russian: "Middle Dasturchi" → "Мидл Разработчик", "Bosh buxgalter" → "Главный бухгалтер", "Sotuvchi" → "Продавец".
11. Do NOT use labels like "Role:" or "Position:" in text values — just provide the content directly.

EXAMPLE:
Input (Russian): "Я работал разработчиком в компании Яндекс"
If target language is English, output: "position": "Developer", "company": "Yandex"
If target language is Spanish, output: "position": "Desarrollador", "company": "Yandex"
"""

    @staticmethod
    def _get_relevance_instruction(target_position: str | None) -> str:
        """Get instruction for filtering content based on position relevance."""
        if not target_position:
            return ""

        return f"""
RELEVANCE FILTERING FOR POSITION: {target_position}

CRITICAL FILTERING RULES:
1. INCLUDE ONLY experiences, projects, skills, and achievements that are RELEVANT to the position: {target_position}
2. EXCLUDE irrelevant work experience, projects, or skills that don't add value to this specific position
3. PRIORITIZE experiences that demonstrate:
   - Direct experience in the target role or similar roles
   - Skills and competencies commonly required for {target_position}
   - Achievements that showcase abilities needed for {target_position}
   - Projects that demonstrate relevant professional capabilities
4. For experiences/projects that are partially relevant:
   - KEEP them but emphasize only the relevant responsibilities and achievements
   - Downplay or remove irrelevant details
5. EXCLUDE:
   - Jobs in completely unrelated fields (unless they demonstrate transferable skills)
   - Projects that don't showcase relevant skills
   - Skills that are not applicable to {target_position}
   - Achievements that don't demonstrate relevant capabilities
6. KEEP:
   - All education (always relevant for credentials)
   - Volunteer experience IF it demonstrates leadership, teamwork, or relevant skills
   - Certifications IF they're industry-relevant or demonstrate continuous learning

EXAMPLES OF FILTERING (Generic for all fields):
Target: "Manager Position"
- INCLUDE: Team leadership roles, Project coordination experience, Management skills
- EXCLUDE: Entry-level roles without leadership, Individual contributor work unrelated to management

Target: "Sales Representative"
- INCLUDE: Customer service roles, Client relations experience, Communication skills
- EXCLUDE: Backend technical work, Non-customer-facing roles

Target: "Teacher/Educator"
- INCLUDE: Tutoring experience, Training roles, Educational content development
- EXCLUDE: Unrelated corporate work, Non-educational projects

Target: "Accountant"
- INCLUDE: Bookkeeping roles, Financial analysis work, Accounting software skills
- EXCLUDE: Non-financial roles, Creative/artistic projects

Target: "Nurse/Healthcare Professional"
- INCLUDE: Patient care experience, Medical certifications, Healthcare-related volunteer work
- EXCLUDE: Non-healthcare jobs, Unrelated technical skills

BALANCE: Be selective but not overly restrictive. Include experiences that show:
- Career progression
- Professional growth
- Transferable soft skills (leadership, communication, problem-solving)
- Well-roundedness (but only if relevant)
"""

    @staticmethod
    def _get_detailed_field_specifications() -> str:
        """Return detailed field specifications for all resume sections."""
        return """
RESUME-LEVEL FIELDS:
- title (string): Optional resume title or branding line (e.g., "Senior Backend Engineer", "Product Designer — Mobile").
- full_name, email, phone, location, position: Top-level contact and positioning fields (as in the JSON template).

CERTIFICATIONS ITEMS MUST CONTAIN:
- name (string): Certification name (e.g., "AWS Certified Solutions Architect") - THIS FIELD IS MANDATORY
- issuer (string): Issuing organization (e.g., "Amazon Web Services")
- date (string): Date of issuance in YYYY-MM-DD format. Leave as empty string "" if the date is not provided or unknown. Do NOT make up or guess dates.
- url (string): Verification or credential URL if available
- description (string): Short description or notes about the certification

IMPORTANT FIELD SPECIFICATIONS:

Social links items must contain:
- name (string): Social media platform name (e.g., "LinkedIn", "GitHub", "Twitter")
- url (string): Social media platform URL (e.g., "https://linkedin.com/in/username", "https://github.com/username")

CRITICAL: Both name and url fields are REQUIRED for each social link. Do not create social links with missing fields.
IMPORTANT: If you cannot provide both name and url for a social link, DO NOT include that social link at all.
IMPORTANT: Never create empty or incomplete social links. Either provide complete information or omit entirely.

EXAMPLES:
CORRECT: {"name": "LinkedIn", "url": "https://linkedin.com/in/johndoe"}
CORRECT: {"name": "GitHub", "url": "https://github.com/johndoe"}
INCORRECT: {"name": "LinkedIn"} (missing url)
INCORRECT: {"url": "https://github.com/johndoe"} (missing name)
INCORRECT: {"name": "", "url": ""} (empty values)
INCORRECT: {"name": "LinkedIn", "url": ""} (empty url)

Experience items must contain:
- company (string): Company name
- position (string): Job title/position
- start_date (string): Start date in YYYY-MM-DD format
- end_date (string|null): End date in YYYY-MM-DD format, or null if current
- current (boolean): true if currently working, false otherwise
- duration (string): Calculated duration (e.g., "2 years 3 months")
- achievements (array): List of quantified achievements
- skills_used (array): List of skills used
- responsibilities (array): List of key responsibilities
- description (string): Brief role description

Education items must contain:
- institution (string): School/university name
- degree (string): Degree type (e.g., "Bachelor of Science") - THIS FIELD IS MANDATORY
- field_of_study (string): Major/field of study
- start_date (string): Start date in YYYY-MM-DD format
- end_date (string|null): End date in YYYY-MM-DD format, or null if current
- current (boolean): true if currently studying, false otherwise
- duration (string): Calculated duration
- description (string): Additional details about the program
- achievements (array): Academic achievements, honors, GPA if notable

CRITICAL: The degree field is MANDATORY for education. If you cannot determine the degree, use a reasonable default like "Bachelor's Degree" or "High School Diploma" based on context.

Project items must contain:
- name (string): Project name
- description (string): Project description
- start_date (string): Start date in YYYY-MM-DD format
- end_date (string|null): End date in YYYY-MM-DD format, or null if ongoing
- current (boolean): true if ongoing, false if completed
- duration (string): Project duration
- role (string): Your role in the project
- organization (string): Company/organization where project was done
- team_size (string): Size of the team (e.g., "5 members")
- achievements (array): Project outcomes and achievements
- responsibilities (array): Your specific responsibilities
- skills_used (array): Technical and soft skills applied
- url (string): Project URL if available
- category (string): Project type (e.g., "web development", "research", "marketing")
- status (string): Project status (e.g., "completed", "ongoing", "cancelled")

Volunteer Experience items must contain:
- organization (string): Organization name
- position (string): Volunteer role/title
- start_date (string): Start date in YYYY-MM-DD format
- end_date (string|null): End date in YYYY-MM-DD format, or null if ongoing
- current (boolean): true if ongoing, false if ended
- duration (string): Duration of volunteer work
- location (string): Location of volunteer work
- description (string): Description of volunteer work
- achievements (array): Impact and achievements from volunteer work
- responsibilities (array): Key responsibilities and duties
- skills_used (array): Skills developed or applied
- hours_per_week (string): Time commitment (e.g., "10 hours per week")
- cause (string): Type of cause (e.g., "education", "environment", "community")
- url (string): Organization website if available

Skills items must contain:
- name (string): Skill name

NOTE: Only include clear, technical skills where possible. Do not invent proficiency levels or categories; the `name` field is sufficient for the AI output.

DATE FORMAT RULES:
- ALL dates must be in YYYY-MM-DD format (e.g., "2023-01-15")
- For current positions: end_date = null, current = true
- For completed positions: end_date = "YYYY-MM-DD", current = false
- If only year is known: use "YYYY-01-01" for start dates, "YYYY-12-31" for end dates
- If year and month known: use "YYYY-MM-01" for start dates, "YYYY-MM-28" for end dates
- CRITICAL: start_date is REQUIRED for all items and must NEVER be empty
- CRITICAL: If you cannot determine a date, use reasonable defaults rather than leaving it empty
- CRITICAL: Never return empty strings for dates - always provide a valid YYYY-MM-DD format
- CRITICAL: For incomplete dates, fill missing parts with reasonable defaults (01 for day, 01 for month)
- CRITICAL: All dates must pass backend validation as valid date format

SOCIAL LINKS VALIDATION RULES:
- Both name and url fields are MANDATORY for each social link
- If either field is missing or empty, omit the entire social link
- Use complete, valid URLs (e.g., "https://linkedin.com/in/username")
- Do not create placeholder or incomplete social links
- If you cannot provide complete social link information, return an empty array []

EDUCATION VALIDATION RULES:
- The degree field is MANDATORY for each education item
- If you cannot determine the degree, use a reasonable default based on context
- Never create education items without a degree field
- If you cannot provide complete education information, return an empty array []

DATA COMPLETENESS RULES:
- Always ensure all required fields are filled
- If a field cannot be determined, use reasonable defaults or omit the entire item
- Never create incomplete objects with missing required fields
- Return empty arrays for sections where you cannot provide complete information
"""

    @staticmethod
    def create_qa_generation_prompt(
        qa_text: str, language: str = "en", target_position: str | None = None
    ) -> str:
        """Create the prompt for Q&A-based resume generation."""
        json_template = json.dumps(get_default_resume_structure(), indent=2)
        field_specs = PromptBuilder._get_detailed_field_specifications()
        translation_instruction = PromptBuilder._get_translation_instruction(language)
        relevance_instruction = PromptBuilder._get_relevance_instruction(target_position)

        return f"""Based on the following Q&A session, generate a comprehensive resume in JSON format.
{translation_instruction}
{relevance_instruction}

Q&A Session:
{qa_text}

{field_specs}

Return a JSON object with the following structure:
{json_template}

CRITICAL REQUIREMENTS:
1. Use EXACTLY the field names specified above for each section
2. ALL dates must be in YYYY-MM-DD format
3. For current positions/education/projects: set end_date to null and current to true
4. For completed items: set end_date to proper date and current = false
5. Include ALL specified fields for each item, even if empty
6. Calculate duration strings in format "X years Y months" or "X months"
7. For social links: BOTH name and url fields are REQUIRED. Use full URLs (e.g., "https://linkedin.com/in/username")
8. If information is not available, leave the field empty string or empty array as appropriate
9. POSITION FIELD: {'Fill the "position" field with: ' + target_position if target_position else 'Only fill the "position" field if a target job position or career objective is explicitly mentioned in the Q&A session. If no position is specified, leave it as an empty string.'}
10. SOCIAL LINKS VALIDATION: Never create social links with missing name or url fields. If a social link is incomplete, omit it entirely.
11. EDUCATION VALIDATION: The degree field is MANDATORY for each education item. If you cannot determine the degree, use a reasonable default like "Bachelor's Degree" or "High School Diploma".
12. SKILLS VALIDATION: Provide skills as simple names only (the `name` field). Do not invent proficiency levels or categories.
13. DATA COMPLETENESS: Never create incomplete objects. If you cannot provide complete information for a section, return an empty array [].
14. REASONABLE DEFAULTS: When information is unclear, use reasonable defaults rather than leaving fields empty or incomplete.
15. VALIDATION ENFORCEMENT: Ensure every item in social_links, education, and skills has all required fields filled.
16. DATE VALIDATION: For experience, education, and projects: ALL dates must be in YYYY-MM-DD format. start_date is REQUIRED and must NEVER be empty. For CERTIFICATIONS: date is OPTIONAL — leave as empty string "" if not provided. Do NOT invent certification dates.
17. BACKEND COMPATIBILITY: All non-empty dates must pass backend validation as valid YYYY-MM-DD format.
18. TRANSLATION: Remember to translate ALL content to {language} as specified in the translation requirements above.
19. RELEVANCE: {"Include ONLY content relevant to the position: " + target_position + ". Exclude unrelated experiences, projects, and skills." if target_position else "Include all relevant professional content."}
20. NAME FORMAT: Use ONLY first name and last name (surname) in the full_name field. No patronymics or middle names. Write in the target language script (e.g., Cyrillic for Russian).
21. LOCATION FORMAT: Use ONLY "Country, City" format. No districts, regions, or neighborhoods.
22. JOB TITLES: Every word must be in the target language. Do not mix languages (e.g., no Uzbek words in a Russian resume).
"""

    @staticmethod
    def create_enhancement_prompt(
        resume_text: str,
        target_position: str | None,
        job_description: str | None,
        language: str = "en",
    ) -> str:
        """Create the prompt for resume enhancement."""
        field_specs = PromptBuilder._get_detailed_field_specifications()
        translation_instruction = PromptBuilder._get_translation_instruction(language)
        relevance_instruction = PromptBuilder._get_relevance_instruction(target_position)

        enhancement_instructions = [
            "Enhance the following resume to be more professional, achievement-oriented, and ATS-friendly.",
            "Focus on:",
            "1. Starting bullet points with strong action verbs",
            "2. Quantifying achievements with metrics where possible",
            "3. Using industry-standard terminology",
            "4. Ensuring consistent formatting throughout",
            "5. Highlighting relevant projects that demonstrate skills and experience",
            "6. Showcasing volunteer experience that adds value and demonstrates character",
            "7. Maintaining EXACT field structure and data types",
        ]

        if target_position:
            enhancement_instructions.append(
                f"8. Tailoring content for the position: {target_position}"
            )
            enhancement_instructions.append(
                "9. Removing or de-emphasizing irrelevant experiences and skills"
            )

        if job_description:
            enhancement_instructions.extend(
                [
                    "10. Incorporating relevant keywords from the job description",
                    f"Job Description:\n{job_description}",
                ]
            )

        return f"""
{translation_instruction}
{relevance_instruction}

{chr(10).join(enhancement_instructions)}

{field_specs}

Current Resume Data (JSON format):
{resume_text}

REQUIREMENTS:
- Maintain EXACT same JSON structure and field names
- Keep all date formats as YYYY-MM-DD
- Preserve current job logic (end_date: null, current: true)
- Include ALL required fields for each section
- SOCIAL LINKS: Ensure all social links have both name and url fields. Remove any incomplete social links.
- EDUCATION: Ensure all education items have a degree field. If missing, add a reasonable default.
- SKILLS: Ensure all skills have a name field. If missing, remove the skill entry.
- DATA COMPLETENESS: Never create incomplete objects. If you cannot provide complete information, omit the item entirely.
- REASONABLE DEFAULTS: Use reasonable defaults for missing required fields rather than leaving them empty.
- DATE VALIDATION: ALL dates must be in YYYY-MM-DD format. start_date is REQUIRED and must NEVER be empty. If you cannot determine a date, use reasonable defaults.
- BACKEND COMPATIBILITY: All dates must pass backend validation as valid date format. Never return empty strings or invalid date formats.
- TRANSLATION: Translate ALL content to {language} as specified in the translation requirements above.
- RELEVANCE: {"Filter content to include ONLY what is relevant to the position: " + target_position + ". Remove unrelated experiences, projects, and skills." if target_position else "Maintain all professional content."}
- Return ONLY the enhanced JSON object, no additional text or markdown
"""

    @staticmethod
    def create_analysis_prompt(resume_text: str, job_description: str | None) -> str:
        """Create the prompt for resume analysis."""
        analysis_points = [
            "Analyze the following resume and provide feedback on its strengths and areas for improvement.",
            "Focus on:",
            "1. Overall structure and organization",
            "2. Use of action verbs and achievement-oriented language",
            "3. Quantification of achievements",
            "4. Clarity and conciseness",
            "5. ATS compatibility",
            "6. Project relevance and presentation",
            "7. Volunteer experience impact and relevance",
            "8. Date consistency and formatting",
            "9. Completeness of required fields",
            "10. Content relevance to target position",
        ]

        if job_description:
            analysis_points.extend(
                [
                    "11. Relevance to the job description",
                    "12. Keyword optimization for the target role",
                    "13. Identification of irrelevant content that should be removed",
                    f"Job Description:\n{job_description}",
                ]
            )

        return f"""
{" ".join(analysis_points)}

Resume Data (JSON format):
{resume_text}

Return your analysis as a JSON object with these keys:
- overall_score (number): 1-10 rating
- strengths (list of strings): Key strengths of the resume
- areas_for_improvement (list of strings): Specific areas that need work
- ats_compatibility (string): Assessment of ATS compatibility
- date_consistency (string): Assessment of date format consistency
- field_completeness (string): Assessment of required field completeness
- content_relevance (string): Assessment of how well content matches the target position
- irrelevant_content (list of strings): Specific items that should be removed or de-emphasized
- keyword_analysis (object): Analysis of keyword usage (if job description provided)
- recommendations (list of strings): Specific recommendations for improvement
- summary (string): Brief overall assessment
"""

    @staticmethod
    def create_cover_letter_prompt(
        resume_data: dict[str, Any],
        job_description: str,
        target_position: str,
        company_name: str,
        hiring_manager: str,
        language: str = "en",
    ) -> str:
        """Create the prompt for cover letter generation."""
        translation_instruction = PromptBuilder._get_translation_instruction(language)

        return f"""
{translation_instruction}

Write a professional cover letter with the following details:

Candidate Information:
{json.dumps(resume_data, indent=2, ensure_ascii=False)}

Target Position: {target_position}
Company Name: {company_name}
Hiring Manager: {hiring_manager}

Job Description:
{job_description}

The cover letter should:
1. Be addressed to the hiring manager
2. Include a strong opening paragraph that captures attention
3. Highlight 2-3 key qualifications that match the job requirements
4. Provide specific examples of achievements from experience, projects, or volunteer work
5. Express enthusiasm for the role and company
6. Close professionally with a call to action
7. Be written entirely in {language}

Format the cover letter in proper business letter format with appropriate spacing.
Generate the cover letter in {language}.
"""

    @staticmethod
    def create_extraction_prompt(
        text: str, language: str = "en", target_position: str | None = None
    ) -> str:
        """Create the prompt for resume information extraction."""
        json_template = json.dumps(get_default_resume_structure(), indent=2)
        field_specs = PromptBuilder._get_detailed_field_specifications()
        translation_instruction = PromptBuilder._get_translation_instruction(language)
        relevance_instruction = PromptBuilder._get_relevance_instruction(target_position)

        return f"""Extract resume information and return as JSON:
{translation_instruction}
{relevance_instruction}

{text}

{field_specs}

Return ONLY the JSON data in this format:
{json_template}

CRITICAL EXTRACTION RULES:
1. Use EXACTLY the field names specified above
2. Convert ALL dates to YYYY-MM-DD format consistently
3. For current positions: set end_date to null and current to true
4. For past positions: set end_date to proper date and current to false
5. Extract ALL types of projects: work projects, research, campaigns, consulting, volunteer projects, academic projects, etc.
6. Extract volunteer experience: community service, pro bono work, charitable activities, board positions, etc.
7. Include project team size and organization details if available
8. Categorize skills appropriately (technical, language, soft skill, other)
9. For projects and volunteer work: include tools used, skills applied, achievements, and any relevant URLs
10. Calculate duration strings in format "X years Y months" or "X months"
11. Include ALL required fields for each item, even if information is not available (use empty strings/arrays)
12. POSITION FIELD: {'Fill the "position" field with: ' + target_position if target_position else 'Only fill the "position" field if a target job position or career objective is explicitly mentioned in the resume text. If no position is specified, leave it as an empty string.'}
13. SOCIAL LINKS EXTRACTION: Only extract social links that have BOTH name and url information. Skip any incomplete social links.
14. EDUCATION EXTRACTION: The degree field is MANDATORY. If you cannot determine the degree, use a reasonable default like "Bachelor's Degree" or "High School Diploma" based on context.
15. SKILLS EXTRACTION: Extract skills as simple names only (the `name` field). Do not invent proficiency levels or categories.
16. DATA COMPLETENESS: Never create incomplete objects. If you cannot provide complete information for a section, return an empty array [].
17. REASONABLE DEFAULTS: When information is unclear, use reasonable defaults rather than leaving fields empty or incomplete.
18. VALIDATION ENFORCEMENT: Ensure every item in social_links, education, and skills has all required fields filled.
19. DATE EXTRACTION: ALL dates must be in YYYY-MM-DD format. start_date is REQUIRED and must NEVER be empty. If you cannot determine a date, use reasonable defaults (e.g., "2020-01-01" for year 2020, "2020-06-01" for June 2020).
20. BACKEND COMPATIBILITY: All dates must pass backend validation as valid date format. Never return empty strings or invalid date formats.
21. TRANSLATION: Translate ALL content to {language} as specified in the translation requirements above.
22. RELEVANCE: {"Extract ONLY content relevant to the position: " + target_position + ". Exclude unrelated experiences, projects, and skills." if target_position else "Extract all relevant professional content."}
"""
