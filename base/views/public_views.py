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
    parameters=[
        OpenApiParameter(
            name="medium_id",
            type=int,
            location=OpenApiParameter.QUERY,
            required=True,
            description="The ID of the medium to filter grades by."
        )
    ],
    responses={
        200: OpenApiResponse(
            response=GradeSerializer(many=True),
            description="A list of grades for the specified medium",
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
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def get_grades_by_medium(request):
    """
    Retrieve a list of subjects filtered by the given medium ID.
    Expects 'medium_id' as a GET parameter.
    """
    medium_id = request.query_params.get('medium_id')
    if not medium_id:
        return Response({"detail": "medium_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        medium = Medium.objects.get(id=medium_id)
    except Medium.DoesNotExist:
        return Response({"detail": "Medium not found."}, status=status.HTTP_404_NOT_FOUND)
    grades = Grade.objects.filter(medium=medium)
    data = GradeSerializer(grades, many=True).data
    return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="grade_id",
            type=int,
            location=OpenApiParameter.QUERY,
            required=True,
            description="The ID of the grade to filter subjects by."
        )
    ],
    responses={
        200: OpenApiResponse(
            response=SubjectSerializer(many=True),
            description="A list of subjects for the specified grade",
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
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def get_subjects_by_grade(request):
    """
    Retrieve a list of subjects filtered by the given medium ID.
    Expects 'medium_id' as a GET parameter.
    """
    grade_id = request.query_params.get('grade_id')
    if not grade_id:
        return Response({"detail": "grade_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        grade = Grade.objects.get(id=grade_id)
    except Medium.DoesNotExist:
        return Response({"detail": "Grade not found."}, status=status.HTTP_404_NOT_FOUND)
    subjects = Subject.objects.filter(grade=grade)
    data = SubjectSerializer(subjects, many=True).data
    return Response(data, status=status.HTTP_200_OK)
