"""Resume serializers."""

from rest_framework import serializers

from apps.resumes.models import (
    Resume,
    ResumeCertification,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeSkill,
    ResumeSocialLink,
    ResumeVolunteerExperience,
)


class ResumeSocialLinkSerializer(serializers.ModelSerializer):
    """Serializer for resume social links."""

    class Meta:
        model = ResumeSocialLink
        fields = ["id", "name", "url"]


class ResumeExperienceSerializer(serializers.ModelSerializer):
    """Serializer for resume experience."""

    class Meta:
        model = ResumeExperience
        fields = [
            "id",
            "category",
            "company",
            "position",
            "address",
            "start_date",
            "end_date",
            "current",
            "duration",
            "responsibilities",
            "achievements",
            "skills_used",
            "description",
        ]


class ResumeEducationSerializer(serializers.ModelSerializer):
    """Serializer for resume education."""

    class Meta:
        model = ResumeEducation
        fields = [
            "id",
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "current",
            "duration",
            "description",
            "achievements",
        ]


class ResumeProjectSerializer(serializers.ModelSerializer):
    """Serializer for resume projects."""

    class Meta:
        model = ResumeProject
        fields = [
            "id",
            "name",
            "description",
            "start_date",
            "end_date",
            "current",
            "duration",
            "role",
            "organization",
            "team_size",
            "url",
            "category",
            "status",
            "achievements",
            "responsibilities",
            "skills_used",
            "tools_used",
        ]


class ResumeSkillSerializer(serializers.ModelSerializer):
    """Serializer for resume skills."""

    class Meta:
        model = ResumeSkill
        fields = ["id", "name"]


class ResumeVolunteerExperienceSerializer(serializers.ModelSerializer):
    """Serializer for volunteer experience."""

    class Meta:
        model = ResumeVolunteerExperience
        fields = [
            "id",
            "organization",
            "position",
            "start_date",
            "end_date",
            "current",
            "duration",
            "location",
            "description",
            "achievements",
            "responsibilities",
            "skills_used",
            "hours_per_week",
            "cause",
            "url",
        ]


class ResumeCertificationSerializer(serializers.ModelSerializer):
    """Serializer for certifications."""

    class Meta:
        model = ResumeCertification
        fields = ["id", "name", "issuer", "date", "credential_id", "url", "description"]


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Resume with nested data."""

    experiences = ResumeExperienceSerializer(many=True, read_only=True)
    educations = ResumeEducationSerializer(many=True, read_only=True)
    projects = ResumeProjectSerializer(many=True, read_only=True)
    skills = ResumeSkillSerializer(many=True, read_only=True)
    social_links = ResumeSocialLinkSerializer(many=True, read_only=True)
    volunteer_experience = ResumeVolunteerExperienceSerializer(many=True, read_only=True)
    certifications = ResumeCertificationSerializer(many=True, read_only=True)

    class Meta:
        model = Resume
        fields = [
            "id",
            "user",
            "title",
            "profile_image",
            "meta",
            "origin",
            "language",
            "full_name",
            "email",
            "phone",
            "location",
            "position",
            "professional_summary",
            "experiences",
            "educations",
            "projects",
            "skills",
            "social_links",
            "volunteer_experience",
            "certifications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "created_at",
            "updated_at",
            "experiences",
            "educations",
            "projects",
            "skills",
            "social_links",
            "volunteer_experience",
            "certifications",
        ]


class ResumeListSerializer(serializers.ModelSerializer):
    """List serializer for Resume (without nested data)."""

    class Meta:
        model = Resume
        fields = ["id", "title", "origin", "language", "created_at", "updated_at"]
        read_only_fields = fields


class ResumeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating resumes."""

    # Accept nested lists for creation/update
    experiences = ResumeExperienceSerializer(many=True, required=False)
    educations = ResumeEducationSerializer(many=True, required=False)
    projects = ResumeProjectSerializer(many=True, required=False)
    skills = ResumeSkillSerializer(many=True, required=False)
    social_links = ResumeSocialLinkSerializer(many=True, required=False)
    volunteer_experience = ResumeVolunteerExperienceSerializer(many=True, required=False)
    certifications = ResumeCertificationSerializer(many=True, required=False)

    class Meta:
        model = Resume
        fields = [
            "title",
            "meta",
            "profile_image",
            "full_name",
            "email",
            "phone",
            "location",
            "position",
            "professional_summary",
            "language",
            "origin",
            "experiences",
            "educations",
            "projects",
            "skills",
            "social_links",
            "volunteer_experience",
            "certifications",
        ]

    def create(self, validated_data):
        """Create resume with nested related rows."""
        experiences_data = validated_data.pop("experiences", [])
        educations_data = validated_data.pop("educations", [])
        projects_data = validated_data.pop("projects", [])
        skills_data = validated_data.pop("skills", [])
        social_links_data = validated_data.pop("social_links", [])
        volunteer_data = validated_data.pop("volunteer_experience", [])
        certifications_data = validated_data.pop("certifications", [])

        resume = Resume(**validated_data)
        resume.save()

        # Create experiences
        for exp in experiences_data:
            ResumeExperience.objects.create(resume=resume, **exp)

        # Create educations
        for edu in educations_data:
            ResumeEducation.objects.create(resume=resume, **edu)

        # Create projects
        for proj in projects_data:
            ResumeProject.objects.create(resume=resume, **proj)

        # Create skills
        for skill in skills_data:
            ResumeSkill.objects.create(resume=resume, **skill)

        # Create related social link rows if provided
        for link in social_links_data:
            name = link.get("name") or link.get("platform") or ""
            url = link.get("url")
            if url:
                ResumeSocialLink.objects.create(resume=resume, name=name, url=url)

        # Create volunteer experiences
        for vol in volunteer_data:
            ResumeVolunteerExperience.objects.create(resume=resume, **vol)

        # Create certifications
        for cert in certifications_data:
            # Ensure 'name' exists for certification
            if cert.get("name"):
                ResumeCertification.objects.create(resume=resume, **cert)

        return resume

    def update(self, instance, validated_data):
        """Update resume and nested relations."""
        experiences_data = validated_data.pop("experiences", None)
        educations_data = validated_data.pop("educations", None)
        projects_data = validated_data.pop("projects", None)
        skills_data = validated_data.pop("skills", None)
        social_links_data = validated_data.pop("social_links", None)
        volunteer_data = validated_data.pop("volunteer_experience", None)
        certifications_data = validated_data.pop("certifications", None)

        # Update remaining simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Sync experiences if provided
        if experiences_data is not None:
            instance.experiences.all().delete()
            for exp in experiences_data:
                ResumeExperience.objects.create(resume=instance, **exp)

        # Sync educations if provided
        if educations_data is not None:
            instance.educations.all().delete()
            for edu in educations_data:
                ResumeEducation.objects.create(resume=instance, **edu)

        # Sync projects if provided
        if projects_data is not None:
            instance.projects.all().delete()
            for proj in projects_data:
                ResumeProject.objects.create(resume=instance, **proj)

        # Sync skills if provided
        if skills_data is not None:
            instance.skills.all().delete()
            for skill in skills_data:
                ResumeSkill.objects.create(resume=instance, **skill)

        # Sync social links if provided: naive replace strategy
        if social_links_data is not None:
            instance.social_links.all().delete()
            for link in social_links_data:
                name = link.get("name") or link.get("platform") or ""
                url = link.get("url")
                if url:
                    ResumeSocialLink.objects.create(resume=instance, name=name, url=url)

        # Sync volunteer experiences
        if volunteer_data is not None:
            instance.volunteer_experience.all().delete()
            for vol in volunteer_data:
                ResumeVolunteerExperience.objects.create(resume=instance, **vol)

        # Sync certifications
        if certifications_data is not None:
            instance.certifications.all().delete()
            for cert in certifications_data:
                if cert.get("name"):
                    ResumeCertification.objects.create(resume=instance, **cert)

        return instance
