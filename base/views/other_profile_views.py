from copy import deepcopy
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from base.models import CustomUser, TeacherProfile, AcademicProfile, Qualification
from base.serializer import  AcademicProfileSerializer, ContactRequestSerializer, QualificationSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from base.custom_permission import IsAuthenticatedAndNotBanned
from base.models import AcademicProfile, TeacherProfile, ContactRequest, UserDashboard
from base.serializer import AcademicProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from rest_framework.exceptions import ValidationError


class AcademicProfileViewSet(viewsets.ModelViewSet):
    serializer_class = AcademicProfileSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if teacher:
            return AcademicProfile.objects.filter(teacher=teacher)
        return AcademicProfile.objects.none()

    def perform_create(self, serializer):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        serializer.save(teacher=teacher)


class QualificationViewSet(viewsets.ModelViewSet):
    serializer_class = QualificationSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if teacher:
            return Qualification.objects.filter(teacher=teacher)
        return Qualification.objects.none()

    def perform_create(self, serializer):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        serializer.save(teacher=teacher)


class ContactRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ContactRequestSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        # Return contact requests where the user is either a student or a teacher (both fields are CustomUser)
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if teacher is None:
            return ContactRequest.objects.filter(student=self.request.user)
        return ContactRequest.objects.filter(
            Q(student=self.request.user) | Q(teacher=teacher)
        ).distinct()

    def perform_create(self, serializer):
        user_dashboard, created = UserDashboard.objects.get_or_create(user=self.request.user)

        if created and user_dashboard.total_pending_requests >= 2:
            raise ValidationError({
                "detail": "You cannot have more than 2 pending contact requests."
            })

        # Save the contact request first
        serializer.save(student=self.request.user)

        # Then update dashboard counters
        user_dashboard.total_requests_sent += 1
        user_dashboard.total_pending_requests += 1
        user_dashboard.save()

    def perform_update(self, serializer):
        # Get the old status before update
        old_status = serializer.instance.status
        
        # Save the updated contact request
        instance = serializer.save()
        
        # If status changed from pending, decrement pending counter
        if old_status == 'pending' and instance.status != 'pending':
            student = instance.student
            user_dashboard, created = UserDashboard.objects.get_or_create(user=student)
            if user_dashboard.total_pending_requests > 0:
                user_dashboard.total_pending_requests -= 1
                user_dashboard.save()
