# apps/questions/views.py
"""Views for questions."""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from apps.common.responses import error_response, success_response
from apps.questions.models import Question
from apps.questions.serializers import QuestionListSerializer, QuestionSerializer


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving questions.
    Read-only since questions are managed via admin/commands.
    """

    queryset = Question.objects.prefetch_related("translations").all()
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]  # Questions are public

    def get_serializer_class(self):
        if self.action == "list":
            return QuestionListSerializer
        return QuestionSerializer

    def get_serializer_context(self):
        """Add language to serializer context"""
        context = super().get_serializer_context()
        context["language"] = self.request.query_params.get("language")
        return context

    def list(self, request, *args, **kwargs):
        """
        List all questions.
        URL: GET /api/v1/questions/?language=en&position=Software Developer
        """
        request.query_params.get("language")
        position = request.query_params.get("position")

        queryset = self.get_queryset()

        # Filter by position (None for generic, specific for position-specific)
        if position:
            queryset = queryset.filter(Q(position__isnull=True) | Q(position=position))
        else:
            # Only generic questions
            queryset = queryset.filter(position__isnull=True)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"], url_path="by-position")
    def by_position(self, request):
        """
        Get questions for a specific position.
        URL: GET /api/v1/questions/by-position/?position=Software Developer&language=en

        Returns personal + generic + position-specific questions.
        """
        position = request.query_params.get("position")
        request.query_params.get("language", "en")

        if not position:
            return error_response(
                message="Position parameter is required", status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get all relevant questions
        queryset = (
            self.get_queryset()
            .filter(Q(position__isnull=True) | Q(position=position))
            .order_by("order")
        )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"], url_path="personal")
    def personal(self, request):
        """
        Get only personal info questions.
        URL: GET /api/v1/questions/personal/?language=en
        """
        queryset = self.get_queryset().filter(category="personal")
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
