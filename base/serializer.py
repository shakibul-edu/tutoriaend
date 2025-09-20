from .models import TeacherProfile, AcademicProfile, Qualification, Availability, Grade, Subject
from rest_framework import serializers




class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ['id', 'day_of_week', 'start_time', 'end_time','tutor']
        extra_kwargs = {
            'tutor': {'read_only': True},
            'id': {'read_only': True},
        }

        
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

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'
        extra_kwargs = {
            'grade': {'required': False, 'allow_null': True},
        }
