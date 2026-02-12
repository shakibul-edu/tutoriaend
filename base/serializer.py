from .models import (TeacherProfile, AcademicProfile, Qualification,
     Availability, Grade, Subject, JobPost, BidJob, JobPostAvailability
     , ContactRequest, TeacherReview, Medium)
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .utils import calculate_distance

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

class MediumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medium
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'
        extra_kwargs = {
            'grade': {'required': False, 'allow_null': True},
        }


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


class JobPostSerializer(serializers.ModelSerializer):
    availability = JobPostAvailabilitySerializer(many=True, read_only=True, source='availabilities')
    grade = GradeSerializer(read_only=True)
    subject_list = SubjectSerializer(read_only=True, many=True)
    medium = MediumSerializer(read_only=True)
    bids_count = serializers.IntegerField(read_only=True)
    editable = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    posted_by_name = serializers.SerializerMethodField()
    is_biddable = serializers.SerializerMethodField()

    # ---------- WRITE (input) ----------
    grade_id = serializers.PrimaryKeyRelatedField(
        queryset=Grade.objects.all(),
        source="grade",
        write_only=True,
        required=False
    )
    medium_id = serializers.PrimaryKeyRelatedField(
        queryset=Medium.objects.all(),
        source="medium",
        write_only=True,
        required=False
    )
    subject_ids = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        source="subject_list",
        many=True,
        write_only=True,
        required=False
    )
    class Meta:
        model = JobPost
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'posted_by': {'read_only': True},
        }
    
    def validate(self, data):
        user = self.context["request"].user

        if self.instance is None:
            open_posts_count = JobPost.objects.filter(
                posted_by=user,
                status="open"
            ).count()

            if open_posts_count > 2:
                raise serializers.ValidationError(
                    {"detail": "You cannot have more than 2 open job posts."}
                )

        return data

    def get_editable(self, obj):
        return obj.posted_by == self.context["request"].user


    def get_posted_by_name(self, obj):
        return obj.posted_by.get_full_name()


    def get_distance(self, obj):
        user = self.context["request"].user
        if user.location and obj.posted_by.location:
            return calculate_distance(user.location, obj.posted_by.location)
        return None

    def get_is_biddable(self, obj):
        request = self.context.get("request")
        user = request.user if request else None

        if not user or not user.is_authenticated:
            return False

        # User must be a teacher
        teacher = getattr(user, "teacher_profile", None)
        if not teacher:
            return False

        # Cannot bid on own job
        if obj.posted_by_id == user.id:
            return False

        # Job must be open
        if obj.status != "open":
            return False

        # Prevent duplicate bid (optimized)
        return not obj.bids.filter(tutor_id=teacher.id).exists()


class BidJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidJob
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
            "tutor": {"read_only": True},
        }

    def validate(self, attrs):
        request = self.context["request"]
        tutor = getattr(request.user, "teacher_profile", None)

        # 🔹 UPDATE (PATCH / PUT)
        if self.instance:
            return attrs

        # 🔹 CREATE only logic
        job = attrs.get("job")

        if not job:
            raise serializers.ValidationError({"job": "Job is required."})

        if not tutor:
            raise serializers.ValidationError(
                {"detail": "Only teachers can place bids."}
            )

        if BidJob.objects.filter(job=job, tutor=tutor).exists():
            raise serializers.ValidationError(
                {"detail": "You have already placed a bid on this job."}
            )

        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["teacher_phone"] = (
            instance.tutor.phone if instance.tutor else None
        )
        return representation

    
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

        # Get status safely
        status = (
            instance.get('status')
            if isinstance(instance, dict)
            else getattr(instance, 'status', None)
        )

        teacher_obj = getattr(instance, 'teacher', None)
        student_obj = getattr(instance, 'student', None)

        teacher_email = None
        teacher_phone = None

        if teacher_obj:
            teacher_email = getattr(teacher_obj, 'email', None)

            if teacher_email is None:
                teacher_user = getattr(teacher_obj, 'user', None)
                teacher_email = getattr(teacher_user, 'email', None)

            # Phone only if accepted
            if status == 'accepted':
                if hasattr(teacher_obj, 'phone'):
                    teacher_phone = getattr(teacher_obj, 'phone', None)
                else:
                    teacher_profile = getattr(teacher_obj, 'teacher_profile', None)
                    teacher_phone = (
                        getattr(teacher_profile, 'phone', None)
                        if teacher_profile else None
                    )

        representation['teacher_email'] = teacher_email
        representation['student_email'] = getattr(student_obj, 'email', None)

        if status == 'accepted':
            representation['teacher_phone'] = teacher_phone

        return representation


class TeacherReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherReview
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True}
        }
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        contact_obj = getattr(instance, 'contact_request', None)
        representation['student_name'] = (
            contact_obj.student.get_full_name() if contact_obj and contact_obj.student else ""
        )
        representation['tutor_id'] = (
            contact_obj.teacher.id if contact_obj and contact_obj.teacher else ""
        )
        return representation
   