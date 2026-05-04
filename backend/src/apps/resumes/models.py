"""Resume models."""

import uuid

from django.contrib.auth import get_user_model
from django.db import models
from pgvector.django import VectorField

User = get_user_model()


class Resume(models.Model):
    """
    Resume model for storing user resumes.
    """

    ORIGIN_CHOICES = [
        ("uploaded", "Uploaded"),
        ("qa_generated", "Generated"),
        ("enhanced", "Enhanced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    title = models.CharField(max_length=255, help_text="Resume title")

    profile_image = models.ImageField(
        upload_to="media/resume_profiles/",
        blank=True,
        null=True,
        help_text="Profile picture for resume (preferably 4:5 ratio)",
    )

    # Resume data stored as JSON
    meta = models.JSONField(
        default=dict, blank=True, help_text="Parsed form fields and resume metadata"
    )
    # Top-level fields matching AI resume structure
    full_name = models.CharField(max_length=255, blank=True, default="")
    email = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=100, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    position = models.CharField(max_length=255, blank=True, default="")
    professional_summary = models.TextField(blank=True, default="")
    language = models.CharField(max_length=10, default="en")

    embedding = VectorField(dimensions=1024, null=True, blank=True)

    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resumes"
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ResumeExperience(models.Model):
    """Work experience section of a resume."""

    CATEGORY_CHOICES = [
        ("JOB", "Job"),
        ("INTERNSHIP", "Internship"),
        ("OTHER", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="experiences")

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="JOB")
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, default="")
    start_date = models.CharField(max_length=20, help_text="YYYY-MM or YYYY-MM-DD")
    end_date = models.CharField(max_length=20, blank=True, null=True)
    current = models.BooleanField(default=False)
    duration = models.CharField(max_length=50, blank=True, default="")

    responsibilities = models.JSONField(default=list, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    skills_used = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_experiences"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.company} - {self.position}"


class ResumeEducation(models.Model):
    """Education section of a resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="educations")

    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True, default="")
    start_date = models.CharField(max_length=20)
    end_date = models.CharField(max_length=20, blank=True, null=True)
    current = models.BooleanField(default=False)
    duration = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")
    achievements = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_educations"
        ordering = ["-start_date"]


class ResumeProject(models.Model):
    """Projects section of a resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="projects")

    name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    start_date = models.CharField(max_length=20)
    end_date = models.CharField(max_length=20, blank=True, null=True)
    current = models.BooleanField(default=False)
    duration = models.CharField(max_length=50, blank=True, default="")
    role = models.CharField(max_length=255, blank=True, default="")
    organization = models.CharField(max_length=255, blank=True, default="")
    team_size = models.CharField(max_length=50, blank=True, default="")
    achievements = models.JSONField(default=list, blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    skills_used = models.JSONField(default=list, blank=True)
    tools_used = models.JSONField(default=list, blank=True)
    url = models.CharField(max_length=1024, blank=True, default="")
    category = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=50, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_projects"


class ResumeVolunteerExperience(models.Model):
    """Volunteer experience section of a resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="volunteer_experience"
    )

    organization = models.CharField(max_length=255, blank=True, default="")
    position = models.CharField(max_length=255, blank=True, default="")
    start_date = models.CharField(max_length=20, blank=True, default="")
    end_date = models.CharField(max_length=20, blank=True, null=True)
    current = models.BooleanField(default=False)
    duration = models.CharField(max_length=50, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    achievements = models.JSONField(default=list, blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    skills_used = models.JSONField(default=list, blank=True)
    hours_per_week = models.CharField(max_length=50, blank=True, default="")
    cause = models.CharField(max_length=100, blank=True, default="")
    url = models.CharField(max_length=1024, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_volunteer_experiences"


class ResumeCertification(models.Model):
    """Certifications or training programs."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="certifications")

    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, default="")
    date = models.CharField(max_length=20, blank=True, default="")
    credential_id = models.CharField(max_length=255, blank=True, default="")
    url = models.CharField(max_length=1024, blank=True, default="")
    description = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_certifications"


class ResumeSkill(models.Model):
    """Skills section of a resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="skills")

    name = models.CharField(max_length=255, blank=True, default="")
    level = models.CharField(max_length=50, blank=True, default="Intermediate")
    category = models.CharField(max_length=50, blank=True, default="other")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_skills"


class ResumeSocialLink(models.Model):
    """Social links section of a resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="social_links")

    name = models.CharField(max_length=100, help_text="e.g., LinkedIn, GitHub")
    url = models.URLField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_social_links"
