from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from base.custom_permission import IsAuthenticatedAndNotBanned
from base.models import JobPost, BidJob, JobPostAvailability
from base.serializer import JobPostSerializer, BidJobSerializer, JobPostAvailabilitySerializer
from rest_framework.response import Response


class JobPostViewSet(ModelViewSet):
    """
    A viewset for viewing and editing job posts.
    """
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]

    def get_queryset(self):
        user = self.request.user
        return JobPost.objects.filter(posted_by=user)
    
    def perform_create(self, serializer):
        return super().perform_create(serializer.save(posted_by=self.request.user))
    
class BidJobViewSet(ModelViewSet):
    """
    A viewset for viewing and editing bids on job posts.
    """
    serializer_class = BidJobSerializer
    permission_classes = [IsAuthenticatedAndNotBanned]

    def get_queryset(self):
        user = self.request.user
        return BidJob.objects.filter(tutor=user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        job_post_id = self.request.data.get('job_post')
        if job_post_id:
            try:
                job_post = JobPost.objects.get(id=job_post_id)
                context['job_post'] = job_post
            except JobPost.DoesNotExist:
                pass
        return context
    
    def perform_create(self, serializer):
        return super().perform_create(serializer.save(tutor=self.request.user))
    
class JobPostAvailabilityViewSet(ModelViewSet):
    """
    A viewset for viewing and editing job post availability.
    """
    serializer_class = JobPostAvailabilitySerializer
    permission_classes = [IsAuthenticatedAndNotBanned]

    def get_queryset(self):
        user = self.request.user
        return JobPostAvailability.objects.filter(job_post__posted_by=user)
    
    def perform_create(self, serializer):
        return super().perform_create(serializer.save())
