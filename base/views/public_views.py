from copy import deepcopy
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from base.models import Medium, Subject, Grade
from base.serializer import GradeSerializer, SubjectSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def get_mediums(request):
    """
    Retrieve a list of all available mediums.
    """
    mediums = Medium.objects.all()
    data = [{"id": medium.id, "name": medium.name} for medium in mediums]
    return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "medium_id": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "A list of medium IDs to filter grades by."
                }
            },
            "required": ["medium_id"]
        }
    },
    responses={
        200: OpenApiResponse(
            response=GradeSerializer(many=True),
            description="A list of grades for the specified mediums",
            examples=[
                OpenApiExample(
                    'Sample Response',
                    summary='Successful response',
                    description='Example list of grades',
                    value=[
                        {
                            "id": 1,
                            "name": "6th",
                            "sequence": 6,
                            "medium": [
                                1,
                                2
                            ]
                        },
                        {
                            "id": 2,
                            "name": "7th",
                            "sequence": 7,
                            "medium": [
                                2
                            ]
                        }
                    ],
                )
            ]
        ),
        400: OpenApiResponse(
            description="Bad Request - missing medium_id",
            examples=[
                OpenApiExample(
                    'Bad Request',
                    value={"detail": "medium_id parameter is required."},
                )
            ]
        ),
        404: OpenApiResponse(
            description="Medium not found",
            examples=[
                OpenApiExample(
                    'Not Found',
                    value={"detail": "Medium not found."},
                )
            ]
        ),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def get_grades_by_medium(request):
    """
    Retrieve a list of grades filtered by the given medium IDs.
    Expects 'medium_id' as a POST field (array of IDs).
    Example: {"medium_id": [1, 2]}
    """
    medium_ids = request.data.get('medium_id')
    if not medium_ids or not isinstance(medium_ids, list):
        return Response({"detail": "medium_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    mediums = Medium.objects.filter(id__in=medium_ids)
    if not mediums.exists():
        return Response({"detail": "Medium not found."}, status=status.HTTP_404_NOT_FOUND)
    grades = Grade.objects.filter(medium__in=mediums).distinct()
    if not grades.exists():
        return Response({"detail": "No grades found for the specified medium."}, status=status.HTTP_404_NOT_FOUND)
    data = GradeSerializer(grades, many=True).data
    return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "grade_id": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "A list of grade IDs to filter subjects by."
                }
            },
            "required": ["grade_id"]
        }
    },
    responses={
        200: OpenApiResponse(
            response=SubjectSerializer(many=True),
            description="A list of subjects for the specified grades",
            examples=[
                OpenApiExample(
                    'Sample Response',
                    summary='Successful response',
                    description='Example list of subjects',
                    value=[
                        {
                            "id": 1,
                            "name": "Mathmatics",
                            "description": "",
                            "subject_code": "MATH-204",
                            "grade": 1
                        },
                        {
                            "id": 2,
                            "name": "Science",
                            "description": "",
                            "subject_code": None,
                            "grade": 1
                        }
                    ]
                )
            ]
        ),
        400: OpenApiResponse(
            description="Bad Request - missing grade_id",
            examples=[
                OpenApiExample(
                    'Bad Request',
                    value={"detail": "grade_id parameter is required."},
                )
            ]
        ),
        404: OpenApiResponse(
            description="Grade not found",
            examples=[
                OpenApiExample(
                    'Not Found',
                    value={"detail": "Grade not found."},
                )
            ]
        ),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def get_subjects_by_grade(request):
    """
    Retrieve a list of subjects filtered by the given grade IDs.
    Expects 'grade_id' as a POST field (array of IDs).
    Example: {"grade_id": [1, 2]}
    """
    grade_ids = request.data.get('grade_id')
    if not grade_ids or not isinstance(grade_ids, list):
        return Response({"detail": "grade_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    grades = Grade.objects.filter(id__in=grade_ids)
    if not grades.exists():
        return Response({"detail": "Grade not found."}, status=status.HTTP_404_NOT_FOUND)
    subjects = Subject.objects.filter(grade__in=grades).distinct()
    if not subjects.exists():
        return Response({"detail": "No subjects found for the specified grade."}, status=status.HTTP_404_NOT_FOUND)
    data = SubjectSerializer(subjects, many=True).data
    return Response(data, status=status.HTTP_200_OK)
