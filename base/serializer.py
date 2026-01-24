from .models import (TeacherProfile, AcademicProfile, Qualification,
     Availability, Grade, Subject, JobPost, BidJob, JobPostAvailability
     , ContactRequest)
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

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
        # Ensure unique availability for the same tutor, day, and time range
        user = self.context['request'].user
        days_of_week = data.get('days_of_week')
        if start_time and end_time and days_of_week:
            exists = Availability.objects.filter(
                tutor__user=user,
                days_of_week=days_of_week,
                start_time=start_time,
                end_time=end_time
            ).exists()
            if exists:
                raise serializers.ValidationError(
                    {"detail": "This availability slot already exists for this tutor."}
                )

        return data



@extend_schema_serializer(
    examples = [
         OpenApiExample(
            'Teacher Profile Example',
            summary='Response Example',
            description='An example representation of a teacher profile with related fields.',
            value={
                "id": 43,
                "verified": False,
                "bio": "This is my first bio",
                "min_salary": 10400,
                "experience_years": 0,
                "gender": "male",
                "teaching_mode": "online",
                "preferred_distance": 5,
                "user": 1,
                "subject_list": [
                {
                    "id": 2,
                    "name": "Mathmatics"
                }
                ],
                "grade_list": [
                {
                    "id": 1,
                    "name": "Class 6th"
                }
                ],
                "medium_list": [
                {
                    "id": 1,
                    "name": "English"
                }
                ]
            },
                        response_only=True, # This example is only for responses
        ),
    ]
)
class TeacherProfileSerializer(serializers.ModelSerializer):
    availability = AvailabilitySerializer(many=True, read_only=True, source='availability_set')
    
    
   

    class Meta:
        model = TeacherProfile
        fields = '__all__'
        extra_kwargs = {
            'verified': {'read_only': True},
            'user': {'read_only': True},
        }

    def validate(self, data):
        teacher = TeacherProfile.objects.filter(user=self.context['request'].user).exists()
        if teacher and self.instance is None:
            raise serializers.ValidationError({"detail": "A teacher profile already exists for this user."})
        return data

    def to_representation(self, instance: TeacherProfile):
        representation = super().to_representation(instance)
        representation['name'] = instance.user.get_full_name() if instance.user else ""
        representation['grade_list'] = [{"id": grade.id, "name": grade.name} for grade in instance.grade_list.all()]
        representation['subject_list'] = [{"id": subject.id, "name": subject.name} for subject in instance.subject_list.all()]
        representation['medium_list'] = [{"id": medium.id, "name": medium.name} for medium in instance.medium_list.all()]
        return representation


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

class JobPostSerializer(serializers.ModelSerializer):
    availability = AvailabilitySerializer(many=True, read_only=True, source='jobpostavailability_set')
    class Meta:
        model = JobPost
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'posted_by': {'read_only': True},
            'status': {'read_only': True},
        }
    
    def validate(self, data):
        # Ensure that the user does not have more than 5 active job posts
        user = self.context['request'].user
        active_posts_count = JobPost.objects.filter(posted_by=user, status='active').count()
        if active_posts_count >= 2:
            raise serializers.ValidationError({"detail": "You cannot have more than 2 active job posts."})
        return data


class BidJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidJob
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'tutor': {'read_only': True},
        }
    
    def validate(self, data):
        tutor = self.context['request'].user
        job_post = self.context['job_post']
        
        # Check if the tutor has already placed a bid on this job post
        if BidJob.objects.filter(tutor=tutor, job_post=job_post).exists():
            raise serializers.ValidationError({"detail": "You have already placed a bid on this job post."})
        
        return data
    
class JobPostAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPostAvailability
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
        }
    
    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be after the start time."}
            )
        return data
    
class ContactRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'student': {'read_only': True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.status == 'accepted':
            try:
                teacher_profile = instance.teacher
                representation['teacher_phone'] = teacher_profile.phone if hasattr(teacher_profile, 'phone') else None
            except TeacherProfile.DoesNotExist:
                representation['teacher_phone'] = None
        return representation