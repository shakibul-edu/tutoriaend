from .models import TeacherProfile, AcademicProfile, Qualification, Availability
from rest_framework import serializers




class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = '__all__'

        
class TeacherProfileSerializer(serializers.ModelSerializer):
    availability = AvailabilitySerializer(many=True, read_only=True, source='availability_set')
    class Meta:
        model = TeacherProfile
        fields = '__all__'
        extra_kwargs = {
            'verified': {'read_only': True},
        }


class AcademicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicProfile
        fields = '__all__'
        extra_kwargs = {
            'validated': {'read_only': True},
        }


class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = '__all__'
        extra_kwargs = {
            'validated': {'read_only': True},
        }
