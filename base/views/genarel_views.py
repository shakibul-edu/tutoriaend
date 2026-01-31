from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view,permission_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny
from base.custom_permission import IsAuthenticatedAndNotBanned
from rest_framework.response import Response
from rest_framework import status
from ..utils import calculate_distance, string_to_point
from copy  import deepcopy
from ..models import (TeacherProfile,
                      Availability, UserDashboard)
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
@permission_classes([IsAuthenticatedAndNotBanned])
def protected_view(request):
    """
    A protected view that requires authentication.
    """
    return Response({"detail": f"This is a protected view, accessed by {request.user.first_name} {request.user.last_name}!"})


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndNotBanned])
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
@permission_classes([IsAuthenticatedAndNotBanned])
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


from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample

@extend_schema(
    summary="List or create availability slots",
    description=(
        "Retrieve or create availability slots for the authenticated teacher. "
        "POST accepts a list of objects with 'start', 'end', and 'days' fields. "
        "Each object will be split into multiple instances, one per day."
    ),
    responses={200: AvailabilitySerializer(many=True)},
    request=AvailabilitySerializer(many=True),
    examples=[
        OpenApiExample(
            name="Availability List Example",
            value=[
                {
                    "start": "20:00",
                    "end": "21:00",
                    "days": ["MO", "WE", "FR"]
                },
                {
                    "start": "20:00",
                    "end": "21:00",
                    "days": ["SA", "SU", "MO"]
                }
            ],
            request_only=True,
            response_only=False,
        )
    ]
)
class AvailabilityViewSet(ModelViewSet):
    """
    A viewset for viewing and editing availability slots for the authenticated teacher.
    Accepts a list of availability objects with 'start', 'end', and 'days' fields.
    Each instance in the model should have only one day, so this viewset will
    split each input object into multiple instances, one per day.
    """
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticatedAndNotBanned]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', None), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if not teacher:
            return Availability.objects.none()
        return Availability.objects.filter(tutor=teacher)

    def create(self, request):
        teacher = get_object_or_404(TeacherProfile, user=request.user)
        data = request.data
        if not isinstance(data, list):
            data = [data]
        instances = []
        errors = []
        
        # Delete all existing availability entries for this teacher
        Availability.objects.filter(tutor=teacher).delete()
        
        for entry in data:
            print(entry)
            if not isinstance(entry, dict):
                errors.append({'error': 'Each entry must be a dictionary.'})
                continue
            start = entry.get('start')
            end = entry.get('end')
            days = entry.get('days', [])
            for day in days:
                instance_data = {
                    'start_time': start,
                    'end_time': end,
                    'days_of_week': day,
                }
                single_serializer = self.get_serializer(data=instance_data)
                if single_serializer.is_valid():
                    instances.append(single_serializer.save(tutor=teacher))
                else:
                    errors.append(single_serializer.errors)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instances, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    

@api_view(['GET'])
@permission_classes([IsAuthenticatedAndNotBanned])
def user_dashboard(request):
    """
    Retrieve the dashboard data for the authenticated user.
    """
    user_dashboard, created = UserDashboard.objects.get_or_create(user=request.user)
   
    dashboard_data = {
        "total_contact_requests_sent": user_dashboard.total_requests_sent,
        "total_contact_requests_received": user_dashboard.total_requests_received,
        "total_pending_requests": user_dashboard.total_pending_requests,
        
    }
    return Response(dashboard_data, status=status.HTTP_200_OK)



