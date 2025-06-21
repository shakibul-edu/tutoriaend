from copy import deepcopy
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from base.models import TeacherProfile, AcademicProfile, Qualification
from base.serializer import TeacherProfileSerializer, AcademicProfileSerializer, QualificationSerializer



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_academic_profile(request):
    teacher = TeacherProfile.objects.filter(user=request.user)
    if not teacher.exists():
        return Response({"detail": "Teacher profile does not exist. Please create a teacher profile first."}, status=status.HTTP_400_BAD_REQUEST)
    data = deepcopy(request.data)
    data['teacher'] = teacher.first().id
    serializer = AcademicProfileSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def edit_academic_profile(request):
    try:
        academic_profile = AcademicProfile.objects.get(id=request.data.get('id'))
    except AcademicProfile.DoesNotExist:
        return Response({"detail": "Academic profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

    data = deepcopy(request.data)
    data['teacher'] = academic_profile.teacher.id
    serializer = AcademicProfileSerializer(academic_profile, data=data, partial=True)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_qualification(request):
    teacher = TeacherProfile.objects.filter(user=request.user)
    if not teacher.exists():
        return Response({"detail": "Teacher profile does not exist. Please create a teacher profile first."}, status=status.HTTP_400_BAD_REQUEST)
    data = deepcopy(request.data)
    data['teacher'] = teacher.first().id
    serializer = QualificationSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def edit_qualification(request):
    try:
        qualification = Qualification.objects.get(id=request.data.get('id'))
    except AcademicProfile.DoesNotExist:
        return Response({"detail": "Qualification profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

    data = deepcopy(request.data)
    data['teacher'] = qualification.teacher.id
    serializer = QualificationSerializer(qualification, data=data, partial=True)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
