"""
Management command to import hardcoded questions into the database.
Usage: python manage.py import_questions
"""

from django.core.management.base import BaseCommand

from apps.questions.management.questions_data import (
    GENERIC_QUESTIONS,
    PERSONAL_INFO_QUESTIONS,
    POSITION_QUESTIONS,
)
from apps.questions.models import Question, QuestionTranslation


class Command(BaseCommand):
    help = "Import hardcoded questions into the database"

    def handle(self, *args, **options):
        self.stdout.write("Starting question import...")

        # Clear existing questions (optional - be careful in production!)
        if self.confirm_action("Clear existing questions?"):
            Question.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing questions"))

        self.import_personal_questions()
        self.import_generic_questions()
        self.import_position_questions()

        self.stdout.write(self.style.SUCCESS("Successfully imported all questions!"))

    def confirm_action(self, message):
        """Ask user for confirmation"""
        response = input(f"{message} (yes/no): ")
        return response.lower() in ["yes", "y"]

    def import_personal_questions(self):
        """Import personal info questions"""
        self.stdout.write("Importing personal info questions...")

        for q_data in PERSONAL_INFO_QUESTIONS:
            question = Question.objects.create(
                position=None,  # Generic for all positions
                category=q_data["category"],
                field_name=q_data["field_name"],
                is_required=q_data["is_required"],
                order=q_data["order"],
                question_type="text",
            )

            # Create translations
            for lang, text in q_data["text"].items():
                QuestionTranslation.objects.create(question=question, language=lang, text=text)

            self.stdout.write(f"  Created: {q_data['field_name']}")

        self.stdout.write(
            self.style.SUCCESS(f"Imported {len(PERSONAL_INFO_QUESTIONS)} personal questions")
        )

    def import_generic_questions(self):
        """Import generic professional questions"""
        self.stdout.write("Importing generic questions...")

        for q_data in GENERIC_QUESTIONS:
            question = Question.objects.create(
                position=None,  # Generic for all positions
                category=q_data["category"],
                field_name=q_data["field_name"],
                is_required=q_data["is_required"],
                order=q_data["order"],
                question_type="text",
            )

            # Create translations
            for lang, text in q_data["text"].items():
                QuestionTranslation.objects.create(question=question, language=lang, text=text)

            self.stdout.write(f"  Created: {q_data['field_name']}")

        self.stdout.write(
            self.style.SUCCESS(f"Imported {len(GENERIC_QUESTIONS)} generic questions")
        )

    def import_position_questions(self):
        """Import position-specific questions"""
        self.stdout.write("Importing position-specific questions...")

        total_count = 0
        for position, questions in POSITION_QUESTIONS.items():
            self.stdout.write(f"  Position: {position}")

            for q_data in questions:
                question = Question.objects.create(
                    position=position,
                    category="position_specific",
                    field_name=q_data["field_name"],
                    is_required=q_data["is_required"],
                    order=q_data["order"],
                    question_type="text",
                )

                # Create translations
                for lang, text in q_data["question"].items():
                    QuestionTranslation.objects.create(question=question, language=lang, text=text)

                total_count += 1
                self.stdout.write(f"    Created: {q_data['field_name']} (order: {q_data['order']})")

        self.stdout.write(self.style.SUCCESS(f"Imported {total_count} position-specific questions"))
