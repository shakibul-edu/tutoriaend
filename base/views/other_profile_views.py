from copy import deepcopy
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from base.models import TeacherProfile, AcademicProfile, Qualification
from base.serializer import  AcademicProfileSerializer, QualificationSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from base.models import AcademicProfile, TeacherProfile
from base.serializer import AcademicProfileSerializer
from rest_framework.parsers import MultiPartParser


class AcademicProfileViewSet(viewsets.ModelViewSet):
    serializer_class = AcademicProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

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
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        if teacher:
            return Qualification.objects.filter(teacher=teacher)
        return Qualification.objects.none()

    def perform_create(self, serializer):
        teacher = TeacherProfile.objects.filter(user=self.request.user).first()
        serializer.save(teacher=teacher)
