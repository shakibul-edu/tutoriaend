# from math import radians, sin, cos, sqrt, atan2

from datetime import time
from .models import Availability, TeacherProfile # Assuming models.py is in the same app
from django.contrib.gis.geos import Point
from geopy.distance import geodesic
from django.contrib.gis.db.models.functions import Distance as GisDistance  

# def calculate_distance(loc1: Point, loc2: Point) -> float:
#     """
#     Calculates the distance in kilometers between two Point objects using the Web Mercator projection.

#     Args:
#         loc1 (Point): The first location as a Point object.
#         loc2 (Point): The second location as a Point object.

#     Returns:
#         float: The distance between the two points in kilometers.
#     """

#     # distance_obj = GisDistance('some_field', loc2).evaluate(loc1, connection=None)
#     # return distance_obj.km

#     loc1_3857 = loc1.transform(3857, clone=True)
#     loc2_3857 = loc2.transform(3857, clone=True)
#     return loc1_3857.distance(loc2_3857) / 1000  # Convert meters to kilometers

def calculate_distance(loc1: Point, loc2: Point) -> float:
    """
    Calculates the distance using geopy's geodesic method between two Point objects.
    """
    # Using geopy's geodesic method for accurate distance calculation
    return geodesic((loc1.y, loc1.x), (loc2.y, loc2.x)).km



    

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
        day_of_week=day_of_week,
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

