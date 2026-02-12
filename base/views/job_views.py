from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework import status
from base.custom_permission import IsAuthenticatedAndNotBanned, IsJobOwner
from base.models import JobPost, BidJob, JobPostAvailability
from base.serializer import JobPostSerializer, BidJobSerializer, JobPostAvailabilitySerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework.exceptions import PermissionDenied


from django.db.models import Count

class JobPostViewSet(ModelViewSet):
    """
    ViewSet for creating, listing, and managing job posts.
    """
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticatedAndNotBanned, IsJobOwner]

    def get_queryset(self):

        queryset = (
            JobPost.objects
            .select_related(
                "posted_by",
                "medium",
                "grade",
            )
            .prefetch_related(
                "subject_list",
                "availabilities",
                "bids"
            )
            .annotate(
                bids_count=Count("bids")
            )
        )
        dashboard = self.request.query_params.get("dashboard")
        if dashboard == "true":
            queryset = queryset.filter(posted_by=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            posted_by=self.request.user,
            status="open"
        )

    
class BidJobViewSet(ModelViewSet):
    """
    A viewset for viewing and editing bids on job posts.
    """
    serializer_class = BidJobSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]

    def get_queryset(self):
        job_id = self.request.query_params.get('job_id')
        dashboard = self.request.query_params.get("dashboard")
        if job_id:
            return BidJob.objects.filter(job_id=job_id)
        if dashboard == "true":
            user = self.request.user
        
            return (
                BidJob.objects.select_related("job", "tutor__user", "job__posted_by")
                .filter(tutor__user=user)
            )
        return BidJob.objects.select_related("job", "tutor__user", "job__posted_by").all()
        
    def perform_update(self, serializer):
        bid = serializer.instance
        user = self.request.user
        new_status = serializer.validated_data.get("status")

        # If status is not being updated, allow update
        if new_status is None:
            serializer.save()
            return

        # Job owner rules
        if new_status in ["accepted", "rejected"] and user != bid.job.posted_by:
            raise PermissionDenied("Only the job post owner can accept or reject bids.")

        # Tutor rules
        if new_status == "closed" and user != bid.tutor.user:
            raise PermissionDenied("Only the tutor can close the bid.")

        serializer.save()

    
    
    def perform_create(self, serializer):
        tutor = getattr(self.request.user, "teacher_profile", None)
        if not tutor:
            raise PermissionDenied("Only teachers can place bids.")
        return super().perform_create(serializer.save(tutor=tutor))
    





@extend_schema(
    summary="List or create job post availability slots",
    description=(
        "Retrieve or create availability slots for job posts created by the authenticated user. "
        "POST accepts a list of objects with 'start', 'end', 'days', and 'job_post' fields. "
        "Each object will be split into multiple instances, one per day."
    ),
    responses={200: JobPostAvailabilitySerializer(many=True)},
    request=JobPostAvailabilitySerializer(many=True),
    examples=[
        OpenApiExample(
            name="Job Post Availability List Example",
            value=[
                {
                    "start": "09:00",
                    "end": "12:00",
                    "days": ["MO", "WE", "FR"],
                    "job_post": 1
                },
                {
                    "start": "14:00",
                    "end": "17:00",
                    "days": ["TU", "TH"],
                    "job_post": 1
                }
            ],
            request_only=True,
            response_only=False,
        )
    ]
)
class JobPostAvailabilityViewSet(ModelViewSet):
    """
    A viewset for viewing and editing availability slots for job posts.
    Accepts a list of availability objects with 'start', 'end', 'days', and 'job_post' fields.
    Each instance in the model should have only one day, so this viewset will
    split each input object into multiple instances, one per day.
    """
    serializer_class = JobPostAvailabilitySerializer
    permission_classes = [IsAuthenticatedAndNotBanned]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', None), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        return JobPostAvailability.objects.filter(job_post__posted_by=user)
    
    def create(self, request):
        data = request.data
        if not isinstance(data, list):
            data = [data]
        instances = []
        errors = []
        
        for entry in data:
            if not isinstance(entry, dict):
                errors.append({'error': 'Each entry must be a dictionary.'})
                continue
            
            job_post_id = entry.get('job_post')
            if not job_post_id:
                errors.append({'error': 'job_post field is required.'})
                continue
            
            try:
                job_post = JobPost.objects.get(id=job_post_id, posted_by=request.user)
            except JobPost.DoesNotExist:
                errors.append({'error': f'JobPost with id {job_post_id} not found or you do not have permission to edit it.'})
                continue
            JobPostAvailability.objects.filter(job_post=job_post).delete()
            start = entry.get('start')
            end = entry.get('end')
            days = entry.get('days', [])
            
            for day in days:
                instance_data = {
                    'start_time': start,
                    'end_time': end,
                    'days_of_week': day,
                    'job_post': job_post_id,
                }
                single_serializer = self.get_serializer(data=instance_data)
                if single_serializer.is_valid():
                    instances.append(single_serializer.save(job_post=job_post))
                else:
                    errors.append(single_serializer.errors)
        
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instances, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
