from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.core.cache import cache

from rest_framework.test import APITestCase
from rest_framework import status

from base.models import TeacherProfile, Subject, ContactRequest, TeacherReview
from seo.cache import invalidate_seo_cache


class SeoTutorDetailViewTestCase(APITestCase):
    """
    Test suite for the public `/api/seo/tutors/<slug>/` endpoint.
    """

    def setUp(self):
        User = get_user_model()
        # Ensure we start with a clean cache
        invalidate_seo_cache()
        cache.clear()

        # Dummy coordinates for location Point
        dummy_location = Point(90.4125, 23.8103)

        # 1. Create a verified tutor with subjects and reviews
        self.verified_user = User.objects.create_user(
            username="verified_tutor",
            email="verified@example.com",
            first_name="Verified",
            last_name="Tutor",
            location=dummy_location,
            is_teacher=True
        )
        self.verified_tutor = TeacherProfile.objects.create(
            user=self.verified_user,
            verified=True,
            bio="Experienced math and science tutor.",
            highest_qualification="honours",
            teaching_mode="online",
            min_salary=6000
        )
        # Add subjects
        self.subject1 = Subject.objects.create(name="Mathematics")
        self.subject2 = Subject.objects.create(name="Physics")
        self.verified_tutor.subject_list.add(self.subject1, self.subject2)

        # Add a review for verified tutor
        student = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            location=dummy_location
        )
        contact = ContactRequest.objects.create(
            student=student,
            teacher=self.verified_tutor,
            student_name="Student",
            student_phone="12345678",
            status="accepted"
        )
        TeacherReview.objects.create(
            contact_request=contact,
            rating=5,
            comment="Excellent teacher!"
        )

        # 2. Create an unverified tutor
        self.unverified_user = User.objects.create_user(
            username="unverified_tutor",
            email="unverified@example.com",
            location=dummy_location,
            is_teacher=True
        )
        self.unverified_tutor = TeacherProfile.objects.create(
            user=self.unverified_user,
            verified=False,
            bio="Unverified tutor bio."
        )

        # 3. Create a banned tutor
        self.banned_user = User.objects.create_user(
            username="banned_tutor",
            email="banned@example.com",
            location=dummy_location,
            is_teacher=True,
            banned=True
        )
        self.banned_tutor = TeacherProfile.objects.create(
            user=self.banned_user,
            verified=True,
            bio="Banned tutor bio."
        )

    def tearDown(self):
        cache.clear()

    def test_retrieve_verified_tutor_public_details(self):
        """
        A guest/unauthenticated user can retrieve public details of a verified tutor by slug.
        """
        # Get slug
        slug = self.verified_tutor.slug
        self.assertIsNotNone(slug)

        url = reverse('seo:seo-tutor-detail', kwargs={'slug': slug})
        
        # Guest request (no credentials)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['name'], "Verified Tutor")
        self.assertEqual(data['bio'], "Experienced math and science tutor.")
        self.assertEqual(data['verified'], True)
        self.assertEqual(data['highest_qualification'], "honours")
        self.assertEqual(data['teaching_mode'], "online")
        self.assertEqual(data['starting_salary'], 6000)
        self.assertEqual(data['rating'], 5.0)
        self.assertEqual(data['review_count'], 1)
        
        # Verify subjects
        subjects = data['subjects_taught']
        self.assertEqual(len(subjects), 2)
        subject_names = [s['name'] for s in subjects]
        self.assertIn("Mathematics", subject_names)
        self.assertIn("Physics", subject_names)
        
        # Verify slug computation in subjects
        for s in subjects:
            self.assertIn('subject_slug', s)
            self.assertIsNotNone(s['subject_slug'])

    def test_retrieve_unverified_tutor_returns_404(self):
        """
        Retrieving an unverified tutor by slug should return 404.
        """
        slug = self.unverified_tutor.slug
        url = reverse('seo:seo-tutor-detail', kwargs={'slug': slug})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_banned_tutor_returns_404(self):
        """
        Retrieving a banned tutor by slug should return 404.
        """
        slug = self.banned_tutor.slug
        url = reverse('seo:seo-tutor-detail', kwargs={'slug': slug})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_caching_and_invalidation(self):
        """
        Verifies that retrieving a tutor caches the result, and saving the profile clears it.
        """
        slug = self.verified_tutor.slug
        url = reverse('seo:seo-tutor-detail', kwargs={'slug': slug})
        cache_key = f'seo:tutors:detail:{slug}'

        # Ensure not in cache initially
        self.assertIsNone(cache.get(cache_key))

        # Retrieve -> populates cache
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['name'], "Verified Tutor")

        # Modify bio directly in DB (bypass signals for test validation)
        TeacherProfile.objects.filter(pk=self.verified_tutor.pk).update(bio="Updated bio without signal.")
        
        # Retrieve again -> should return cached (stale) data
        response = self.client.get(url)
        self.assertEqual(response.data['bio'], "Experienced math and science tutor.")

        # Save profile -> triggers signal to invalidate cache
        self.verified_tutor.bio = "Updated bio with signal."
        self.verified_tutor.save()

        # Cache key should be cleared
        self.assertIsNone(cache.get(cache_key))

        # Retrieve again -> should return fresh data
        response = self.client.get(url)
        self.assertEqual(response.data['bio'], "Updated bio with signal.")


class SeoOtherDetailViewsTestCase(APITestCase):
    """
    Test suite for location, subject, and class detail endpoints.
    """

    def setUp(self):
        User = get_user_model()
        cache.clear()

        dummy_location = Point(90.4125, 23.8103)

        # Create user with location slug
        self.user = User.objects.create_user(
            username="teacher_with_loc",
            email="teacherloc@example.com",
            location=dummy_location,
            is_teacher=True,
            location_name="Dhaka",
            location_slug="dhaka"
        )
        self.tutor = TeacherProfile.objects.create(
            user=self.user,
            verified=True
        )

        from base.models import Grade
        self.grade = Grade.objects.create(name="Class 10", sequence=10)
        self.subject = Subject.objects.create(name="Accounting - Class 10")
        
        self.tutor.grade_list.add(self.grade)
        self.tutor.subject_list.add(self.subject)

    def tearDown(self):
        cache.clear()

    def test_location_detail_success_and_404(self):
        # 1. Success case
        url = reverse('seo:seo-location-detail', kwargs={'slug': 'dhaka'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location_name'], "Dhaka")
        self.assertEqual(response.data['location_slug'], "dhaka")

        # 2. 404 case (querying an invalid location slug like a subject name)
        url = reverse('seo:seo-location-detail', kwargs={'slug': 'accounting-class-10'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Ensure it returns JSON
        self.assertIn('detail', response.data)

    def test_subject_detail_success_and_404(self):
        # 1. Success case
        url = reverse('seo:seo-subject-detail', kwargs={'slug': 'accounting-class-10'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Accounting - Class 10")
        self.assertEqual(response.data['subject_slug'], "accounting-class-10")

        # 2. 404 case
        url = reverse('seo:seo-subject-detail', kwargs={'slug': 'dhaka'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_class_detail_success_and_404(self):
        # 1. Success case
        url = reverse('seo:seo-class-detail', kwargs={'slug': 'class-10'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Class 10")
        self.assertEqual(response.data['class_slug'], "class-10")

        # 2. 404 case
        url = reverse('seo:seo-class-detail', kwargs={'slug': 'dhaka'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

