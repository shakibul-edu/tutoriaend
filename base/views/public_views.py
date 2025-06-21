from copy import deepcopy
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from base.models import Medium, Subject, Grade
from base.serializer import GradeSerializer, SubjectSerializer




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
