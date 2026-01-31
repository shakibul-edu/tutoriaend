from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from base.models import TeacherProfile, AcademicProfile, Qualification
from base.utils import get_availability_grouped_by_time, calculate_distance, get_average_review
from base.serializer import TeacherProfileSerializer, AcademicProfileSerializer, QualificationSerializer
from django.contrib.gis.measure import D
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from base.custom_permission import IsAuthenticatedAndNotBanned
from base.models import TeacherProfile, Availability, ContactRequest,TeacherReview
from base.serializer import TeacherProfileSerializer, AvailabilitySerializer



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





@extend_schema(
    operation_id="getTeacherFullProfile",
    description="Retrieve a teacher's full profile (teacher profile, academic profiles, qualifications and scheduled availability).",
    parameters=[
        OpenApiParameter(name="pk", location=OpenApiParameter.PATH, required=True, type=int, description="TeacherProfile ID")
    ],
    responses={
        200: OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "teacher_profile": {"$ref": "#/components/schemas/TeacherProfile"},
                    "academic_profiles": {"type": "array", "items": {"$ref": "#/components/schemas/AcademicProfile"}},
                    "qualifications": {"type": "array", "items": {"$ref": "#/components/schemas/Qualification"}},
                    "scheduled_availability": {"type": "array", "items": {"$ref": "#/components/schemas/Availability"}}
                }
            }
        ),
        404: OpenApiResponse(description="Teacher profile not found.")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedAndNotBanned])
def get_teacher_full_profile(request, pk):
    """
    Retrieve the TeacherProfile, AcademicProfiles, and Qualifications for the authenticated user.
    """
    try:
        teacher_profile = TeacherProfile.objects.get(pk=pk)
        teacher_profile_data = TeacherProfileSerializer(teacher_profile).data
        contact_request = ContactRequest.objects.filter(student=request.user, teacher=teacher_profile)

        if contact_request.exists() and contact_request[0].status in ['accepted', 'contacted']:
            pass
        else:
            teacher_profile_data['phone'] = None
    except TeacherProfile.DoesNotExist:
        return Response({"detail": "Teacher profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

    academic_profiles = AcademicProfile.objects.filter(teacher=teacher_profile)
    academic_profiles_data = AcademicProfileSerializer(academic_profiles, many=True).data
    qualifications = Qualification.objects.filter(teacher=teacher_profile)
    qualifications_data = QualificationSerializer(qualifications, many=True).data
    availability = Availability.objects.filter(tutor=teacher_profile)
    availability_data = AvailabilitySerializer(availability, many=True).data

    return Response({
        "teacher_profile": teacher_profile_data,
        "academic_profiles": academic_profiles_data,
        "qualifications": qualifications_data,
        "scheduled_availability": availability_data
    }, status=status.HTTP_200_OK)



@extend_schema(
    operation_id="filterTeachers",
    description="Retrieve a filtered list of teacher profile overviews. Supports filtering by expected salary range, gender, grade id, and optional distance (km) from the requesting user's location (only applied if user has a location).",
    parameters=[
        OpenApiParameter(
            name="min_salary",
            location="query",
            required=False,
            type=int,
            description="Minimum expected salary."
        ),
        OpenApiParameter(
            name="max_salary",
            location="query",
            required=False,
            type=int,
            description="Maximum expected salary."
        ),
        OpenApiParameter(
            name="gender",
            location="query",
            required=False,
            type=str,
            description="Filter by gender (case-insensitive).",
            examples=[
                OpenApiExample("Male", value="male"),
                OpenApiExample("Female", value="female")
            ]
        ),
        OpenApiParameter(
            name="grade",
            location="query",
            required=False,
            type=int,
            description="Grade ID to filter teachers qualified for that grade."
        ),
        OpenApiParameter(
            name="distance",
            location="query",
            required=False,
            type=float,
            description="Maximum distance in kilometers from the requesting user's location."
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="List of teacher overview objects.",
            response={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "gender": {"type": "string"},
                        "expected_salary": {"type": ["number", "null"]},
                        "grades": {"type": "string", "description": "Representation of grades field."},
                        "profile_picture": {"type": ["string", "null"], "format": "uri"}
                    }
                }
            },
            examples=[
                OpenApiExample(
                    "SampleResponse",
                    value=[
                        {
                            "id": 12,
                            "name": "Jane Doe",
                            "gender": "female",
                            "expected_salary": 50000,
                            "grades": "Grade 6, Grade 7",
                            "profile_picture": "https://example.com/media/pic.jpg"
                        }
                    ]
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedAndNotBanned])
def filter_teachers(request):
    """
    Retrieve a filtered list of TeacherProfile overviews.
    Filters: min_salary, max_salary, gender, grade, distance (optional).
    """
    # Use select_related and prefetch_related to optimize queries and avoid missing relations
    queryset = TeacherProfile.objects.select_related('user').prefetch_related('grade_list', 'medium_list').all()

    # serializers = TeacherProfileSerializer(queryset, many=True)
    # return Response(serializers.data, status=status.HTTP_200_OK)

    max_salary = request.GET.get('feeRange')
    gender = request.GET.get('gender')
    grade = request.GET.get('grade')
    distance = request.GET.get('distance')
    tuition_type = request.GET.get('tuitionType')
    
    # Only apply distance filter if user has a valid location (not None)
    if distance and hasattr(request.user, 'location') and request.user.location is not None:
        try:
            user_location = request.user.location
            queryset = queryset.filter(user__location__distance_lte=(user_location, D(km=float(distance))))
        except Exception as e:
            # Log the error but don't fail the entire request
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Distance filter failed: {e}")

    if max_salary:
        queryset = queryset.filter(min_salary__lte=max_salary)
    if gender and gender in ['male', 'female']:
        queryset = queryset.filter(gender__iexact=gender)
    if grade:
        queryset = queryset.filter(grades__id=grade)
    if tuition_type and tuition_type in ['online', 'offline']:
        queryset = queryset.filter(teaching_mode__iexact=tuition_type)

    # Only return overview fields
    data = []
    import logging
    logger = logging.getLogger(__name__)
    
    for teacher in queryset:
        try:
            # Skip teachers without a valid user
            if not hasattr(teacher, 'user') or teacher.user is None:
                logger.warning(f"Teacher {teacher.id} has no user associated")
                continue
            
            # Safely calculate distance only if both locations exist and are not None
            distance_value = None
            try:
                if (hasattr(request.user, 'location') and request.user.location is not None and 
                    hasattr(teacher.user, 'location') and teacher.user.location is not None):
                    distance_value = calculate_distance(request.user.location, teacher.user.location)
            except Exception as e:
                logger.warning(f"Distance calculation failed for teacher {teacher.id}: {e}")
            
            # Safely get grade list
            try:
                grade_list = teacher.grade_list.all()
                maximum_grade = max((grade for grade in grade_list), key=lambda g: g.sequence, default=None).name if grade_list else None
            except Exception as e:
                logger.warning(f"Grade list access failed for teacher {teacher.id}: {e}")
                maximum_grade = None
            
            # Safely get medium list
            try:
                medium_list_str = ", ".join([medium.name for medium in teacher.medium_list.all()])
            except Exception as e:
                logger.warning(f"Medium list access failed for teacher {teacher.id}: {e}")
                medium_list_str = ""
            
            # Safely get review data
            try:
                reviews_average, reviews_count = get_average_review(teacher)
            except Exception as e:
                logger.warning(f"Review calculation failed for teacher {teacher.id}: {e}")
                reviews_average, reviews_count = None, 0
            
            data.append({
                "id": teacher.id,
                "name": teacher.user.get_full_name() if teacher.user else "Unknown",
                "gender": getattr(teacher, 'gender', None),
                "verified": getattr(teacher, 'verified', False),
                "highest_qualification": getattr(teacher, 'highest_qualification', None),
                "medium_list": medium_list_str,
                "teaching_mode": getattr(teacher, 'teaching_mode', None),
                "reviews_average": reviews_average,
                "reviews_count": reviews_count,
                "distance": distance_value,
                "expected_salary": getattr(teacher, 'min_salary', None),
                "maximum_grade": maximum_grade,
                "profile_picture": teacher.profile_picture.url if hasattr(teacher, 'profile_picture') and teacher.profile_picture else None,
            })
        except Exception as e:
            # Log the full error and skip this teacher
            logger.error(f"Failed to process teacher {teacher.id}: {str(e)}", exc_info=True)
            continue
    
    return Response(data, status=status.HTTP_200_OK)

