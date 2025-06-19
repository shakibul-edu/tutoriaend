
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .utils import calculate_distance, get_availability_grouped_by_time
from copy  import deepcopy
from .models import TeacherProfile, AcademicProfile, Qualification, Availability
from .serializer import TeacherProfileSerializer, AcademicProfileSerializer, QualificationSerializer, AvailabilitySerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def home(request):
    """
    Home view that returns a simple welcome message.
    """
    return Response({"message": "Welcome to the Tutoria API!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    """
    A protected view that requires authentication.
    """
    return Response({"detail": f"This is a protected view, accessed by {request.user.first_name} {request.user.last_name}!"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_location(request):
    """
    A protected view to set the user's location.
    Expects a JSON body with a 'location' field.
    """
    print("initiated set_location view")
    location = request.data.get('location')
    if not location:
        return Response({"error": "Location is required."}, status=400)
    # Check if user already has a location
    previous_location = getattr(request.user, "location", None)
    update_param = request.data.get("update", False)

    
    if previous_location:
        distance = calculate_distance(previous_location, location)
        print(f"Previous location: {previous_location}, New location: {location}, Distance: {distance} km")
        if distance is not None and distance >= .2 and not update_param:
            return Response(
                {
                    "detail": "Location update available. The new location is more than 200 meters away from the previous location.",
                    "distance_km": round(distance, 3),
                    "update_required": True
                },
                status=200
            )
        else:
            return Response({"detail": "Location don't need to be updated. The new location is within 200 meters of the previous location."},status=200)
    user = request.user
    user.location = location
    user.save()
    return Response({"detail": "Location updated successfully."}, status=200)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_availability_slots(request):
    """
    Create multiple availability slots for the authenticated teacher.
    Expects a list of availability slot data in the request body.
    """
    teacher = TeacherProfile.objects.filter(user=request.user).first()
    if not teacher:
        return Response({"detail": "Teacher profile does not exist. Please create a teacher profile first."}, status=status.HTTP_400_BAD_REQUEST)
    data = deepcopy(request.data)
    slots_data = data if isinstance(data, list) else data.get('slots', [])
    if not isinstance(slots_data, list) or not slots_data:
        return Response({"detail": "A list of availability slots is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Attach teacher id to each slot
    for slot in slots_data:
        slot['tutor'] = teacher.id
        print(slot)

    serializer = AvailabilitySerializer(data=slots_data, many=True)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def edit_availability_slots(request):
    """
    Edit multiple availability slots for the authenticated teacher.
    Expects a list of slot updates, each with an 'id' field.
    """
    teacher = TeacherProfile.objects.filter(user=request.user).first()
    if not teacher:
        return Response({"detail": "Teacher profile does not exist. Please create a teacher profile first."}, status=status.HTTP_400_BAD_REQUEST)
    data = deepcopy(request.data)
    slots_data = data if isinstance(data, list) else data.get('slots', [])
    if not isinstance(slots_data, list) or not slots_data:
        return Response({"detail": "A list of availability slots is required."}, status=status.HTTP_400_BAD_REQUEST)

    updated_slots = []
    errors = []
    for slot_data in slots_data:
        slot_id = slot_data.get('id')
        if not slot_id:
            errors.append({"detail": "Slot 'id' is required.", "slot": slot_data})
            continue
        try:
            slot = Availability.objects.get(id=slot_id, tutor=teacher)
        except Availability.DoesNotExist:
            errors.append({"detail": f"Availability slot with id {slot_id} does not exist.", "slot": slot_data})
            continue
        slot_data['tutor'] = teacher.id
        serializer = AvailabilitySerializer(slot, data=slot_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            updated_slots.append(serializer.data)
        else:
            errors.append({"slot": slot_data, "errors": serializer.errors})

    response_data = {"updated_slots": updated_slots}
    if errors:
        response_data["errors"] = errors
    return Response(response_data, status=status.HTTP_200_OK if updated_slots else status.HTTP_400_BAD_REQUEST)








