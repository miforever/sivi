"""
Professional PDF generation service for resumes with comprehensive field support.
Handles all resume fields with dual layouts for image/non-image versions.
Includes Cyrillic (Russian) font support.
"""

import base64
import logging
import os
from io import BytesIO

from django.conf import settings
from django.utils.translation import activate, deactivate
from django.utils.translation import gettext as _
from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating professional PDF resumes."""

    PRIMARY_COLOR = HexColor("#000000")
    TEXT_COLOR = HexColor("#000000")
    LINK_COLOR = HexColor("#0066CC")

    @staticmethod
    def generate_resume_pdf(resume_data):
        """
        Generate a professional PDF resume from structured resume data.

        Args:
            resume_data (dict): Complete structured resume data

        Returns:
            BytesIO: PDF content as a byte stream
        """
        buffer = BytesIO()
        generator = ResumeGenerator(buffer, resume_data)
        generator.generate()

        return BytesIO(buffer.getvalue())


class ResumeGenerator:
    """Handles the actual PDF generation with professional styling."""

    def __init__(self, buffer, resume_data):
        self.buffer = buffer
        self.resume_data = resume_data
        self.language = resume_data.get("language", "en")
        self.has_image = bool(resume_data.get("profile_image"))

        # Register Cyrillic-compatible fonts
        self.register_fonts()

        # Page setup with standard margins
        self.doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        self.setup_styles()
        try:
            activate(self.language)
        except Exception:
            pass

    def register_fonts(self):
        """Register fonts that support Cyrillic characters from project folder."""
        try:
            base_paths = [
                os.path.join(settings.BASE_DIR, "static", "fonts"),
                os.path.join(settings.BASE_DIR, "apps", "static", "fonts"),
                os.path.join(settings.BASE_DIR, "fonts"),
                os.path.join(settings.BASE_DIR, "staticfiles", "fonts"),
            ]

            fonts_registered = False

            for base_path in base_paths:
                if not os.path.exists(base_path):
                    continue

                font_files = {
                    "normal": os.path.join(base_path, "DejaVuSans.ttf"),
                    "bold": os.path.join(base_path, "DejaVuSans-Bold.ttf"),
                    "italic": os.path.join(base_path, "DejaVuSans-Oblique.ttf"),
                }

                if os.path.exists(font_files["normal"]):
                    try:
                        pdfmetrics.registerFont(TTFont("DejaVu", font_files["normal"]))
                        fonts_registered = True

                        if os.path.exists(font_files["bold"]):
                            pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_files["bold"]))

                        if os.path.exists(font_files["italic"]):
                            pdfmetrics.registerFont(TTFont("DejaVu-Oblique", font_files["italic"]))

                        logger.info("Fonts loaded successfully from: %s", base_path)
                        break

                    except Exception:
                        logger.exception("Could not register fonts from %s", base_path)

            if fonts_registered:
                self.font_normal = "DejaVu"
                self.font_bold = "DejaVu-Bold"
                self.font_italic = "DejaVu-Oblique"
            else:
                path = os.path.join(settings.BASE_DIR, "static", "fonts")
                logger.warning(
                    "DejaVu fonts not found in %s. Cyrillic characters may not display correctly.",
                    path,
                )
                self.font_normal = "Helvetica"
                self.font_bold = "Helvetica-Bold"
                self.font_italic = "Helvetica-Oblique"

        except Exception:
            logger.exception("Font registration error")
            self.font_normal = "Helvetica"
            self.font_bold = "Helvetica-Bold"
            self.font_italic = "Helvetica-Oblique"

    def setup_styles(self):
        """Create comprehensive style definitions."""
        self.styles = getSampleStyleSheet()

        def add_style_safely(name, style):
            if name not in self.styles:
                self.styles.add(style)

        add_style_safely(
            "NameStyle",
            ParagraphStyle(
                name="NameStyle",
                parent=self.styles["Normal"],
                fontSize=20,
                leading=24,
                textColor=PDFService.PRIMARY_COLOR,
                spaceAfter=4,
                alignment=TA_CENTER,
                fontName=self.font_bold,
            ),
        )

        add_style_safely(
            "ContactStyle",
            ParagraphStyle(
                name="ContactStyle",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
                textColor=PDFService.TEXT_COLOR,
                spaceAfter=8,
                alignment=TA_CENTER,
                fontName=self.font_normal,
            ),
        )

        add_style_safely(
            "SectionHeader",
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontSize=11,
                leading=14,
                textColor=PDFService.PRIMARY_COLOR,
                spaceAfter=4,
                spaceBefore=8,
                fontName=self.font_bold,
            ),
        )

        add_style_safely(
            "SummaryText",
            ParagraphStyle(
                name="SummaryText",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
                textColor=PDFService.TEXT_COLOR,
                spaceAfter=4,
                alignment=TA_LEFT,
                fontName=self.font_normal,
            ),
        )

        add_style_safely(
            "ItemTitle",
            ParagraphStyle(
                name="ItemTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
                textColor=PDFService.PRIMARY_COLOR,
                spaceAfter=1,
                fontName=self.font_bold,
            ),
        )

        add_style_safely(
            "OrgDate",
            ParagraphStyle(
                name="OrgDate",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
                textColor=PDFService.TEXT_COLOR,
                spaceAfter=2,
                fontName=self.font_italic,
            ),
        )

        add_style_safely(
            "BulletPoint",
            ParagraphStyle(
                name="BulletPoint",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
                textColor=PDFService.TEXT_COLOR,
                spaceAfter=1,
                leftIndent=0,
                bulletIndent=0,
                fontName=self.font_normal,
            ),
        )

        add_style_safely(
            "SkillsText",
            ParagraphStyle(
                name="SkillsText",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=12,
                textColor=PDFService.TEXT_COLOR,
                spaceAfter=2,
                fontName=self.font_normal,
            ),
        )

    def process_profile_image(self, img_data):
        """Process and resize profile image with 4:5 aspect ratio (portrait)."""
        try:
            if isinstance(img_data, str):
                img_data = base64.b64decode(img_data)

            pil_img = PILImage.open(BytesIO(img_data))

            if pil_img.mode not in ("RGB", "L"):
                pil_img = pil_img.convert("RGB")

            width, height = pil_img.size

            target_width = 240
            target_height = 300

            scale_width = target_width / width
            scale_height = target_height / height
            scale = max(scale_width, scale_height)

            new_width = int(width * scale)
            new_height = int(height * scale)

            pil_img = pil_img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height

            pil_img = pil_img.crop((left, top, right, bottom))

            img_buffer = BytesIO()
            pil_img.save(img_buffer, format="JPEG", quality=95, optimize=True)

            return Image(BytesIO(img_buffer.getvalue()), width=1.6 * inch, height=2 * inch)

        except Exception:
            logger.exception("Error processing profile image")
            return None

    def create_header_with_image(self):
        """Create header with image layout."""
        elements = []

        img = None
        if profile_img_data := self.resume_data.get("profile_image"):
            img = self.process_profile_image(profile_img_data)

        if img:
            name = self.resume_data.get("full_name", "")
            contact_info = self.get_contact_info()
            social_links = self.get_social_links()

            left_content = []
            if name:
                left_content.append(Paragraph(name, self.styles["NameStyle"]))
                left_content.append(Spacer(1, 2))

            if contact_info:
                left_content.append(Paragraph(contact_info, self.styles["ContactStyle"]))

            if social_links:
                left_content.append(Paragraph(social_links, self.styles["ContactStyle"]))

            header_table = Table([[left_content, img]], colWidths=[4.5 * inch, 2 * inch])

            header_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )

            elements.append(header_table)
        else:
            elements.extend(self.create_header_without_image())

        return elements

    def create_header_without_image(self):
        """Create header without image - centered layout."""
        elements = []

        name = self.resume_data.get("full_name", "")
        if name:
            elements.append(Paragraph(name, self.styles["NameStyle"]))
            elements.append(Spacer(1, 2))

        contact_info = self.get_contact_info()
        if contact_info:
            elements.append(Paragraph(contact_info, self.styles["ContactStyle"]))

        social_links = self.get_social_links()
        if social_links:
            elements.append(Paragraph(social_links, self.styles["ContactStyle"]))

        return elements

    def get_contact_info(self):
        """Format primary contact information."""
        contact_parts = []

        if email := self.resume_data.get("email"):
            contact_parts.append(email)
        if phone := self.resume_data.get("phone"):
            contact_parts.append(phone)
        if location := self.resume_data.get("location"):
            contact_parts.append(location)

        return " | ".join(contact_parts)

    def get_social_links(self):
        """Format social media links with clickable usernames."""
        social_data = self.resume_data.get("social_links", [])
        links = []

        for link in social_data:
            platform = link.get("name", "").title()
            url = link.get("url", "")

            if not platform or not url:
                continue

            parts = url.rstrip("/").split("/")
            username = parts[-1] if parts[-1] else parts[-2] if len(parts) > 2 else url

            if not url.startswith("http"):
                url = "https://" + url

            display = (
                f'<a href="{url}">'
                f'<font color="{PDFService.LINK_COLOR}">'
                f"{platform.lower()}.com/in/{username}"
                f"</font></a>"
            )

            links.append(display)

        return " | ".join(links) if links else ""

    def create_section_header(self, title):
        """Create a styled section header with separator line."""
        translated = _(title)
        header_paragraph = Paragraph(f"<b>{translated}</b>", self.styles["SectionHeader"])

        line = HRFlowable(
            width="100%", thickness=0.5, color=PDFService.PRIMARY_COLOR, spaceBefore=2, spaceAfter=4
        )

        return [header_paragraph, line]

    def create_professional_summary(self):
        """Create professional summary section - max 2 lines."""
        elements = []

        summary_text = self.resume_data.get("professional_summary", "")

        if summary_text:
            if len(summary_text) > 300:
                summary_text = summary_text[:297] + "..."

            elements.extend(self.create_section_header(_("Professional Summary")))
            elements.append(Paragraph(summary_text, self.styles["SummaryText"]))
            elements.append(Spacer(1, 4))

        return elements

    def create_experience_section(self):
        """Create experience section - bullet points only, max 3-4 bullets."""
        elements = []

        experiences = self.resume_data.get("experiences", [])
        if not experiences:
            return elements

        elements.extend(self.create_section_header(_("Professional Experience")))
        elements.append(Spacer(1, 2))

        for i, exp in enumerate(experiences):
            exp_elements = []

            position = exp.get("position", "")
            company = exp.get("company", "")

            if position and company:
                title_line = f"<b>{position}</b>, {company}"
                exp_elements.append(Paragraph(title_line, self.styles["ItemTitle"]))
            elif position:
                exp_elements.append(Paragraph(f"<b>{position}</b>", self.styles["ItemTitle"]))

            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", _("Present")) if not exp.get("current") else _("Present")
            location = exp.get("location", "")

            date_parts = []
            if location:
                date_parts.append(location)
            if start_date:
                date_range = f"{start_date} - {end_date}"
                date_parts.append(date_range)

            if date_parts:
                exp_elements.append(Paragraph(" - ".join(date_parts), self.styles["OrgDate"]))

            bullets = []

            if description := exp.get("description"):
                bullets.append(description)

            if responsibilities := exp.get("responsibilities"):
                bullets.extend(responsibilities[:2])

            if achievements := exp.get("achievements"):
                bullets.extend(achievements[:2])

            bullets = bullets[:4]

            for bullet in bullets:
                exp_elements.append(Paragraph(f"• {bullet}", self.styles["BulletPoint"]))

            elements.append(KeepTogether(exp_elements))

            if i < len(experiences) - 1:
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 6))
        return elements

    def create_education_section(self):
        """Create education section."""
        elements = []

        education = self.resume_data.get("education", [])
        if not education:
            return elements

        elements.extend(self.create_section_header(_("Education")))
        elements.append(Spacer(1, 2))

        for i, edu in enumerate(education):
            edu_elements = []

            institution = edu.get("institution", "")
            degree = edu.get("degree", "")
            field = edu.get("field_of_study", "")

            if institution:
                edu_elements.append(Paragraph(f"<b>{institution}</b>", self.styles["ItemTitle"]))

            degree_text = f"{degree} in {field}" if field else degree
            start_date = edu.get("start_date", "")
            end_date = edu.get("end_date", _("Present")) if not edu.get("current") else _("Present")

            date_parts = []
            if degree_text:
                date_parts.append(degree_text)
            if start_date:
                date_range = f"{start_date} - {end_date}"
                date_parts.append(date_range)

            if date_parts:
                edu_elements.append(Paragraph(" - ".join(date_parts), self.styles["OrgDate"]))

            if achievements := edu.get("achievements"):
                for achievement in achievements[:3]:
                    edu_elements.append(Paragraph(f"• {achievement}", self.styles["BulletPoint"]))

            elements.append(KeepTogether(edu_elements))

            if i < len(education) - 1:
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 6))
        return elements

    def create_projects_section(self):
        """Create projects section - bullet points only."""
        elements = []

        projects = self.resume_data.get("projects", [])
        if not projects:
            return elements

        elements.extend(self.create_section_header(_("Projects")))
        elements.append(Spacer(1, 2))

        for i, project in enumerate(projects):
            proj_elements = []

            name = project.get("name", "")
            if name:
                proj_elements.append(Paragraph(f"<b>{name}</b>", self.styles["ItemTitle"]))

            org_parts = []
            if organization := project.get("organization"):
                org_parts.append(organization)
            if role := project.get("role"):
                org_parts.append(f"{_('Role')}: {role}")
            if url := project.get("url"):
                org_parts.append(
                    f'<a href="{url}"><font color="{PDFService.LINK_COLOR}">{_("URL")}</font></a>'
                )

            if org_parts:
                proj_elements.append(Paragraph(" | ".join(org_parts), self.styles["OrgDate"]))

            bullets = []

            if description := project.get("description"):
                bullets.append(description)

            if responsibilities := project.get("responsibilities"):
                bullets.extend(responsibilities[:2])

            if achievements := project.get("achievements"):
                bullets.extend(achievements[:1])

            bullets = bullets[:4]

            for bullet in bullets:
                proj_elements.append(Paragraph(f"• {bullet}", self.styles["BulletPoint"]))

            elements.append(KeepTogether(proj_elements))

            if i < len(projects) - 1:
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 6))
        return elements

    def create_volunteer_section(self):
        """Create volunteer experience section - bullet points only."""
        elements = []

        volunteer = self.resume_data.get("volunteer_experience", [])
        if not volunteer:
            return elements

        elements.extend(self.create_section_header(_("Volunteer Experience")))
        elements.append(Spacer(1, 2))

        for i, vol in enumerate(volunteer):
            vol_elements = []

            position = vol.get("position", "")
            organization = vol.get("organization", "")

            if position and organization:
                vol_elements.append(
                    Paragraph(f"<b>{position}</b>, {organization}", self.styles["ItemTitle"])
                )
            elif position:
                vol_elements.append(Paragraph(f"<b>{position}</b>", self.styles["ItemTitle"]))

            org_parts = []
            if cause := vol.get("cause"):
                org_parts.append(f"{_('Cause')}: {cause}")
            if location := vol.get("location"):
                org_parts.append(location)

            if org_parts:
                vol_elements.append(Paragraph(" | ".join(org_parts), self.styles["OrgDate"]))

            bullets = []

            if description := vol.get("description"):
                bullets.append(description)

            if responsibilities := vol.get("responsibilities"):
                bullets.extend(responsibilities[:2])

            if achievements := vol.get("achievements"):
                bullets.extend(achievements[:1])

            bullets = bullets[:4]

            for bullet in bullets:
                vol_elements.append(Paragraph(f"• {bullet}", self.styles["BulletPoint"]))

            elements.append(KeepTogether(vol_elements))

            if i < len(volunteer) - 1:
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 6))
        return elements

    def create_skills_section(self):
        """Create ONE centralized skills section - compact format."""
        elements = []

        skills = self.resume_data.get("skills", [])
        if not skills:
            return elements

        elements.extend(self.create_section_header(_("Skills")))

        categorized_skills = {}
        for skill in skills:
            if isinstance(skill, dict):
                category = skill.get("category", "Other").title()
                name = skill.get("name", "").strip()
                if name:
                    if category not in categorized_skills:
                        categorized_skills[category] = []
                    categorized_skills[category].append(name)
            else:
                name = str(skill).strip()
                if name:
                    if "Other" not in categorized_skills:
                        categorized_skills["Other"] = []
                    categorized_skills["Other"].append(name)

        for category, skill_list in categorized_skills.items():
            if skill_list:
                skills_text = ", ".join(skill_list)
                elements.append(
                    Paragraph(f"<b>{category}:</b> {skills_text}", self.styles["SkillsText"])
                )

        return elements

    def create_certifications_section(self):
        """Create certifications section."""
        elements = []

        certifications = self.resume_data.get("certifications", [])
        if not certifications:
            return elements

        elements.extend(self.create_section_header(_("Certifications")))
        elements.append(Spacer(1, 2))

        for i, cert in enumerate(certifications):
            cert_elements = []

            name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            date = cert.get("date", "")
            url = cert.get("url", "")

            if name:
                cert_elements.append(Paragraph(f"<b>{name}</b>", self.styles["ItemTitle"]))

            issuer_parts = []
            if issuer:
                issuer_parts.append(issuer)
            if date:
                issuer_parts.append(date)
            if url:
                issuer_parts.append(
                    f'<a href="{url}"><font color="{PDFService.LINK_COLOR}">{_("URL")}</font></a>'
                )

            if issuer_parts:
                cert_elements.append(Paragraph(" | ".join(issuer_parts), self.styles["OrgDate"]))

            elements.append(KeepTogether(cert_elements))

            if i < len(certifications) - 1:
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 6))
        return elements

    def generate(self):
        """Generate the complete professional PDF resume."""
        story = []

        if self.has_image:
            story.extend(self.create_header_with_image())
        else:
            story.extend(self.create_header_without_image())

        story.append(Spacer(1, 6))

        story.extend(self.create_professional_summary())
        story.extend(self.create_experience_section())
        story.extend(self.create_education_section())
        story.extend(self.create_projects_section())
        story.extend(self.create_volunteer_section())
        story.extend(self.create_certifications_section())
        story.extend(self.create_skills_section())

        try:
            self.doc.build(story)
            return self.buffer
        finally:
            try:
                deactivate()
            except Exception:
                pass
