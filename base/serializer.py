from .models import TeacherProfile, AcademicProfile, Qualification, Availability, Grade, Subject
from rest_framework import serializers

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ['id', 'days_of_week', 'start_time', 'end_time','tutor']
        extra_kwargs = {
            'tutor': {'read_only': True},
            'id': {'read_only': True},
        }
    
    def validate(self, data):
        # Time validation is still handled here
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be after the start time."}
            )
        # The unique check will be done in the viewset or view
        return data

        
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
            'id': {'read_only': True},
            'teacher': {'read_only': True},
        }
    def validate_certificates(self, value):
        # 1. File Type Validation
        file_name = value.name.lower()
        if not (file_name.endswith('.pdf') or
                file_name.endswith('.jpg') or
                file_name.endswith('.jpeg') or
                file_name.endswith('.png')):
            raise serializers.ValidationError("Only PDF and image files (JPG, JPEG, PNG) are allowed.")

        # 2. File Size Validation (e.g., limit to 5 MB)
        max_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 5 MB.")

        return value


class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = '__all__'
        extra_kwargs = {
            'validated': {'read_only': True},
            'id': {'read_only': True},
            'teacher': {'read_only': True},
        }
    def validate_certificates(self, value):
        # 1. File Type Validation
        file_name = value.name.lower()
        if not (file_name.endswith('.pdf') or
                file_name.endswith('.jpg') or
                file_name.endswith('.jpeg') or
                file_name.endswith('.png')):
            raise serializers.ValidationError("Only PDF and image files (JPG, JPEG, PNG) are allowed.")

        # 2. File Size Validation (e.g., limit to 5 MB)
        max_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 5 MB.")

        return value

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
