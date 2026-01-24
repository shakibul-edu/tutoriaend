from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter


app_name = 'base'

router = DefaultRouter()
router.register(r'teacher-profile', views.TeacherProfileViewSet, basename='teacher_profile')
router.register(r'availability', views.AvailabilityViewSet, basename='availability')
router.register(r'academic-profile', views.AcademicProfileViewSet, basename='academic_profile')
router.register(r'qualification', views.QualificationViewSet, basename='qualification')
router.register(r'job-post', views.JobPostViewSet, basename='job_post')
router.register(r'bid-job', views.BidJobViewSet, basename='bid_job')
router.register(r'job-post-availability', views.JobPostAvailabilityViewSet, basename='job_post_availability')
router.register(r'contact-request', views.ContactRequestViewSet, basename='contact_request')




urlpatterns = [
    path('', views.home, name='home'),
    path('protected/', views.protected_view, name='protected_view'),
    path('set-location/', views.set_location, name='set_location'),
    path('get-location/', views.get_location, name='get_location'),
    path('mediums/', views.get_mediums, name='get_mediums'),
    path('grade-by-medium/', views.get_grades_by_medium, name='get_grade_by_medium'),
    path('subject-by-grade/', views.get_subjects_by_grade, name='get_subject_by_grade'),
    path('teacher/full-profile/<int:pk>/', views.get_teacher_full_profile, name='get_teacher_full_profile'),
    path('filter-teachers/', views.filter_teachers, name='filter_teachers'),
]
urlpatterns += router.urls