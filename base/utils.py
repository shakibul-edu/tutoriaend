
from datetime import time
from .models import Availability, TeacherProfile,TeacherReview 
from django.contrib.gis.geos import Point
from django.db.models import Avg
from geopy.distance import geodesic
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework that logs errors
    and provides better error responses in production.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception details
    if response is None:
        # This means the exception was not handled by DRF's default handler
        # Log the full exception for debugging
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )
        
        # Return a generic 500 error response
        return Response(
            {
                'detail': 'An internal server error occurred. Please try again later.',
                'error_type': exc.__class__.__name__
            },
            status=500
        )
    
    # Log handled exceptions at warning level
    logger.warning(
        f"API exception: {exc.__class__.__name__}: {str(exc)}",
        extra={
            'status_code': response.status_code,
            'context': context
        }
    )
    
    return response

def calculate_distance(loc1: Point, loc2: Point) -> float:
    """
    Calculates the distance using geopy's geodesic method between two Point objects.
    """
    return round(geodesic((loc1.y, loc1.x), (loc2.y, loc2.x)).km,2)



    

def string_to_point(location: str) -> Point:
    """
    Converts a string representation of a location (lon,lat) into a Point object.
    
    Args:
        location (str): A string in the format "lon,lat".
    
    Returns:
        Point: A Point object representing the geographical location.
    """
    lat, lon, accu = map(float, location.split(','))
    print(f"Converting string to point: {lat}, {lon}, {accu}")
    return Point(lon, lat, srid=4326)  # Using WGS 84 coordinate system

# def calculate_distance(loc1, loc2):
#     lat1, lon1, accu1 = map(float, loc1.split(","))
#     lat2, lon2, accu1 = map(float, loc2.split(","))
#     R = 6371  # Earth radius in km
#     dlat = radians(lat2 - lat1)
#     dlon = radians(lon2 - lon1)
    
#     a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
#     return R * c





def find_available_tutors(day_of_week: str, desired_start_time: time, desired_end_time: time) -> list[TeacherProfile]:
    """
    Finds tutors who are available for the entire specified time range on a given day.

    Args:
        day_of_week (str): The three-letter code for the day (e.g., 'MON', 'TUE').
                           Must match the choices defined in Availability.DAY_CHOICES.
        desired_start_time (datetime.time): The start time of the desired booking slot.
        desired_end_time (datetime.time): The end time of the desired booking slot.

    Returns:
        list[Tutor]: A list of Tutor objects who are available for the entire
                     specified duration on the given day.
    """
    # Basic validation for time range
    if desired_start_time >= desired_end_time:
        print("Error: Desired end time must be after desired start time.")
        return []

    # 1. Filter Availability slots by day of the week
    # 2. Filter for availability slots where the desired range fits entirely within
    #    the tutor's available slot.
    #    This means:
    #    - The availability slot's start_time must be less than or equal to the desired_start_time.
    #    - The availability slot's end_time must be greater than or equal to the desired_end_time.
    available_slots = Availability.objects.filter(
        days_of_week=day_of_week,
        start_time__lte=desired_start_time, # Availability starts before or at desired start
        end_time__gte=desired_end_time      # Availability ends after or at desired end
    ).select_related('tutor') # Optimize by pre-fetching related Tutor objects

    # Extract unique tutors from the filtered availability slots
    # Using a set to ensure uniqueness of tutors
    found_tutors = set()
    for slot in available_slots:
        found_tutors.add(slot.tutor)

    # Convert the set back to a list for consistent return type
    return list(found_tutors)



def get_availability_grouped_by_time(teacher:TeacherProfile):
    """
    Returns the availability slots for the authenticated teacher,
    grouped by days that share the same time frame.
    """
    
    slots = Availability.objects.filter(tutor=teacher)
    grouped = {}
    for slot in slots:
        # Assuming slot has 'start_time' and 'end_time' fields and 'day' field
        time_key = f"{slot.start_time}-{slot.end_time}"
        if time_key not in grouped:
            grouped[time_key] = {
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "days": []
            }
        grouped[time_key]["days"].append(slot.day_of_week)
    
    result = list(grouped.values())
    return result

def get_average_review(tutor: TeacherProfile):
    reviews = TeacherReview.objects.filter(contact_request__teacher=tutor)
    reviews_count = reviews.count()
    if not reviews.exists():
        return None, 0
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    return round(avg_rating, 2), reviews_count

