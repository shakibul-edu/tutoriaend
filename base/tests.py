from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import time
from .models import TeacherProfile, Availability # Import your models
from .utils import find_available_tutors # Import the function to be tested

class FindAvailableTutorsTestCase(TestCase):
    """
    Test suite for the find_available_tutors function.
    """

    def setUp(self):
        """
        Set up test data (tutors and their availabilities) before each test method.
        """
        User = get_user_model()
        from django.contrib.gis.geos import Point
        dummy_location = Point(90.4125, 23.8103)
        # Create User instances
        user1 = User.objects.create_user(username="junaid", email="junaid@gmail.com", location=dummy_location)
        user2 = User.objects.create_user(username="tarikul", email="tarikul@gmail.com", location=dummy_location)
        user3 = User.objects.create_user(username="tasmin", email="tasmin@gmail.com", location=dummy_location)
        user4 = User.objects.create_user(username="243000522e", email="243000522e@gmail.com", location=dummy_location)

        # Create TeacherProfile instances
        self.tutor1 = TeacherProfile.objects.create(user=user1)
        self.tutor2 = TeacherProfile.objects.create(user=user2)
        self.tutor3 = TeacherProfile.objects.create(user=user3)
        self.tutor4 = TeacherProfile.objects.create(user=user4)

        # Create Availability instances for Tutor 1 (Alice)
        Availability.objects.create(tutor=self.tutor1, days_of_week='MON',
                                   start_time=time(9, 0), end_time=time(12, 0))
        Availability.objects.create(tutor=self.tutor1, days_of_week='MON',
                                   start_time=time(14, 0), end_time=time(17, 0))
        Availability.objects.create(tutor=self.tutor1, days_of_week='TUE',
                                   start_time=time(10, 0), end_time=time(13, 0))

        # Create Availability instances for Tutor 2 (Bob)
        Availability.objects.create(tutor=self.tutor2, days_of_week='MON',
                                   start_time=time(10, 0), end_time=time(13, 0))
        Availability.objects.create(tutor=self.tutor2, days_of_week='WED',
                                   start_time=time(9, 0), end_time=time(12, 0))

        # Create Availability instances for Tutor 3 (Charlie)
        Availability.objects.create(tutor=self.tutor3, days_of_week='MON',
                                   start_time=time(9, 30), end_time=time(11, 30))
        Availability.objects.create(tutor=self.tutor3, days_of_week='MON',
                                   start_time=time(15, 0), end_time=time(16, 0))

        # Create Availability instances for Tutor 4 (Diana) - No Monday availability
        Availability.objects.create(tutor=self.tutor4, days_of_week='TUE',
                                   start_time=time(9, 0), end_time=time(17, 0))


    def test_exact_match_availability(self):
        """
        Test finding tutors for a time slot that exactly matches an availability.
        """
        desired_day = 'MON'
        desired_start = time(9, 0)
        desired_end = time(12, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertIn(self.tutor1, found_tutors)
        self.assertEqual(len(found_tutors), 1) # Only Alice should be found

    def test_within_availability(self):
        """
        Test finding tutors for a time slot that is completely within a larger availability.
        """
        desired_day = 'MON'
        desired_start = time(10, 0)
        desired_end = time(11, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertIn(self.tutor1, found_tutors) # Alice (9-12)
        self.assertIn(self.tutor2, found_tutors) # Bob (10-13)
        self.assertIn(self.tutor3, found_tutors) # Charlie (9:30-11:30)
        self.assertEqual(len(found_tutors), 3)

    def test_multiple_tutors_for_same_slot(self):
        """
        Test finding multiple tutors available for the same specific slot.
        """
        desired_day = 'MON'
        desired_start = time(10, 30)
        desired_end = time(11, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertIn(self.tutor1, found_tutors) # Alice (9-12)
        self.assertIn(self.tutor2, found_tutors) # Bob (10-13)
        self.assertIn(self.tutor3, found_tutors) # Charlie (9:30-11:30)
        self.assertEqual(len(found_tutors), 3)

    def test_no_tutors_available(self):
        """
        Test case where no tutors are available for the desired slot.
        """
        desired_day = 'MON'
        desired_start = time(12, 30) # Between Alice's two slots, and after Bob's first slot
        desired_end = time(13, 30)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertEqual(len(found_tutors), 0)

    def test_overlap_but_not_contained(self):
        """
        Test case where an availability slot overlaps but does not fully contain the desired slot.
        The function should NOT return tutors whose availability doesn't cover the *entire* requested period.
        """
        # Desired: 11:00 AM - 1:00 PM
        # Alice: 9-12 (overlaps, but ends too early)
        # Bob: 10-13 (overlaps, but starts too late if desired_start was earlier)
        # Charlie: 9:30-11:30 (overlaps, but ends too early)
        desired_day = 'MON'
        desired_start = time(11, 0)
        desired_end = time(13, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertIn(self.tutor2, found_tutors) # Bob (10-13) is the only one who covers it fully
        self.assertEqual(len(found_tutors), 1)

    def test_different_day(self):
        """
        Test finding tutors on a different day.
        """
        desired_day = 'TUE'
        desired_start = time(10, 30)
        desired_end = time(12, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertIn(self.tutor1, found_tutors) # Alice (10-13)
        self.assertIn(self.tutor4, found_tutors) # Diana (9-17)
        self.assertEqual(len(found_tutors), 2)

    def test_invalid_time_range(self):
        """
        Test with an invalid desired time range (end time before start time).
        Should return an empty list.
        """
        desired_day = 'MON'
        desired_start = time(15, 0)
        desired_end = time(14, 0) # Invalid range
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertEqual(len(found_tutors), 0)

    def test_edge_case_start_equal_end(self):
        """
        Test with desired start time equal to desired end time.
        Should return an empty list.
        """
        desired_day = 'MON'
        desired_start = time(10, 0)
        desired_end = time(10, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertEqual(len(found_tutors), 0)

    def test_finding_tutor_with_multiple_slots_covering(self):
        """
        Test a scenario where a tutor has multiple slots, and one of them covers the desired time.
        """
        desired_day = 'MON'
        desired_start = time(14, 30)
        desired_end = time(16, 30)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertIn(self.tutor1, found_tutors) # Alice's 2-5 PM slot covers this
        self.assertEqual(len(found_tutors), 1)

    def test_no_availability_for_day(self):
        """
        Test a day for which no tutors have availability.
        """
        desired_day = 'FRI' # No tutor has Friday availability in setUp
        desired_start = time(9, 0)
        desired_end = time(10, 0)
        found_tutors = find_available_tutors(desired_day, desired_start, desired_end)
        self.assertEqual(len(found_tutors), 0)