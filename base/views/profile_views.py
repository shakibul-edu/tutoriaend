from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from copy import deepcopy
from base.models import TeacherProfile, AcademicProfile, Qualification
from base.utils import get_availability_grouped_by_time, calculate_distance
from base.serializer import TeacherProfileSerializer, AcademicProfileSerializer, QualificationSerializer
from django.contrib.gis.measure import D
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse



@extend_schema(
    summary="Create Teacher Profile",
    description="Creates a new TeacherProfile for the authenticated user. Requires authentication.",
    request=TeacherProfileSerializer,
    responses={
        201: OpenApiResponse(response=TeacherProfileSerializer, description="Teacher profile created successfully."),
        400: OpenApiResponse(description="Bad request or profile already exists."),
    },
    examples=[
        OpenApiExample(
            "Create Teacher Profile Example",
            value={
                "bio": "Experienced math teacher.",
                "gender": "male",
                "min_salary": 50000,
                "experience_years": 5,
                "teaching_mode": "both",
                "preferred_distance": 10,
                "medium": [1, 2],
                "subject_list": [1, 2, 3],
                "grades": [1, 2, 3],
                 # Add other required fields as per your TeacherProfile model
                            },
                            request_only=True,
                        ),
                    ],
                )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_teacher(request):
    teacher = TeacherProfile.objects.filter(user=request.user)
    if not teacher.exists():
        data = deepcopy(request.data)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_teachers(request):
    """
    Retrieve a filtered list of TeacherProfile overviews.
    Filters: min_salary, max_salary, gender, grade, distance (optional).
    """
    queryset = TeacherProfile.objects.all()

    serializers = TeacherProfileSerializer(queryset, many=True)
    return Response(serializers.data, status=status.HTTP_200_OK)

    min_salary = request.GET.get('min_salary')
    max_salary = request.GET.get('max_salary')
    gender = request.GET.get('gender')
    grade = request.GET.get('grade')
    distance = request.GET.get('distance')
    if distance and hasattr(request.user, 'location'):
        user_location = request.user.location
        queryset = queryset.filter(user__location__distance_lte=(user_location, D(km=float(distance))))

    if min_salary:
        queryset = queryset.filter(expected_salary__gte=min_salary)
    if max_salary:
        queryset = queryset.filter(expected_salary__lte=max_salary)
    if gender:
        queryset = queryset.filter(gender__iexact=gender)
    if grade:
        queryset = queryset.filter(grades__id=grade)

    # Only return overview fields
    data = [
        {
            "id": teacher.id,
            "name": teacher.user.get_full_name(),
            "gender": teacher.gender,
            "expected_salary": teacher.expected_salary,
            "grades": teacher.grades,
            "profile_picture": teacher.profile_picture.url if teacher.profile_picture else None,
            # Add more overview fields as needed
        }
        for teacher in queryset
    ]
    return Response(data, status=status.HTTP_200_OK)

