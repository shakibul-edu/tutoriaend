
from rest_framework.decorators import api_view,permission_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from ..utils import calculate_distance, string_to_point
from copy  import deepcopy
from ..models import (TeacherProfile,
                      Availability)
from ..serializer import ( AvailabilitySerializer)
from rest_framework.viewsets import ModelViewSet
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

@extend_schema(exclude=True)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location(request):
    print("initiated get_location view")
    """
    A protected view to get the user's location.
    """
    if hasattr(request.user, "location") and request.user.location:
        location = request.user.location
        return Response({"location": {
            "latitude": location.y,
            "longitude": location.x,
            "accuracy": 0  # Accuracy is not stored; set to 0 or handle as needed
        }}, status=200)
    else:
        return Response({"detail": "Location not set."}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_location(request):
    """
    A protected view to set the user's location.
    Expects a JSON body with a 'location' field.
    """
    print("initiated set_location view")
    location = string_to_point(request.data.get('location'))
    
    if not location:
        return Response({"error": "Location is required."}, status=400)
    # Check if user already has a location
    previous_location = getattr(request.user, "location", None)

    print(f"Received location: {location}")
    print(f"Received location: {previous_location}")
    update_param = request.GET.get("update")

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
        elif distance is not None and distance < .2:
            return Response({"detail": "Location don't need to be updated. The new location is within 200 meters of the previous location."},status=200)
    user = request.user
    if not location:
        return Response({"error": "Invalid location format. Use 'lon,lat' format."}, status=400)
    user.location = location
    user.save()
    return Response({"detail": "Location updated successfully."}, status=200)




# @extend_schema(
#     request=AvailabilitySerializer(many=True),
#     responses={201: AvailabilitySerializer(many=True)},
#     description="Create multiple availability slots for the authenticated teacher. Expects a list of availability slot data."
# )
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_availability_slots(request):
#     """
#     Create multiple availability slots for the authenticated teacher.
#     Expects a list of availability slot data in the request body.
#     """
#     teacher = TeacherProfile.objects.filter(user=request.user).first()
#     if not teacher:
#         return Response({"detail": "Teacher profile does not exist. Please create a teacher profile first."}, status=status.HTTP_404_NOT_FOUND)
#     data = deepcopy(request.data)
#     slots_data = data if isinstance(data, list) else data.get('slots', [])
#     if not isinstance(slots_data, list) or not slots_data:
#         return Response({"detail": "A list of availability slots is required."}, status=status.HTTP_400_BAD_REQUEST)
    
#     # Attach teacher id to each slot
#     for slot in slots_data:
#         slot['tutor'] = teacher.id
#         print(slot)

#     serializer = AvailabilitySerializer(data=slots_data, many=True)
#     if serializer.is_valid(raise_exception=True):
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# @api_view(['PUT', 'PATCH'])
# @permission_classes([IsAuthenticated])
# def edit_availability_slots(request):
#     """
#     Edit multiple availability slots for the authenticated teacher.
#     Expects a list of slot updates, each with an 'id' field.
#     """
#     teacher = TeacherProfile.objects.filter(user=request.user).first()
#     if not teacher:
#         return Response({"detail": "Teacher profile does not exist. Please create a teacher profile first."}, status=status.HTTP_400_BAD_REQUEST)
#     data = deepcopy(request.data)
#     slots_data = data if isinstance(data, list) else data.get('slots', [])
#     if not isinstance(slots_data, list) or not slots_data:
#         return Response({"detail": "A list of availability slots is required."}, status=status.HTTP_400_BAD_REQUEST)

#     updated_slots = []
#     errors = []
#     for slot_data in slots_data:
#         slot_id = slot_data.get('id')
#         if not slot_id:
#             errors.append({"detail": "Slot 'id' is required.", "slot": slot_data})
#             continue
#         try:
#             slot = Availability.objects.get(id=slot_id, tutor=teacher)
#         except Availability.DoesNotExist:
#             errors.append({"detail": f"Availability slot with id {slot_id} does not exist.", "slot": slot_data})
#             continue
#         slot_data['tutor'] = teacher.id
#         serializer = AvailabilitySerializer(slot, data=slot_data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             updated_slots.append(serializer.data)
#         else:
#             errors.append({"slot": slot_data, "errors": serializer.errors})

#     response_data = {"updated_slots": updated_slots}
#     if errors:
#         response_data["errors"] = errors
#     return Response(response_data, status=status.HTTP_200_OK if updated_slots else status.HTTP_400_BAD_REQUEST)



class AvailabilityViewSet(ModelViewSet):
    """
    A viewset for viewing and editing availability slots for the authenticated teacher.
    """
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get_queryset(self):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if not teacher:
            return Availability.objects.none()
        return Availability.objects.filter(tutor=teacher)

    def perform_create(self, serializer):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if not teacher:
            raise serializers.ValidationError("Teacher profile does not exist. Please create a teacher profile first.")
        serializer.save(tutor=teacher)





