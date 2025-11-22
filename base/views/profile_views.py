from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from base.models import TeacherProfile, AcademicProfile, Qualification
from base.utils import get_availability_grouped_by_time, calculate_distance
from base.serializer import TeacherProfileSerializer, AcademicProfileSerializer, QualificationSerializer
from django.contrib.gis.measure import D
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from base.custom_permission import IsAuthenticatedAndNotBanned
from base.models import TeacherProfile
from base.serializer import TeacherProfileSerializer



class TeacherProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing teacher profiles.
    """
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]

    def get_queryset(self):
        id = self.request.GET.get('id')
        if id:
            return TeacherProfile.objects.filter(id=id)
        user = self.request.user
        return TeacherProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.user == self.request.user:
            serializer.save()
        else:
            raise PermissionDenied("You can only update your own profile.")






@api_view(['GET'])
@permission_classes([IsAuthenticatedAndNotBanned])
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
@permission_classes([IsAuthenticatedAndNotBanned])
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

