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
from base.models import AcademicProfile, TeacherProfile, ContactRequest
from base.serializer import AcademicProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q


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
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if teacher:
        # Return contact requests where the user is either a student or a teacher
            return ContactRequest.objects.filter(
                Q(student=self.request.user) | Q(teacher=teacher)
            ).distinct()
        else:
            return ContactRequest.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        
        serializer.save(student=self.request.user)
