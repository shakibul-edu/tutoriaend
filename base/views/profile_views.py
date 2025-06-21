from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from copy import deepcopy
from base.models import TeacherProfile, AcademicProfile, Qualification
from base.utils import get_availability_grouped_by_time
from base.serializer import TeacherProfileSerializer, AcademicProfileSerializer, QualificationSerializer



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_teacher(request):
    teacher = TeacherProfile.objects.filter(user=request.user)
    if not teacher.exists():
        data = deepcopy(request.data)
        print(request.user.id)
        data['user'] = request.user.id
        serializer = TeacherProfileSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            request.user.is_teacher = True
            request.user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    else:
        return Response({"detail": "Teacher profile already exists."}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def edit_teacher(request):
    try:
        teacher = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return Response({"detail": "Teacher profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

    data = deepcopy(request.data)
    data['user'] = request.user.id 
    serializer = TeacherProfileSerializer(teacher, data=data, partial=True)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_full_profile(request):
    """
    Retrieve the TeacherProfile, AcademicProfiles, and Qualifications for the authenticated user.
    """
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return Response({"detail": "Teacher profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

    teacher_profile_data = TeacherProfileSerializer(teacher_profile).data
    academic_profiles = AcademicProfile.objects.filter(teacher=teacher_profile)
    academic_profiles_data = AcademicProfileSerializer(academic_profiles, many=True).data
    qualifications = Qualification.objects.filter(teacher=teacher_profile)
    qualifications_data = QualificationSerializer(qualifications, many=True).data

    return Response({
        "teacher_profile": teacher_profile_data,
        "academic_profiles": academic_profiles_data,
        "qualifications": qualifications_data,
        "scheduled_availability": get_availability_grouped_by_time(teacher_profile)
    }, status=status.HTTP_200_OK)

